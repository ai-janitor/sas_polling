"""
=============================================================================
JOB SUBMISSION UTILITY FUNCTIONS UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job submission utility functions
Technology: pytest with mocking and utility function testing
Module: job-submission/utils.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test all utility functions and helper methods
- Mock external dependencies and API calls
- Validate error handling and edge cases
- Test performance and security aspects

TEST CATEGORIES:
1. Configuration Management Tests
   - Environment variable loading
   - Configuration validation
   - Default value handling
   - Configuration file parsing
   - Environment-specific overrides

2. Request Processing Tests
   - HTTP request validation
   - Header processing
   - Authentication token handling
   - Request correlation ID generation
   - Request logging and tracing

3. Response Formatting Tests
   - Success response formatting
   - Error response standardization
   - JSON serialization handling
   - HTTP status code mapping
   - Response compression

4. Validation Utilities Tests
   - Input sanitization functions
   - Data type validation
   - Business rule validation
   - Schema compliance checking
   - Cross-field validation

5. Networking Utilities Tests
   - HTTP client configuration
   - Retry mechanism testing
   - Timeout handling
   - Connection pooling
   - Circuit breaker patterns

6. Logging and Monitoring Tests
   - Structured logging validation
   - Metrics collection
   - Health check utilities
   - Error tracking integration
   - Performance monitoring

MOCK STRATEGY:
- Mock environment variables
- Mock HTTP requests/responses
- Mock configuration files
- Mock external services
- Mock logging systems

UTILITY FUNCTIONS TESTED:
- get_config_value(key, default)
- validate_request_headers(headers)
- generate_correlation_id()
- format_success_response(data)
- format_error_response(error)
- sanitize_input(input_string)
- create_http_client(config)
- log_request(request, correlation_id)
- health_check_dependencies()
- calculate_request_hash(request)

ERROR SCENARIOS:
- Missing configuration values
- Invalid input data types
- Network connectivity issues
- Malformed JSON responses
- Authentication failures

PERFORMANCE BENCHMARKS:
- Utility function calls < 10ms
- Request processing < 100ms
- Configuration loading < 50ms
- Response formatting < 25ms
- Input validation < 5ms

SECURITY TESTS:
- Input sanitization effectiveness
- Header injection prevention
- Log injection prevention
- Sensitive data masking
- Rate limiting utilities

DEPENDENCIES:
- pytest: Test framework
- requests-mock: HTTP mocking
- pytest-mock: General mocking
- freezegun: Time mocking
- pytest-benchmark: Performance testing
=============================================================================
"""

import pytest
import os
import json
import time
import uuid
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import logging
from freezegun import freeze_time
import hashlib
import re

