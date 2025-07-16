"""
Global pytest configuration and fixtures.

This file contains shared fixtures and configuration that are available
to all test modules in the project.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "tests" / "data"
TEST_LOGS_DIR = Path(__file__).parent / "tests" / "logs"

# Ensure test directories exist
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def test_config():
    """Global test configuration."""
    return {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'name': 'datafit_test',
            'user': 'test_user',
            'password': 'test_password'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 1  # Use different DB for tests
        },
        'api': {
            'base_url': 'http://localhost:8000',
            'timeout': 30
        },
        'security': {
            'secret_key': 'test_secret_key_for_testing_only_not_for_production',
            'token_expiry_hours': 1
        },
        'logging': {
            'level': 'DEBUG',
            'file_path': str(TEST_LOGS_DIR / 'test.log')
        }
    }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_date_range():
    """Sample date range for testing."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 30)
    return {
        'start_date': start_date,
        'end_date': end_date,
        'start_str': start_date.strftime('%Y-%m-%d'),
        'end_str': end_date.strftime('%Y-%m-%d')
    }


@pytest.fixture
def mock_database():
    """Mock database connection and operations."""
    mock_db = Mock()
    
    # Mock connection
    mock_connection = Mock()
    mock_cursor = Mock()
    
    mock_connection.cursor.return_value = mock_cursor
    mock_db.connect.return_value = mock_connection
    
    # Mock query results
    mock_cursor.fetchall.return_value = [
        ('user1', 'John', 'Doe', 'john@example.com'),
        ('user2', 'Jane', 'Smith', 'jane@example.com')
    ]
    mock_cursor.fetchone.return_value = ('user1', 'John', 'Doe', 'john@example.com')
    mock_cursor.rowcount = 2
    
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis cache operations."""
    mock_redis = Mock()
    
    # Mock basic operations
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    mock_redis.expire.return_value = True
    
    # Mock pipeline
    mock_pipeline = Mock()
    mock_pipeline.execute.return_value = [True, True, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    return mock_redis


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing."""
    return pd.DataFrame({
        'customer_id': ['CUST000001', 'CUST000002', 'CUST000003'],
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        'account_balance': [10000.50, 25000.75, 5500.25],
        'risk_profile': ['MODERATE', 'CONSERVATIVE', 'AGGRESSIVE'],
        'created_date': [
            datetime(2023, 1, 15),
            datetime(2023, 3, 20),
            datetime(2023, 6, 10)
        ]
    })


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    np.random.seed(42)
    
    n_transactions = 100
    return pd.DataFrame({
        'transaction_id': [f'TXN{i:07d}' for i in range(1, n_transactions + 1)],
        'account_id': np.random.choice(['ACC00001', 'ACC00002', 'ACC00003'], n_transactions),
        'amount': np.random.uniform(-5000, 5000, n_transactions),
        'transaction_type': np.random.choice(['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'FEE'], n_transactions),
        'transaction_date': [
            datetime(2024, 1, 1) + timedelta(days=np.random.randint(0, 180))
            for _ in range(n_transactions)
        ],
        'status': np.random.choice(['COMPLETED', 'PENDING', 'FAILED'], n_transactions, p=[0.9, 0.08, 0.02])
    })


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        'shares': [100, 50, 75, 25, 30],
        'purchase_price': [150.00, 2500.00, 300.00, 800.00, 3200.00],
        'current_price': [175.50, 2650.75, 320.25, 750.80, 3100.45],
        'market_value': [17550.00, 132537.50, 24018.75, 18770.00, 93013.50],
        'asset_class': ['EQUITY', 'EQUITY', 'EQUITY', 'EQUITY', 'EQUITY'],
        'sector': ['Technology', 'Technology', 'Technology', 'Consumer Discretionary', 'Consumer Discretionary']
    })


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    np.random.seed(42)
    
    date_range = pd.date_range(start='2024-01-01', end='2024-06-30', freq='D')
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    market_data = []
    for symbol in symbols:
        base_price = {'AAPL': 150, 'GOOGL': 2500, 'MSFT': 300}[symbol]
        
        for date in date_range:
            # Generate realistic price movements
            price_change = np.random.normal(0, 0.02)  # 2% daily volatility
            base_price *= (1 + price_change)
            
            market_data.append({
                'date': date,
                'symbol': symbol,
                'open': base_price * np.random.uniform(0.99, 1.01),
                'high': base_price * np.random.uniform(1.00, 1.05),
                'low': base_price * np.random.uniform(0.95, 1.00),
                'close': base_price,
                'volume': np.random.randint(1000000, 10000000)
            })
    
    return pd.DataFrame(market_data)


