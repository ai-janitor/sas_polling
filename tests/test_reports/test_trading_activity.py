"""
=============================================================================
TRADING ACTIVITY REPORT GENERATOR UNIT TESTS
=============================================================================
Purpose: Unit tests for trading activity and transaction analysis report
Module: reports/trading_activity.py

TEST CATEGORIES:
1. Trade Execution Analysis
2. Market Impact Assessment
3. Performance Attribution
4. Risk Management Validation
=============================================================================
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

class TradingActivityReport:
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.required_fields = ['trading_date', 'portfolio_id', 'trader_id']
        self.data = None
        
    def validate_parameters(self):
        errors = []
        for field in self.required_fields:
            if field not in self.parameters:
                errors.append(f"Required field '{field}' is missing")
        
        if 'trading_date' in self.parameters:
            try:
                datetime.strptime(self.parameters['trading_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Trading date must be in YYYY-MM-DD format")
        
        return errors
    
    def load_trading_data(self):
        np.random.seed(42)
        n_trades = 2000
        
        self.data = pd.DataFrame({
            'trade_id': [f'TRD{i:06d}' for i in range(1, n_trades + 1)],
            'timestamp': pd.date_range('2024-06-30 09:30:00', periods=n_trades, freq='30S'),
            'symbol': np.random.choice(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META'], n_trades),
            'side': np.random.choice(['BUY', 'SELL'], n_trades),
            'quantity': np.random.randint(100, 10000, n_trades),
            'price': np.random.uniform(50, 300, n_trades),
            'execution_price': np.random.uniform(49.5, 300.5, n_trades),
            'order_type': np.random.choice(['MARKET', 'LIMIT', 'STOP'], n_trades),
            'venue': np.random.choice(['NYSE', 'NASDAQ', 'BATS', 'ARCA'], n_trades),
            'trader_id': np.random.choice(['TRD001', 'TRD002', 'TRD003'], n_trades),
            'commission': np.random.uniform(1, 25, n_trades),
            'market_impact': np.random.uniform(0.001, 0.05, n_trades)
        })
        
        # Calculate additional metrics
        self.data['notional_value'] = self.data['quantity'] * self.data['execution_price']
        self.data['slippage'] = (self.data['execution_price'] - self.data['price']) / self.data['price']
        self.data['total_cost'] = self.data['commission'] + (self.data['notional_value'] * self.data['market_impact'])
        
        return self.data
    
    def analyze_execution_quality(self):
        """Analyze trade execution quality metrics."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        execution_metrics = {
            'total_trades': len(self.data),
            'total_volume': self.data['notional_value'].sum(),
            'avg_trade_size': self.data['notional_value'].mean(),
            'avg_slippage': self.data['slippage'].mean(),
            'slippage_volatility': self.data['slippage'].std(),
            'execution_by_venue': self._analyze_venue_performance(),
            'execution_by_order_type': self._analyze_order_type_performance(),
            'time_weighted_metrics': self._calculate_time_weighted_metrics()
        }
        
        return execution_metrics
    
    def _analyze_venue_performance(self):
        """Analyze execution performance by trading venue."""
        venue_stats = self.data.groupby('venue').agg({
            'slippage': ['mean', 'std', 'count'],
            'market_impact': ['mean', 'std'],
            'notional_value': 'sum'
        }).round(4)
        
        venue_stats.columns = ['_'.join(col).strip() for col in venue_stats.columns]
        return venue_stats.to_dict('index')
    
    def _analyze_order_type_performance(self):
        """Analyze execution performance by order type."""
        order_stats = self.data.groupby('order_type').agg({
            'slippage': ['mean', 'std'],
            'market_impact': 'mean',
            'execution_price': 'count'
        }).round(4)
        
        order_stats.columns = ['_'.join(col).strip() for col in order_stats.columns]
        return order_stats.to_dict('index')
    
    def _calculate_time_weighted_metrics(self):
        """Calculate time-weighted execution metrics."""
        self.data['hour'] = self.data['timestamp'].dt.hour
        
        hourly_metrics = self.data.groupby('hour').agg({
            'slippage': 'mean',
            'market_impact': 'mean',
            'notional_value': 'sum',
            'trade_id': 'count'
        }).round(4)
        
        return {
            'hourly_patterns': hourly_metrics.to_dict('index'),
            'peak_trading_hour': hourly_metrics['trade_id_count'].idxmax(),
            'best_execution_hour': hourly_metrics['slippage_mean'].idxmin()
        }
    
    def calculate_performance_attribution(self):
        """Calculate trading performance attribution."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Group by trader for performance analysis
        trader_performance = self.data.groupby('trader_id').agg({
            'notional_value': ['sum', 'count'],
            'slippage': 'mean',
            'market_impact': 'mean',
            'total_cost': 'sum'
        }).round(4)
        
        trader_performance.columns = ['_'.join(col).strip() for col in trader_performance.columns]
        
        # Calculate trading efficiency scores
        efficiency_scores = {}
        for trader in trader_performance.index:
            trader_data = self.data[self.data['trader_id'] == trader]
            
            # Weighted average slippage by trade size
            weighted_slippage = np.average(trader_data['slippage'], weights=trader_data['notional_value'])
            
            # Cost efficiency (lower is better)
            cost_ratio = trader_data['total_cost'].sum() / trader_data['notional_value'].sum()
            
            efficiency_scores[trader] = {
                'weighted_slippage': weighted_slippage,
                'cost_efficiency': cost_ratio,
                'trade_count': len(trader_data),
                'total_volume': trader_data['notional_value'].sum()
            }
        
        return {
            'trader_statistics': trader_performance.to_dict('index'),
            'efficiency_scores': efficiency_scores,
            'top_performer': min(efficiency_scores.keys(), 
                               key=lambda x: efficiency_scores[x]['weighted_slippage'])
        }
    
    def assess_market_impact(self):
        """Assess market impact of trading activity."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Analyze market impact by symbol and trade size
        impact_analysis = {
            'overall_impact': self.data['market_impact'].mean(),
            'impact_by_symbol': self._analyze_symbol_impact(),
            'impact_by_size': self._analyze_size_impact(),
            'temporal_impact': self._analyze_temporal_impact()
        }
        
        return impact_analysis
    
    def _analyze_symbol_impact(self):
        """Analyze market impact by trading symbol."""
        symbol_impact = self.data.groupby('symbol').agg({
            'market_impact': ['mean', 'std'],
            'notional_value': 'sum',
            'quantity': 'sum'
        }).round(4)
        
        symbol_impact.columns = ['_'.join(col).strip() for col in symbol_impact.columns]
        return symbol_impact.to_dict('index')
    
    def _analyze_size_impact(self):
        """Analyze market impact by trade size buckets."""
        # Create trade size buckets
        self.data['size_bucket'] = pd.cut(self.data['notional_value'], 
                                        bins=[0, 10000, 50000, 100000, 500000, float('inf')],
                                        labels=['<10K', '10K-50K', '50K-100K', '100K-500K', '500K+'])
        
        size_impact = self.data.groupby('size_bucket').agg({
            'market_impact': ['mean', 'std'],
            'slippage': 'mean',
            'trade_id': 'count'
        }).round(4)
        
        size_impact.columns = ['_'.join(col).strip() for col in size_impact.columns]
        return size_impact.to_dict('index')
    
    def _analyze_temporal_impact(self):
        """Analyze how market impact changes throughout the trading day."""
        self.data['time_bucket'] = pd.cut(self.data['timestamp'].dt.hour,
                                        bins=[9, 11, 13, 15, 16],
                                        labels=['Morning', 'Late Morning', 'Afternoon', 'Close'])
        
        temporal_impact = self.data.groupby('time_bucket').agg({
            'market_impact': ['mean', 'std'],
            'slippage': 'mean'
        }).round(4)
        
        temporal_impact.columns = ['_'.join(col).strip() for col in temporal_impact.columns]
        return temporal_impact.to_dict('index')
    
    def generate_risk_metrics(self):
        """Generate trading risk metrics."""
        if self.data is None:
            raise ValueError("Data not loaded")
        
        # Calculate position and exposure metrics
        net_positions = self.data.groupby('symbol').apply(
            lambda x: (x[x['side'] == 'BUY']['quantity'].sum() - 
                      x[x['side'] == 'SELL']['quantity'].sum())
        )
        
        gross_exposure = self.data.groupby('symbol')['notional_value'].sum()
        
        risk_metrics = {
            'net_positions': net_positions.to_dict(),
            'gross_exposure': gross_exposure.to_dict(),
            'concentration_risk': self._calculate_concentration_risk(gross_exposure),
            'turnover_metrics': self._calculate_turnover_metrics(),
            'execution_risk': self._assess_execution_risk()
        }
        
        return risk_metrics
    
    def _calculate_concentration_risk(self, gross_exposure):
        """Calculate portfolio concentration risk."""
        total_exposure = gross_exposure.sum()
        concentration_ratios = gross_exposure / total_exposure
        
        return {
            'max_concentration': concentration_ratios.max(),
            'top_3_concentration': concentration_ratios.nlargest(3).sum(),
            'herfindahl_index': (concentration_ratios ** 2).sum(),
            'effective_symbols': 1 / (concentration_ratios ** 2).sum()
        }
    
    def _calculate_turnover_metrics(self):
        """Calculate portfolio turnover metrics."""
        buy_volume = self.data[self.data['side'] == 'BUY']['notional_value'].sum()
        sell_volume = self.data[self.data['side'] == 'SELL']['notional_value'].sum()
        
        return {
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'total_turnover': buy_volume + sell_volume,
            'net_flow': buy_volume - sell_volume,
            'turnover_ratio': min(buy_volume, sell_volume) / max(buy_volume, sell_volume)
        }
    
    def _assess_execution_risk(self):
        """Assess execution-related risks."""
        large_trades = self.data[self.data['notional_value'] > self.data['notional_value'].quantile(0.95)]
        
        return {
            'large_trade_count': len(large_trades),
            'large_trade_slippage': large_trades['slippage'].mean(),
            'execution_variance': self.data['slippage'].std(),
            'worst_execution': self.data['slippage'].min(),
            'failed_execution_rate': (self.data['slippage'].abs() > 0.05).mean()
        }
    
    def generate(self):
        """Generate complete trading activity report."""
        validation_errors = self.validate_parameters()
        if validation_errors:
            raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
        
        self.load_trading_data()
        
        # Perform all analyses
        execution_quality = self.analyze_execution_quality()
        performance_attribution = self.calculate_performance_attribution()
        market_impact = self.assess_market_impact()
        risk_metrics = self.generate_risk_metrics()
        
        # Generate report
        report_data = {
            'trading_summary': {
                'trading_date': self.parameters.get('trading_date'),
                'portfolio_id': self.parameters.get('portfolio_id'),
                'total_trades': execution_quality['total_trades'],
                'total_volume': execution_quality['total_volume'],
                'avg_slippage': execution_quality['avg_slippage']
            },
            'execution_quality': execution_quality,
            'performance_attribution': performance_attribution,
            'market_impact_analysis': market_impact,
            'risk_metrics': risk_metrics
        }
        
        json_content = json.dumps(report_data, indent=2, default=str)
        
        return {
            'status': 'completed',
            'files': [{
                'filename': f"trading_activity_{self.parameters.get('trading_date', 'latest')}.json",
                'content': json_content,
                'content_type': 'application/json',
                'size': len(json_content.encode('utf-8'))
            }],
            'metadata': {
                'report_type': 'Trading Activity',
                'trading_date': self.parameters.get('trading_date'),
                'total_trades': execution_quality['total_trades'],
                'best_performer': performance_attribution['top_performer']
            }
        }


