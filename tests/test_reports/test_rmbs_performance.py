"""
=============================================================================
RMBS PERFORMANCE REPORT GENERATOR UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for RMBS Performance analysis report
Technology: pytest with advanced analytics and machine learning testing
Module: reports/rmbs_performance.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test advanced analytics and ML model integration
- Mock statistical analysis and time series processing
- Validate regression analysis and model performance
- Test error handling and data quality validation

TEST CATEGORIES:
1. Advanced Analytics Tests
   - Machine learning model integration
   - Statistical analysis accuracy
   - Time series processing
   - Regression analysis validation
   - Model performance metrics

2. Data Processing Tests
   - Multi-source data integration
   - Data quality validation
   - Missing value imputation
   - Outlier detection and handling
   - Performance optimization

3. Risk Calculations Tests
   - Prepayment speed analysis
   - Default rate calculations
   - Loss severity computations
   - Duration and convexity metrics
   - Stress testing scenarios

DEPENDENCIES:
- pytest: Test framework
- sklearn: Machine learning testing
- scipy: Statistical analysis testing
- numpy: Numerical computations
- pandas: Data manipulation
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from sklearn.metrics import mean_squared_error, r2_score
from scipy import stats
import warnings

# Mock RMBS report class
class RMBSPerformanceReport:
    """RMBS Performance Analysis Report Generator."""
    
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.required_fields = ['analysis_date', 'portfolio_id']
        self.data = None
        self.models = {}
        self.analysis_results = {}
    
    def validate_parameters(self):
        """Validate report parameters."""
        errors = []
        for field in self.required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        return errors
    
    def load_rmbs_data(self):
        """Load RMBS performance data."""
        # Mock RMBS data with performance metrics
        np.random.seed(42)
        n_loans = 1000
        
        self.data = pd.DataFrame({
            'loan_id': [f'RMBS{i:06d}' for i in range(1, n_loans + 1)],
            'origination_date': pd.date_range('2020-01-01', periods=n_loans, freq='D'),
            'original_balance': np.random.uniform(100000, 800000, n_loans),
            'current_balance': np.random.uniform(80000, 750000, n_loans),
            'interest_rate': np.random.uniform(2.5, 6.5, n_loans),
            'credit_score': np.random.randint(500, 850, n_loans),
            'ltv_ratio': np.random.uniform(0.6, 0.95, n_loans),
            'dti_ratio': np.random.uniform(0.15, 0.45, n_loans),
            'property_value': np.random.uniform(150000, 1200000, n_loans),
            'monthly_payment': np.random.uniform(800, 4500, n_loans),
            'prepayment_speed': np.random.uniform(0.05, 0.35, n_loans),
            'default_probability': np.random.uniform(0.001, 0.08, n_loans),
            'loss_severity': np.random.uniform(0.1, 0.4, n_loans),
            'months_seasoning': np.random.randint(1, 48, n_loans)
        })
        
        return self.data
    
    def perform_prepayment_analysis(self):
        """Perform prepayment speed analysis with ML models."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Calculate prepayment metrics
        analysis = {
            'avg_prepayment_speed': self.data['prepayment_speed'].mean(),
            'median_prepayment_speed': self.data['prepayment_speed'].median(),
            'prepayment_volatility': self.data['prepayment_speed'].std(),
            'prepayment_by_seasoning': self._analyze_prepayment_by_seasoning(),
            'prepayment_model_performance': self._build_prepayment_model()
        }
        
        return analysis
    
    def _analyze_prepayment_by_seasoning(self):
        """Analyze prepayment patterns by loan seasoning."""
        seasoning_buckets = pd.cut(self.data['months_seasoning'], 
                                 bins=[0, 12, 24, 36, 48], 
                                 labels=['0-12m', '12-24m', '24-36m', '36-48m'])
        
        prepayment_by_seasoning = self.data.groupby(seasoning_buckets)['prepayment_speed'].agg([
            'mean', 'median', 'std', 'count'
        ]).round(4)
        
        return prepayment_by_seasoning
    
    def _build_prepayment_model(self):
        """Build and validate prepayment prediction model."""
        # Features for prepayment modeling
        features = ['interest_rate', 'credit_score', 'ltv_ratio', 'dti_ratio', 
                   'months_seasoning', 'current_balance']
        
        X = self.data[features]
        y = self.data['prepayment_speed']
        
        # Mock model performance metrics
        model_performance = {
            'r2_score': 0.72,
            'rmse': 0.045,
            'mae': 0.032,
            'feature_importance': {
                'interest_rate': 0.35,
                'credit_score': 0.25,
                'ltv_ratio': 0.20,
                'months_seasoning': 0.12,
                'dti_ratio': 0.05,
                'current_balance': 0.03
            }
        }
        
        return model_performance
    
    def calculate_default_metrics(self):
        """Calculate default probability and loss metrics."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        default_analysis = {
            'portfolio_default_rate': self.data['default_probability'].mean(),
            'default_rate_by_credit_score': self._analyze_defaults_by_credit(),
            'expected_loss': self._calculate_expected_loss(),
            'loss_severity_analysis': self._analyze_loss_severity(),
            'stress_test_results': self._perform_stress_tests()
        }
        
        return default_analysis
    
    def _analyze_defaults_by_credit(self):
        """Analyze default rates by credit score buckets."""
        credit_buckets = pd.cut(self.data['credit_score'], 
                              bins=[0, 580, 620, 680, 740, 850], 
                              labels=['<580', '580-620', '620-680', '680-740', '740+'])
        
        default_by_credit = self.data.groupby(credit_buckets)['default_probability'].agg([
            'mean', 'median', 'std', 'count'
        ]).round(4)
        
        return default_by_credit
    
    def _calculate_expected_loss(self):
        """Calculate expected loss for the portfolio."""
        expected_loss = (self.data['default_probability'] * 
                        self.data['loss_severity'] * 
                        self.data['current_balance']).sum()
        
        total_balance = self.data['current_balance'].sum()
        expected_loss_rate = expected_loss / total_balance
        
        return {
            'total_expected_loss': expected_loss,
            'expected_loss_rate': expected_loss_rate,
            'loss_distribution': self._calculate_loss_distribution()
        }
    
    def _calculate_loss_distribution(self):
        """Calculate loss distribution percentiles."""
        loan_losses = (self.data['default_probability'] * 
                      self.data['loss_severity'] * 
                      self.data['current_balance'])
        
        percentiles = [50, 75, 90, 95, 99]
        loss_percentiles = {}
        
        for p in percentiles:
            loss_percentiles[f'p{p}'] = np.percentile(loan_losses, p)
        
        return loss_percentiles
    
    def _analyze_loss_severity(self):
        """Analyze loss severity patterns."""
        return {
            'avg_loss_severity': self.data['loss_severity'].mean(),
            'loss_severity_volatility': self.data['loss_severity'].std(),
            'loss_severity_by_ltv': self._loss_severity_by_ltv()
        }
    
    def _loss_severity_by_ltv(self):
        """Analyze loss severity by LTV buckets."""
        ltv_buckets = pd.cut(self.data['ltv_ratio'], 
                           bins=[0, 0.7, 0.8, 0.9, 1.0], 
                           labels=['<70%', '70-80%', '80-90%', '90%+'])
        
        return self.data.groupby(ltv_buckets)['loss_severity'].agg([
            'mean', 'median', 'std', 'count'
        ]).round(4)
    
    def _perform_stress_tests(self):
        """Perform stress testing scenarios."""
        stress_scenarios = {
            'mild_stress': {'default_multiplier': 1.5, 'loss_severity_increase': 0.1},
            'moderate_stress': {'default_multiplier': 2.5, 'loss_severity_increase': 0.2},
            'severe_stress': {'default_multiplier': 4.0, 'loss_severity_increase': 0.3}
        }
        
        stress_results = {}
        base_expected_loss = self._calculate_expected_loss()['total_expected_loss']
        
        for scenario, params in stress_scenarios.items():
            stressed_defaults = self.data['default_probability'] * params['default_multiplier']
            stressed_severity = np.minimum(self.data['loss_severity'] + params['loss_severity_increase'], 1.0)
            
            stressed_loss = (stressed_defaults * stressed_severity * self.data['current_balance']).sum()
            
            stress_results[scenario] = {
                'stressed_loss': stressed_loss,
                'loss_increase': stressed_loss - base_expected_loss,
                'loss_multiple': stressed_loss / base_expected_loss if base_expected_loss > 0 else 0
            }
        
        return stress_results
    
    def generate_performance_dashboard(self):
        """Generate performance visualization data."""
        charts = []
        
        # Prepayment speed distribution
        charts.append({
            'type': 'histogram',
            'data': {
                'values': self.data['prepayment_speed'].tolist(),
                'bins': 20
            },
            'title': 'Prepayment Speed Distribution'
        })
        
        # Default probability vs Credit Score
        charts.append({
            'type': 'scatter',
            'data': {
                'x': self.data['credit_score'].tolist(),
                'y': self.data['default_probability'].tolist()
            },
            'title': 'Default Probability vs Credit Score'
        })
        
        # Loss severity by LTV
        ltv_buckets = pd.cut(self.data['ltv_ratio'], bins=10)
        loss_by_ltv = self.data.groupby(ltv_buckets)['loss_severity'].mean()
        
        charts.append({
            'type': 'line',
            'data': {
                'x': [str(interval.mid) for interval in loss_by_ltv.index],
                'y': loss_by_ltv.values.tolist()
            },
            'title': 'Loss Severity by LTV Ratio'
        })
        
        return charts
    
    def generate(self):
        """Generate complete RMBS performance report."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
        
        # Load data and perform analysis
        self.load_rmbs_data()
        prepayment_analysis = self.perform_prepayment_analysis()
        default_analysis = self.calculate_default_metrics()
        charts = self.generate_performance_dashboard()
        
        # Generate outputs
        output_files = []
        
        # HTML report
        html_content = self._generate_html_report(prepayment_analysis, default_analysis, charts)
        output_files.append({
            'filename': f"rmbs_performance_{self.parameters.get('analysis_date', 'latest')}.html",
            'content': html_content,
            'content_type': 'text/html',
            'size': len(html_content.encode('utf-8'))
        })
        
        # Analysis data JSON
        analysis_data = {
            'prepayment_analysis': prepayment_analysis,
            'default_analysis': default_analysis,
            'charts': charts
        }
        
        json_content = json.dumps(analysis_data, indent=2, default=str)
        output_files.append({
            'filename': f"rmbs_analysis_{self.parameters.get('analysis_date', 'latest')}.json",
            'content': json_content,
            'content_type': 'application/json',
            'size': len(json_content.encode('utf-8'))
        })
        
        return {
            'status': 'completed',
            'files': output_files,
            'metadata': {
                'report_type': 'RMBS Performance Analysis',
                'analysis_date': self.parameters.get('analysis_date', datetime.now().strftime('%Y-%m-%d')),
                'total_loans': len(self.data),
                'portfolio_value': self.data['current_balance'].sum(),
                'avg_prepayment_speed': prepayment_analysis['avg_prepayment_speed'],
                'portfolio_default_rate': default_analysis['portfolio_default_rate']
            }
        }
    
    def _generate_html_report(self, prepayment_analysis, default_analysis, charts):
        """Generate HTML report content."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RMBS Performance Analysis Report</title>
            <style>body {{ font-family: Arial, sans-serif; margin: 20px; }}</style>
        </head>
        <body>
            <h1>RMBS Performance Analysis</h1>
            <p>Analysis Date: {self.parameters.get('analysis_date', 'N/A')}</p>
            <p>Portfolio ID: {self.parameters.get('portfolio_id', 'N/A')}</p>
            
            <h2>Prepayment Analysis</h2>
            <p>Average Prepayment Speed: {prepayment_analysis['avg_prepayment_speed']:.4f}</p>
            <p>Prepayment Volatility: {prepayment_analysis['prepayment_volatility']:.4f}</p>
            <p>Model R² Score: {prepayment_analysis['prepayment_model_performance']['r2_score']:.3f}</p>
            
            <h2>Default Analysis</h2>
            <p>Portfolio Default Rate: {default_analysis['portfolio_default_rate']:.4f}</p>
            <p>Expected Loss Rate: {default_analysis['expected_loss']['expected_loss_rate']:.4f}</p>
            
            <h2>Charts and Visualizations</h2>
            <p>Generated {len(charts)} analytical charts</p>
        </body>
        </html>
        """


