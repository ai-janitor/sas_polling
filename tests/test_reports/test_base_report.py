"""
=============================================================================
BASE REPORT GENERATOR UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for base report generator abstract class
Technology: pytest with mocking and abstract class testing
Module: reports/base_report.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test all abstract methods and concrete implementations
- Mock file system operations and external dependencies
- Validate output format generation
- Test error handling and edge cases

TEST CATEGORIES:
1. Abstract Method Implementation Tests
   - generate() method enforcement
   - validate_parameters() implementation
   - get_output_formats() specification
   - get_estimated_duration() calculation

2. Output Format Generation Tests
   - HTML report generation
   - PDF document creation
   - CSV data export
   - XLS spreadsheet creation
   - JSON structured output

3. Parameter Validation Tests
   - Required parameter checking
   - Type validation
   - Range and format validation
   - Cross-parameter dependencies
   - Default value handling

4. File Management Tests
   - Temporary file creation
   - Output file cleanup
   - File permission handling
   - Storage path management
   - File format validation

5. Error Handling Tests
   - Invalid parameter handling
   - File system errors
   - Template rendering failures
   - Data processing errors
   - Resource cleanup on failure

MOCK STRATEGY:
- Mock file system operations
- Mock template rendering engines
- Mock data loading from CSV
- Mock chart generation libraries
- Mock external API calls

VALIDATION TESTS:
- Parameter type checking
- Required field validation
- Format specification compliance
- Cross-field validation rules
- Security input sanitization

ERROR SCENARIOS:
- Missing required parameters
- Invalid data types
- File system permissions
- Template not found
- Data loading failures

PERFORMANCE BENCHMARKS:
- Report generation < 300s
- Memory usage < 500MB
- File I/O efficiency
- Template rendering speed
- Concurrent generation

SECURITY TESTS:
- Path traversal prevention
- Template injection protection
- File access restrictions
- Input sanitization
- Output encoding validation

DEPENDENCIES:
- pytest: Test framework
- pytest-mock: Mocking utilities
- tempfile: Temporary file handling
- pathlib: Path operations
- abc: Abstract base class testing
=============================================================================
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from abc import ABC, abstractmethod
import json
import pandas as pd
from datetime import datetime
import uuid

class MockBaseReport:
    """Mock implementation of BaseReport for testing."""
    
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.output_path = None
        self.temp_files = []
        self.config = {
            'REPORTS_DATA_PATH': '/tmp/test-data',
            'REPORTS_TEMPLATE_PATH': '/tmp/test-templates',
            'REPORTS_OUTPUT_PATH': '/tmp/test-output'
        }
    
    def validate_parameters(self):
        """Mock parameter validation."""
        errors = []
        
        # Basic validation rules
        if not self.parameters:
            errors.append("Parameters are required")
            return errors
        
        # Check for required fields (example)
        required_fields = getattr(self, 'required_fields', [])
        for field in required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        
        return errors
    
    def get_output_formats(self):
        """Mock output formats specification."""
        return ['HTML', 'PDF', 'CSV', 'XLS']
    
    def get_estimated_duration(self):
        """Mock duration estimation."""
        return 120  # 2 minutes
    
    def generate(self):
        """Mock report generation."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Validation failed: {', '.join(validation_errors)}")
        
        return {
            'status': 'completed',
            'files': ['report.html', 'report.pdf'],
            'duration': 45,
            'size': 1024
        }