class TestTradingActivityReport:
    @pytest.fixture
    def report_instance(self):
        return TradingActivityReport()
    
    @pytest.fixture
    def valid_parameters(self):
        return {
            'trading_date': '2024-06-30',
            'portfolio_id': 'TRADING_001',
            'trader_id': 'TRD001'
        }
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, report_instance, valid_parameters):
        report_instance.parameters = valid_parameters
        errors = report_instance.validate_parameters()
        assert errors == []
    
    @pytest.mark.unit
    def test_invalid_date_format(self, report_instance):
        report_instance.parameters = {
            'trading_date': '30-06-2024',  # Wrong format
            'portfolio_id': 'TEST',
            'trader_id': 'TRD001'
        }
        errors = report_instance.validate_parameters()
        assert len(errors) > 0
        assert any('YYYY-MM-DD format' in error for error in errors)
    
    @pytest.mark.unit
    def test_load_trading_data(self, report_instance):
        data = report_instance.load_trading_data()
        
        assert data is not None
        assert len(data) > 0
        
        required_columns = ['trade_id', 'symbol', 'side', 'quantity', 'price', 'execution_price']
        for col in required_columns:
            assert col in data.columns
        
        # Check calculated fields
        assert 'notional_value' in data.columns
        assert 'slippage' in data.columns
        assert 'total_cost' in data.columns
    
    @pytest.mark.unit
    def test_execution_quality_analysis(self, report_instance):
        report_instance.load_trading_data()
        quality_metrics = report_instance.analyze_execution_quality()
        
        assert 'total_trades' in quality_metrics
        assert 'total_volume' in quality_metrics
        assert 'avg_slippage' in quality_metrics
        assert 'execution_by_venue' in quality_metrics
        assert 'execution_by_order_type' in quality_metrics
        
        assert quality_metrics['total_trades'] > 0
        assert quality_metrics['total_volume'] > 0
    
    @pytest.mark.unit
    def test_performance_attribution(self, report_instance):
        report_instance.load_trading_data()
        performance = report_instance.calculate_performance_attribution()
        
        assert 'trader_statistics' in performance
        assert 'efficiency_scores' in performance
        assert 'top_performer' in performance
        
        # Check that we have efficiency scores for each trader
        assert len(performance['efficiency_scores']) > 0
        
        for trader, scores in performance['efficiency_scores'].items():
            assert 'weighted_slippage' in scores
            assert 'cost_efficiency' in scores
            assert 'trade_count' in scores
    
    @pytest.mark.unit
    def test_market_impact_assessment(self, report_instance):
        report_instance.load_trading_data()
        impact_analysis = report_instance.assess_market_impact()
        
        assert 'overall_impact' in impact_analysis
        assert 'impact_by_symbol' in impact_analysis
        assert 'impact_by_size' in impact_analysis
        assert 'temporal_impact' in impact_analysis
        
        assert impact_analysis['overall_impact'] >= 0
        assert len(impact_analysis['impact_by_symbol']) > 0
    
    @pytest.mark.unit
    def test_risk_metrics_generation(self, report_instance):
        report_instance.load_trading_data()
        risk_metrics = report_instance.generate_risk_metrics()
        
        assert 'net_positions' in risk_metrics
        assert 'gross_exposure' in risk_metrics
        assert 'concentration_risk' in risk_metrics
        assert 'turnover_metrics' in risk_metrics
        
        # Check concentration risk metrics
        concentration = risk_metrics['concentration_risk']
        assert 'max_concentration' in concentration
        assert 'herfindahl_index' in concentration
        assert 0 <= concentration['max_concentration'] <= 1
    
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
        assert 'trading_summary' in report_data
        assert 'execution_quality' in report_data
        assert 'performance_attribution' in report_data
        assert 'market_impact_analysis' in report_data
    
    @pytest.mark.performance
    def test_large_dataset_performance(self, report_instance, valid_parameters):
        """Test performance with large trading dataset."""
        import time
        
        # Create large dataset
        np.random.seed(42)
        n_trades = 100000
        
        large_data = pd.DataFrame({
            'trade_id': [f'TRD{i:07d}' for i in range(1, n_trades + 1)],
            'timestamp': pd.date_range('2024-06-30 09:30:00', periods=n_trades, freq='1S'),
            'symbol': np.random.choice(['AAPL', 'GOOGL', 'MSFT'] * 10, n_trades),
            'side': np.random.choice(['BUY', 'SELL'], n_trades),
            'quantity': np.random.randint(100, 10000, n_trades),
            'price': np.random.uniform(50, 300, n_trades),
            'execution_price': np.random.uniform(49.5, 300.5, n_trades),
            'order_type': np.random.choice(['MARKET', 'LIMIT', 'STOP'], n_trades),
            'venue': np.random.choice(['NYSE', 'NASDAQ', 'BATS'], n_trades),
            'trader_id': np.random.choice(['TRD001', 'TRD002', 'TRD003'], n_trades),
            'commission': np.random.uniform(1, 25, n_trades),
            'market_impact': np.random.uniform(0.001, 0.05, n_trades)
        })
        
        # Add calculated fields
        large_data['notional_value'] = large_data['quantity'] * large_data['execution_price']
        large_data['slippage'] = (large_data['execution_price'] - large_data['price']) / large_data['price']
        large_data['total_cost'] = large_data['commission'] + (large_data['notional_value'] * large_data['market_impact'])
        
        report_instance.data = large_data
        report_instance.parameters = valid_parameters
        
        # Test execution quality performance
        start_time = time.time()
        execution_metrics = report_instance.analyze_execution_quality()
        execution_time = time.time() - start_time
        
        # Test market impact performance
        start_time = time.time()
        impact_metrics = report_instance.assess_market_impact()
        impact_time = time.time() - start_time
        
        # Performance assertions
        assert execution_time < 5.0, f"Execution analysis took {execution_time:.3f}s"
        assert impact_time < 3.0, f"Market impact analysis took {impact_time:.3f}s"
        
        # Results should be reasonable
        assert execution_metrics['total_trades'] == n_trades
        assert execution_metrics['total_volume'] > 0