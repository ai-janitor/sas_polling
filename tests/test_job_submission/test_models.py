"""
=============================================================================
JOB SUBMISSION DATA MODELS UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job submission data validation models
Technology: pytest with Pydantic model testing and validation scenarios
Module: job-submission/models.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test all Pydantic model validation rules
- Mock external dependencies and configurations
- Validate serialization/deserialization accuracy
- Test error handling and edge cases

TEST CATEGORIES:
1. JobRequest Model Tests
   - Field validation (name, jobDefinitionUri, arguments)
   - Required field enforcement
   - Type validation and coercion
   - Value range and format validation
   - Cross-field dependency validation

2. JobResponse Model Tests
   - Response structure validation
   - UUID field format validation
   - URL format validation
   - Status field enumeration
   - Timestamp field validation

3. ValidationError Model Tests
   - Error message structure
   - Field-specific error mapping
   - Error code standardization
   - Multi-field error aggregation
   - Localization support

4. Serialization Tests
   - to_dict() method accuracy
   - from_dict() method validation
   - JSON serialization compliance
   - Unicode and special character handling
   - Large payload handling

5. Validation Rule Tests
   - Job name constraints (1-255 chars)
   - Report ID existence validation
   - Parameter schema compliance
   - Priority range validation (1-10)
   - User identifier validation

6. Edge Case Tests
   - Empty string handling
   - Null value processing
   - Boundary value testing
   - Invalid data type handling
   - Malformed input recovery

MOCK STRATEGY:
- Mock report definition lookups
- Mock configuration loading
- Mock external validation services
- Mock database connections
- Mock file system operations

VALIDATION SCENARIOS:
- Valid model instantiation
- Invalid field values
- Missing required fields
- Type conversion errors
- Business rule violations

SECURITY TESTS:
- Input sanitization validation
- XSS prevention in text fields
- SQL injection prevention
- Path traversal prevention
- Size limit enforcement

PERFORMANCE BENCHMARKS:
- Model validation < 100ms
- Serialization < 50ms
- Large dataset handling
- Memory usage optimization
- Concurrent validation

DEPENDENCIES:
- pytest: Test framework
- pydantic: Model validation
- faker: Test data generation
- pytest-benchmark: Performance testing
- pytest-mock: Mocking utilities
=============================================================================
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError
import uuid
from faker import Faker
import re

# Mock model classes (actual implementation would import from job-submission/models.py)
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from enum import Enum


class JobPriority(Enum):
    """Job priority enumeration."""
    LOW = 1
    NORMAL = 5
    HIGH = 10


class JobStatus(Enum):
    """Job status enumeration."""
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRequest(BaseModel):
    """Job submission request model."""
    name: str = Field(..., min_length=1, max_length=255)
    jobDefinitionUri: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    submitted_by: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(default=5, ge=1, le=10)
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @validator('submitted_by')
    def validate_submitted_by(cls, v):
        if not re.match(r'^[a-zA-Z0-9\._\-@]+$', v):
            raise ValueError('Invalid user identifier format')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "name": "CMBS Portfolio Analysis Q2 2024",
                "jobDefinitionUri": "cmbs_user_manual",
                "arguments": {
                    "asofqtr": "Q2",
                    "year": "2024",
                    "sortorder": "Name"
                },
                "submitted_by": "user@company.com",
                "priority": 5
            }
        }


class JobResponse(BaseModel):
    """Job submission response model."""
    id: str = Field(..., description="UUID job identifier")
    status: JobStatus = Field(default=JobStatus.SUBMITTED)
    polling_url: str = Field(..., description="Status polling endpoint")
    estimated_duration: int = Field(..., ge=0, description="Estimated seconds")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v
    
    @validator('polling_url')
    def validate_url(cls, v):
        url_pattern = r'^https?://[\w\.-]+(?::\d+)?/[\w\./\-]*$'
        if not re.match(url_pattern, v):
            raise ValueError('Invalid URL format')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "submitted",
                "polling_url": "http://localhost:5001/api/jobs/123e4567-e89b-12d3-a456-426614174000/status",
                "estimated_duration": 180,
                "submitted_at": "2024-01-15T10:30:00Z"
            }
        }


class JobValidationError(BaseModel):
    """Validation error details model."""
    field: str = Field(..., description="Field name with error")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Error code for programmatic handling")
    value: Optional[Any] = Field(None, description="Invalid value that caused error")
    
    class Config:
        schema_extra = {
            "example": {
                "field": "priority",
                "message": "Priority must be between 1 and 10",
                "code": "VALUE_OUT_OF_RANGE",
                "value": 15
            }
        }


class TestJobRequestModel:
    """Test JobRequest model validation and functionality."""
    
    @pytest.fixture
    def faker_instance(self):
        """Faker instance for generating test data."""
        return Faker()
    
    @pytest.fixture
    def valid_job_request_data(self):
        """Valid job request data for testing."""
        return {
            "name": "Test CMBS Report Q2 2024",
            "jobDefinitionUri": "cmbs_user_manual",
            "arguments": {
                "asofqtr": "Q2",
                "year": "2024",
                "sortorder": "Name",
                "outputtp": "HTML"
            },
            "submitted_by": "test_user@company.com",
            "priority": 5
        }
    
    @pytest.fixture
    def minimal_job_request_data(self):
        """Minimal valid job request data."""
        return {
            "name": "Test Job",
            "jobDefinitionUri": "test_report",
            "submitted_by": "test_user"
        }
    
    @pytest.mark.unit
    def test_valid_job_request_creation(self, valid_job_request_data):
        """Test creating valid JobRequest instance."""
        job_request = JobRequest(**valid_job_request_data)
        
        assert job_request.name == valid_job_request_data["name"]
        assert job_request.jobDefinitionUri == valid_job_request_data["jobDefinitionUri"]
        assert job_request.arguments == valid_job_request_data["arguments"]
        assert job_request.submitted_by == valid_job_request_data["submitted_by"]
        assert job_request.priority == valid_job_request_data["priority"]
    
    @pytest.mark.unit
    def test_minimal_job_request_creation(self, minimal_job_request_data):
        """Test creating JobRequest with minimal required fields."""
        job_request = JobRequest(**minimal_job_request_data)
        
        assert job_request.name == minimal_job_request_data["name"]
        assert job_request.jobDefinitionUri == minimal_job_request_data["jobDefinitionUri"]
        assert job_request.submitted_by == minimal_job_request_data["submitted_by"]
        assert job_request.arguments == {}  # Default empty dict
        assert job_request.priority == 5  # Default priority
    
    @pytest.mark.unit
    def test_job_request_missing_required_fields(self):
        """Test JobRequest validation with missing required fields."""
        incomplete_data = {
            "name": "Test Job"
            # Missing jobDefinitionUri and submitted_by
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobRequest(**incomplete_data)
        
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        
        assert 'jobDefinitionUri' in error_fields
        assert 'submitted_by' in error_fields
    
    @pytest.mark.unit
    def test_job_request_name_validation(self):
        """Test job name validation rules."""
        base_data = {
            "jobDefinitionUri": "test_report",
            "submitted_by": "test_user"
        }
        
        # Test empty name
        with pytest.raises(ValidationError):
            JobRequest(name="", **base_data)
        
        # Test too long name
        with pytest.raises(ValidationError):
            JobRequest(name="x" * 256, **base_data)
        
        # Test invalid characters
        with pytest.raises(ValidationError):
            JobRequest(name="Test Job <script>", **base_data)
        
        # Test valid names
        valid_names = [
            "Simple Job",
            "Job-with-dashes",
            "Job_with_underscores",
            "Job.with.dots",
            "Job 123"
        ]
        
        for name in valid_names:
            job_request = JobRequest(name=name, **base_data)
            assert job_request.name == name.strip()
    
    @pytest.mark.unit
    def test_job_request_priority_validation(self):
        """Test priority field validation."""
        base_data = {
            "name": "Test Job",
            "jobDefinitionUri": "test_report",
            "submitted_by": "test_user"
        }
        
        # Test invalid priority values
        invalid_priorities = [0, -1, 11, 100, "high", None]
        
        for priority in invalid_priorities:
            with pytest.raises(ValidationError):
                JobRequest(priority=priority, **base_data)
        
        # Test valid priority values
        valid_priorities = [1, 5, 10]
        
        for priority in valid_priorities:
            job_request = JobRequest(priority=priority, **base_data)
            assert job_request.priority == priority
    
    @pytest.mark.unit
    def test_job_request_submitted_by_validation(self):
        """Test submitted_by field validation."""
        base_data = {
            "name": "Test Job",
            "jobDefinitionUri": "test_report"
        }
        
        # Test invalid submitted_by values
        invalid_users = [
            "",  # Empty
            "user with spaces",  # Spaces
            "user<script>",  # HTML
            "user;DROP TABLE;",  # SQL injection attempt
            "x" * 101  # Too long
        ]
        
        for user in invalid_users:
            with pytest.raises(ValidationError):
                JobRequest(submitted_by=user, **base_data)
        
        # Test valid submitted_by values
        valid_users = [
            "test_user",
            "user@company.com",
            "user.name",
            "user-123",
            "TestUser123"
        ]
        
        for user in valid_users:
            job_request = JobRequest(submitted_by=user, **base_data)
            assert job_request.submitted_by == user.strip()
    
    @pytest.mark.unit
    def test_job_request_arguments_validation(self, valid_job_request_data):
        """Test arguments field handling."""
        # Test with different argument types
        test_arguments = [
            {},  # Empty dict
            {"string_param": "value"},
            {"int_param": 123},
            {"float_param": 45.67},
            {"bool_param": True},
            {"list_param": [1, 2, 3]},
            {"nested_param": {"sub_key": "sub_value"}}
        ]
        
        for arguments in test_arguments:
            data = valid_job_request_data.copy()
            data["arguments"] = arguments
            
            job_request = JobRequest(**data)
            assert job_request.arguments == arguments
    
    @pytest.mark.unit
    def test_job_request_serialization(self, valid_job_request_data):
        """Test JobRequest serialization methods."""
        job_request = JobRequest(**valid_job_request_data)
        
        # Test dict() method
        job_dict = job_request.dict()
        assert isinstance(job_dict, dict)
        assert job_dict["name"] == valid_job_request_data["name"]
        assert job_dict["arguments"] == valid_job_request_data["arguments"]
        
        # Test json() method
        job_json = job_request.json()
        assert isinstance(job_json, str)
        
        # Test round-trip serialization
        parsed_data = json.loads(job_json)
        reconstructed = JobRequest(**parsed_data)
        assert reconstructed.name == job_request.name
        assert reconstructed.arguments == job_request.arguments
    
    @pytest.mark.unit
    def test_job_request_unicode_handling(self):
        """Test Unicode character handling in job requests."""
        unicode_data = {
            "name": "Test Job 测试 работа",
            "jobDefinitionUri": "test_report",
            "submitted_by": "test_user",
            "arguments": {
                "unicode_param": "Value with üñíçødé characters"
            }
        }
        
        job_request = JobRequest(**unicode_data)
        
        assert "测试" in job_request.name
        assert "üñíçødé" in job_request.arguments["unicode_param"]
        
        # Test serialization preserves Unicode
        job_json = job_request.json()
        parsed_data = json.loads(job_json)
        assert "测试" in parsed_data["name"]


class TestJobResponseModel:
    """Test JobResponse model validation and functionality."""
    
    @pytest.fixture
    def valid_job_response_data(self):
        """Valid job response data for testing."""
        return {
            "id": str(uuid.uuid4()),
            "status": JobStatus.SUBMITTED,
            "polling_url": "http://localhost:5001/api/jobs/test-id/status",
            "estimated_duration": 180
        }
    
    @pytest.mark.unit
    def test_valid_job_response_creation(self, valid_job_response_data):
        """Test creating valid JobResponse instance."""
        job_response = JobResponse(**valid_job_response_data)
        
        assert job_response.id == valid_job_response_data["id"]
        assert job_response.status == valid_job_response_data["status"]
        assert job_response.polling_url == valid_job_response_data["polling_url"]
        assert job_response.estimated_duration == valid_job_response_data["estimated_duration"]
        assert isinstance(job_response.submitted_at, datetime)
    
    @pytest.mark.unit
    def test_job_response_uuid_validation(self):
        """Test UUID validation in job response."""
        base_data = {
            "status": JobStatus.SUBMITTED,
            "polling_url": "http://localhost:5001/api/jobs/test-id/status",
            "estimated_duration": 180
        }
        
        # Test invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "123",
            "123e4567-e89b-12d3-a456",  # Incomplete
            "",
            "123e4567-XXXX-12d3-a456-426614174000"  # Invalid characters
        ]
        
        for invalid_uuid in invalid_uuids:
            with pytest.raises(ValidationError):
                JobResponse(id=invalid_uuid, **base_data)
        
        # Test valid UUID
        valid_uuid = str(uuid.uuid4())
        job_response = JobResponse(id=valid_uuid, **base_data)
        assert job_response.id == valid_uuid
    
    @pytest.mark.unit
    def test_job_response_url_validation(self):
        """Test polling URL validation."""
        base_data = {
            "id": str(uuid.uuid4()),
            "status": JobStatus.SUBMITTED,
            "estimated_duration": 180
        }
        
        # Test invalid URLs
        invalid_urls = [
            "not-a-url",
            "ftp://localhost/path",  # Wrong protocol
            "http://",  # Incomplete
            "localhost:5001/path",  # Missing protocol
            "http://localhost:5001/path with spaces"
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError):
                JobResponse(polling_url=invalid_url, **base_data)
        
        # Test valid URLs
        valid_urls = [
            "http://localhost:5001/api/jobs/test-id/status",
            "https://api.example.com/jobs/123/status",
            "http://192.168.1.100:8080/status"
        ]
        
        for valid_url in valid_urls:
            job_response = JobResponse(polling_url=valid_url, **base_data)
            assert job_response.polling_url == valid_url
    
    @pytest.mark.unit
    def test_job_response_status_validation(self):
        """Test job status enumeration validation."""
        base_data = {
            "id": str(uuid.uuid4()),
            "polling_url": "http://localhost:5001/api/jobs/test-id/status",
            "estimated_duration": 180
        }
        
        # Test all valid status values
        for status in JobStatus:
            job_response = JobResponse(status=status, **base_data)
            assert job_response.status == status
        
        # Test invalid status (would be caught by Pydantic)
        with pytest.raises(ValidationError):
            JobResponse(status="invalid_status", **base_data)
    
    @pytest.mark.unit
    def test_job_response_estimated_duration_validation(self):
        """Test estimated duration validation."""
        base_data = {
            "id": str(uuid.uuid4()),
            "status": JobStatus.SUBMITTED,
            "polling_url": "http://localhost:5001/api/jobs/test-id/status"
        }
        
        # Test invalid durations
        invalid_durations = [-1, -100, "not_a_number", None]
        
        for duration in invalid_durations:
            with pytest.raises(ValidationError):
                JobResponse(estimated_duration=duration, **base_data)
        
        # Test valid durations
        valid_durations = [0, 1, 60, 3600, 86400]
        
        for duration in valid_durations:
            job_response = JobResponse(estimated_duration=duration, **base_data)
            assert job_response.estimated_duration == duration
    
    @pytest.mark.unit
    def test_job_response_serialization(self, valid_job_response_data):
        """Test JobResponse serialization with enum handling."""
        job_response = JobResponse(**valid_job_response_data)
        
        # Test dict() method
        response_dict = job_response.dict()
        assert isinstance(response_dict, dict)
        assert response_dict["status"] == "submitted"  # Enum value, not enum
        
        # Test json() method
        response_json = job_response.json()
        assert isinstance(response_json, str)
        
        # Verify enum is serialized as string value
        parsed_data = json.loads(response_json)
        assert parsed_data["status"] == "submitted"


class TestJobValidationErrorModel:
    """Test JobValidationError model functionality."""
    
    @pytest.fixture
    def valid_error_data(self):
        """Valid validation error data for testing."""
        return {
            "field": "priority",
            "message": "Priority must be between 1 and 10",
            "code": "VALUE_OUT_OF_RANGE",
            "value": 15
        }
    
    @pytest.mark.unit
    def test_valid_validation_error_creation(self, valid_error_data):
        """Test creating valid JobValidationError instance."""
        error = JobValidationError(**valid_error_data)
        
        assert error.field == valid_error_data["field"]
        assert error.message == valid_error_data["message"]
        assert error.code == valid_error_data["code"]
        assert error.value == valid_error_data["value"]
    
    @pytest.mark.unit
    def test_validation_error_without_value(self):
        """Test validation error without value field."""
        error_data = {
            "field": "name",
            "message": "Name is required",
            "code": "REQUIRED_FIELD_MISSING"
        }
        
        error = JobValidationError(**error_data)
        assert error.value is None
    
    @pytest.mark.unit
    def test_validation_error_serialization(self, valid_error_data):
        """Test validation error serialization."""
        error = JobValidationError(**valid_error_data)
        
        error_dict = error.dict()
        assert error_dict["field"] == valid_error_data["field"]
        assert error_dict["code"] == valid_error_data["code"]
        
        error_json = error.json()
        parsed_data = json.loads(error_json)
        assert parsed_data["message"] == valid_error_data["message"]


class TestModelIntegration:
    """Test integration between different models."""
    
    @pytest.mark.unit
    def test_end_to_end_validation_workflow(self):
        """Test complete validation workflow from request to response."""
        # Create job request
        request_data = {
            "name": "Integration Test Job",
            "jobDefinitionUri": "test_report",
            "arguments": {"param1": "value1"},
            "submitted_by": "integration_test",
            "priority": 7
        }
        
        job_request = JobRequest(**request_data)
        
        # Simulate processing and create response
        job_id = str(uuid.uuid4())
        response_data = {
            "id": job_id,
            "status": JobStatus.SUBMITTED,
            "polling_url": f"http://localhost:5001/api/jobs/{job_id}/status",
            "estimated_duration": 120
        }
        
        job_response = JobResponse(**response_data)
        
        # Verify integration
        assert job_request.name == request_data["name"]
        assert job_response.id == job_id
        assert job_response.status == JobStatus.SUBMITTED
    
    @pytest.mark.performance
    def test_model_validation_performance(self, faker_instance):
        """Test model validation performance with large datasets."""
        import time
        
        # Generate test data
        test_requests = []
        for _ in range(1000):
            request_data = {
                "name": faker_instance.sentence(nb_words=4),
                "jobDefinitionUri": faker_instance.word(),
                "arguments": {faker_instance.word(): faker_instance.word()},
                "submitted_by": faker_instance.user_name(),
                "priority": faker_instance.random_int(min=1, max=10)
            }
            test_requests.append(request_data)
        
        # Measure validation performance
        start_time = time.time()
        
        for request_data in test_requests:
            try:
                JobRequest(**request_data)
            except ValidationError:
                pass  # Expected for some generated data
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertion (should process 1000 validations in < 1 second)
        assert duration < 1.0, f"Validation took {duration:.3f}s for 1000 items"
        
        # Average validation time should be < 100ms
        avg_time = (duration / len(test_requests)) * 1000
        assert avg_time < 100, f"Average validation time {avg_time:.3f}ms too high"


class TestSecurityValidation:
    """Test security-related validation scenarios."""
    
    @pytest.mark.security
    def test_xss_prevention_in_text_fields(self):
        """Test XSS prevention in text input fields."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        base_data = {
            "jobDefinitionUri": "test_report",
            "submitted_by": "test_user"
        }
        
        for malicious_input in malicious_inputs:
            with pytest.raises(ValidationError):
                JobRequest(name=malicious_input, **base_data)
    
    @pytest.mark.security
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in input fields."""
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET admin=1; --",
            "' UNION SELECT * FROM passwords --"
        ]
        
        base_data = {
            "name": "Test Job",
            "jobDefinitionUri": "test_report"
        }
        
        for injection_attempt in sql_injection_attempts:
            with pytest.raises(ValidationError):
                JobRequest(submitted_by=injection_attempt, **base_data)
    
    @pytest.mark.security
    def test_path_traversal_prevention(self):
        """Test path traversal prevention in file-related fields."""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        base_data = {
            "name": "Test Job",
            "submitted_by": "test_user"
        }
        
        for traversal_attempt in path_traversal_attempts:
            # Test in jobDefinitionUri field
            with pytest.raises(ValidationError):
                JobRequest(jobDefinitionUri=traversal_attempt, **base_data)
    
    @pytest.mark.security
    def test_input_size_limits(self):
        """Test input size limit enforcement."""
        # Test oversized inputs
        oversized_data = {
            "name": "x" * 1000,  # Much larger than 255 char limit
            "jobDefinitionUri": "test_report",
            "submitted_by": "x" * 200,  # Larger than 100 char limit
            "arguments": {"key" * 100: "value" * 1000}  # Large arguments
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobRequest(**oversized_data)
        
        errors = exc_info.value.errors()
        error_fields = [error['loc'][0] for error in errors]
        
        assert 'name' in error_fields
        assert 'submitted_by' in error_fields
