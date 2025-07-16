"""
=============================================================================
DATAFIT TEST CONFIGURATION
=============================================================================
Purpose: Pytest configuration and shared fixtures for all test modules
Technology: pytest with comprehensive test fixtures and utilities

STRICT REQUIREMENTS:
- 80% minimum code coverage for all modules
- Isolated test environments with cleanup
- Mock external dependencies and services
- Parameterized tests for comprehensive coverage
- Performance and load testing capabilities

FIXTURE CATEGORIES:
1. Application fixtures (Flask/FastAPI apps)
2. Database fixtures (test data isolation)
3. Mock service fixtures (external API mocking)
4. File system fixtures (temporary directories)
5. Configuration fixtures (test environment setup)

TESTING STANDARDS:
- Unit tests for all public methods
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Performance tests for critical paths
- Security tests for input validation

MOCK STRATEGY:
- Mock all external HTTP requests
- Mock file system operations
- Mock time-dependent operations
- Mock random number generation
- Mock environment variables

DATA MANAGEMENT:
- Isolated test database per test
- Clean test data generation
- Realistic mock data volumes
- Test data cleanup after each test
- Data validation helpers

ENVIRONMENT ISOLATION:
- Separate test configuration
- Temporary file directories
- Mock external services
- Test-specific environment variables
- Network isolation for security

PERFORMANCE TESTING:
- Response time benchmarks
- Memory usage monitoring
- Concurrent request handling
- Large dataset processing
- Resource cleanup verification

SECURITY TESTING:
- Input validation tests
- Authentication bypass attempts
- Authorization boundary tests
- SQL injection prevention
- XSS protection verification

COVERAGE REQUIREMENTS:
- Line coverage: 80% minimum
- Branch coverage: 75% minimum
- Function coverage: 90% minimum
- Class coverage: 85% minimum
- File coverage: 100% (all files tested)

TEST ORGANIZATION:
- Unit tests in module-specific directories
- Integration tests in dedicated directory
- End-to-end tests with full system
- Performance tests with benchmarks
- Security tests with attack vectors

REPORTING:
- JUnit XML output for CI/CD
- Coverage reports in HTML and XML
- Performance benchmark results
- Security test findings
- Test execution timing

DEPENDENCIES:
- pytest: Test framework and runner
- pytest-asyncio: Async test support
- pytest-mock: Mocking utilities
- pytest-cov: Coverage reporting
- pytest-benchmark: Performance testing
- requests-mock: HTTP request mocking
- freezegun: Time mocking
- factory-boy: Test data generation

USAGE EXAMPLES:
```python
def test_job_submission(app_client, mock_polling_service):
    response = app_client.post('/api/jobs', json=job_data)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_async_job_processing(async_app, test_job):
    result = await process_job(test_job)
    assert result.status == 'completed'
```
=============================================================================
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta
import uuid

# Test configuration
TEST_CONFIG = {
    'TESTING': True,
    'DEBUG': False,
    'DATABASE_URL': 'sqlite:///:memory:',
    'TEMP_DIR': None,  # Will be set in session fixture
    'LOG_LEVEL': 'DEBUG',
    'MOCK_EXTERNAL_SERVICES': True
}

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture for all tests."""
    return TEST_CONFIG.copy()

@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="datafit_test_")
    TEST_CONFIG['TEMP_DIR'] = temp_path
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_config(temp_dir):
    """Mock configuration with test values."""
    config = {
        'GUI_PORT': 3001,
        'SUBMISSION_PORT': 5001,
        'POLLING_PORT': 5002,
        'FILE_STORAGE_PATH': os.path.join(temp_dir, 'files'),
        'REPORTS_DATA_PATH': os.path.join(temp_dir, 'mock-data'),
        'REPORT_DEFINITIONS_FILE': os.path.join(temp_dir, 'report-definitions.json'),
        'LOG_LEVEL': 'DEBUG',
        'TESTING': True
    }
    
    # Create necessary directories
    os.makedirs(config['FILE_STORAGE_PATH'], exist_ok=True)
    os.makedirs(config['REPORTS_DATA_PATH'], exist_ok=True)
    
    return config

