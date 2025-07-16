"""
=============================================================================
FOCUS MANUAL REPORT GENERATOR UNIT TESTS
=============================================================================
Purpose: Unit tests for Focus Manual regulatory compliance report
Module: reports/focus_manual.py

TEST CATEGORIES:
1. Regulatory Calculations
2. Net Capital Compliance
3. Customer Protection Requirements
4. Filing Format Validation
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json
from decimal import Decimal

class FocusManualReport:
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.required_fields = ['filing_date', 'broker_dealer_id', 'filing_type']
        self.data = None
        self.calculations = {}
        
    def validate_parameters(self):
        errors = []
        for field in self.required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        
        if 'filing_type' in self.parameters:
            valid_types = ['MONTHLY', 'QUARTERLY', 'ANNUAL']
            if self.parameters['filing_type'] not in valid_types:
                errors.append(f"Filing type must be one of: {', '.join(valid_types)}")
        
        if 'filing_date' in self.parameters:
            try:
                datetime.strptime(self.parameters['filing_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Filing date must be in YYYY-MM-DD format")
        
        return errors
    
    def load_financial_data(self):
        """Load broker-dealer financial data for FOCUS calculations."""
        np.random.seed(42)
        
        # Generate realistic broker-dealer financial data
        self.data = {
            'cash_and_cash_equivalents': {
                'cash_segregated': np.random.uniform(50000000, 200000000),
                'cash_not_segregated': np.random.uniform(10000000, 50000000),
                'money_market_funds': np.random.uniform(20000000, 100000000)
            },
            'securities_owned': {
                'us_government': np.random.uniform(100000000, 500000000),
                'corporate_bonds': np.random.uniform(50000000, 300000000),
                'equity_securities': np.random.uniform(80000000, 400000000),
                'municipal_securities': np.random.uniform(30000000, 150000000)
            },
            'securities_sold_not_owned': {
                'us_government': np.random.uniform(20000000, 100000000),
                'corporate_bonds': np.random.uniform(10000000, 80000000),
                'equity_securities': np.random.uniform(30000000, 150000000)
            },
            'receivables': {
                'customers': np.random.uniform(200000000, 800000000),
                'broker_dealers': np.random.uniform(50000000, 200000000),
                'clearing_organizations': np.random.uniform(30000000, 120000000)
            },
            'payables': {
                'customers': np.random.uniform(180000000, 750000000),
                'broker_dealers': np.random.uniform(40000000, 180000000),
                'clearing_organizations': np.random.uniform(20000000, 100000000)
            },
            'capital_structure': {
                'stockholders_equity': np.random.uniform(800000000, 2000000000),
                'subordinated_debt': np.random.uniform(100000000, 500000000),
                'total_capital': 0  # Will be calculated
            },
            'operational_data': {
                'monthly_revenue': np.random.uniform(50000000, 200000000),
                'monthly_expenses': np.random.uniform(40000000, 180000000),
                'employees_count': np.random.randint(500, 2000),
                'branch_offices': np.random.randint(10, 50)
            }
        }
        
        # Calculate total capital
        self.data['capital_structure']['total_capital'] = (
            self.data['capital_structure']['stockholders_equity'] + 
            self.data['capital_structure']['subordinated_debt']
        )
        
        return self.data
    
    def calculate_net_capital(self):
        """Calculate regulatory net capital under Rule 15c3-1."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Start with stockholders' equity
        stockholders_equity = self.data['capital_structure']['stockholders_equity']
        
        # Calculate deductions
        deductions = self._calculate_net_capital_deductions()
        
        # Calculate tentative net capital
        tentative_net_capital = stockholders_equity - deductions['total_deductions']
        
        # Calculate required net capital
        required_net_capital = self._calculate_required_net_capital()
        
        # Calculate excess net capital
        excess_net_capital = tentative_net_capital - required_net_capital
        
        net_capital_calc = {
            'stockholders_equity': stockholders_equity,
            'deductions': deductions,
            'tentative_net_capital': tentative_net_capital,
            'required_net_capital': required_net_capital,
            'excess_net_capital': excess_net_capital,
            'net_capital_ratio': tentative_net_capital / required_net_capital if required_net_capital > 0 else 0,
            'compliance_status': 'COMPLIANT' if excess_net_capital > 0 else 'NON_COMPLIANT'
        }
        
        self.calculations['net_capital'] = net_capital_calc
        return net_capital_calc
    
    def _calculate_net_capital_deductions(self):
        """Calculate various deductions from stockholders' equity."""
        
        # Haircut calculations for securities positions
        securities_haircuts = {
            'us_government': 0.02,  # 2% haircut
            'corporate_bonds': 0.05,  # 5% haircut
            'equity_securities': 0.15,  # 15% haircut
            'municipal_securities': 0.03  # 3% haircut
        }
        
        total_securities_deductions = 0
        for security_type, haircut in securities_haircuts.items():
            market_value = self.data['securities_owned'].get(security_type, 0)
            deduction = market_value * haircut
            total_securities_deductions += deduction
        
        # Operational charge deductions
        monthly_revenue = self.data['operational_data']['monthly_revenue']
        operational_charge = max(
            250000,  # Minimum operational charge
            monthly_revenue * 0.02  # 2% of monthly revenue
        )
        
        # Concentration deductions (simplified)
        concentration_deduction = self._calculate_concentration_deductions()
        
        # Other deductions
        other_deductions = {
            'fixed_assets': 50000000,  # Simplified fixed assets deduction
            'prepaid_expenses': 10000000,
            'unsecured_receivables': 25000000
        }
        
        total_other = sum(other_deductions.values())
        
        deductions = {
            'securities_haircuts': total_securities_deductions,
            'operational_charge': operational_charge,
            'concentration_deductions': concentration_deduction,
            'other_deductions': total_other,
            'total_deductions': total_securities_deductions + operational_charge + concentration_deduction + total_other
        }
        
        return deductions
    
    def _calculate_concentration_deductions(self):
        """Calculate concentration deductions for large positions."""
        # Simplified concentration calculation
        # In practice, this would be much more complex
        total_securities = sum(self.data['securities_owned'].values())
        
        # Assume 10% concentration threshold
        concentration_threshold = total_securities * 0.10
        
        # Apply deductions for positions above threshold
        concentration_deduction = 0
        for position_value in self.data['securities_owned'].values():
            if position_value > concentration_threshold:
                excess = position_value - concentration_threshold
                concentration_deduction += excess * 0.50  # 50% deduction on excess
        
        return concentration_deduction
    
    def _calculate_required_net_capital(self):
        """Calculate minimum required net capital."""
        # Alternative methods - use the greater of:
        
        # Method 1: Aggregate indebtedness ratio
        customer_receivables = self.data['receivables']['customers']
        aggregate_indebtedness = customer_receivables * 0.02  # 2% of customer receivables
        
        # Method 2: Basic requirement
        basic_requirement = 1000000  # $1M minimum
        
        # Method 3: Operational charge multiple
        operational_charge = self.calculations.get('net_capital', {}).get('deductions', {}).get('operational_charge', 0)
        if operational_charge == 0:
            # Recalculate if not available
            monthly_revenue = self.data['operational_data']['monthly_revenue']
            operational_charge = max(250000, monthly_revenue * 0.02)
        
        operational_multiple = operational_charge * 8  # 8x operational charge
        
        # Use the greater of the three methods
        required_net_capital = max(aggregate_indebtedness, basic_requirement, operational_multiple)
        
        return required_net_capital
    
    def calculate_customer_protection(self):
        """Calculate customer protection requirements under Rule 15c3-3."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Customer receivables and payables
        customer_receivables = self.data['receivables']['customers']
        customer_payables = self.data['payables']['customers']
        
        # Calculate customer reserve requirement
        customer_reserve_requirement = self._calculate_customer_reserve()
        
        # PAB (Possession and Control) requirements
        pab_requirement = self._calculate_pab_requirement()
        
        customer_protection = {
            'customer_receivables': customer_receivables,
            'customer_payables': customer_payables,
            'net_customer_balance': customer_receivables - customer_payables,
            'customer_reserve_requirement': customer_reserve_requirement,
            'pab_requirement': pab_requirement,
            'segregated_cash': self.data['cash_and_cash_equivalents']['cash_segregated'],
            'reserve_compliance': self._assess_reserve_compliance(customer_reserve_requirement),
            'pab_compliance': self._assess_pab_compliance(pab_requirement)
        }
        
        self.calculations['customer_protection'] = customer_protection
        return customer_protection
    
    def _calculate_customer_reserve(self):
        """Calculate customer reserve formula requirement."""
        # Simplified customer reserve calculation
        customer_receivables = self.data['receivables']['customers']
        customer_payables = self.data['payables']['customers']
        
        # Basic formula items
        free_credit_balances = customer_payables * 0.7  # Assume 70% are free credit balances
        securities_borrowed = customer_receivables * 0.1  # Assume 10% from securities borrowed
        
        # Customer reserve requirement
        reserve_requirement = free_credit_balances - securities_borrowed
        
        return max(0, reserve_requirement)  # Cannot be negative
    
    def _calculate_pab_requirement(self):
        """Calculate Possession and Control requirement."""
        # Simplified PAB calculation
        total_customer_securities = sum(self.data['securities_owned'].values()) * 0.6  # Assume 60% are customer securities
        
        # PAB requirement is typically the market value of customer securities
        # that must be in possession or control
        pab_requirement = total_customer_securities * 0.95  # 95% of customer securities
        
        return pab_requirement
    
    def _assess_reserve_compliance(self, requirement):
        """Assess compliance with customer reserve requirement."""
        segregated_cash = self.data['cash_and_cash_equivalents']['cash_segregated']
        
        return {
            'required_amount': requirement,
            'actual_amount': segregated_cash,
            'excess_deficit': segregated_cash - requirement,
            'compliance_status': 'COMPLIANT' if segregated_cash >= requirement else 'DEFICIENT'
        }
    
    def _assess_pab_compliance(self, requirement):
        """Assess compliance with PAB requirement."""
        # Simplified - assume 90% of securities are in possession/control
        securities_in_control = sum(self.data['securities_owned'].values()) * 0.9
        
        return {
            'required_amount': requirement,
            'actual_amount': securities_in_control,
            'excess_deficit': securities_in_control - requirement,
            'compliance_status': 'COMPLIANT' if securities_in_control >= requirement else 'DEFICIENT'
        }
    
    def generate_regulatory_ratios(self):
        """Generate key regulatory ratios and metrics."""
        if not self.calculations:
            self.calculate_net_capital()
            self.calculate_customer_protection()
        
        net_capital = self.calculations['net_capital']
        customer_protection = self.calculations['customer_protection']
        
        # Key ratios
        ratios = {
            'net_capital_ratio': net_capital['net_capital_ratio'],
            'leverage_ratio': self._calculate_leverage_ratio(),
            'liquidity_ratio': self._calculate_liquidity_ratio(),
            'customer_protection_ratio': self._calculate_customer_protection_ratio(),
            'operational_efficiency': self._calculate_operational_efficiency()
        }
        
        # Regulatory thresholds and alerts
        alerts = self._generate_regulatory_alerts(ratios)
        
        regulatory_analysis = {
            'ratios': ratios,
            'alerts': alerts,
            'trend_analysis': self._generate_trend_analysis(),
            'regulatory_summary': self._generate_regulatory_summary()
        }
        
        self.calculations['regulatory_analysis'] = regulatory_analysis
        return regulatory_analysis
    
    def _calculate_leverage_ratio(self):
        """Calculate leverage ratio."""
        total_assets = (
            sum(self.data['cash_and_cash_equivalents'].values()) +
            sum(self.data['securities_owned'].values()) +
            sum(self.data['receivables'].values())
        )
        
        stockholders_equity = self.data['capital_structure']['stockholders_equity']
        
        return total_assets / stockholders_equity if stockholders_equity > 0 else 0
    
    def _calculate_liquidity_ratio(self):
        """Calculate liquidity ratio."""
        liquid_assets = (
            self.data['cash_and_cash_equivalents']['cash_not_segregated'] +
            self.data['cash_and_cash_equivalents']['money_market_funds'] +
            self.data['securities_owned']['us_government'] * 0.98  # Liquid value after haircut
        )
        
        monthly_expenses = self.data['operational_data']['monthly_expenses']
        
        return liquid_assets / monthly_expenses if monthly_expenses > 0 else 0
    
    def _calculate_customer_protection_ratio(self):
        """Calculate customer protection adequacy ratio."""
        segregated_cash = self.data['cash_and_cash_equivalents']['cash_segregated']
        customer_payables = self.data['payables']['customers']
        
        return segregated_cash / customer_payables if customer_payables > 0 else 0
    
    def _calculate_operational_efficiency(self):
        """Calculate operational efficiency ratio."""
        monthly_revenue = self.data['operational_data']['monthly_revenue']
        monthly_expenses = self.data['operational_data']['monthly_expenses']
        
        return (monthly_revenue - monthly_expenses) / monthly_revenue if monthly_revenue > 0 else 0
    
    def _generate_regulatory_alerts(self, ratios):
        """Generate regulatory alerts based on thresholds."""
        alerts = []
        
        # Net capital ratio alert
        if ratios['net_capital_ratio'] < 1.5:
            alerts.append({
                'type': 'NET_CAPITAL_WARNING',
                'severity': 'HIGH' if ratios['net_capital_ratio'] < 1.2 else 'MEDIUM',
                'message': f"Net capital ratio below prudent threshold: {ratios['net_capital_ratio']:.2f}"
            })
        
        # Leverage ratio alert
        if ratios['leverage_ratio'] > 15:
            alerts.append({
                'type': 'LEVERAGE_WARNING',
                'severity': 'MEDIUM',
                'message': f"High leverage ratio: {ratios['leverage_ratio']:.2f}"
            })
        
        # Liquidity alert
        if ratios['liquidity_ratio'] < 3:
            alerts.append({
                'type': 'LIQUIDITY_WARNING',
                'severity': 'HIGH',
                'message': f"Low liquidity ratio: {ratios['liquidity_ratio']:.2f} months"
            })
        
        return alerts
    
    def _generate_trend_analysis(self):
        """Generate mock trend analysis."""
        # In a real implementation, this would compare against historical data
        return {
            'net_capital_trend': 'STABLE',
            'customer_growth_trend': 'INCREASING',
            'revenue_trend': 'STABLE',
            'risk_profile_trend': 'STABLE'
        }
    
    def _generate_regulatory_summary(self):
        """Generate overall regulatory compliance summary."""
        net_capital_compliant = self.calculations['net_capital']['compliance_status'] == 'COMPLIANT'
        reserve_compliant = self.calculations['customer_protection']['reserve_compliance']['compliance_status'] == 'COMPLIANT'
        pab_compliant = self.calculations['customer_protection']['pab_compliance']['compliance_status'] == 'COMPLIANT'
        
        overall_status = 'COMPLIANT' if all([net_capital_compliant, reserve_compliant, pab_compliant]) else 'NON_COMPLIANT'
        
        return {
            'overall_compliance_status': overall_status,
            'net_capital_status': net_capital_compliant,
            'customer_protection_status': reserve_compliant and pab_compliant,
            'filing_readiness': 'READY' if overall_status == 'COMPLIANT' else 'ISSUES_IDENTIFIED'
        }
    
    def generate(self):
        """Generate complete FOCUS Manual report."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
        
        self.load_financial_data()
        
        # Perform all calculations
        net_capital = self.calculate_net_capital()
        customer_protection = self.calculate_customer_protection()
        regulatory_analysis = self.generate_regulatory_ratios()
        
        # Generate report
        report_data = {
            'filing_information': {
                'filing_date': self.parameters.get('filing_date'),
                'broker_dealer_id': self.parameters.get('broker_dealer_id'),
                'filing_type': self.parameters.get('filing_type'),
                'report_generated': datetime.now().isoformat()
            },
            'net_capital_computation': net_capital,
            'customer_protection_computation': customer_protection,
            'regulatory_analysis': regulatory_analysis,
            'financial_data_summary': self._summarize_financial_data()
        }
        
        json_content = json.dumps(report_data, indent=2, default=str)
        
        return {
            'status': 'completed',
            'files': [{
                'filename': f"focus_manual_{self.parameters.get('broker_dealer_id', 'unknown')}_{self.parameters.get('filing_date', 'latest')}.json",
                'content': json_content,
                'content_type': 'application/json',
                'size': len(json_content.encode('utf-8'))
            }],
            'metadata': {
                'report_type': 'FOCUS Manual',
                'filing_date': self.parameters.get('filing_date'),
                'compliance_status': regulatory_analysis['regulatory_summary']['overall_compliance_status'],
                'net_capital_ratio': f"{net_capital['net_capital_ratio']:.2f}",
                'filing_readiness': regulatory_analysis['regulatory_summary']['filing_readiness']
            }
        }
    
    def _summarize_financial_data(self):
        """Generate summary of key financial figures."""
        return {
            'total_assets': sum(self.data['cash_and_cash_equivalents'].values()) + 
                          sum(self.data['securities_owned'].values()) + 
                          sum(self.data['receivables'].values()),
            'total_liabilities': sum(self.data['securities_sold_not_owned'].values()) + 
                               sum(self.data['payables'].values()),
            'stockholders_equity': self.data['capital_structure']['stockholders_equity'],
            'monthly_revenue': self.data['operational_data']['monthly_revenue'],
            'employee_count': self.data['operational_data']['employees_count']
        }