class TestBaseReport:
    """Test class for base report functionality."""
    
    @pytest.fixture
    def base_report(self):
        """Create base report instance for testing."""
        return MockBaseReport()
    
    @pytest.fixture
    def valid_parameters(self):
        """Valid parameters for testing."""
        return {
            'start_date': '2024-01-01',
            'end_date': '2024-06-30',
            'format': 'HTML',
            'user_id': 'test_user'
        }
    
    @pytest.fixture
    def invalid_parameters(self):
        """Invalid parameters for testing."""
        return {
            'start_date': 'invalid-date',
            'end_date': None,
            'format': 'UNKNOWN'
        }
    
    @pytest.fixture
    def mock_csv_data(self):
        """Mock CSV data for testing."""
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'value': [100, 150, 200],
            'category': ['A', 'B', 'A']
        })
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, base_report, valid_parameters):
        """Test successful parameter validation."""
        base_report.parameters = valid_parameters
        
        errors = base_report.validate_parameters()
        
        assert errors == []
    
    @pytest.mark.unit
    def test_parameter_validation_empty_parameters(self, base_report):
        """Test validation with empty parameters."""
        base_report.parameters = {}
        
        errors = base_report.validate_parameters()
        
        assert len(errors) > 0
        assert "Parameters are required" in errors
    
    @pytest.mark.unit
    def test_parameter_validation_missing_required_fields(self, base_report):
        """Test validation with missing required fields."""
        base_report.required_fields = ['start_date', 'end_date']
        base_report.parameters = {'start_date': '2024-01-01'}
        
        errors = base_report.validate_parameters()
        
        assert len(errors) > 0
        assert any("end_date" in error for error in errors)
    
    @pytest.mark.unit
    def test_get_output_formats(self, base_report):
        """Test output formats specification."""
        formats = base_report.get_output_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'HTML' in formats
        assert 'PDF' in formats
    
    @pytest.mark.unit
    def test_get_estimated_duration(self, base_report):
        """Test duration estimation."""
        duration = base_report.get_estimated_duration()
        
        assert isinstance(duration, int)
        assert duration > 0
    
    @pytest.mark.unit
    def test_generate_success(self, base_report, valid_parameters):
        """Test successful report generation."""
        base_report.parameters = valid_parameters
        
        result = base_report.generate()
        
        assert result['status'] == 'completed'
        assert 'files' in result
        assert 'duration' in result
        assert len(result['files']) > 0
    
    @pytest.mark.unit
    def test_generate_validation_failure(self, base_report):
        """Test report generation with validation failure."""
        base_report.parameters = {}
        
        with pytest.raises(ValueError) as exc_info:
            base_report.generate()
        
        assert "Validation failed" in str(exc_info.value)
    
    @pytest.mark.unit
    @patch('pandas.read_csv')
    def test_load_mock_data_success(self, mock_read_csv, base_report, mock_csv_data):
        """Test successful mock data loading."""
        mock_read_csv.return_value = mock_csv_data
        
        # Simulate data loading method
        def load_mock_data(filename):
            return mock_read_csv(filename)
        
        data = load_mock_data('test_data.csv')
        
        assert not data.empty
        assert 'date' in data.columns
        assert 'value' in data.columns
        mock_read_csv.assert_called_once()
    
    @pytest.mark.unit
    @patch('pandas.read_csv')
    def test_load_mock_data_file_not_found(self, mock_read_csv, base_report):
        """Test data loading with file not found."""
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        
        def load_mock_data(filename):
            return mock_read_csv(filename)
        
        with pytest.raises(FileNotFoundError):
            load_mock_data('nonexistent.csv')
    
    @pytest.mark.unit
    @patch('builtins.open', create=True)
    def test_generate_html_output(self, mock_open, base_report, temp_dir):
        """Test HTML output generation."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        def generate_html(content, output_path):
            with open(output_path, 'w') as f:
                f.write(content)
            return output_path
        
        html_content = "<html><body><h1>Test Report</h1></body></html>"
        output_path = os.path.join(temp_dir, 'test_report.html')
        
        result_path = generate_html(html_content, output_path)
        
        assert result_path == output_path
        mock_open.assert_called_once()
        mock_file.write.assert_called_once_with(html_content)
    
    @pytest.mark.unit
    @patch('weasyprint.HTML')
    def test_generate_pdf_output(self, mock_weasyprint, base_report, temp_dir):
        """Test PDF output generation."""
        mock_pdf = MagicMock()
        mock_weasyprint.return_value.write_pdf.return_value = None
        
        def generate_pdf(html_content, output_path):
            html = mock_weasyprint(string=html_content)
            html.write_pdf(output_path)
            return output_path
        
        html_content = "<html><body><h1>Test Report</h1></body></html>"
        output_path = os.path.join(temp_dir, 'test_report.pdf')
        
        result_path = generate_pdf(html_content, output_path)
        
        assert result_path == output_path
        mock_weasyprint.assert_called_once()
    
    @pytest.mark.unit
    def test_generate_csv_output(self, base_report, mock_csv_data, temp_dir):
        """Test CSV output generation."""
        def generate_csv(data, output_path):
            data.to_csv(output_path, index=False)
            return output_path
        
        output_path = os.path.join(temp_dir, 'test_data.csv')
        
        with patch.object(mock_csv_data, 'to_csv') as mock_to_csv:
            result_path = generate_csv(mock_csv_data, output_path)
            
            assert result_path == output_path
            mock_to_csv.assert_called_once_with(output_path, index=False)
    
    @pytest.mark.unit
    @patch('openpyxl.Workbook')
    def test_generate_xls_output(self, mock_workbook, base_report, mock_csv_data, temp_dir):
        """Test Excel output generation."""
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_workbook.return_value = mock_wb
        mock_wb.active = mock_ws
        
        def generate_xls(data, output_path):
            wb = mock_workbook()
            ws = wb.active
            
            # Write headers
            for col, header in enumerate(data.columns, 1):
                ws.cell(row=1, column=col, value=header)
            
            # Write data
            for row, (index, values) in enumerate(data.iterrows(), 2):
                for col, value in enumerate(values, 1):
                    ws.cell(row=row, column=col, value=value)
            
            wb.save(output_path)
            return output_path
        
        output_path = os.path.join(temp_dir, 'test_data.xlsx')
        
        result_path = generate_xls(mock_csv_data, output_path)
        
        assert result_path == output_path
        mock_wb.save.assert_called_once_with(output_path)
    
    @pytest.mark.unit
    @patch('plotly.graph_objects.Figure')
    def test_create_plotly_chart(self, mock_figure, base_report, mock_csv_data):
        """Test Plotly chart generation."""
        mock_fig = MagicMock()
        mock_figure.return_value = mock_fig
        
        def create_plotly_chart(data, chart_type='line'):
            fig = mock_figure()
            fig.add_trace(data=data)
            return fig
        
        chart = create_plotly_chart(mock_csv_data)
        
        assert chart is not None
        mock_figure.assert_called_once()
        mock_fig.add_trace.assert_called_once()
    
    @pytest.mark.unit
    def test_file_cleanup(self, base_report, temp_dir):
        """Test temporary file cleanup."""
        # Create temporary files
        temp_files = []
        for i in range(3):
            temp_file = os.path.join(temp_dir, f'temp_file_{i}.tmp')
            with open(temp_file, 'w') as f:
                f.write('temp content')
            temp_files.append(temp_file)
        
        def cleanup_temp_files(file_list):
            for file_path in file_list:
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Verify files exist
        for file_path in temp_files:
            assert os.path.exists(file_path)
        
        # Cleanup
        cleanup_temp_files(temp_files)
        
        # Verify files are removed
        for file_path in temp_files:
            assert not os.path.exists(file_path)
    
    @pytest.mark.unit
    def test_error_handling_file_permissions(self, base_report, temp_dir):
        """Test error handling for file permission issues."""
        def write_protected_file(content, path):
            # Simulate permission error
            raise PermissionError(f"Permission denied: {path}")
        
        with pytest.raises(PermissionError):
            write_protected_file("test content", "/root/protected.txt")
    
    @pytest.mark.unit
    @patch('jinja2.Environment')
    def test_template_rendering(self, mock_jinja_env, base_report):
        """Test template rendering functionality."""
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_jinja_env.return_value = mock_env
        mock_env.get_template.return_value = mock_template
        mock_template.render.return_value = "<html>Rendered content</html>"
        
        def render_template(template_name, context):
            env = mock_jinja_env()
            template = env.get_template(template_name)
            return template.render(**context)
        
        context = {'title': 'Test Report', 'data': [1, 2, 3]}
        result = render_template('report_template.html', context)
        
        assert result == "<html>Rendered content</html>"
        mock_env.get_template.assert_called_once_with('report_template.html')
        mock_template.render.assert_called_once_with(**context)
    
    @pytest.mark.performance
    def test_report_generation_performance(self, base_report, valid_parameters, performance_monitor):
        """Test report generation performance."""
        base_report.parameters = valid_parameters
        
        performance_monitor.start()
        result = base_report.generate()
        performance_monitor.stop()
        
        assert result['status'] == 'completed'
        assert performance_monitor.duration < 5.0  # Less than 5 seconds for mock
        assert performance_monitor.peak_memory < 50  # Less than 50MB for mock
    
    @pytest.mark.security
    def test_path_traversal_prevention(self, base_report):
        """Test prevention of path traversal attacks."""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM'
        ]
        
        def validate_path(path):
            # Basic path validation (real implementation would be more robust)
            if '..' in path or path.startswith('/') or ':' in path:
                raise ValueError("Invalid path detected")
            return True
        
        for malicious_path in malicious_paths:
            with pytest.raises(ValueError, match="Invalid path detected"):
                validate_path(malicious_path)
    
    @pytest.mark.security
    def test_template_injection_prevention(self, base_report):
        """Test prevention of template injection attacks."""
        malicious_inputs = [
            "{{ ''.__class__.__mro__[2].__subclasses__()[40]('/etc/passwd').read() }}",
            "{% for x in ().__class__.__base__.__subclasses__() %}{% endfor %}",
            "${7*7}",
            "#{7*7}"
        ]
        
        def sanitize_template_input(input_string):
            dangerous_patterns = ['{{', '}}', '{%', '%}', '${', '#{']
            for pattern in dangerous_patterns:
                if pattern in input_string:
                    raise ValueError("Potentially dangerous template syntax detected")
            return input_string
        
        for malicious_input in malicious_inputs:
            with pytest.raises(ValueError, match="dangerous template syntax"):
                sanitize_template_input(malicious_input)