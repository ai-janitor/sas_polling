"""
=============================================================================
BASE REPORT GENERATOR CLASS
=============================================================================
Purpose: Abstract base class for all report generators
Framework: ABC (Abstract Base Classes) with common functionality

STRICT REQUIREMENTS:
- Abstract methods that all reports must implement
- Common utility functions for file generation
- Standardized parameter validation
- Consistent output format handling
- Error handling and logging patterns

ABSTRACT METHODS (must be implemented by subclasses):
- generate(): Main report generation logic
- validate_parameters(): Validate input parameters
- get_output_formats(): Return supported output formats
- get_estimated_duration(): Return estimated processing time

COMMON FUNCTIONALITY:
- Parameter loading and validation
- Output file generation (HTML, PDF, CSV, XLS)
- Error handling with detailed messages
- Progress tracking for long-running reports
- Temporary file management

OUTPUT FORMAT SUPPORT:
- HTML: Interactive reports with Plotly charts
- PDF: Print-ready formatted documents
- CSV: Raw data export
- XLS: Excel-compatible spreadsheets
- JSON: Structured data output

UTILITY METHODS:
- load_mock_data(): Load CSV data for report
- generate_html(): Create HTML output with templates
- generate_pdf(): Convert HTML to PDF
- generate_csv(): Export data as CSV
- generate_xls(): Create Excel files
- create_plotly_chart(): Generate interactive charts

ERROR HANDLING:
- Parameter validation errors
- Data loading failures
- File generation errors
- Timeout handling for long reports
- Resource cleanup on failures

CONFIGURATION:
- REPORTS_DATA_PATH: Path to mock data files
- REPORTS_TEMPLATE_PATH: Path to HTML templates
- REPORTS_OUTPUT_PATH: Temporary output directory
- REPORT_TIMEOUT: Maximum execution time
=============================================================================
"""

import os
import json
import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from jinja2 import Environment, FileSystemLoader, Template
import weasyprint
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import tempfile
import uuid