@pytest.fixture
def mock_api_client():
    """Mock API client for external service calls."""
    mock_client = Mock()
    
    # Mock successful responses
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 'success',
        'data': {'key': 'value'},
        'timestamp': datetime.now().isoformat()
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    mock_fs = Mock()
    
    # Mock file operations
    mock_fs.exists.return_value = True
    mock_fs.read_file.return_value = "Mock file content"
    mock_fs.write_file.return_value = True
    mock_fs.delete_file.return_value = True
    mock_fs.list_files.return_value = ['file1.txt', 'file2.json', 'file3.csv']
    
    # Mock directory operations
    mock_fs.create_directory.return_value = True
    mock_fs.list_directories.return_value = ['dir1', 'dir2', 'dir3']
    
    return mock_fs


@pytest.fixture
def sample_report_parameters():
    """Sample report parameters for testing."""
    return {
        'cmbs_report': {
            'analysis_date': '2024-06-30',
            'portfolio_id': 'PORT123456',
            'include_stress_tests': True,
            'stress_scenarios': ['mild', 'moderate', 'severe']
        },
        'var_report': {
            'calculation_date': '2024-06-30',
            'portfolio_id': 'VAR_PORT_001',
            'confidence_level': 0.95,
            'method': 'HISTORICAL',
            'lookback_days': 252
        },
        'aml_report': {
            'report_date': '2024-06-30',
            'jurisdiction': 'US',
            'alert_severity': 'HIGH',
            'include_false_positives': False
        }
    }


@pytest.fixture
def mock_job_queue():
    """Mock job queue for testing async operations."""
    mock_queue = Mock()
    
    # Mock job submission
    mock_job = Mock()
    mock_job.id = 'job_12345'
    mock_job.status = 'QUEUED'
    mock_job.created_at = datetime.now()
    mock_job.updated_at = datetime.now()
    
    mock_queue.submit_job.return_value = mock_job
    mock_queue.get_job.return_value = mock_job
    mock_queue.list_jobs.return_value = [mock_job]
    mock_queue.cancel_job.return_value = True
    
    return mock_queue


@pytest.fixture
def performance_timer():
    """Utility fixture for measuring test performance."""
    import time
    
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.duration
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceTimer()


@pytest.fixture(autouse=True)
def reset_numpy_random_seed():
    """Reset numpy random seed before each test for reproducibility."""
    np.random.seed(42)


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Clear test-related environment variables
    test_env_vars = [
        'TEST_DATABASE_URL',
        'TEST_REDIS_URL',
        'TEST_API_KEY',
        'TEST_SECRET_KEY'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Pytest hooks and configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark slow tests
        if "slow" in item.keywords or "performance" in item.keywords:
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests (default)
        if not any(mark.name in ["integration", "performance", "slow"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


def pytest_runtest_setup(item):
    """Setup before each test."""
    # Skip slow tests unless explicitly requested
    if "slow" in item.keywords and not item.config.getoption("--runslow", default=False):
        pytest.skip("need --runslow option to run")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--runperformance",
        action="store_true",
        default=False,
        help="run performance tests"
    )


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging behavior."""
    mock_logger = Mock()
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.critical = Mock()
    return mock_logger


# Financial calculation utilities for tests
@pytest.fixture
def financial_calculator():
    """Financial calculation utilities for tests."""
    class FinancialCalculator:
        @staticmethod
        def present_value(future_value, rate, periods):
            """Calculate present value."""
            return future_value / ((1 + rate) ** periods)
        
        @staticmethod
        def var_calculation(returns, confidence_level=0.95):
            """Simple VaR calculation for testing."""
            return np.percentile(returns, (1 - confidence_level) * 100)
        
        @staticmethod
        def sharpe_ratio(returns, risk_free_rate=0.02):
            """Calculate Sharpe ratio."""
            excess_returns = np.mean(returns) - risk_free_rate
            return excess_returns / np.std(returns)
        
        @staticmethod
        def portfolio_return(weights, returns):
            """Calculate portfolio return."""
            return np.dot(weights, returns)
    
    return FinancialCalculator()


# Test data validation utilities
@pytest.fixture
def data_validator():
    """Data validation utilities for tests."""
    class DataValidator:
        @staticmethod
        def validate_dataframe_structure(df, required_columns, min_rows=1):
            """Validate DataFrame structure."""
            errors = []
            
            if not isinstance(df, pd.DataFrame):
                errors.append("Input is not a DataFrame")
                return errors
            
            if len(df) < min_rows:
                errors.append(f"DataFrame has {len(df)} rows, minimum {min_rows} required")
            
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                errors.append(f"Missing columns: {missing_columns}")
            
            return errors
        
        @staticmethod
        def validate_date_range(start_date, end_date):
            """Validate date range."""
            errors = []
            
            if start_date >= end_date:
                errors.append("Start date must be before end date")
            
            if (end_date - start_date).days > 365 * 5:  # 5 years
                errors.append("Date range exceeds 5 years")
            
            return errors
        
        @staticmethod
        def validate_financial_amounts(amounts):
            """Validate financial amounts."""
            errors = []
            
            if any(pd.isna(amounts)):
                errors.append("Contains NaN values")
            
            if any(amount < 0 for amount in amounts if not pd.isna(amount)):
                errors.append("Contains negative amounts")
            
            return errors
    
    return DataValidator()