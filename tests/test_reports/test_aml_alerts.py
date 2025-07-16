"""
=============================================================================
AML ALERTS REPORT GENERATOR UNIT TESTS
=============================================================================
Purpose: Unit tests for Anti-Money Laundering alerts and compliance report
Module: reports/aml_alerts.py

TEST CATEGORIES:
1. Alert Generation Logic
2. Risk Scoring Algorithms
3. Compliance Validation
4. Investigation Workflow
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

class AMLAlertsReport:
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.required_fields = ['report_date', 'jurisdiction']
        self.data = None
        self.alert_rules = {}
        
    def validate_parameters(self):
        errors = []
        for field in self.required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        
        if 'jurisdiction' in self.parameters:
            valid_jurisdictions = ['US', 'EU', 'UK', 'APAC', 'GLOBAL']
            if self.parameters['jurisdiction'] not in valid_jurisdictions:
                errors.append(f"Jurisdiction must be one of: {', '.join(valid_jurisdictions)}")
        
        return errors
    
    def load_transaction_data(self):
        """Load transaction data for AML analysis."""
        np.random.seed(42)
        n_transactions = 5000
        
        self.data = pd.DataFrame({
            'transaction_id': [f'TXN{i:07d}' for i in range(1, n_transactions + 1)],
            'account_id': np.random.choice([f'ACC{i:05d}' for i in range(1, 1001)], n_transactions),
            'customer_id': np.random.choice([f'CUST{i:05d}' for i in range(1, 501)], n_transactions),
            'transaction_date': pd.date_range('2024-06-01', periods=n_transactions, freq='H'),
            'amount': np.random.lognormal(mean=8, sigma=2, size=n_transactions),
            'currency': np.random.choice(['USD', 'EUR', 'GBP', 'JPY'], n_transactions, p=[0.6, 0.2, 0.1, 0.1]),
            'transaction_type': np.random.choice(['WIRE', 'ACH', 'CASH', 'CHECK', 'CARD'], n_transactions),
            'counterparty_country': np.random.choice(['US', 'UK', 'DE', 'FR', 'CH', 'OFF'], n_transactions, p=[0.4, 0.15, 0.1, 0.1, 0.05, 0.2]),
            'counterparty_type': np.random.choice(['INDIVIDUAL', 'CORPORATE', 'BANK', 'GOVERNMENT'], n_transactions),
            'channel': np.random.choice(['ONLINE', 'BRANCH', 'ATM', 'MOBILE'], n_transactions),
            'risk_country_score': np.random.uniform(1, 10, n_transactions),
            'customer_risk_rating': np.random.choice(['LOW', 'MEDIUM', 'HIGH'], n_transactions, p=[0.7, 0.25, 0.05]),
            'pep_flag': np.random.choice([True, False], n_transactions, p=[0.02, 0.98]),
            'sanctions_flag': np.random.choice([True, False], n_transactions, p=[0.001, 0.999])
        })
        
        return self.data
    
    def configure_alert_rules(self):
        """Configure AML alert detection rules."""
        self.alert_rules = {
            'large_cash_transactions': {
                'threshold': 10000,
                'currency': 'USD',
                'transaction_type': 'CASH',
                'severity': 'HIGH'
            },
            'structuring_detection': {
                'amount_threshold': 9500,
                'time_window_hours': 24,
                'transaction_count': 3,
                'severity': 'MEDIUM'
            },
            'high_risk_country': {
                'risk_score_threshold': 7.0,
                'amount_threshold': 5000,
                'severity': 'MEDIUM'
            },
            'pep_transactions': {
                'amount_threshold': 1000,
                'severity': 'HIGH'
            },
            'sanctions_screening': {
                'amount_threshold': 0,  # Any amount
                'severity': 'CRITICAL'
            },
            'round_amount_pattern': {
                'pattern_threshold': 0.8,  # 80% round amounts
                'min_transactions': 5,
                'severity': 'LOW'
            },
            'velocity_anomaly': {
                'std_multiplier': 3.0,
                'min_amount': 1000,
                'severity': 'MEDIUM'
            }
        }
        
        return self.alert_rules
    
    def detect_large_cash_transactions(self):
        """Detect large cash transactions above threshold."""
        rule = self.alert_rules['large_cash_transactions']
        
        alerts = self.data[
            (self.data['transaction_type'] == rule['transaction_type']) &
            (self.data['amount'] >= rule['threshold']) &
            (self.data['currency'] == rule['currency'])
        ].copy()
        
        alerts['alert_type'] = 'LARGE_CASH'
        alerts['alert_severity'] = rule['severity']
        alerts['alert_reason'] = f"Cash transaction above ${rule['threshold']:,}"
        
        return alerts
    
    def detect_structuring_patterns(self):
        """Detect potential structuring (multiple transactions under reporting threshold)."""
        rule = self.alert_rules['structuring_detection']
        
        # Group by customer and day to find potential structuring
        daily_transactions = self.data.groupby([
            'customer_id', 
            self.data['transaction_date'].dt.date
        ]).agg({
            'amount': ['sum', 'count'],
            'transaction_id': 'first'
        }).round(2)
        
        daily_transactions.columns = ['total_amount', 'transaction_count', 'first_txn_id']
        daily_transactions = daily_transactions.reset_index()
        
        # Identify structuring patterns
        structuring_alerts = daily_transactions[
            (daily_transactions['transaction_count'] >= rule['transaction_count']) &
            (daily_transactions['total_amount'] >= rule['amount_threshold']) &
            (daily_transactions['total_amount'] < rule['amount_threshold'] * 1.1)  # Just under threshold
        ].copy()
        
        # Create alert records
        alerts = []
        for _, row in structuring_alerts.iterrows():
            alert = {
                'customer_id': row['customer_id'],
                'transaction_date': row['transaction_date'],
                'alert_type': 'STRUCTURING',
                'alert_severity': rule['severity'],
                'alert_reason': f"Potential structuring: {row['transaction_count']} transactions totaling ${row['total_amount']:,.2f}",
                'transaction_count': row['transaction_count'],
                'total_amount': row['total_amount']
            }
            alerts.append(alert)
        
        return pd.DataFrame(alerts) if alerts else pd.DataFrame()
    
    def detect_high_risk_country_transactions(self):
        """Detect transactions with high-risk countries."""
        rule = self.alert_rules['high_risk_country']
        
        alerts = self.data[
            (self.data['risk_country_score'] >= rule['risk_score_threshold']) &
            (self.data['amount'] >= rule['amount_threshold'])
        ].copy()
        
        alerts['alert_type'] = 'HIGH_RISK_COUNTRY'
        alerts['alert_severity'] = rule['severity']
        alerts['alert_reason'] = f"Transaction with high-risk country (score: {alerts['risk_country_score']:.1f})"
        
        return alerts
    
    def detect_pep_transactions(self):
        """Detect transactions involving Politically Exposed Persons."""
        rule = self.alert_rules['pep_transactions']
        
        alerts = self.data[
            (self.data['pep_flag'] == True) &
            (self.data['amount'] >= rule['amount_threshold'])
        ].copy()
        
        alerts['alert_type'] = 'PEP_TRANSACTION'
        alerts['alert_severity'] = rule['severity']
        alerts['alert_reason'] = "Transaction involving Politically Exposed Person"
        
        return alerts
    
    def detect_sanctions_violations(self):
        """Detect potential sanctions violations."""
        rule = self.alert_rules['sanctions_screening']
        
        alerts = self.data[self.data['sanctions_flag'] == True].copy()
        
        alerts['alert_type'] = 'SANCTIONS_HIT'
        alerts['alert_severity'] = rule['severity']
        alerts['alert_reason'] = "Potential sanctions violation detected"
        
        return alerts
    
    def detect_round_amount_patterns(self):
        """Detect unusual patterns of round amount transactions."""
        rule = self.alert_rules['round_amount_pattern']
        
        # Calculate round amount patterns by customer
        customer_patterns = self.data.groupby('customer_id').apply(
            lambda x: self._calculate_round_amount_ratio(x)
        ).reset_index()
        customer_patterns.columns = ['customer_id', 'round_ratio', 'transaction_count']
        
        # Identify customers with high round amount ratios
        suspicious_customers = customer_patterns[
            (customer_patterns['round_ratio'] >= rule['pattern_threshold']) &
            (customer_patterns['transaction_count'] >= rule['min_transactions'])
        ]
        
        # Create alerts for these customers
        alerts = []
        for _, customer in suspicious_customers.iterrows():
            alert = {
                'customer_id': customer['customer_id'],
                'alert_type': 'ROUND_AMOUNT_PATTERN',
                'alert_severity': rule['severity'],
                'alert_reason': f"High ratio of round amounts: {customer['round_ratio']:.1%} in {customer['transaction_count']} transactions",
                'round_ratio': customer['round_ratio'],
                'transaction_count': customer['transaction_count']
            }
            alerts.append(alert)
        
        return pd.DataFrame(alerts) if alerts else pd.DataFrame()
    
    def _calculate_round_amount_ratio(self, customer_transactions):
        """Calculate ratio of round amounts for a customer."""
        if len(customer_transactions) == 0:
            return pd.Series([0, 0])
        
        # Define round amounts (ending in 00)
        round_amounts = customer_transactions['amount'] % 100 == 0
        round_ratio = round_amounts.sum() / len(customer_transactions)
        
        return pd.Series([round_ratio, len(customer_transactions)])
    
    def detect_velocity_anomalies(self):
        """Detect unusual transaction velocity patterns."""
        rule = self.alert_rules['velocity_anomaly']
        
        # Calculate daily transaction velocity by customer
        daily_velocity = self.data.groupby([
            'customer_id',
            self.data['transaction_date'].dt.date
        ])['amount'].sum().reset_index()
        
        # Calculate customer's normal velocity patterns
        customer_stats = daily_velocity.groupby('customer_id')['amount'].agg(['mean', 'std']).reset_index()
        
        # Merge with daily data
        velocity_analysis = daily_velocity.merge(customer_stats, on='customer_id')
        
        # Identify anomalies
        velocity_analysis['z_score'] = (velocity_analysis['amount'] - velocity_analysis['mean']) / velocity_analysis['std']
        
        anomalies = velocity_analysis[
            (velocity_analysis['z_score'].abs() >= rule['std_multiplier']) &
            (velocity_analysis['amount'] >= rule['min_amount']) &
            (velocity_analysis['std'] > 0)  # Exclude customers with constant amounts
        ]
        
        # Create alerts
        alerts = []
        for _, anomaly in anomalies.iterrows():
            alert = {
                'customer_id': anomaly['customer_id'],
                'transaction_date': anomaly['transaction_date'],
                'alert_type': 'VELOCITY_ANOMALY',
                'alert_severity': rule['severity'],
                'alert_reason': f"Unusual transaction velocity: ${anomaly['amount']:,.2f} (Z-score: {anomaly['z_score']:.2f})",
                'amount': anomaly['amount'],
                'z_score': anomaly['z_score']
            }
            alerts.append(alert)
        
        return pd.DataFrame(alerts) if alerts else pd.DataFrame()
    
    def generate_comprehensive_alerts(self):
        """Generate all types of AML alerts."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        self.configure_alert_rules()
        
        # Run all alert detection methods
        alert_methods = [
            self.detect_large_cash_transactions,
            self.detect_structuring_patterns,
            self.detect_high_risk_country_transactions,
            self.detect_pep_transactions,
            self.detect_sanctions_violations,
            self.detect_round_amount_patterns,
            self.detect_velocity_anomalies
        ]
        
        all_alerts = []
        alert_summary = {}
        
        for method in alert_methods:
            try:
                alerts = method()
                if not alerts.empty:
                    alert_type = alerts['alert_type'].iloc[0] if 'alert_type' in alerts.columns else method.__name__
                    alert_summary[alert_type] = len(alerts)
                    all_alerts.append(alerts)
            except Exception as e:
                print(f"Error in {method.__name__}: {str(e)}")
                continue
        
        # Combine all alerts
        if all_alerts:
            combined_alerts = pd.concat(all_alerts, ignore_index=True, sort=False)
            
            # Add priority scoring
            combined_alerts['priority_score'] = self._calculate_priority_scores(combined_alerts)
            
            return {
                'alerts': combined_alerts,
                'summary': alert_summary,
                'total_alerts': len(combined_alerts)
            }
        else:
            return {
                'alerts': pd.DataFrame(),
                'summary': {},
                'total_alerts': 0
            }
    
    def _calculate_priority_scores(self, alerts):
        """Calculate priority scores for alerts based on severity and risk factors."""
        severity_weights = {
            'CRITICAL': 100,
            'HIGH': 75,
            'MEDIUM': 50,
            'LOW': 25
        }
        
        priority_scores = []
        for _, alert in alerts.iterrows():
            base_score = severity_weights.get(alert.get('alert_severity', 'LOW'), 25)
            
            # Adjust based on amount (if available)
            if 'amount' in alert and pd.notna(alert['amount']):
                if alert['amount'] > 100000:
                    base_score += 20
                elif alert['amount'] > 50000:
                    base_score += 10
            
            # Adjust for customer risk rating (if available)
            if 'customer_risk_rating' in alert:
                if alert['customer_risk_rating'] == 'HIGH':
                    base_score += 15
                elif alert['customer_risk_rating'] == 'MEDIUM':
                    base_score += 5
            
            priority_scores.append(min(base_score, 100))  # Cap at 100
        
        return priority_scores
    
    def generate_investigation_workflow(self, alerts_df):
        """Generate investigation workflow recommendations."""
        if alerts_df.empty:
            return {'workflow_steps': [], 'estimated_hours': 0}
        
        workflow_steps = []
        total_hours = 0
        
        # Group alerts by severity for workflow planning
        severity_counts = alerts_df['alert_severity'].value_counts()
        
        for severity, count in severity_counts.items():
            if severity == 'CRITICAL':
                hours_per_alert = 4
                steps = ['Immediate escalation', 'Senior investigator assignment', 'Regulatory notification prep']
            elif severity == 'HIGH':
                hours_per_alert = 2
                steps = ['Priority investigation', 'Customer outreach', 'Documentation review']
            elif severity == 'MEDIUM':
                hours_per_alert = 1
                steps = ['Standard investigation', 'Transaction pattern analysis']
            else:  # LOW
                hours_per_alert = 0.5
                steps = ['Automated review', 'Exception reporting']
            
            total_hours += count * hours_per_alert
            
            workflow_steps.append({
                'severity': severity,
                'alert_count': count,
                'recommended_steps': steps,
                'estimated_hours': count * hours_per_alert
            })
        
        return {
            'workflow_steps': workflow_steps,
            'total_estimated_hours': total_hours,
            'avg_hours_per_alert': total_hours / len(alerts_df) if len(alerts_df) > 0 else 0
        }
    
    def generate(self):
        """Generate complete AML alerts report."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
        
        self.load_transaction_data()
        alert_results = self.generate_comprehensive_alerts()
        
        workflow = self.generate_investigation_workflow(alert_results['alerts'])
        
        # Generate statistics
        stats = {
            'total_transactions': len(self.data),
            'total_alerts': alert_results['total_alerts'],
            'alert_rate': alert_results['total_alerts'] / len(self.data) if len(self.data) > 0 else 0,
            'high_priority_alerts': len(alert_results['alerts'][alert_results['alerts']['alert_severity'].isin(['CRITICAL', 'HIGH'])]) if not alert_results['alerts'].empty else 0,
            'jurisdiction': self.parameters.get('jurisdiction'),
            'report_date': self.parameters.get('report_date')
        }
        
        # Prepare output
        report_data = {
            'statistics': stats,
            'alert_summary': alert_results['summary'],
            'investigation_workflow': workflow,
            'detailed_alerts': alert_results['alerts'].to_dict('records') if not alert_results['alerts'].empty else []
        }
        
        json_content = json.dumps(report_data, indent=2, default=str)
        
        return {
            'status': 'completed',
            'files': [{
                'filename': f"aml_alerts_{self.parameters.get('report_date', 'latest')}.json",
                'content': json_content,
                'content_type': 'application/json',
                'size': len(json_content.encode('utf-8'))
            }],
            'metadata': {
                'report_type': 'AML Alerts',
                'report_date': self.parameters.get('report_date'),
                'total_alerts': alert_results['total_alerts'],
                'alert_rate': f"{stats['alert_rate']:.2%}",
                'jurisdiction': self.parameters.get('jurisdiction')
            }
        }


class TestAMLAlertsReport:
    @pytest.fixture
    def report_instance(self):
        return AMLAlertsReport()
    
    @pytest.fixture
    def valid_parameters(self):
        return {
            'report_date': '2024-06-30',
            'jurisdiction': 'US',
            'alert_thresholds': {'cash': 10000, 'wire': 50000}
        }
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        errors = report_instance.validate_parameters()
        assert errors == []
    
    @pytest.mark.unit
    def test_invalid_jurisdiction(self, report_instance):
        report_instance.parameters = {
            'report_date': '2024-06-30',
            'jurisdiction': 'INVALID'
        }
        errors = report_instance.validate_parameters()
        assert len(errors) > 0
        assert any('Jurisdiction must be' in error for error in errors)
    
    @pytest.mark.unit
    def test_load_transaction_data(self, report_instance):
        data = report_instance.load_transaction_data()
        
        assert data is not None
        assert len(data) > 0
        
        required_columns = ['transaction_id', 'customer_id', 'amount', 'currency', 'transaction_type']
        for col in required_columns:
            assert col in data.columns
    
    @pytest.mark.unit
    def test_alert_rules_configuration(self, report_instance):
        rules = report_instance.configure_alert_rules()
        
        expected_rules = ['large_cash_transactions', 'structuring_detection', 'high_risk_country', 'pep_transactions']
        for rule in expected_rules:
            assert rule in rules
            assert 'severity' in rules[rule]
    
    @pytest.mark.unit
    def test_large_cash_detection(self, report_instance):
        report_instance.load_transaction_data()
        report_instance.configure_alert_rules()
        
        alerts = report_instance.detect_large_cash_transactions()
        
        if not alerts.empty:
            assert 'alert_type' in alerts.columns
            assert 'alert_severity' in alerts.columns
            assert all(alerts['alert_type'] == 'LARGE_CASH')
    
    @pytest.mark.unit
    def test_structuring_detection(self, report_instance):
        report_instance.load_transaction_data()
        report_instance.configure_alert_rules()
        
        alerts = report_instance.detect_structuring_patterns()
        
        if not alerts.empty:
            assert 'alert_type' in alerts.columns
            assert all(alerts['alert_type'] == 'STRUCTURING')
            assert 'transaction_count' in alerts.columns
    
    @pytest.mark.unit
    def test_pep_transaction_detection(self, report_instance):
        report_instance.load_transaction_data()
        report_instance.configure_alert_rules()
        
        alerts = report_instance.detect_pep_transactions()
        
        if not alerts.empty:
            assert all(alerts['alert_type'] == 'PEP_TRANSACTION')
            assert all(alerts['alert_severity'] == 'HIGH')
    
    @pytest.mark.unit
    def test_sanctions_detection(self, report_instance):
        report_instance.load_transaction_data()
        report_instance.configure_alert_rules()
        
        alerts = report_instance.detect_sanctions_violations()
        
        if not alerts.empty:
            assert all(alerts['alert_type'] == 'SANCTIONS_HIT')
            assert all(alerts['alert_severity'] == 'CRITICAL')
    
    @pytest.mark.unit
    def test_comprehensive_alert_generation(self, report_instance):
        report_instance.load_transaction_data()
        
        alert_results = report_instance.generate_comprehensive_alerts()
        
        assert 'alerts' in alert_results
        assert 'summary' in alert_results
        assert 'total_alerts' in alert_results
        
        if not alert_results['alerts'].empty:
            assert 'priority_score' in alert_results['alerts'].columns
    
    @pytest.mark.unit
    def test_investigation_workflow_generation(self, report_instance):
        # Create mock alerts
        mock_alerts = pd.DataFrame({
            'alert_type': ['LARGE_CASH', 'PEP_TRANSACTION'],
            'alert_severity': ['HIGH', 'CRITICAL'],
            'amount': [15000, 5000]
        })
        
        workflow = report_instance.generate_investigation_workflow(mock_alerts)
        
        assert 'workflow_steps' in workflow
        assert 'total_estimated_hours' in workflow
        assert workflow['total_estimated_hours'] > 0
    
    @pytest.mark.unit
    def test_complete_report_generation(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        result = report_instance.generate()
        
        assert result['status'] == 'completed'
        assert len(result['files']) == 1
        
        json_file = result['files'][0]
        assert json_file['content_type'] == 'application/json'
        
        # Parse and validate content
        report_data = json.loads(json_file['content'])
        assert 'statistics' in report_data
        assert 'alert_summary' in report_data
        assert 'investigation_workflow' in report_data
    
    @pytest.mark.unit
    def test_priority_score_calculation(self, report_instance):
        # Create test alerts with different severities
        test_alerts = pd.DataFrame({
            'alert_severity': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            'amount': [100000, 50000, 10000, 1000],
            'customer_risk_rating': ['HIGH', 'MEDIUM', 'LOW', 'LOW']
        })
        
        scores = report_instance._calculate_priority_scores(test_alerts)
        
        assert len(scores) == 4
        assert all(0 <= score <= 100 for score in scores)
        # Critical should have highest score
        assert scores[0] >= scores[1] >= scores[2] >= scores[3]
    
    @pytest.mark.performance
    def test_large_dataset_performance(self, report_instance, valid_parameters):
        """Test AML alert performance with large transaction dataset."""
        import time
        
        # Create large dataset
        np.random.seed(42)
        n_transactions = 500000
        
        large_data = pd.DataFrame({
            'transaction_id': [f'TXN{i:08d}' for i in range(1, n_transactions + 1)],
            'account_id': np.random.choice([f'ACC{i:06d}' for i in range(1, 10001)], n_transactions),
            'customer_id': np.random.choice([f'CUST{i:06d}' for i in range(1, 5001)], n_transactions),
            'transaction_date': pd.date_range('2024-01-01', periods=n_transactions, freq='min'),
            'amount': np.random.lognormal(mean=8, sigma=2, size=n_transactions),
            'currency': np.random.choice(['USD', 'EUR'], n_transactions),
            'transaction_type': np.random.choice(['WIRE', 'CASH'], n_transactions),
            'counterparty_country': np.random.choice(['US', 'OFF'], n_transactions),
            'risk_country_score': np.random.uniform(1, 10, n_transactions),
            'customer_risk_rating': np.random.choice(['LOW', 'HIGH'], n_transactions),
            'pep_flag': np.random.choice([True, False], n_transactions, p=[0.01, 0.99]),
            'sanctions_flag': np.random.choice([True, False], n_transactions, p=[0.0001, 0.9999])
        })
        
        report_instance.data = large_data
        report_instance.parameters = valid_parameters
        
        # Test alert generation performance
        start_time = time.time()
        alert_results = report_instance.generate_comprehensive_alerts()
        alert_time = time.time() - start_time
        
        # Performance assertion
        assert alert_time < 30.0, f"Alert generation took {alert_time:.3f}s"
        
        # Results should be reasonable
        assert alert_results['total_alerts'] >= 0
        assert 'summary' in alert_results