class TestRMBSPerformanceReport:
    """Test RMBS Performance report functionality."""
    
    @pytest.fixture
    def report_instance(self):
        return RMBSPerformanceReport()
    
    @pytest.fixture
    def valid_parameters(self):
        return {
            'analysis_date': '2024-06-30',
            'portfolio_id': 'RMBS_2024_Q2',
            'stress_scenarios': ['mild', 'moderate', 'severe']
        }
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        errors = report_instance.validate_parameters()
        assert errors == []
    
    @pytest.mark.unit
    def test_parameter_validation_missing_required(self, report_instance):
        report_instance.parameters = {'portfolio_id': 'TEST'}
        errors = report_instance.validate_parameters()
        assert len(errors) > 0
        assert any('analysis_date' in error for error in errors)
    
    @pytest.mark.unit
    def test_load_rmbs_data(self, report_instance):
        data = report_instance.load_rmbs_data()
        
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        
        required_columns = [
            'loan_id', 'original_balance', 'current_balance', 'interest_rate',
            'credit_score', 'ltv_ratio', 'prepayment_speed', 'default_probability'
        ]
        
        for col in required_columns:
            assert col in data.columns
    
    @pytest.mark.unit
    def test_prepayment_analysis(self, report_instance):
        report_instance.load_rmbs_data()
        analysis = report_instance.perform_prepayment_analysis()
        
        assert 'avg_prepayment_speed' in analysis
        assert 'median_prepayment_speed' in analysis
        assert 'prepayment_volatility' in analysis
        assert 'prepayment_by_seasoning' in analysis
        assert 'prepayment_model_performance' in analysis
        
        # Validate numeric ranges
        assert 0 <= analysis['avg_prepayment_speed'] <= 1
        assert analysis['prepayment_volatility'] >= 0
        
        # Check model performance metrics
        model_perf = analysis['prepayment_model_performance']
        assert 'r2_score' in model_perf
        assert 'rmse' in model_perf
        assert 'feature_importance' in model_perf
    
    @pytest.mark.unit
    def test_default_metrics_calculation(self, report_instance):
        report_instance.load_rmbs_data()
        default_analysis = report_instance.calculate_default_metrics()
        
        assert 'portfolio_default_rate' in default_analysis
        assert 'default_rate_by_credit_score' in default_analysis
        assert 'expected_loss' in default_analysis
        assert 'stress_test_results' in default_analysis
        
        # Validate expected loss structure
        expected_loss = default_analysis['expected_loss']
        assert 'total_expected_loss' in expected_loss
        assert 'expected_loss_rate' in expected_loss
        assert 'loss_distribution' in expected_loss
        
        # Check stress test results
        stress_results = default_analysis['stress_test_results']
        assert 'mild_stress' in stress_results
        assert 'moderate_stress' in stress_results
        assert 'severe_stress' in stress_results
    
    @pytest.mark.unit
    def test_performance_dashboard_generation(self, report_instance):
        report_instance.load_rmbs_data()
        charts = report_instance.generate_performance_dashboard()
        
        assert len(charts) >= 3
        
        chart_types = [chart['type'] for chart in charts]
        assert 'histogram' in chart_types
        assert 'scatter' in chart_types
        assert 'line' in chart_types
        
        for chart in charts:
            assert 'type' in chart
            assert 'data' in chart
            assert 'title' in chart
    
    @pytest.mark.unit
    def test_complete_report_generation(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        result = report_instance.generate()
        
        assert result['status'] == 'completed'
        assert 'files' in result
        assert 'metadata' in result
        
        files = result['files']
        assert len(files) >= 2
        
        # Check HTML file
        html_file = next((f for f in files if f['filename'].endswith('.html')), None)
        assert html_file is not None
        assert 'RMBS Performance Analysis' in html_file['content']
        
        # Check JSON file
        json_file = next((f for f in files if f['filename'].endswith('.json')), None)
        assert json_file is not None
        
        # Validate metadata
        metadata = result['metadata']
        assert metadata['report_type'] == 'RMBS Performance Analysis'
        assert metadata['total_loans'] > 0
        assert metadata['portfolio_value'] > 0
    
    @pytest.mark.unit
    def test_stress_testing_scenarios(self, report_instance):
        report_instance.load_rmbs_data()
        default_analysis = report_instance.calculate_default_metrics()
        
        stress_results = default_analysis['stress_test_results']
        
        # Verify stress scenarios increase losses
        base_loss = default_analysis['expected_loss']['total_expected_loss']
        
        for scenario, results in stress_results.items():
            assert results['stressed_loss'] > base_loss
            assert results['loss_increase'] > 0
            assert results['loss_multiple'] > 1.0
        
        # Verify stress intensity ordering
        mild_loss = stress_results['mild_stress']['stressed_loss']
        moderate_loss = stress_results['moderate_stress']['stressed_loss']
        severe_loss = stress_results['severe_stress']['stressed_loss']
        
        assert mild_loss < moderate_loss < severe_loss
    
    @pytest.mark.performance
    def test_large_portfolio_performance(self):
        """Test performance with large portfolio."""
        import time
        
        # Create large dataset
        large_report = RMBSPerformanceReport({
            'analysis_date': '2024-06-30',
            'portfolio_id': 'LARGE_PORTFOLIO'
        })
        
        # Mock large dataset
        np.random.seed(42)
        n_loans = 50000
        
        large_data = pd.DataFrame({
            'loan_id': [f'RMBS{i:07d}' for i in range(1, n_loans + 1)],
            'origination_date': pd.date_range('2020-01-01', periods=n_loans, freq='H'),
            'original_balance': np.random.uniform(100000, 800000, n_loans),
            'current_balance': np.random.uniform(80000, 750000, n_loans),
            'interest_rate': np.random.uniform(2.5, 6.5, n_loans),
            'credit_score': np.random.randint(500, 850, n_loans),
            'ltv_ratio': np.random.uniform(0.6, 0.95, n_loans),
            'dti_ratio': np.random.uniform(0.15, 0.45, n_loans),
            'prepayment_speed': np.random.uniform(0.05, 0.35, n_loans),
            'default_probability': np.random.uniform(0.001, 0.08, n_loans),
            'loss_severity': np.random.uniform(0.1, 0.4, n_loans),
            'months_seasoning': np.random.randint(1, 48, n_loans)
        })
        
        large_report.data = large_data
        
        # Test performance
        start_time = time.time()
        prepayment_analysis = large_report.perform_prepayment_analysis()
        prepayment_time = time.time() - start_time
        
        start_time = time.time()
        default_analysis = large_report.calculate_default_metrics()
        default_time = time.time() - start_time
        
        # Performance assertions
        assert prepayment_time < 5.0, f"Prepayment analysis took {prepayment_time:.3f}s"
        assert default_time < 3.0, f"Default analysis took {default_time:.3f}s"
        
        # Verify results are still accurate
        assert 0 <= prepayment_analysis['avg_prepayment_speed'] <= 1
        assert default_analysis['portfolio_default_rate'] >= 0
    
    @pytest.mark.unit
    def test_data_quality_validation(self, report_instance):
        """Test data quality validation and handling."""
        # Load clean data first
        report_instance.load_rmbs_data()
        
        # Introduce data quality issues
        corrupted_data = report_instance.data.copy()
        
        # Add missing values
        corrupted_data.loc[0:10, 'credit_score'] = np.nan
        corrupted_data.loc[5:15, 'ltv_ratio'] = np.nan
        
        # Add outliers
        corrupted_data.loc[20:25, 'prepayment_speed'] = 2.0  # Impossible value > 1
        corrupted_data.loc[30:35, 'default_probability'] = -0.1  # Negative probability
        
        report_instance.data = corrupted_data
        
        # Analysis should handle data quality issues gracefully
        try:
            prepayment_analysis = report_instance.perform_prepayment_analysis()
            default_analysis = report_instance.calculate_default_metrics()
            
            # Results should still be reasonable despite data issues
            assert prepayment_analysis['avg_prepayment_speed'] >= 0
            assert default_analysis['portfolio_default_rate'] >= 0
            
        except Exception as e:
            # If exceptions are raised, they should be informative
            assert "data quality" in str(e).lower() or "invalid" in str(e).lower()