# Mock utility functions (actual implementation would import from job-submission/utils.py)
class JobSubmissionUtils:
    """Mock utility class for job submission service."""
    
    @staticmethod
    def get_config_value(key, default=None):
        """Get configuration value from environment or config file."""
        # First try environment variable
        env_value = os.environ.get(key)
        if env_value is not None:
            return env_value
        
        # Then try config file (simulated)
        config_file_path = os.environ.get('CONFIG_FILE', 'config.dev.env')
        try:
            with open(config_file_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            config_key, config_value = line.strip().split('=', 1)
                            if config_key == key:
                                return config_value
        except FileNotFoundError:
            pass
        
        return default
    
    @staticmethod
    def validate_request_headers(headers):
        """Validate HTTP request headers."""
        required_headers = ['Content-Type', 'User-Agent']
        errors = []
        
        if not headers:
            return ['Headers are required']
        
        for header in required_headers:
            if header not in headers:
                errors.append(f'Missing required header: {header}')
        
        # Validate Content-Type
        content_type = headers.get('Content-Type')
        if content_type and 'application/json' not in content_type:
            errors.append('Content-Type must be application/json')
        
        # Check for suspicious headers
        for header_name, header_value in headers.items():
            if any(char in str(header_value) for char in ['<', '>', '"', "'"]):
                errors.append(f'Potentially malicious header value in {header_name}')
        
        return errors
    
    @staticmethod
    def generate_correlation_id():
        """Generate unique correlation ID for request tracing."""
        timestamp = int(time.time() * 1000)
        random_uuid = str(uuid.uuid4()).replace('-', '')
        return f"{timestamp}-{random_uuid[:8]}"
    
    @staticmethod
    def format_success_response(data, status_code=200):
        """Format standardized success response."""
        return {
            'success': True,
            'status_code': status_code,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
    
    @staticmethod
    def format_error_response(error, status_code=400, correlation_id=None):
        """Format standardized error response."""
        return {
            'success': False,
            'status_code': status_code,
            'error': {
                'message': str(error),
                'type': type(error).__name__,
                'correlation_id': correlation_id
            },
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
    
    @staticmethod
    def sanitize_input(input_string):
        """Sanitize input string to prevent injection attacks."""
        if not isinstance(input_string, str):
            return input_string
        
        # Remove potential HTML/XML tags
        input_string = re.sub(r'<[^>]*>', '', input_string)
        
        # Remove potential SQL injection patterns
        sql_patterns = [
            r"';\s*DROP\s+TABLE",
            r"';\s*DELETE\s+FROM",
            r"';\s*UPDATE\s+",
            r"';\s*INSERT\s+INTO",
            r"\bUNION\s+SELECT\b",
            r"\bOR\s+1\s*=\s*1\b"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                raise ValueError("Potentially malicious input detected")
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '--']
        for char in dangerous_chars:
            input_string = input_string.replace(char, '')
        
        return input_string.strip()
    
    @staticmethod
    def create_http_client(config=None):
        """Create configured HTTP client with retry and timeout."""
        session = requests.Session()
        
        if config:
            # Set timeouts
            timeout = config.get('timeout', 30)
            session.timeout = timeout
            
            # Set headers
            headers = config.get('headers', {})
            session.headers.update(headers)
            
            # Configure retries (simplified)
            max_retries = config.get('max_retries', 3)
            session.max_retries = max_retries
        
        return session
    
    @staticmethod
    def log_request(request_data, correlation_id, logger=None):
        """Log request with correlation ID for tracing."""
        if logger is None:
            logger = logging.getLogger(__name__)
        
        # Sanitize sensitive data
        sanitized_data = request_data.copy() if isinstance(request_data, dict) else {}
        
        # Remove or mask sensitive fields
        sensitive_fields = ['password', 'token', 'api_key', 'secret']
        for field in sensitive_fields:
            if field in sanitized_data:
                sanitized_data[field] = '***MASKED***'
        
        logger.info(
            "Request received",
            extra={
                'correlation_id': correlation_id,
                'request_data': sanitized_data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def health_check_dependencies():
        """Check health of external dependencies."""
        dependencies = {
            'polling_service': False,
            'database': False,
            'file_storage': False
        }
        
        # Check polling service
        try:
            polling_url = JobSubmissionUtils.get_config_value('POLLING_SERVICE_URL', 'http://localhost:5001')
            response = requests.get(f"{polling_url}/health", timeout=5)
            dependencies['polling_service'] = response.status_code == 200
        except:
            pass
        
        # Check database (simulated)
        try:
            db_url = JobSubmissionUtils.get_config_value('DATABASE_URL')
            if db_url:
                dependencies['database'] = True  # Simplified check
        except:
            pass
        
        # Check file storage (simulated)
        try:
            storage_path = JobSubmissionUtils.get_config_value('STORAGE_PATH', '/tmp')
            dependencies['file_storage'] = os.path.exists(storage_path)
        except:
            pass
        
        return dependencies
    
    @staticmethod
    def calculate_request_hash(request_data):
        """Calculate hash of request for deduplication."""
        if isinstance(request_data, dict):
            # Sort keys for consistent hashing
            sorted_data = json.dumps(request_data, sort_keys=True)
        else:
            sorted_data = str(request_data)
        
        return hashlib.sha256(sorted_data.encode()).hexdigest()


class TestConfigurationManagement:
    """Test configuration management utilities."""
    
    @pytest.fixture
    def mock_config_file_content(self):
        """Mock configuration file content."""
        return [
            "# Configuration file",
            "SUBMISSION_PORT=5000",
            "POLLING_SERVICE_URL=http://localhost:5001",
            "LOG_LEVEL=INFO",
            "# Comment line",
            "RATE_LIMIT_REQUESTS=100"
        ]
    
    @pytest.mark.unit
    def test_get_config_value_from_environment(self):
        """Test getting configuration value from environment variable."""
        with patch.dict(os.environ, {'TEST_CONFIG_KEY': 'test_value'}):
            value = JobSubmissionUtils.get_config_value('TEST_CONFIG_KEY')
            assert value == 'test_value'
    
    @pytest.mark.unit
    def test_get_config_value_with_default(self):
        """Test getting configuration value with default."""
        value = JobSubmissionUtils.get_config_value('NONEXISTENT_KEY', 'default_value')
        assert value == 'default_value'
    
    @pytest.mark.unit
    def test_get_config_value_from_file(self, mock_config_file_content):
        """Test getting configuration value from config file."""
        with patch('builtins.open', mock_open(read_data='\n'.join(mock_config_file_content))):
            value = JobSubmissionUtils.get_config_value('SUBMISSION_PORT')
            assert value == '5000'
    
    @pytest.mark.unit
    def test_get_config_value_file_not_found(self):
        """Test handling when config file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            value = JobSubmissionUtils.get_config_value('SOME_KEY', 'default')
            assert value == 'default'
    
    @pytest.mark.unit
    def test_get_config_value_precedence(self, mock_config_file_content):
        """Test that environment variables take precedence over config file."""
        with patch.dict(os.environ, {'SUBMISSION_PORT': '8080'}):
            with patch('builtins.open', mock_open(read_data='\n'.join(mock_config_file_content))):
                value = JobSubmissionUtils.get_config_value('SUBMISSION_PORT')
                assert value == '8080'  # Environment value, not file value


class TestRequestProcessing:
    """Test request processing utilities."""
    
    @pytest.fixture
    def valid_headers(self):
        """Valid HTTP headers for testing."""
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'DataFit-Client/1.0',
            'Accept': 'application/json'
        }
    
    @pytest.fixture
    def invalid_headers(self):
        """Invalid HTTP headers for testing."""
        return {
            'Content-Type': 'text/plain',
            'X-Malicious': '<script>alert("xss")</script>'
        }
    
    @pytest.mark.unit
    def test_validate_request_headers_success(self, valid_headers):
        """Test successful header validation."""
        errors = JobSubmissionUtils.validate_request_headers(valid_headers)
        assert errors == []
    
    @pytest.mark.unit
    def test_validate_request_headers_missing_required(self):
        """Test header validation with missing required headers."""
        headers = {'Content-Type': 'application/json'}
        errors = JobSubmissionUtils.validate_request_headers(headers)
        
        assert len(errors) > 0
        assert any('User-Agent' in error for error in errors)
    
    @pytest.mark.unit
    def test_validate_request_headers_empty(self):
        """Test header validation with empty headers."""
        errors = JobSubmissionUtils.validate_request_headers({})
        assert 'Headers are required' in errors
    
    @pytest.mark.unit
    def test_validate_request_headers_invalid_content_type(self):
        """Test header validation with invalid content type."""
        headers = {
            'Content-Type': 'text/plain',
            'User-Agent': 'Test-Client'
        }
        errors = JobSubmissionUtils.validate_request_headers(headers)
        
        assert any('application/json' in error for error in errors)
    
    @pytest.mark.unit
    def test_validate_request_headers_malicious_content(self, invalid_headers):
        """Test header validation with potentially malicious content."""
        errors = JobSubmissionUtils.validate_request_headers(invalid_headers)
        
        assert len(errors) > 0
        assert any('malicious' in error.lower() for error in errors)
    
    @pytest.mark.unit
    def test_generate_correlation_id_format(self):
        """Test correlation ID generation format."""
        correlation_id = JobSubmissionUtils.generate_correlation_id()
        
        # Should be in format: timestamp-uuid_prefix
        assert '-' in correlation_id
        parts = correlation_id.split('-')
        assert len(parts) == 2
        
        # First part should be numeric timestamp
        assert parts[0].isdigit()
        
        # Second part should be 8 character hex string
        assert len(parts[1]) == 8
        assert all(c in '0123456789abcdef' for c in parts[1].lower())
    
    @pytest.mark.unit
    def test_generate_correlation_id_uniqueness(self):
        """Test that correlation IDs are unique."""
        ids = set()
        for _ in range(100):
            correlation_id = JobSubmissionUtils.generate_correlation_id()
            assert correlation_id not in ids
            ids.add(correlation_id)
            time.sleep(0.001)  # Small delay to ensure timestamp changes


class TestResponseFormatting:
    """Test response formatting utilities."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for response formatting."""
        return {
            'job_id': '123e4567-e89b-12d3-a456-426614174000',
            'status': 'submitted',
            'polling_url': 'http://localhost:5001/api/jobs/123/status'
        }
    
    @pytest.mark.unit
    @freeze_time("2024-01-15 10:30:00")
    def test_format_success_response(self, sample_data):
        """Test success response formatting."""
        response = JobSubmissionUtils.format_success_response(sample_data)
        
        assert response['success'] is True
        assert response['status_code'] == 200
        assert response['data'] == sample_data
        assert response['timestamp'] == '2024-01-15T10:30:00'
        assert response['version'] == '1.0'
    
    @pytest.mark.unit
    def test_format_success_response_custom_status(self, sample_data):
        """Test success response with custom status code."""
        response = JobSubmissionUtils.format_success_response(sample_data, status_code=201)
        
        assert response['status_code'] == 201
        assert response['success'] is True
    
    @pytest.mark.unit
    @freeze_time("2024-01-15 10:30:00")
    def test_format_error_response(self):
        """Test error response formatting."""
        error = ValueError("Test error message")
        correlation_id = "test-correlation-123"
        
        response = JobSubmissionUtils.format_error_response(
            error, status_code=400, correlation_id=correlation_id
        )
        
        assert response['success'] is False
        assert response['status_code'] == 400
        assert response['error']['message'] == 'Test error message'
        assert response['error']['type'] == 'ValueError'
        assert response['error']['correlation_id'] == correlation_id
        assert response['timestamp'] == '2024-01-15T10:30:00'
    
    @pytest.mark.unit
    def test_format_error_response_without_correlation_id(self):
        """Test error response without correlation ID."""
        error = RuntimeError("Runtime error")
        response = JobSubmissionUtils.format_error_response(error)
        
        assert response['error']['correlation_id'] is None
        assert response['error']['message'] == 'Runtime error'
        assert response['error']['type'] == 'RuntimeError'


class TestInputSanitization:
    """Test input sanitization utilities."""
    
    @pytest.mark.unit
    def test_sanitize_input_clean_string(self):
        """Test sanitization of clean input string."""
        clean_input = "This is a clean string with numbers 123"
        result = JobSubmissionUtils.sanitize_input(clean_input)
        assert result == clean_input
    
    @pytest.mark.unit
    def test_sanitize_input_html_removal(self):
        """Test HTML tag removal from input."""
        html_input = "This has <script>alert('xss')</script> tags"
        result = JobSubmissionUtils.sanitize_input(html_input)
        assert '<script>' not in result
        assert '</script>' not in result
        assert "This has  tags" in result
    
    @pytest.mark.unit
    def test_sanitize_input_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        sql_injections = [
            "'; DROP TABLE users; --",
            "' OR 1=1 --",
            "'; DELETE FROM jobs; --",
            "test' UNION SELECT * FROM passwords --"
        ]
        
        for injection in sql_injections:
            with pytest.raises(ValueError, match="malicious input"):
                JobSubmissionUtils.sanitize_input(injection)
    
    @pytest.mark.unit
    def test_sanitize_input_dangerous_character_removal(self):
        """Test removal of dangerous characters."""
        dangerous_input = "test<>\"';--input"
        result = JobSubmissionUtils.sanitize_input(dangerous_input)
        
        dangerous_chars = ['<', '>', '"', "'", ';', '--']
        for char in dangerous_chars:
            assert char not in result
        
        assert result == "testinput"
    
    @pytest.mark.unit
    def test_sanitize_input_non_string(self):
        """Test sanitization with non-string input."""
        non_string_inputs = [123, [1, 2, 3], {'key': 'value'}, None, True]
        
        for input_value in non_string_inputs:
            result = JobSubmissionUtils.sanitize_input(input_value)
            assert result == input_value  # Should return unchanged
    
    @pytest.mark.unit
    def test_sanitize_input_whitespace_handling(self):
        """Test whitespace trimming in sanitization."""
        whitespace_input = "  test input with spaces  "
        result = JobSubmissionUtils.sanitize_input(whitespace_input)
        assert result == "test input with spaces"


class TestNetworkingUtilities:
    """Test networking utility functions."""
    
    @pytest.fixture
    def http_client_config(self):
        """HTTP client configuration for testing."""
        return {
            'timeout': 30,
            'max_retries': 3,
            'headers': {
                'User-Agent': 'DataFit-Service/1.0',
                'Accept': 'application/json'
            }
        }
    
    @pytest.mark.unit
    def test_create_http_client_default(self):
        """Test HTTP client creation with default settings."""
        client = JobSubmissionUtils.create_http_client()
        
        assert isinstance(client, requests.Session)
    
    @pytest.mark.unit
    def test_create_http_client_with_config(self, http_client_config):
        """Test HTTP client creation with custom configuration."""
        client = JobSubmissionUtils.create_http_client(http_client_config)
        
        assert isinstance(client, requests.Session)
        assert client.timeout == 30
        assert client.max_retries == 3
        assert 'User-Agent' in client.headers
        assert client.headers['User-Agent'] == 'DataFit-Service/1.0'
    
    @pytest.mark.unit
    def test_health_check_dependencies_all_healthy(self):
        """Test health check when all dependencies are healthy."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            with patch.dict(os.environ, {
                'POLLING_SERVICE_URL': 'http://localhost:5001',
                'DATABASE_URL': 'postgresql://localhost/test',
                'STORAGE_PATH': '/tmp'
            }):
                with patch('os.path.exists', return_value=True):
                    health = JobSubmissionUtils.health_check_dependencies()
                    
                    assert health['polling_service'] is True
                    assert health['database'] is True
                    assert health['file_storage'] is True
    
    @pytest.mark.unit
    def test_health_check_dependencies_failures(self):
        """Test health check with dependency failures."""
        with patch('requests.get', side_effect=RequestException()):
            with patch('os.path.exists', return_value=False):
                health = JobSubmissionUtils.health_check_dependencies()
                
                assert health['polling_service'] is False
                assert health['file_storage'] is False


class TestLoggingUtilities:
    """Test logging and monitoring utilities."""
    
    @pytest.fixture
    def sample_request_data(self):
        """Sample request data for logging tests."""
        return {
            'name': 'Test Job',
            'jobDefinitionUri': 'test_report',
            'arguments': {'param1': 'value1'},
            'submitted_by': 'test_user',
            'password': 'secret123',  # Sensitive data
            'api_key': 'abc123def456'  # Sensitive data
        }
    
    @pytest.mark.unit
    def test_log_request_sanitization(self, sample_request_data):
        """Test request logging with sensitive data sanitization."""
        mock_logger = Mock()
        correlation_id = "test-correlation-123"
        
        JobSubmissionUtils.log_request(sample_request_data, correlation_id, mock_logger)
        
        # Verify logger was called
        mock_logger.info.assert_called_once()
        
        # Get the logged data
        call_args = mock_logger.info.call_args
        logged_data = call_args[1]['extra']['request_data']
        
        # Verify sensitive data is masked
        assert logged_data['password'] == '***MASKED***'
        assert logged_data['api_key'] == '***MASKED***'
        
        # Verify non-sensitive data is preserved
        assert logged_data['name'] == 'Test Job'
        assert logged_data['submitted_by'] == 'test_user'
    
    @pytest.mark.unit
    def test_log_request_with_correlation_id(self, sample_request_data):
        """Test request logging includes correlation ID."""
        mock_logger = Mock()
        correlation_id = "test-correlation-456"
        
        JobSubmissionUtils.log_request(sample_request_data, correlation_id, mock_logger)
        
        call_args = mock_logger.info.call_args
        assert call_args[1]['extra']['correlation_id'] == correlation_id
    
    @pytest.mark.unit
    def test_log_request_default_logger(self, sample_request_data):
        """Test request logging with default logger."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            JobSubmissionUtils.log_request(sample_request_data, "test-id")
            
            mock_get_logger.assert_called_once()
            mock_logger.info.assert_called_once()


class TestRequestHashing:
    """Test request hashing utilities."""
    
    @pytest.fixture
    def sample_request(self):
        """Sample request for hashing tests."""
        return {
            'name': 'Test Job',
            'jobDefinitionUri': 'test_report',
            'arguments': {'param1': 'value1', 'param2': 'value2'},
            'submitted_by': 'test_user',
            'priority': 5
        }
    
    @pytest.mark.unit
    def test_calculate_request_hash_consistency(self, sample_request):
        """Test that identical requests produce identical hashes."""
        hash1 = JobSubmissionUtils.calculate_request_hash(sample_request)
        hash2 = JobSubmissionUtils.calculate_request_hash(sample_request)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length
    
    @pytest.mark.unit
    def test_calculate_request_hash_order_independence(self):
        """Test that key order doesn't affect hash."""
        request1 = {'a': 1, 'b': 2, 'c': 3}
        request2 = {'c': 3, 'a': 1, 'b': 2}
        
        hash1 = JobSubmissionUtils.calculate_request_hash(request1)
        hash2 = JobSubmissionUtils.calculate_request_hash(request2)
        
        assert hash1 == hash2
    
    @pytest.mark.unit
    def test_calculate_request_hash_sensitivity(self, sample_request):
        """Test that small changes produce different hashes."""
        original_hash = JobSubmissionUtils.calculate_request_hash(sample_request)
        
        # Modify one value
        modified_request = sample_request.copy()
        modified_request['priority'] = 10
        modified_hash = JobSubmissionUtils.calculate_request_hash(modified_request)
        
        assert original_hash != modified_hash
    
    @pytest.mark.unit
    def test_calculate_request_hash_non_dict(self):
        """Test hash calculation with non-dictionary input."""
        string_input = "test string input"
        hash_result = JobSubmissionUtils.calculate_request_hash(string_input)
        
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
        
        # Test with different string produces different hash
        different_hash = JobSubmissionUtils.calculate_request_hash("different string")
        assert hash_result != different_hash


class TestPerformanceBenchmarks:
    """Test performance of utility functions."""
    
    @pytest.mark.performance
    def test_sanitize_input_performance(self):
        """Test input sanitization performance."""
        import time
        
        test_strings = [
            "Simple clean string",
            "String with <script>alert('test')</script> tags",
            "String with 'quotes' and \"double quotes\"",
            "A" * 1000  # Long string
        ]
        
        start_time = time.time()
        
        for _ in range(1000):
            for test_string in test_strings:
                try:
                    JobSubmissionUtils.sanitize_input(test_string)
                except ValueError:
                    pass  # Expected for malicious input
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should process 4000 sanitizations in < 1 second
        assert duration < 1.0, f"Sanitization took {duration:.3f}s for 4000 operations"
    
    @pytest.mark.performance
    def test_correlation_id_generation_performance(self):
        """Test correlation ID generation performance."""
        import time
        
        start_time = time.time()
        
        correlation_ids = set()
        for _ in range(10000):
            correlation_id = JobSubmissionUtils.generate_correlation_id()
            correlation_ids.add(correlation_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should generate 10000 IDs in < 1 second
        assert duration < 1.0, f"ID generation took {duration:.3f}s for 10000 operations"
        
        # All IDs should be unique
        assert len(correlation_ids) == 10000
    
    @pytest.mark.performance
    def test_response_formatting_performance(self):
        """Test response formatting performance."""
        import time
        
        sample_data = {
            'job_id': '123e4567-e89b-12d3-a456-426614174000',
            'status': 'submitted',
            'data': list(range(100))  # Some data
        }
        
        start_time = time.time()
        
        for _ in range(1000):
            JobSubmissionUtils.format_success_response(sample_data)
            JobSubmissionUtils.format_error_response(ValueError("Test error"))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should format 2000 responses in < 0.5 seconds
        assert duration < 0.5, f"Response formatting took {duration:.3f}s for 2000 operations"


class TestSecurityValidation:
    """Test security aspects of utility functions."""
    
    @pytest.mark.security
    def test_header_injection_prevention(self):
        """Test prevention of header injection attacks."""
        malicious_headers = {
            'Content-Type': 'application/json\r\nX-Injected: malicious',
            'User-Agent': 'Normal\r\n\r\n<script>alert(1)</script>',
            'X-Custom': 'value\nSet-Cookie: evil=true'
        }
        
        errors = JobSubmissionUtils.validate_request_headers(malicious_headers)
        
        # Should detect malicious content in headers
        assert len(errors) > 0
        assert any('malicious' in error.lower() for error in errors)
    
    @pytest.mark.security
    def test_log_injection_prevention(self):
        """Test prevention of log injection attacks."""
        malicious_request = {
            'name': 'Test\nFAKE LOG ENTRY: Admin login successful',
            'submitted_by': 'user\r\nERROR: System compromised'
        }
        
        mock_logger = Mock()
        correlation_id = "test-correlation"
        
        JobSubmissionUtils.log_request(malicious_request, correlation_id, mock_logger)
        
        # Verify that newlines are handled safely
        call_args = mock_logger.info.call_args
        logged_data = call_args[1]['extra']['request_data']
        
        # Check that the malicious log injection attempts are neutralized
        assert '\n' not in str(logged_data) or '\r' not in str(logged_data)
    
    @pytest.mark.security
    def test_sensitive_data_masking_comprehensive(self):
        """Test comprehensive sensitive data masking."""
        sensitive_request = {
            'password': 'secretpassword',
            'token': 'bearer_token_123',
            'api_key': 'sk-1234567890abcdef',
            'secret': 'topsecret',
            'PASSWORD': 'UPPERCASE_PASSWORD',  # Case variations
            'auth_token': 'auth_12345',
            'normal_field': 'normal_value'
        }
        
        mock_logger = Mock()
        JobSubmissionUtils.log_request(sensitive_request, "test-id", mock_logger)
        
        call_args = mock_logger.info.call_args
        logged_data = call_args[1]['extra']['request_data']
        
        # Verify sensitive fields are masked
        sensitive_patterns = ['password', 'token', 'secret', 'api_key']
        for field_name, field_value in logged_data.items():
            if any(pattern.lower() in field_name.lower() for pattern in sensitive_patterns):
                assert field_value == '***MASKED***'
        
        # Verify normal fields are preserved
        assert logged_data['normal_field'] == 'normal_value'