class ReportGenerationError(Exception):
    """Custom exception for report generation errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "REPORT_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class BaseReport(ABC):
    """
    Abstract base class for all report generators.
    
    Provides common functionality for data loading, file generation,
    and output format handling while requiring subclasses to implement
    report-specific logic.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger = None):
        """
        Initialize base report with configuration and logger.
        
        Args:
            config: Configuration dictionary from environment
            logger: Logger instance for this report
        """
        self.config = config
        self.logger = logger or self._setup_logger()
        self.report_id = str(uuid.uuid4())
        self.start_time = None
        self.end_time = None
        self.generated_files = []
        
        # Load configuration
        self.data_path = config.get('REPORTS_DATA_PATH', '/app/mock-data')
        self.template_path = config.get('REPORTS_TEMPLATE_PATH', '/app/templates')
        self.output_path = config.get('REPORTS_OUTPUT_PATH', '/tmp/datafit/output')
        self.timeout = int(config.get('REPORT_TIMEOUT', 300))
        
        # Ensure output directory exists
        Path(self.output_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader(self.template_path),
            autoescape=True
        )
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the report."""
        logger = logging.getLogger(f"{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    def generate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the report with given parameters.
        
        Args:
            parameters: Report-specific parameters from job request
            
        Returns:
            Dictionary containing generated file paths and metadata
            
        Raises:
            ReportGenerationError: If report generation fails
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate input parameters for the report.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    @abstractmethod
    def get_output_formats(self) -> List[str]:
        """
        Return list of supported output formats for this report.
        
        Returns:
            List of format strings (e.g., ['html', 'pdf', 'csv'])
        """
        pass
    
    @abstractmethod
    def get_estimated_duration(self, parameters: Dict[str, Any]) -> int:
        """
        Estimate report generation time in seconds.
        
        Args:
            parameters: Report parameters
            
        Returns:
            Estimated duration in seconds
        """
        pass
    
    def load_mock_data(self, filename: str) -> pd.DataFrame:
        """
        Load mock data from CSV file.
        
        Args:
            filename: CSV filename in the data directory
            
        Returns:
            Pandas DataFrame with the data
            
        Raises:
            ReportGenerationError: If file cannot be loaded
        """
        try:
            file_path = Path(self.data_path) / filename
            if not file_path.exists():
                raise ReportGenerationError(
                    f"Data file not found: {filename}",
                    "DATA_FILE_NOT_FOUND",
                    {"file_path": str(file_path)}
                )
            
            df = pd.read_csv(file_path)
            self.logger.info(f"Loaded {len(df)} rows from {filename}")
            return df
            
        except pd.errors.EmptyDataError:
            raise ReportGenerationError(
                f"Data file is empty: {filename}",
                "DATA_FILE_EMPTY"
            )
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to load data file {filename}: {str(e)}",
                "DATA_LOAD_ERROR",
                {"original_error": str(e)}
            )
    
    def create_plotly_chart(self, data: pd.DataFrame, chart_type: str, 
                           title: str, **kwargs) -> go.Figure:
        """
        Create a Plotly chart from data.
        
        Args:
            data: DataFrame containing chart data
            chart_type: Type of chart ('line', 'bar', 'scatter', 'pie')
            title: Chart title
            **kwargs: Additional chart-specific parameters
            
        Returns:
            Plotly Figure object
        """
        try:
            # Chart configuration from config
            theme = self.config.get('PLOTLY_THEME', 'plotly_white')
            width = int(self.config.get('PLOTLY_WIDTH', 800))
            height = int(self.config.get('PLOTLY_HEIGHT', 600))
            show_legend = self.config.get('PLOTLY_SHOW_LEGEND', 'true').lower() == 'true'
            
            if chart_type == 'line':
                fig = px.line(data, title=title, **kwargs)
            elif chart_type == 'bar':
                fig = px.bar(data, title=title, **kwargs)
            elif chart_type == 'scatter':
                fig = px.scatter(data, title=title, **kwargs)
            elif chart_type == 'pie':
                fig = px.pie(data, title=title, **kwargs)
            else:
                raise ReportGenerationError(
                    f"Unsupported chart type: {chart_type}",
                    "INVALID_CHART_TYPE"
                )
            
            # Apply theme and layout
            fig.update_layout(
                template=theme,
                width=width,
                height=height,
                showlegend=show_legend,
                title={'x': 0.5, 'xanchor': 'center'}
            )
            
            return fig
            
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to create chart: {str(e)}",
                "CHART_CREATION_ERROR",
                {"chart_type": chart_type, "original_error": str(e)}
            )
    
    def generate_html(self, template_name: str, context: Dict[str, Any], 
                     output_filename: str) -> str:
        """
        Generate HTML output using Jinja2 template.
        
        Args:
            template_name: Name of template file
            context: Template context variables
            output_filename: Output file name
            
        Returns:
            Path to generated HTML file
        """
        try:
            template = self.template_env.get_template(template_name)
            html_content = template.render(**context)
            
            output_path = Path(self.output_path) / f"{self.report_id}_{output_filename}"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.generated_files.append(str(output_path))
            self.logger.info(f"Generated HTML file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate HTML: {str(e)}",
                "HTML_GENERATION_ERROR",
                {"template": template_name, "original_error": str(e)}
            )
    
    def generate_pdf(self, html_file_path: str, output_filename: str) -> str:
        """
        Generate PDF from HTML file.
        
        Args:
            html_file_path: Path to HTML file
            output_filename: Output PDF filename
            
        Returns:
            Path to generated PDF file
        """
        try:
            output_path = Path(self.output_path) / f"{self.report_id}_{output_filename}"
            
            # PDF configuration from config
            page_size = self.config.get('PDF_PAGE_SIZE', 'A4')
            orientation = self.config.get('PDF_ORIENTATION', 'portrait')
            
            html_doc = weasyprint.HTML(filename=html_file_path)
            html_doc.write_pdf(
                str(output_path),
                stylesheets=[weasyprint.CSS(string=f'@page {{ size: {page_size} {orientation}; }}')]
            )
            
            self.generated_files.append(str(output_path))
            self.logger.info(f"Generated PDF file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate PDF: {str(e)}",
                "PDF_GENERATION_ERROR",
                {"html_file": html_file_path, "original_error": str(e)}
            )
    
    def generate_csv(self, data: pd.DataFrame, output_filename: str) -> str:
        """
        Generate CSV file from DataFrame.
        
        Args:
            data: DataFrame to export
            output_filename: Output CSV filename
            
        Returns:
            Path to generated CSV file
        """
        try:
            output_path = Path(self.output_path) / f"{self.report_id}_{output_filename}"
            
            delimiter = self.config.get('CSV_DELIMITER', ',')
            data.to_csv(output_path, sep=delimiter, index=False)
            
            self.generated_files.append(str(output_path))
            self.logger.info(f"Generated CSV file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate CSV: {str(e)}",
                "CSV_GENERATION_ERROR",
                {"original_error": str(e)}
            )
    
    def generate_excel(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
                      output_filename: str) -> str:
        """
        Generate Excel file from DataFrame(s).
        
        Args:
            data: DataFrame or dict of DataFrames for multiple sheets
            output_filename: Output Excel filename
            
        Returns:
            Path to generated Excel file
        """
        try:
            output_path = Path(self.output_path) / f"{self.report_id}_{output_filename}"
            
            if isinstance(data, pd.DataFrame):
                # Single sheet
                sheet_name = self.config.get('EXCEL_SHEET_NAME', 'Report Data')
                data.to_excel(output_path, sheet_name=sheet_name, index=False)
            else:
                # Multiple sheets
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for sheet_name, df in data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            self.generated_files.append(str(output_path))
            self.logger.info(f"Generated Excel file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate Excel: {str(e)}",
                "EXCEL_GENERATION_ERROR",
                {"original_error": str(e)}
            )
    
    def generate_json(self, data: Dict[str, Any], output_filename: str) -> str:
        """
        Generate JSON file from data.
        
        Args:
            data: Data to serialize as JSON
            output_filename: Output JSON filename
            
        Returns:
            Path to generated JSON file
        """
        try:
            output_path = Path(self.output_path) / f"{self.report_id}_{output_filename}"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.generated_files.append(str(output_path))
            self.logger.info(f"Generated JSON file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate JSON: {str(e)}",
                "JSON_GENERATION_ERROR",
                {"original_error": str(e)}
            )
    
    def cleanup_files(self):
        """Clean up generated files for this report."""
        for file_path in self.generated_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"Cleaned up file: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup file {file_path}: {e}")
        
        self.generated_files.clear()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics for this report.
        
        Returns:
            Dictionary with execution statistics
        """
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            "report_id": self.report_id,
            "report_type": self.__class__.__name__,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "generated_files": len(self.generated_files),
            "file_paths": self.generated_files.copy()
        }
    
    def run_with_timeout(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run report generation with timeout handling.
        
        Args:
            parameters: Report parameters
            
        Returns:
            Dictionary with generated files and metadata
            
        Raises:
            ReportGenerationError: If generation fails or times out
        """
        self.start_time = datetime.now()
        
        try:
            # Validate parameters first
            validation_errors = self.validate_parameters(parameters)
            if validation_errors:
                raise ReportGenerationError(
                    "Parameter validation failed",
                    "VALIDATION_ERROR",
                    {"errors": validation_errors}
                )
            
            self.logger.info(f"Starting report generation: {self.__class__.__name__}")
            self.logger.info(f"Parameters: {parameters}")
            
            # Generate report
            result = self.generate(parameters)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            self.logger.info(f"Report generation completed in {duration:.2f} seconds")
            
            # Add execution stats to result
            result["execution_stats"] = self.get_execution_stats()
            
            return result
            
        except ReportGenerationError:
            self.end_time = datetime.now()
            raise
        except Exception as e:
            self.end_time = datetime.now()
            self.logger.error(f"Unexpected error in report generation: {e}")
            raise ReportGenerationError(
                f"Unexpected error: {str(e)}",
                "UNEXPECTED_ERROR",
                {"original_error": str(e)}
            )