@pytest.fixture
def sample_report_definitions():
    """Sample report definitions for testing."""
    return {
        "categories": [
            {
                "name": "Test Reports",
                "reports": [
                    {
                        "name": "Test Report 1",
                        "id": "test-report-1",
                        "description": "A test report for unit testing",
                        "estimated_duration": 60,
                        "output_formats": ["HTML", "PDF"],
                        "prompts": [
                            {
                                "test_param": {
                                    "active": "true",
                                    "hide": "false",
                                    "inputType": "inputtext",
                                    "label": "Test Parameter",
                                    "required": "true"
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

@pytest.fixture
def sample_job_request():
    """Sample job request data for testing."""
    return {
        "name": "Test Job",
        "jobDefinitionUri": "test-report-1",
        "arguments": {
            "test_param": "test_value"
        },
        "submitted_by": "test_user",
        "priority": 5
    }

@pytest.fixture
def sample_job_response():
    """Sample job response data for testing."""
    job_id = str(uuid.uuid4())
    return {
        "id": job_id,
        "status": "submitted",
        "polling_url": f"/api/jobs/{job_id}/status",
        "estimated_duration": 60
    }

@pytest.fixture
def mock_csv_data():
    """Mock CSV data for report generation."""
    return """date,value,category
2024-01-01,100,A
2024-01-02,150,B
2024-01-03,200,A
2024-01-04,175,C
2024-01-05,225,B"""

@pytest.fixture
def create_test_csv_files(temp_dir, mock_csv_data):
    """Create test CSV files in temp directory."""
    files_created = []
    
    csv_files = [
        'cmbs_data.csv',
        'rmbs_performance.csv',
        'var_daily.csv',
        'stress_test_results.csv',
        'trading_activity.csv',
        'aml_alerts.csv',
        'focus_manual.csv'
    ]
    
    for filename in csv_files:
        file_path = os.path.join(temp_dir, 'mock-data', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(mock_csv_data)
        
        files_created.append(file_path)
    
    yield files_created
    
    # Cleanup is handled by temp_dir fixture

@pytest.fixture
def mock_time():
    """Mock time for consistent testing."""
    with patch('time.time', return_value=1640995200):  # 2022-01-01 00:00:00
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2022, 1, 1, 0, 0, 0)
            mock_datetime.utcnow.return_value = datetime(2022, 1, 1, 0, 0, 0)
            yield mock_datetime

@pytest.fixture
def mock_uuid():
    """Mock UUID generation for predictable testing."""
    test_uuid = 'test-uuid-1234-5678-9abc-def012345678'
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID)):
        with patch('uuid.uuid4().hex', test_uuid):
            with patch('str') as mock_str:
                mock_str.return_value = test_uuid
                yield test_uuid

@pytest.fixture
def mock_requests():
    """Mock external HTTP requests."""
    with patch('requests.get') as mock_get:
        with patch('requests.post') as mock_post:
            with patch('requests.put') as mock_put:
                with patch('requests.delete') as mock_delete:
                    
                    # Configure default responses
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {}
                    
                    mock_post.return_value.status_code = 201
                    mock_post.return_value.json.return_value = {}
                    
                    mock_put.return_value.status_code = 200
                    mock_put.return_value.json.return_value = {}
                    
                    mock_delete.return_value.status_code = 204
                    
                    yield {
                        'get': mock_get,
                        'post': mock_post,
                        'put': mock_put,
                        'delete': mock_delete
                    }

@pytest.fixture
def mock_file_operations():
    """Mock file system operations."""
    with patch('builtins.open', create=True) as mock_open:
        with patch('os.makedirs') as mock_makedirs:
            with patch('os.path.exists', return_value=True) as mock_exists:
                with patch('shutil.rmtree') as mock_rmtree:
                    yield {
                        'open': mock_open,
                        'makedirs': mock_makedirs,
                        'exists': mock_exists,
                        'rmtree': mock_rmtree
                    }

@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture for benchmark tests."""
    import time
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_usage = []
            self.monitoring = False
            self.monitor_thread = None
        
        def start(self):
            self.start_time = time.time()
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_memory)
            self.monitor_thread.start()
        
        def stop(self):
            self.end_time = time.time()
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
        
        def _monitor_memory(self):
            process = psutil.Process()
            while self.monitoring:
                self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
                time.sleep(0.1)
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
        
        @property
        def peak_memory(self):
            return max(self.memory_usage) if self.memory_usage else 0
        
        @property
        def avg_memory(self):
            return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
    
    return PerformanceMonitor()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in unit test directories
        if "test_unit" in str(item.fspath) or "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "test_integration" in str(item.fspath) or "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to benchmark tests
        if "benchmark" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to long-running tests
        if "slow" in item.name or item.get_closest_marker("slow"):
            item.add_marker(pytest.mark.slow)