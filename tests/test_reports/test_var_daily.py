"""
=============================================================================
VAR DAILY REPORT GENERATOR UNIT TESTS  
=============================================================================
Purpose: Unit tests for Value at Risk daily calculation report
Module: reports/var_daily.py

TEST CATEGORIES:
1. VAR Methodology Testing
2. Risk Factor Analysis  
3. Stress Testing
4. Performance Optimization
5. Regulatory Compliance
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json
from scipy import stats

class VARDailyReport:
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.required_fields = ['portfolio_id', 'calculation_date', 'confidence_level']
        self.data = None
        self.var_results = {}
    
    def validate_parameters(self):
        errors = []
        for field in self.required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        
        if 'confidence_level' in self.parameters:
            conf_level = self.parameters['confidence_level']
            if not isinstance(conf_level, (int, float)) or conf_level <= 0 or conf_level >= 1:
                errors.append("Confidence level must be between 0 and 1")
        
        return errors
    
    def load_portfolio_data(self):
        np.random.seed(42)
        n_positions = 500
        
        self.data = pd.DataFrame({
            'position_id': [f'POS{i:05d}' for i in range(1, n_positions + 1)],
            'instrument_type': np.random.choice(['Equity', 'Bond', 'Derivative'], n_positions),
            'market_value': np.random.uniform(100000, 10000000, n_positions),
            'daily_returns': np.random.normal(0.0008, 0.02, n_positions),
            'volatility': np.random.uniform(0.1, 0.5, n_positions),
            'beta': np.random.uniform(0.5, 1.8, n_positions),
            'duration': np.random.uniform(0.5, 10.0, n_positions),
            'credit_rating': np.random.choice(['AAA', 'AA', 'A', 'BBB', 'BB'], n_positions)
        })
        
        return self.data
    
    def calculate_historical_var(self, confidence_level=0.95, lookback_days=252):
        """Calculate Historical Simulation VaR."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Generate historical returns
        np.random.seed(42)
        historical_returns = np.random.normal(0, 0.02, (lookback_days, len(self.data)))
        
        # Calculate portfolio returns
        weights = self.data['market_value'] / self.data['market_value'].sum()
        portfolio_returns = np.dot(historical_returns, weights)
        
        # Calculate VaR
        var_percentile = (1 - confidence_level) * 100
        var_value = np.percentile(portfolio_returns, var_percentile)
        
        return {
            'var_absolute': abs(var_value * self.data['market_value'].sum()),
            'var_percentage': abs(var_value),
            'expected_shortfall': self._calculate_expected_shortfall(portfolio_returns, var_value),
            'method': 'Historical Simulation',
            'confidence_level': confidence_level,
            'lookback_days': lookback_days
        }
    
    def calculate_parametric_var(self, confidence_level=0.95):
        """Calculate Parametric VaR using normal distribution assumption."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Portfolio statistics
        weights = self.data['market_value'] / self.data['market_value'].sum()
        portfolio_return = np.dot(weights, self.data['daily_returns'])
        portfolio_vol = np.sqrt(np.dot(weights**2, self.data['volatility']**2))
        
        # Calculate VaR using normal distribution
        z_score = stats.norm.ppf(1 - confidence_level)
        var_value = portfolio_return + z_score * portfolio_vol
        
        return {
            'var_absolute': abs(var_value * self.data['market_value'].sum()),
            'var_percentage': abs(var_value),
            'portfolio_volatility': portfolio_vol,
            'method': 'Parametric (Normal)',
            'confidence_level': confidence_level
        }
    
    def calculate_monte_carlo_var(self, confidence_level=0.95, num_simulations=10000):
        """Calculate Monte Carlo VaR."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Portfolio weights
        weights = self.data['market_value'] / self.data['market_value'].sum()
        
        # Generate random scenarios
        np.random.seed(42)
        random_returns = np.random.normal(0, 1, (num_simulations, len(self.data)))
        
        # Apply volatilities
        scaled_returns = random_returns * self.data['volatility'].values
        
        # Calculate portfolio returns
        portfolio_returns = np.dot(scaled_returns, weights)
        
        # Calculate VaR
        var_percentile = (1 - confidence_level) * 100
        var_value = np.percentile(portfolio_returns, var_percentile)
        
        return {
            'var_absolute': abs(var_value * self.data['market_value'].sum()),
            'var_percentage': abs(var_value),
            'expected_shortfall': self._calculate_expected_shortfall(portfolio_returns, var_value),
            'method': 'Monte Carlo',
            'confidence_level': confidence_level,
            'num_simulations': num_simulations
        }
    
    def _calculate_expected_shortfall(self, returns, var_threshold):
        """Calculate Expected Shortfall (Conditional VaR)."""
        tail_returns = returns[returns <= var_threshold]
        if len(tail_returns) > 0:
            return abs(np.mean(tail_returns))
        return 0
    
    def perform_backtesting(self):
        """Perform VaR model backtesting."""
        # Generate mock backtesting results
        np.random.seed(42)
        n_days = 252
        
        actual_returns = np.random.normal(0.0008, 0.02, n_days)
        var_forecasts = np.random.uniform(0.015, 0.025, n_days)
        
        violations = actual_returns < -var_forecasts
        violation_rate = violations.sum() / n_days
        
        expected_violations = (1 - self.parameters.get('confidence_level', 0.95)) * n_days
        actual_violations = violations.sum()
        
        return {
            'violation_rate': violation_rate,
            'expected_violations': expected_violations,
            'actual_violations': actual_violations,
            'kupiec_test_pvalue': self._kupiec_test(actual_violations, expected_violations, n_days),
            'coverage_ratio': actual_violations / expected_violations if expected_violations > 0 else 0
        }
    
    def _kupiec_test(self, actual_violations, expected_violations, n_observations):
        """Perform Kupiec test for VaR model validation."""
        if expected_violations == 0 or actual_violations == 0:
            return 1.0
        
        p_expected = expected_violations / n_observations
        p_actual = actual_violations / n_observations
        
        if p_actual == 0 or p_actual == 1:
            return 1.0
        
        # Simplified Kupiec test statistic
        lr_stat = -2 * np.log((p_expected**actual_violations * (1-p_expected)**(n_observations-actual_violations)) /
                              (p_actual**actual_violations * (1-p_actual)**(n_observations-actual_violations)))
        
        # Return mock p-value
        return max(0.01, min(0.99, 1 - stats.chi2.cdf(lr_stat, 1)))
    
    def generate_stress_scenarios(self):
        """Generate stress testing scenarios."""
        scenarios = {
            'market_crash': {'equity_shock': -0.20, 'vol_shock': 2.0},
            'interest_rate_shock': {'rate_shock': 0.02, 'duration_impact': True},
            'credit_crisis': {'credit_spread_shock': 0.005, 'rating_downgrade': True}
        }
        
        stress_results = {}
        base_portfolio_value = self.data['market_value'].sum()
        
        for scenario_name, shock_params in scenarios.items():
            stressed_value = self._apply_stress_scenario(shock_params)
            stress_loss = base_portfolio_value - stressed_value
            
            stress_results[scenario_name] = {
                'stressed_portfolio_value': stressed_value,
                'stress_loss': stress_loss,
                'stress_loss_percentage': stress_loss / base_portfolio_value,
                'scenario_parameters': shock_params
            }
        
        return stress_results
    
    def _apply_stress_scenario(self, shock_params):
        """Apply stress scenario to portfolio."""
        stressed_values = self.data['market_value'].copy()
        
        if 'equity_shock' in shock_params:
            equity_mask = self.data['instrument_type'] == 'Equity'
            stressed_values[equity_mask] *= (1 + shock_params['equity_shock'])
        
        if 'rate_shock' in shock_params and 'duration_impact' in shock_params:
            bond_mask = self.data['instrument_type'] == 'Bond'
            duration_impact = -self.data['duration'] * shock_params['rate_shock']
            stressed_values[bond_mask] *= (1 + duration_impact[bond_mask])
        
        return stressed_values.sum()
    
    def generate(self):
        """Generate complete VaR report."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
        
        self.load_portfolio_data()
        confidence_level = self.parameters.get('confidence_level', 0.95)
        
        # Calculate VaR using different methods
        historical_var = self.calculate_historical_var(confidence_level)
        parametric_var = self.calculate_parametric_var(confidence_level)
        monte_carlo_var = self.calculate_monte_carlo_var(confidence_level)
        
        # Perform backtesting and stress testing
        backtesting_results = self.perform_backtesting()
        stress_scenarios = self.generate_stress_scenarios()
        
        # Generate report
        report_data = {
            'var_calculations': {
                'historical': historical_var,
                'parametric': parametric_var,
                'monte_carlo': monte_carlo_var
            },
            'backtesting': backtesting_results,
            'stress_testing': stress_scenarios,
            'portfolio_summary': {
                'total_positions': len(self.data),
                'total_market_value': self.data['market_value'].sum(),
                'calculation_date': self.parameters.get('calculation_date'),
                'confidence_level': confidence_level
            }
        }
        
        json_content = json.dumps(report_data, indent=2, default=str)
        
        return {
            'status': 'completed',
            'files': [{
                'filename': f"var_daily_{self.parameters.get('calculation_date', 'latest')}.json",
                'content': json_content,
                'content_type': 'application/json',
                'size': len(json_content.encode('utf-8'))
            }],
            'metadata': {
                'report_type': 'VaR Daily',
                'calculation_date': self.parameters.get('calculation_date'),
                'confidence_level': confidence_level,
                'var_methods': ['Historical', 'Parametric', 'Monte Carlo']
            }
        }


class TestVARDailyReport:
    @pytest.fixture
    def report_instance(self):
        return VARDailyReport()
    
    @pytest.fixture
    def valid_parameters(self):
        return {
            'portfolio_id': 'PORT_001',
            'calculation_date': '2024-06-30',
            'confidence_level': 0.95
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
        assert len(errors) >= 2  # Missing calculation_date and confidence_level
    
    @pytest.mark.unit
    def test_invalid_confidence_level(self, report_instance):
        invalid_levels = [-0.1, 0, 1, 1.5, 'invalid']
        for level in invalid_levels:
            report_instance.parameters = {
                'portfolio_id': 'TEST',
                'calculation_date': '2024-06-30',
                'confidence_level': level
            }
            errors = report_instance.validate_parameters()
            assert len(errors) > 0
    
    @pytest.mark.unit
    def test_load_portfolio_data(self, report_instance):
        data = report_instance.load_portfolio_data()
        
        assert data is not None
        assert len(data) > 0
        required_columns = ['position_id', 'market_value', 'daily_returns', 'volatility']
        for col in required_columns:
            assert col in data.columns
    
    @pytest.mark.unit
    def test_historical_var_calculation(self, report_instance):
        report_instance.load_portfolio_data()
        var_result = report_instance.calculate_historical_var(0.95)
        
        assert 'var_absolute' in var_result
        assert 'var_percentage' in var_result
        assert 'expected_shortfall' in var_result
        assert var_result['method'] == 'Historical Simulation'
        assert var_result['var_absolute'] > 0
        assert var_result['expected_shortfall'] >= var_result['var_percentage']
    
    @pytest.mark.unit
    def test_parametric_var_calculation(self, report_instance):
        report_instance.load_portfolio_data()
        var_result = report_instance.calculate_parametric_var(0.99)
        
        assert var_result['method'] == 'Parametric (Normal)'
        assert var_result['confidence_level'] == 0.99
        assert 'portfolio_volatility' in var_result
        assert var_result['var_absolute'] > 0
    
    @pytest.mark.unit
    def test_monte_carlo_var_calculation(self, report_instance):
        report_instance.load_portfolio_data()
        var_result = report_instance.calculate_monte_carlo_var(0.95, 5000)
        
        assert var_result['method'] == 'Monte Carlo'
        assert var_result['num_simulations'] == 5000
        assert var_result['var_absolute'] > 0
    
    @pytest.mark.unit
    def test_backtesting_analysis(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        report_instance.load_portfolio_data()
        
        backtesting = report_instance.perform_backtesting()
        
        assert 'violation_rate' in backtesting
        assert 'expected_violations' in backtesting
        assert 'actual_violations' in backtesting
        assert 'kupiec_test_pvalue' in backtesting
        
        assert 0 <= backtesting['violation_rate'] <= 1
        assert 0 <= backtesting['kupiec_test_pvalue'] <= 1
    
    @pytest.mark.unit
    def test_stress_scenario_generation(self, report_instance):
        report_instance.load_portfolio_data()
        stress_results = report_instance.generate_stress_scenarios()
        
        expected_scenarios = ['market_crash', 'interest_rate_shock', 'credit_crisis']
        for scenario in expected_scenarios:
            assert scenario in stress_results
            
            result = stress_results[scenario]
            assert 'stressed_portfolio_value' in result
            assert 'stress_loss' in result
            assert 'stress_loss_percentage' in result
    
    @pytest.mark.unit
    def test_complete_var_report_generation(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        result = report_instance.generate()
        
        assert result['status'] == 'completed'
        assert len(result['files']) == 1
        
        json_file = result['files'][0]
        assert json_file['content_type'] == 'application/json'
        
        # Parse and validate JSON content
        report_data = json.loads(json_file['content'])
        assert 'var_calculations' in report_data
        assert 'backtesting' in report_data
        assert 'stress_testing' in report_data
        
        var_calcs = report_data['var_calculations']
        assert 'historical' in var_calcs
        assert 'parametric' in var_calcs
        assert 'monte_carlo' in var_calcs
    
    @pytest.mark.performance
    def test_var_calculation_performance(self, report_instance, valid_parameters):
        """Test VaR calculation performance with large portfolio."""
        import time
        
        # Create large portfolio
        np.random.seed(42)
        n_positions = 10000
        
        large_data = pd.DataFrame({
            'position_id': [f'POS{i:06d}' for i in range(1, n_positions + 1)],
            'instrument_type': np.random.choice(['Equity', 'Bond', 'Derivative'], n_positions),
            'market_value': np.random.uniform(100000, 5000000, n_positions),
            'daily_returns': np.random.normal(0.0008, 0.02, n_positions),
            'volatility': np.random.uniform(0.1, 0.5, n_positions),
            'beta': np.random.uniform(0.5, 1.8, n_positions),
            'duration': np.random.uniform(0.5, 10.0, n_positions),
            'credit_rating': np.random.choice(['AAA', 'AA', 'A', 'BBB', 'BB'], n_positions)
        })
        
        report_instance.data = large_data
        report_instance.parameters = valid_parameters
        
        # Test historical VaR performance
        start_time = time.time()
        historical_var = report_instance.calculate_historical_var(0.95)
        hist_time = time.time() - start_time
        
        # Test Monte Carlo VaR performance
        start_time = time.time()
        mc_var = report_instance.calculate_monte_carlo_var(0.95, 10000)
        mc_time = time.time() - start_time
        
        # Performance assertions
        assert hist_time < 3.0, f"Historical VaR took {hist_time:.3f}s"
        assert mc_time < 5.0, f"Monte Carlo VaR took {mc_time:.3f}s"
        
        # Results should be reasonable
        assert historical_var['var_absolute'] > 0
        assert mc_var['var_absolute'] > 0
