"""
=============================================================================
RMBS PERFORMANCE ANALYSIS REPORT GENERATOR
=============================================================================
Purpose: Generate Residential Mortgage-Backed Securities performance analysis
Technology: Python with advanced analytics and visualization libraries
Report ID: 2c3f7895-f9e5-5fbc-c429-888db441cc28

STRICT REQUIREMENTS:
- Inherit from base_report.BaseReport abstract class
- Real-time performance calculations and analytics
- Advanced statistical analysis and modeling
- Interactive dashboard-style visualizations
- Comprehensive data validation and quality checks

INPUT PARAMETERS:
- quarter: Quarter selection (Q1, Q2, Q3, Q4) - required
- year: Year (YYYY format) - required  
- analysis_type: Analysis depth (Basic, Standard, Advanced) - optional, defaults to Standard
- benchmark_comparison: Include benchmark comparison (true/false) - optional, defaults to true
- risk_metrics: Include risk analysis (true/false) - optional, defaults to true

DATA SOURCES:
- Primary: /app/mock-data/rmbs_performance.csv
- Benchmark data: /app/mock-data/mortgage_benchmarks.csv
- Historical trends: /app/mock-data/rmbs_historical.csv
- Market data: /app/mock-data/housing_market.csv

REPORT SECTIONS:
1. Executive Dashboard
   - Key performance indicators
   - Portfolio performance summary
   - Risk-adjusted returns
   - Peer comparison metrics

2. Performance Analytics
   - Prepayment speed analysis
   - Default and loss severity trends
   - Vintage performance comparison
   - Cohort analysis by origination period

3. Risk Assessment
   - Credit risk metrics (CPR, CDR, Loss Severity)
   - Interest rate sensitivity analysis
   - Duration and convexity metrics
   - Stress testing scenarios

4. Market Environment
   - Housing price index trends
   - Interest rate environment impact
   - Unemployment correlation analysis
   - Regional market variations

5. Portfolio Composition
   - Loan-to-value distribution
   - FICO score analysis
   - Property type breakdown
   - Geographic concentration

ADVANCED ANALYTICS:
- Machine learning models for prepayment prediction
- Monte Carlo simulations for stress testing
- Time series analysis for trend identification
- Regression analysis for factor attribution
- Clustering analysis for risk segmentation

INTERACTIVE FEATURES:
- Drill-down capabilities by geography/vintage
- Dynamic filtering and sorting
- Real-time calculation updates
- Comparative analysis tools
- Export functionality for specific views

VALIDATION FRAMEWORK:
- Data quality checks and outlier detection
- Cross-validation with external sources
- Consistency checks across time periods
- Completeness and accuracy verification
- Automated data lineage tracking

PERFORMANCE OPTIMIZATION:
- Vectorized calculations using NumPy
- Parallel processing for complex analytics
- Efficient memory management
- Cached intermediate results
- Progressive loading for large datasets

COMPLIANCE AND STANDARDS:
- GAAP accounting standards adherence
- Regulatory reporting requirements
- Data governance policies
- Audit trail maintenance
- Change management documentation

VISUALIZATION LIBRARY:
- Plotly for interactive charts
- Seaborn for statistical visualizations
- Matplotlib for custom graphics
- Bokeh for real-time dashboards
- D3.js integration for advanced interactions

ERROR HANDLING AND RECOVERY:
- Graceful degradation for missing data
- Alternative calculation methods
- User notification for data issues
- Automatic retry mechanisms
- Detailed error logging and reporting

DEPENDENCIES:
- pandas: Data manipulation and analysis
- numpy: Numerical computations
- scipy: Statistical analysis
- plotly: Interactive visualizations
- scikit-learn: Machine learning models
- statsmodels: Time series analysis
- base_report: Abstract base class

USAGE EXAMPLE:
```python
from reports.rmbs_performance import RMBSPerformanceReport

parameters = {
    "quarter": "Q2",
    "year": "2024",
    "analysis_type": "Advanced",
    "benchmark_comparison": True,
    "risk_metrics": True
}

report = RMBSPerformanceReport(parameters)
result = report.generate()
```
=============================================================================
"""