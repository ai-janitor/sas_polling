"""
=============================================================================
DAILY VALUE AT RISK REPORT GENERATOR
=============================================================================
Purpose: Generate comprehensive daily VaR calculations across all portfolios
Framework: Inherits from base_report.py
Output Formats: HTML, PDF, CSV, XLS

STRICT REQUIREMENTS:
- Load VaR data from mock-data/var_daily.csv
- Support multiple confidence levels (95%, 99%, 99.9%)
- Generate Plotly charts for HTML output
- Calculate VaR by portfolio and aggregate
- Include historical VaR trends
- Validate input parameters

REPORT SECTIONS:
1. Executive Summary
2. Portfolio VaR by Confidence Level
3. Historical VaR Trends (30 days)
4. VaR Components by Asset Class
5. Risk Factor Contributions
6. Data Quality and Assumptions

PARAMETERS:
- calculation_date: Date for VaR calculation
- confidence_level: Statistical confidence (95, 99, 99.9)
- portfolio_filter: Portfolio type filter
- include_charts: Whether to generate visualizations

OUTPUT FILES:
- var_daily_report.html: Interactive HTML with charts
- var_daily_report.pdf: Print-ready PDF version
- var_daily_data.csv: Raw VaR data export
- var_daily_summary.xlsx: Excel workbook with multiple sheets

MOCK DATA STRUCTURE:
var_daily.csv columns:
- date: Calculation date
- portfolio_id: Portfolio identifier
- portfolio_name: Portfolio display name
- asset_class: Asset classification
- confidence_95: VaR at 95% confidence
- confidence_99: VaR at 99% confidence
- confidence_999: VaR at 99.9% confidence
- position_value: Portfolio market value
- volatility: Historical volatility
- risk_factor: Primary risk driver
=============================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from base_report import BaseReport

class VarDailyReport(BaseReport):
    def __init__(self):
        super().__init__()
        self.report_id = "var_daily"
        self.report_name = "Daily Value at Risk Report"
        
    def validate_parameters(self, params):
        """Validate input parameters for VaR report"""
        errors = []
        
        if not params.get('calculation_date'):
            errors.append("Calculation date is required")
        else:
            try:
                calc_date = datetime.strptime(params['calculation_date'], '%Y-%m-%d')
                if calc_date > datetime.now():
                    errors.append("Calculation date cannot be in the future")
            except ValueError:
                errors.append("Invalid date format for calculation_date")
        
        confidence_level = params.get('confidence_level', '99')
        if confidence_level not in ['95', '99', '99.9']:
            errors.append("Confidence level must be 95, 99, or 99.9")
        
        portfolio_filter = params.get('portfolio_filter', 'all')
        valid_filters = ['all', 'equity', 'fixed_income', 'derivatives']
        if portfolio_filter not in valid_filters:
            errors.append(f"Portfolio filter must be one of: {', '.join(valid_filters)}")
        
        return errors
    
    def get_output_formats(self):
        """Return supported output formats"""
        return ['HTML', 'PDF', 'CSV', 'XLS']
    
    def get_estimated_duration(self):
        """Return estimated processing time in seconds"""
        return 120
    
    def load_data(self, params):
        """Load and filter VaR data"""
        try:
            # Load mock VaR data
            data_path = os.path.join(self.get_data_path(), 'var_daily.csv')
            df = pd.read_csv(data_path)
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Filter by calculation date
            calc_date = datetime.strptime(params['calculation_date'], '%Y-%m-%d')
            
            # Get data for the calculation date and previous 30 days for trends
            end_date = calc_date
            start_date = end_date - timedelta(days=30)
            
            filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # Filter by portfolio type if specified
            portfolio_filter = params.get('portfolio_filter', 'all')
            if portfolio_filter != 'all':
                filtered_df = filtered_df[filtered_df['asset_class'] == portfolio_filter]
            
            return filtered_df
            
        except Exception as e:
            raise Exception(f"Failed to load VaR data: {str(e)}")
    
    def calculate_var_metrics(self, df, params):
        """Calculate VaR metrics and aggregations"""
        calc_date = datetime.strptime(params['calculation_date'], '%Y-%m-%d')
        confidence_level = params.get('confidence_level', '99')
        
        # Get data for the specific calculation date
        current_data = df[df['date'] == calc_date]
        
        if current_data.empty:
            raise Exception(f"No VaR data available for {calc_date.strftime('%Y-%m-%d')}")
        
        # Select VaR column based on confidence level
        var_column = f"confidence_{confidence_level.replace('.', '')}"
        
        # Calculate portfolio-level VaR
        portfolio_var = current_data.groupby(['portfolio_id', 'portfolio_name']).agg({
            var_column: 'sum',
            'position_value': 'sum',
            'asset_class': 'first'
        }).reset_index()
        
        # Calculate total VaR (with diversification benefit)
        total_var = current_data[var_column].sum() * 0.85  # 15% diversification benefit
        total_position_value = current_data['position_value'].sum()
        
        # Calculate VaR by asset class
        asset_class_var = current_data.groupby('asset_class').agg({
            var_column: 'sum',
            'position_value': 'sum'
        }).reset_index()
        
        # Calculate VaR percentage of portfolio value
        portfolio_var['var_percentage'] = (portfolio_var[var_column] / portfolio_var['position_value'] * 100).round(2)
        asset_class_var['var_percentage'] = (asset_class_var[var_column] / asset_class_var['position_value'] * 100).round(2)
        
        # Historical VaR trend (last 30 days)
        historical_var = df.groupby('date')[var_column].sum().reset_index()
        historical_var = historical_var.sort_values('date').tail(30)
        
        return {
            'portfolio_var': portfolio_var,
            'asset_class_var': asset_class_var,
            'total_var': total_var,
            'total_position_value': total_position_value,
            'var_percentage': (total_var / total_position_value * 100) if total_position_value > 0 else 0,
            'historical_var': historical_var,
            'var_column': var_column,
            'confidence_level': confidence_level
        }
    
    def generate_html_charts(self, metrics, params):
        """Generate Plotly charts for HTML output"""
        charts = {}
        
        if not params.get('include_charts', True):
            return charts
        
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            
            # Portfolio VaR Chart
            fig_portfolio = go.Figure(data=[
                go.Bar(
                    x=metrics['portfolio_var']['portfolio_name'],
                    y=metrics['portfolio_var'][metrics['var_column']],
                    name='VaR',
                    marker_color='red',
                    text=metrics['portfolio_var']['var_percentage'],
                    texttemplate='%{text}%',
                    textposition='outside'
                )
            ])
            fig_portfolio.update_layout(
                title=f"Portfolio VaR ({metrics['confidence_level']}% Confidence)",
                xaxis_title="Portfolio",
                yaxis_title="VaR ($)",
                template="plotly_white"
            )
            charts['portfolio_var'] = fig_portfolio.to_html(include_plotlyjs='cdn', div_id="portfolio_var_chart")
            
            # Asset Class VaR Pie Chart
            fig_asset = go.Figure(data=[
                go.Pie(
                    labels=metrics['asset_class_var']['asset_class'],
                    values=metrics['asset_class_var'][metrics['var_column']],
                    hole=0.4
                )
            ])
            fig_asset.update_layout(
                title="VaR by Asset Class",
                template="plotly_white"
            )
            charts['asset_class_var'] = fig_asset.to_html(include_plotlyjs='cdn', div_id="asset_class_var_chart")
            
            # Historical VaR Trend
            fig_trend = go.Figure(data=[
                go.Scatter(
                    x=metrics['historical_var']['date'],
                    y=metrics['historical_var'][metrics['var_column']],
                    mode='lines+markers',
                    name='Daily VaR',
                    line=dict(color='blue', width=2)
                )
            ])
            fig_trend.update_layout(
                title="Historical VaR Trend (30 Days)",
                xaxis_title="Date",
                yaxis_title="VaR ($)",
                template="plotly_white"
            )
            charts['historical_trend'] = fig_trend.to_html(include_plotlyjs='cdn', div_id="historical_trend_chart")
            
        except ImportError:
            # Plotly not available, skip charts
            pass
        except Exception as e:
            print(f"Warning: Failed to generate charts: {str(e)}")
        
        return charts
    
    def generate(self, params, output_path):
        """Main report generation method"""
        try:
            # Validate parameters
            validation_errors = self.validate_parameters(params)
            if validation_errors:
                raise Exception(f"Parameter validation failed: {', '.join(validation_errors)}")
            
            # Load and process data
            df = self.load_data(params)
            metrics = self.calculate_var_metrics(df, params)
            
            # Generate outputs
            outputs = {}
            
            # HTML Report
            if 'HTML' in self.get_output_formats():
                charts = self.generate_html_charts(metrics, params)
                html_content = self.generate_html_report(metrics, params, charts)
                html_path = os.path.join(output_path, f"{self.report_id}_report.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                outputs['HTML'] = html_path
            
            # CSV Export
            if 'CSV' in self.get_output_formats():
                csv_path = os.path.join(output_path, f"{self.report_id}_data.csv")
                df.to_csv(csv_path, index=False)
                outputs['CSV'] = csv_path
            
            # Excel Export
            if 'XLS' in self.get_output_formats():
                excel_path = os.path.join(output_path, f"{self.report_id}_summary.xlsx")
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    metrics['portfolio_var'].to_excel(writer, sheet_name='Portfolio VaR', index=False)
                    metrics['asset_class_var'].to_excel(writer, sheet_name='Asset Class VaR', index=False)
                    metrics['historical_var'].to_excel(writer, sheet_name='Historical Trend', index=False)
                outputs['XLS'] = excel_path
            
            # PDF (would require additional libraries like weasyprint)
            if 'PDF' in self.get_output_formats():
                pdf_path = os.path.join(output_path, f"{self.report_id}_report.pdf")
                # For now, create a placeholder
                with open(pdf_path, 'w') as f:
                    f.write("PDF generation requires additional libraries (weasyprint, reportlab)")
                outputs['PDF'] = pdf_path
            
            return outputs
            
        except Exception as e:
            raise Exception(f"VaR report generation failed: {str(e)}")
    
    def generate_html_report(self, metrics, params, charts):
        """Generate HTML report content"""
        calc_date = params['calculation_date']
        confidence_level = metrics['confidence_level']
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Daily VaR Report - {calc_date}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; margin-bottom: 20px; }}
                .summary {{ background: #f8fafc; padding: 15px; margin-bottom: 20px; border-left: 4px solid #2563eb; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .chart-container {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #dc2626; }}
                .metric-label {{ font-size: 14px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Daily Value at Risk Report</h1>
                <p>Calculation Date: {calc_date} | Confidence Level: {confidence_level}%</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <div class="metric-value">${metrics['total_var']:,.0f}</div>
                    <div class="metric-label">Total Portfolio VaR</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${metrics['total_position_value']:,.0f}</div>
                    <div class="metric-label">Total Position Value</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics['var_percentage']:.2f}%</div>
                    <div class="metric-label">VaR as % of Portfolio</div>
                </div>
            </div>
            
            <h2>Portfolio VaR Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>Portfolio</th>
                        <th>Asset Class</th>
                        <th>Position Value ($)</th>
                        <th>VaR ($)</th>
                        <th>VaR %</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in metrics['portfolio_var'].iterrows():
            html_template += f"""
                    <tr>
                        <td>{row['portfolio_name']}</td>
                        <td>{row['asset_class']}</td>
                        <td>${row['position_value']:,.0f}</td>
                        <td>${row[metrics['var_column']]:,.0f}</td>
                        <td>{row['var_percentage']:.2f}%</td>
                    </tr>
            """
        
        html_template += """
                </tbody>
            </table>
        """
        
        # Add charts if available
        if charts:
            html_template += """
            <h2>Visualizations</h2>
            """
            for chart_name, chart_html in charts.items():
                html_template += f"""
                <div class="chart-container">
                    {chart_html}
                </div>
                """
        
        html_template += f"""
            <h2>Asset Class VaR Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Asset Class</th>
                        <th>Position Value ($)</th>
                        <th>VaR ($)</th>
                        <th>VaR %</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in metrics['asset_class_var'].iterrows():
            html_template += f"""
                    <tr>
                        <td>{row['asset_class']}</td>
                        <td>${row['position_value']:,.0f}</td>
                        <td>${row[metrics['var_column']]:,.0f}</td>
                        <td>{row['var_percentage']:.2f}%</td>
                    </tr>
            """
        
        html_template += """
                </tbody>
            </table>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #6b7280;">
                <p>Generated by DataFit on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                <p>This report contains confidential and proprietary information.</p>
            </div>
        </body>
        </html>
        """
        
        return html_template