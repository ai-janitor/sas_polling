"""
=============================================================================
CMBS USER MANUAL REPORT GENERATOR
=============================================================================
Purpose: Generate Commercial Mortgage-Backed Securities user manual reports
Technology: Python with Pandas, Plotly, and report templates
Report ID: 1b2e6894-e8d4-4eba-b318-999ca330bb19

STRICT REQUIREMENTS:
- Inherit from base_report.BaseReport abstract class
- Support all output formats: HTML, PDF, CSV, XLS
- Validate all input parameters before processing
- Handle missing data gracefully with warnings
- Generate interactive Plotly charts for visualizations

INPUT PARAMETERS:
- hidden_username: SEC User Name (hidden field, required)
- asofqtr: Quarter (Q1, Q2, Q3, Q4) - optional, defaults to current quarter
- year: Year (YYYY format) - optional, defaults to current year
- sortorder: Sort order (Name, Date, Performance) - optional, defaults to Name
- outputtp: Output type (HTML, PDF, XLS) - optional, defaults to HTML

DATA SOURCES:
- Mock data from: /app/mock-data/cmbs_data.csv
- Template: /app/templates/cmbs_template.html
- Configuration from config.dev.env

REPORT CONTENT:
1. Executive Summary
   - Portfolio overview statistics
   - Performance highlights
   - Risk metrics summary

2. Portfolio Composition
   - Property type breakdown
   - Geographic distribution
   - Loan size distribution

3. Performance Analysis
   - Historical performance trends
   - Delinquency rates
   - Loss severity analysis

4. Risk Assessment
   - Credit risk metrics
   - Market risk indicators
   - Stress testing results

5. Interactive Visualizations
   - Performance trend charts
   - Geographic heat maps
   - Risk distribution plots

OUTPUT FORMATS:
- HTML: Interactive report with Plotly charts
- PDF: Static print-ready document
- CSV: Raw data export
- XLS: Excel workbook with multiple sheets

VALIDATION RULES:
- username: Must be valid SEC user identifier
- quarter: Must be Q1, Q2, Q3, or Q4
- year: Must be 4-digit year (2000-2030)
- sortorder: Must be valid sort option
- outputtp: Must be supported output format

ERROR HANDLING:
- Invalid parameter values
- Missing required data files
- Template rendering errors
- Chart generation failures
- File export errors

PERFORMANCE CONSIDERATIONS:
- Efficient data loading and processing
- Memory management for large datasets
- Optimized chart rendering
- Concurrent file generation
- Caching for repeated requests

COMPLIANCE:
- SEC reporting standards
- Data privacy regulations
- Audit trail requirements
- Access control compliance
- Document retention policies

DEPENDENCIES:
- pandas: Data manipulation and analysis
- plotly: Interactive chart generation
- jinja2: HTML template rendering
- openpyxl: Excel file generation
- weasyprint: PDF generation
- base_report: Abstract base class

USAGE EXAMPLE:
```python
from reports.cmbs_user_manual import CMBSUserManualReport

parameters = {
    "hidden_username": "user123",
    "asofqtr": "Q2",
    "year": "2024",
    "sortorder": "Performance",
    "outputtp": "HTML"
}

report = CMBSUserManualReport(parameters)
result = report.generate()
```
=============================================================================
"""