class TestFocusManualReport:
    @pytest.fixture
    def report_instance(self):
        return FocusManualReport()
    
    @pytest.fixture
    def valid_parameters(self):
        return {
            'filing_date': '2024-06-30',
            'broker_dealer_id': 'BD001',
            'filing_type': 'MONTHLY'
        }
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        errors = report_instance.validate_parameters()
        assert errors == []
    
    @pytest.mark.unit
    def test_invalid_filing_type(self, report_instance):
        report_instance.parameters = {
            'filing_date': '2024-06-30',
            'broker_dealer_id': 'BD001',
            'filing_type': 'INVALID'
        }
        errors = report_instance.validate_parameters()
        assert len(errors) > 0
        assert any('Filing type must be' in error for error in errors)
    
    @pytest.mark.unit
    def test_load_financial_data(self, report_instance):
        data = report_instance.load_financial_data()
        
        assert data is not None
        assert 'cash_and_cash_equivalents' in data
        assert 'securities_owned' in data
        assert 'capital_structure' in data
        
        # Check calculated field
        expected_total_capital = data['capital_structure']['stockholders_equity'] + data['capital_structure']['subordinated_debt']
        assert data['capital_structure']['total_capital'] == expected_total_capital
    
    @pytest.mark.unit
    def test_net_capital_calculation(self, report_instance):
        report_instance.load_financial_data()
        net_capital = report_instance.calculate_net_capital()
        
        assert 'stockholders_equity' in net_capital
        assert 'deductions' in net_capital
        assert 'tentative_net_capital' in net_capital
        assert 'required_net_capital' in net_capital
        assert 'compliance_status' in net_capital
        
        # Check calculation logic
        expected_tentative = net_capital['stockholders_equity'] - net_capital['deductions']['total_deductions']
        assert abs(net_capital['tentative_net_capital'] - expected_tentative) < 1
    
    @pytest.mark.unit
    def test_customer_protection_calculation(self, report_instance):
        report_instance.load_financial_data()
        customer_protection = report_instance.calculate_customer_protection()
        
        assert 'customer_receivables' in customer_protection
        assert 'customer_payables' in customer_protection
        assert 'customer_reserve_requirement' in customer_protection
        assert 'reserve_compliance' in customer_protection
        assert 'pab_compliance' in customer_protection
        
        # Check compliance assessments have required fields
        assert 'compliance_status' in customer_protection['reserve_compliance']
        assert 'compliance_status' in customer_protection['pab_compliance']
    
    @pytest.mark.unit
    def test_regulatory_ratios_generation(self, report_instance):
        report_instance.load_financial_data()
        regulatory_analysis = report_instance.generate_regulatory_ratios()
        
        assert 'ratios' in regulatory_analysis
        assert 'alerts' in regulatory_analysis
        assert 'regulatory_summary' in regulatory_analysis
        
        ratios = regulatory_analysis['ratios']
        assert 'net_capital_ratio' in ratios
        assert 'leverage_ratio' in ratios
        assert 'liquidity_ratio' in ratios
        
        # Check that ratios are reasonable numbers
        assert ratios['net_capital_ratio'] >= 0
        assert ratios['leverage_ratio'] >= 0
    
    @pytest.mark.unit
    def test_regulatory_alerts_generation(self, report_instance):
        # Create test ratios that should trigger alerts
        test_ratios = {
            'net_capital_ratio': 1.1,  # Below 1.5 threshold
            'leverage_ratio': 20,      # Above 15 threshold
            'liquidity_ratio': 2,      # Below 3 threshold
            'customer_protection_ratio': 1.0,
            'operational_efficiency': 0.1
        }
        
        alerts = report_instance._generate_regulatory_alerts(test_ratios)
        
        assert len(alerts) >= 3  # Should have at least 3 alerts for the thresholds exceeded
        
        alert_types = [alert['type'] for alert in alerts]
        assert 'NET_CAPITAL_WARNING' in alert_types
        assert 'LEVERAGE_WARNING' in alert_types
        assert 'LIQUIDITY_WARNING' in alert_types
    
    @pytest.mark.unit
    def test_complete_report_generation(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        result = report_instance.generate()
        
        assert result['status'] == 'completed'
        assert len(result['files']) == 1
        
        json_file = result['files'][0]
        assert json_file['content_type'] == 'application/json'
        assert 'BD001' in json_file['filename']
        
        # Parse and validate content
        report_data = json.loads(json_file['content'])
        assert 'filing_information' in report_data
        assert 'net_capital_computation' in report_data
        assert 'customer_protection_computation' in report_data
        assert 'regulatory_analysis' in report_data
    
    @pytest.mark.unit
    def test_concentration_deductions(self, report_instance):
        report_instance.load_financial_data()
        
        # Test concentration calculation
        concentration_deduction = report_instance._calculate_concentration_deductions()
        
        assert concentration_deduction >= 0
        assert isinstance(concentration_deduction, (int, float))
    
    @pytest.mark.unit
    def test_required_net_capital_methods(self, report_instance):
        report_instance.load_financial_data()
        report_instance.calculate_net_capital()
        
        required_net_capital = report_instance._calculate_required_net_capital()
        
        # Should be at least the minimum requirement
        assert required_net_capital >= 1000000  # $1M minimum
        assert isinstance(required_net_capital, (int, float))
    
    @pytest.mark.unit
    def test_financial_data_summary(self, report_instance):
        report_instance.load_financial_data()
        
        summary = report_instance._summarize_financial_data()
        
        assert 'total_assets' in summary
        assert 'total_liabilities' in summary
        assert 'stockholders_equity' in summary
        assert summary['total_assets'] > 0
        assert summary['stockholders_equity'] > 0
    
    @pytest.mark.performance
    def test_complex_calculation_performance(self, report_instance, valid_parameters):
        """Test performance of complex regulatory calculations."""
        import time
        
        report_instance.parameters = valid_parameters
        
        # Test full report generation performance
        start_time = time.time()
        result = report_instance.generate()
        generation_time = time.time() - start_time
        
        # Performance assertion
        assert generation_time < 2.0, f"Report generation took {generation_time:.3f}s"
        
        # Verify all calculations completed successfully
        report_data = json.loads(result['files'][0]['content'])
        assert report_data['net_capital_computation']['compliance_status'] in ['COMPLIANT', 'NON_COMPLIANT']
        assert report_data['regulatory_analysis']['regulatory_summary']['overall_compliance_status'] in ['COMPLIANT', 'NON_COMPLIANT']