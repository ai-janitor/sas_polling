"""
=============================================================================
STRESS TEST REPORT GENERATOR UNIT TESTS
=============================================================================
Purpose: Unit tests for regulatory stress testing report (CCAR/DFAST)
Module: reports/stress_test.py

TEST CATEGORIES:
1. Stress Scenario Generation
2. Portfolio Impact Analysis
3. Regulatory Compliance
4. Capital Adequacy Assessment
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

class StressTestReport:
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.required_fields = ['test_type', 'scenario_year', 'bank_id']
        self.data = None
        
    def validate_parameters(self):
        errors = []
        for field in self.required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        
        if 'test_type' in self.parameters:
            valid_types = ['CCAR', 'DFAST', 'ICAAP', 'Custom']
            if self.parameters['test_type'] not in valid_types:
                errors.append(f"Test type must be one of: {', '.join(valid_types)}")
        
        return errors
    
    def load_portfolio_data(self):
        np.random.seed(42)
        n_exposures = 1000
        
        self.data = pd.DataFrame({
            'exposure_id': [f'EXP{i:05d}' for i in range(1, n_exposures + 1)],
            'asset_class': np.random.choice(['Corporate', 'Retail', 'RE_Commercial', 'RE_Residential'], n_exposures),
            'geography': np.random.choice(['US', 'EU', 'APAC', 'Other'], n_exposures),
            'exposure_amount': np.random.uniform(1000000, 100000000, n_exposures),
            'pd_baseline': np.random.uniform(0.005, 0.15, n_exposures),
            'lgd_baseline': np.random.uniform(0.2, 0.6, n_exposures),
            'rating': np.random.choice(['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC'], n_exposures),
            'maturity': np.random.uniform(0.5, 15.0, n_exposures)
        })
        
        return self.data
    
    def generate_stress_scenarios(self):
        """Generate regulatory stress scenarios."""
        scenarios = {
            'severely_adverse': {
                'gdp_shock': -0.055,
                'unemployment_peak': 0.105,
                'house_price_decline': -0.25,
                'equity_shock': -0.45,
                'credit_spread_shock': 0.004
            },
            'adverse': {
                'gdp_shock': -0.035,
                'unemployment_peak': 0.08,
                'house_price_decline': -0.15,
                'equity_shock': -0.25,
                'credit_spread_shock': 0.002
            },
            'baseline': {
                'gdp_shock': 0.025,
                'unemployment_peak': 0.045,
                'house_price_decline': 0.05,
                'equity_shock': 0.08,
                'credit_spread_shock': 0.0
            }
        }
        
        return scenarios
    
    def calculate_credit_losses(self, scenario_params):
        """Calculate expected credit losses under stress."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Apply stress factors to PD and LGD
        stressed_pd = self._apply_pd_stress(scenario_params)
        stressed_lgd = self._apply_lgd_stress(scenario_params)
        
        # Calculate expected losses
        expected_losses = self.data['exposure_amount'] * stressed_pd * stressed_lgd
        
        # Aggregate by asset class
        loss_by_asset_class = self.data.groupby('asset_class').apply(
            lambda x: (x['exposure_amount'] * 
                      stressed_pd[x.index] * 
                      stressed_lgd[x.index]).sum()
        )
        
        return {
            'total_expected_loss': expected_losses.sum(),
            'loss_rate': expected_losses.sum() / self.data['exposure_amount'].sum(),
            'loss_by_asset_class': loss_by_asset_class.to_dict(),
            'stressed_pd_avg': stressed_pd.mean(),
            'stressed_lgd_avg': stressed_lgd.mean()
        }
    
    def _apply_pd_stress(self, scenario_params):
        """Apply stress factors to probability of default."""
        gdp_impact = max(0, -scenario_params.get('gdp_shock', 0)) * 2.0
        unemployment_impact = scenario_params.get('unemployment_peak', 0.045) * 1.5
        
        stress_multiplier = 1 + gdp_impact + unemployment_impact
        return np.minimum(self.data['pd_baseline'] * stress_multiplier, 0.99)
    
    def _apply_lgd_stress(self, scenario_params):
        """Apply stress factors to loss given default."""
        house_price_impact = max(0, -scenario_params.get('house_price_decline', 0)) * 0.3
        
        # Real estate exposures more sensitive to house price declines
        lgd_stress = self.data['lgd_baseline'].copy()
        re_mask = self.data['asset_class'].isin(['RE_Commercial', 'RE_Residential'])
        lgd_stress[re_mask] += house_price_impact
        
        return np.minimum(lgd_stress, 0.95)
    
    def calculate_capital_impact(self, credit_losses, pre_provision_nii):
        """Calculate impact on capital ratios."""
        # Mock capital calculations
        current_cet1_capital = 50000000000  # $50B
        current_rwa = 400000000000  # $400B
        
        baseline_cet1_ratio = current_cet1_capital / current_rwa
        
        # Calculate stressed capital
        stressed_capital = current_cet1_capital - credit_losses + pre_provision_nii
        stressed_cet1_ratio = stressed_capital / current_rwa
        
        return {
            'baseline_cet1_ratio': baseline_cet1_ratio,
            'stressed_cet1_ratio': stressed_cet1_ratio,
            'capital_depletion': current_cet1_capital - stressed_capital,
            'minimum_required_ratio': 0.045,  # 4.5% minimum
            'buffer_remaining': stressed_cet1_ratio - 0.045,
            'passes_minimum': stressed_cet1_ratio >= 0.045
        }
    
    def generate_comprehensive_analysis(self):
        """Generate comprehensive stress test analysis."""
        scenarios = self.generate_stress_scenarios()
        results = {}
        
        for scenario_name, scenario_params in scenarios.items():
            credit_losses = self.calculate_credit_losses(scenario_params)
            
            # Mock pre-provision net interest income
            pre_provision_nii = np.random.uniform(8000000000, 12000000000)  # $8-12B
            
            capital_impact = self.calculate_capital_impact(
                credit_losses['total_expected_loss'], 
                pre_provision_nii
            )
            
            results[scenario_name] = {
                'scenario_parameters': scenario_params,
                'credit_losses': credit_losses,
                'capital_impact': capital_impact,
                'pre_provision_nii': pre_provision_nii
            }
        
        return results
    
    def generate(self):
        """Generate complete stress test report."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
        
        self.load_portfolio_data()
        analysis_results = self.generate_comprehensive_analysis()
        
        # Generate summary
        summary = {
            'test_details': {
                'test_type': self.parameters.get('test_type'),
                'scenario_year': self.parameters.get('scenario_year'),
                'bank_id': self.parameters.get('bank_id'),
                'portfolio_size': len(self.data),
                'total_exposure': self.data['exposure_amount'].sum()
            },
            'scenario_results': analysis_results,
            'regulatory_compliance': self._assess_regulatory_compliance(analysis_results)
        }
        
        json_content = json.dumps(summary, indent=2, default=str)
        
        return {
            'status': 'completed',
            'files': [{
                'filename': f"stress_test_{self.parameters.get('test_type', 'unknown')}_{self.parameters.get('scenario_year', 'latest')}.json",
                'content': json_content,
                'content_type': 'application/json',
                'size': len(json_content.encode('utf-8'))
            }],
            'metadata': {
                'report_type': 'Stress Test',
                'test_type': self.parameters.get('test_type'),
                'scenarios_tested': list(analysis_results.keys()),
                'compliance_status': 'PASS' if all(r['capital_impact']['passes_minimum'] for r in analysis_results.values()) else 'FAIL'
            }
        }
    
    def _assess_regulatory_compliance(self, results):
        """Assess regulatory compliance across scenarios."""
        compliance = {}
        
        for scenario_name, scenario_results in results.items():
            capital_impact = scenario_results['capital_impact']
            compliance[scenario_name] = {
                'meets_minimum_capital': capital_impact['passes_minimum'],
                'cet1_ratio': capital_impact['stressed_cet1_ratio'],
                'buffer_above_minimum': capital_impact['buffer_remaining']
            }
        
        return compliance


class TestStressTestReport:
    @pytest.fixture
    def report_instance(self):
        return StressTestReport()
    
    @pytest.fixture
    def valid_parameters(self):
        return {
            'test_type': 'CCAR',
            'scenario_year': '2024',
            'bank_id': 'BANK_001'
        }
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        errors = report_instance.validate_parameters()
        assert errors == []
    
    @pytest.mark.unit
    def test_invalid_test_type(self, report_instance):
        report_instance.parameters = {
            'test_type': 'INVALID',
            'scenario_year': '2024',
            'bank_id': 'BANK_001'
        }
        errors = report_instance.validate_parameters()
        assert len(errors) > 0
        assert any('Test type must be' in error for error in errors)
    
    @pytest.mark.unit
    def test_stress_scenario_generation(self, report_instance):
        scenarios = report_instance.generate_stress_scenarios()
        
        expected_scenarios = ['severely_adverse', 'adverse', 'baseline']
        for scenario in expected_scenarios:
            assert scenario in scenarios
            
        # Check scenario structure
        for scenario_name, params in scenarios.items():
            assert 'gdp_shock' in params
            assert 'unemployment_peak' in params
            assert 'house_price_decline' in params
    
    @pytest.mark.unit
    def test_credit_loss_calculation(self, report_instance):
        report_instance.load_portfolio_data()
        
        # Test with severely adverse scenario
        scenario_params = {
            'gdp_shock': -0.055,
            'unemployment_peak': 0.105,
            'house_price_decline': -0.25
        }
        
        losses = report_instance.calculate_credit_losses(scenario_params)
        
        assert 'total_expected_loss' in losses
        assert 'loss_rate' in losses
        assert 'loss_by_asset_class' in losses
        assert losses['total_expected_loss'] > 0
        assert 0 <= losses['loss_rate'] <= 1
    
    @pytest.mark.unit
    def test_capital_impact_calculation(self, report_instance):
        credit_losses = 5000000000  # $5B losses
        pre_provision_nii = 10000000000  # $10B income
        
        capital_impact = report_instance.calculate_capital_impact(credit_losses, pre_provision_nii)
        
        assert 'baseline_cet1_ratio' in capital_impact
        assert 'stressed_cet1_ratio' in capital_impact
        assert 'passes_minimum' in capital_impact
        
        assert capital_impact['baseline_cet1_ratio'] > 0
        assert capital_impact['stressed_cet1_ratio'] >= 0
    
    @pytest.mark.unit
    def test_comprehensive_analysis(self, report_instance):
        report_instance.load_portfolio_data()
        results = report_instance.generate_comprehensive_analysis()
        
        expected_scenarios = ['severely_adverse', 'adverse', 'baseline']
        for scenario in expected_scenarios:
            assert scenario in results
            
            scenario_result = results[scenario]
            assert 'scenario_parameters' in scenario_result
            assert 'credit_losses' in scenario_result
            assert 'capital_impact' in scenario_result
    
    @pytest.mark.unit
    def test_complete_stress_test_generation(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        result = report_instance.generate()
        
        assert result['status'] == 'completed'
        assert len(result['files']) == 1
        
        json_file = result['files'][0]
        assert 'CCAR' in json_file['filename']
        
        # Parse and validate content
        report_data = json.loads(json_file['content'])
        assert 'test_details' in report_data
        assert 'scenario_results' in report_data
        assert 'regulatory_compliance' in report_data
    
    @pytest.mark.unit
    def test_regulatory_compliance_assessment(self, report_instance):
        # Mock scenario results
        mock_results = {
            'severely_adverse': {
                'capital_impact': {
                    'passes_minimum': True,
                    'stressed_cet1_ratio': 0.08,
                    'buffer_remaining': 0.035
                }
            },
            'baseline': {
                'capital_impact': {
                    'passes_minimum': True,
                    'stressed_cet1_ratio': 0.12,
                    'buffer_remaining': 0.075
                }
            }
        }
        
        compliance = report_instance._assess_regulatory_compliance(mock_results)
        
        for scenario_name in mock_results.keys():
            assert scenario_name in compliance
            assert 'meets_minimum_capital' in compliance[scenario_name]
            assert compliance[scenario_name]['meets_minimum_capital'] is True
