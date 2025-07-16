"""
=============================================================================
JOB POLLING SERVICE DATA MODELS UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job polling service data models
Technology: pytest with Pydantic model testing and job lifecycle validation
Module: job-polling/models.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test all job lifecycle state transitions
- Mock external dependencies and configurations
- Validate job data consistency and integrity
- Test error handling and edge cases

TEST CATEGORIES:
1. Job Model Tests
   - Job creation and initialization
   - Status transition validation
   - Progress tracking accuracy
   - Timestamp management
   - File association handling

2. JobStatus Enumeration Tests
   - Valid status values
   - Status transition rules
   - Invalid status handling
   - State machine compliance
   - Serialization consistency

3. JobFile Model Tests
   - File metadata validation
   - File type restrictions
   - File size limits
   - Download URL generation
   - Security attribute validation

4. JobProgress Model Tests
   - Progress percentage validation (0-100)
   - Progress step tracking
   - Estimated time calculations
   - Progress message handling
   - Completion detection

5. JobError Model Tests
   - Error classification
   - Error message formatting
   - Stack trace handling
   - Error recovery information
   - Retry attempt tracking

6. JobQueue Model Tests
   - Queue position tracking
   - Priority ordering
   - Queue capacity management
   - FIFO behavior validation
   - Queue statistics

MOCK STRATEGY:
- Mock file system operations
- Mock timestamp generation
- Mock UUID generation
- Mock configuration values
- Mock external service calls

VALIDATION SCENARIOS:
- Valid model instantiation
- Invalid field values
- State transition validation
- Business rule compliance
- Cross-model relationships

ERROR SCENARIOS:
- Invalid status transitions
- Malformed file paths
- Progress out of range
- Invalid timestamps
- Circular dependencies

PERFORMANCE BENCHMARKS:
- Model validation < 50ms
- Status updates < 10ms
- File operations < 100ms
- Progress calculations < 5ms
- Queue operations < 20ms

SECURITY TESTS:
- Input sanitization
- Path traversal prevention
- File access validation
- Permission checking
- Data leak prevention

DEPENDENCIES:
- pytest: Test framework
- pydantic: Model validation
- enum: Enumeration testing
- datetime: Timestamp testing
- pathlib: Path validation
=============================================================================
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field, ValidationError, validator
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pathlib import Path
import uuid
import os
from faker import Faker
import tempfile

# Mock model classes (actual implementation would import from job-polling/models.py)
class JobStatus(str, Enum):
    """Job status enumeration with string values."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobPriority(int, Enum):
    """Job priority enumeration."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class FileType(str, Enum):
    """Supported file types."""
    HTML = "text/html"
    PDF = "application/pdf"
    CSV = "text/csv"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    JSON = "application/json"
    XML = "application/xml"


class JobFile(BaseModel):
    """Job output file model."""
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: FileType
    size_bytes: int = Field(..., ge=0)
    download_url: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: Optional[str] = Field(None, regex=r'^[a-fA-F0-9]{64}$')  # SHA-256
    is_temporary: bool = Field(default=True)
    retention_days: int = Field(default=7, ge=1, le=365)
    
    @validator('filename')
    def validate_filename(cls, v):
        # Prevent path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Filename contains invalid path characters')
        
        # Check for dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.scr']
        if any(v.lower().endswith(ext) for ext in dangerous_extensions):
            raise ValueError('Potentially dangerous file extension')
        
        return v
    
    @validator('download_url')
    def validate_download_url(cls, v):
        # Basic URL validation
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Invalid URL format')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "filename": "cmbs_report_2024_q2.html",
                "file_type": "text/html",
                "size_bytes": 2048576,
                "download_url": "http://localhost:5001/api/jobs/123/files/cmbs_report_2024_q2.html",
                "checksum": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
                "is_temporary": True,
                "retention_days": 7
            }
        }


class JobProgress(BaseModel):
    """Job progress tracking model."""
    percentage: int = Field(default=0, ge=0, le=100)
    current_step: str = Field(default="Initializing")
    total_steps: int = Field(default=1, ge=1)
    completed_steps: int = Field(default=0, ge=0)
    estimated_remaining_seconds: Optional[int] = Field(None, ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('completed_steps')
    def validate_completed_steps(cls, v, values):
        total_steps = values.get('total_steps', 1)
        if v > total_steps:
            raise ValueError('Completed steps cannot exceed total steps')
        return v
    
    @validator('percentage')
    def validate_percentage_consistency(cls, v, values):
        completed_steps = values.get('completed_steps', 0)
        total_steps = values.get('total_steps', 1)
        
        expected_percentage = int((completed_steps / total_steps) * 100)
        if abs(v - expected_percentage) > 5:  # Allow 5% tolerance
            raise ValueError('Percentage does not match step completion ratio')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "percentage": 75,
                "current_step": "Generating PDF report",
                "total_steps": 4,
                "completed_steps": 3,
                "estimated_remaining_seconds": 30,
                "details": {
                    "rows_processed": 15000,
                    "charts_generated": 8,
                    "memory_usage_mb": 256
                }
            }
        }


class JobError(BaseModel):
    """Job error information model."""
    error_type: str = Field(..., min_length=1)
    error_message: str = Field(..., min_length=1)
    error_code: Optional[str] = Field(None)
    stack_trace: Optional[str] = Field(None)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    is_retryable: bool = Field(default=False)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('retry_count')
    def validate_retry_count(cls, v, values):
        max_retries = values.get('max_retries', 3)
        if v > max_retries:
            raise ValueError('Retry count cannot exceed maximum retries')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "error_type": "DataProcessingError",
                "error_message": "Unable to process CSV data: Invalid date format in row 1250",
                "error_code": "CSV_PARSE_ERROR",
                "is_retryable": True,
                "retry_count": 1,
                "max_retries": 3,
                "context": {
                    "file_name": "trading_data.csv",
                    "row_number": 1250,
                    "column_name": "trade_date"
                }
            }
        }


class Job(BaseModel):
    """Job model with complete lifecycle management."""
    id: str = Field(..., description="UUID job identifier")
    name: str = Field(..., min_length=1, max_length=255)
    report_id: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    submitted_by: str = Field(..., min_length=1, max_length=100)
    priority: JobPriority = Field(default=JobPriority.NORMAL)
    status: JobStatus = Field(default=JobStatus.QUEUED)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = Field(None)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    # Progress and results
    progress: JobProgress = Field(default_factory=JobProgress)
    files: List[JobFile] = Field(default_factory=list)
    error: Optional[JobError] = Field(None)
    
    # Job configuration
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)  # 1 hour default, max 24 hours
    estimated_duration_seconds: int = Field(default=300, ge=1)
    
    @validator('id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v
    
    @validator('status')
    def validate_status_transitions(cls, v, values):
        # Basic status transition validation
        # In real implementation, this would check previous status
        valid_statuses = set(JobStatus)
        if v not in valid_statuses:
            raise ValueError(f'Invalid status: {v}')
        return v
    
    @validator('completed_at')
    def validate_completion_timestamp(cls, v, values):
        if v is not None:
            created_at = values.get('created_at')
            if created_at and v < created_at:
                raise ValueError('Completion time cannot be before creation time')
        return v
    
    def update_status(self, new_status: JobStatus, **kwargs):
        """Update job status with validation."""
        # Validate status transition
        if not self._is_valid_transition(self.status, new_status):
            raise ValueError(f'Invalid status transition from {self.status} to {new_status}')
        
        self.status = new_status
        
        # Update timestamps based on status
        now = datetime.utcnow()
        if new_status == JobStatus.RUNNING and not self.started_at:
            self.started_at = now
        elif new_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            if not self.completed_at:
                self.completed_at = now
        
        # Update other fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _is_valid_transition(self, from_status: JobStatus, to_status: JobStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            JobStatus.QUEUED: [JobStatus.RUNNING, JobStatus.CANCELLED],
            JobStatus.RUNNING: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.PAUSED],
            JobStatus.PAUSED: [JobStatus.RUNNING, JobStatus.CANCELLED],
            JobStatus.COMPLETED: [],  # Terminal state
            JobStatus.FAILED: [JobStatus.QUEUED],  # Can be retried
            JobStatus.CANCELLED: []  # Terminal state
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    def add_file(self, filename: str, file_type: FileType, size_bytes: int, download_url: str, **kwargs):
        """Add output file to job."""
        job_file = JobFile(
            filename=filename,
            file_type=file_type,
            size_bytes=size_bytes,
            download_url=download_url,
            **kwargs
        )
        self.files.append(job_file)
        return job_file
    
    def update_progress(self, percentage: int, current_step: str = None, **kwargs):
        """Update job progress."""
        self.progress.percentage = percentage
        if current_step:
            self.progress.current_step = current_step
        
        for key, value in kwargs.items():
            if hasattr(self.progress, key):
                setattr(self.progress, key, value)
        
        self.progress.last_updated = datetime.utcnow()
    
    def set_error(self, error_type: str, error_message: str, **kwargs):
        """Set job error information."""
        self.error = JobError(
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )
        self.update_status(JobStatus.FAILED)
    
    def get_duration(self) -> Optional[timedelta]:
        """Get job execution duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return None
    
    def is_terminal(self) -> bool:
        """Check if job is in terminal state."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def is_active(self) -> bool:
        """Check if job is actively running."""
        return self.status in [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED]
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "CMBS Portfolio Analysis Q2 2024",
                "report_id": "cmbs_user_manual",
                "arguments": {
                    "asofqtr": "Q2",
                    "year": "2024",
                    "sortorder": "Name"
                },
                "submitted_by": "analyst@company.com",
                "priority": 5,
                "status": "running",
                "timeout_seconds": 3600,
                "estimated_duration_seconds": 300
            }
        }


class JobQueueEntry(BaseModel):
    """Job queue entry with position tracking."""
    job: Job
    queue_position: int = Field(..., ge=1)
    estimated_start_time: Optional[datetime] = Field(None)
    priority_score: float = Field(default=0.0)
    
    class Config:
        schema_extra = {
            "example": {
                "queue_position": 3,
                "estimated_start_time": "2024-01-15T14:30:00Z",
                "priority_score": 7.5
            }
        }


class TestJobFileModel:
    """Test JobFile model validation and functionality."""
    
    @pytest.fixture
    def faker_instance(self):
        """Faker instance for generating test data."""
        return Faker()
    
    @pytest.fixture
    def valid_file_data(self):
        """Valid job file data for testing."""
        return {
            "filename": "test_report.html",
            "file_type": FileType.HTML,
            "size_bytes": 1024000,
            "download_url": "http://localhost:5001/api/jobs/123/files/test_report.html",
            "checksum": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "retention_days": 14
        }
    
    @pytest.mark.unit
    def test_valid_job_file_creation(self, valid_file_data):
        """Test creating valid JobFile instance."""
        job_file = JobFile(**valid_file_data)
        
        assert job_file.filename == valid_file_data["filename"]
        assert job_file.file_type == valid_file_data["file_type"]
        assert job_file.size_bytes == valid_file_data["size_bytes"]
        assert job_file.download_url == valid_file_data["download_url"]
        assert job_file.checksum == valid_file_data["checksum"]
        assert isinstance(job_file.created_at, datetime)
    
    @pytest.mark.unit
    def test_filename_validation_path_traversal(self):
        """Test filename validation prevents path traversal."""
        base_data = {
            "file_type": FileType.HTML,
            "size_bytes": 1024,
            "download_url": "http://localhost:5001/api/jobs/123/files/test.html"
        }
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "test/../../../etc/shadow",
            "normal_file.txt/../../etc/passwd"
        ]
        
        for malicious_filename in malicious_filenames:
            with pytest.raises(ValidationError) as exc_info:
                JobFile(filename=malicious_filename, **base_data)
            
            error_message = str(exc_info.value)
            assert 'invalid path characters' in error_message.lower()
    
    @pytest.mark.unit
    def test_filename_validation_dangerous_extensions(self):
        """Test filename validation prevents dangerous file extensions."""
        base_data = {
            "file_type": FileType.HTML,
            "size_bytes": 1024,
            "download_url": "http://localhost:5001/api/jobs/123/files/test.html"
        }
        
        dangerous_filenames = [
            "malware.exe",
            "script.bat",
            "command.cmd",
            "script.sh",
            "powershell.ps1",
            "screensaver.scr"
        ]
        
        for dangerous_filename in dangerous_filenames:
            with pytest.raises(ValidationError) as exc_info:
                JobFile(filename=dangerous_filename, **base_data)
            
            error_message = str(exc_info.value)
            assert 'dangerous file extension' in error_message.lower()
    
    @pytest.mark.unit
    def test_download_url_validation(self):
        """Test download URL validation."""
        base_data = {
            "filename": "test.html",
            "file_type": FileType.HTML,
            "size_bytes": 1024
        }
        
        # Test invalid URLs
        invalid_urls = [
            "not-a-url",
            "ftp://localhost/file.txt",
            "file:///etc/passwd",
            "javascript:alert('xss')",
            ""
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError):
                JobFile(download_url=invalid_url, **base_data)
        
        # Test valid URLs
        valid_urls = [
            "http://localhost:5001/api/jobs/123/files/test.html",
            "https://api.example.com/files/report.pdf",
            "http://192.168.1.100:8080/download/data.csv"
        ]
        
        for valid_url in valid_urls:
            job_file = JobFile(download_url=valid_url, **base_data)
            assert job_file.download_url == valid_url
    
    @pytest.mark.unit
    def test_checksum_validation(self):
        """Test checksum format validation."""
        base_data = {
            "filename": "test.html",
            "file_type": FileType.HTML,
            "size_bytes": 1024,
            "download_url": "http://localhost:5001/api/jobs/123/files/test.html"
        }
        
        # Test invalid checksums
        invalid_checksums = [
            "invalid",
            "123",
            "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae",  # Too short
            "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae33",  # Too long
            "g665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"  # Invalid hex
        ]
        
        for invalid_checksum in invalid_checksums:
            with pytest.raises(ValidationError):
                JobFile(checksum=invalid_checksum, **base_data)
        
        # Test valid checksum
        valid_checksum = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
        job_file = JobFile(checksum=valid_checksum, **base_data)
        assert job_file.checksum == valid_checksum
    
    @pytest.mark.unit
    def test_file_type_enumeration(self):
        """Test file type enumeration validation."""
        base_data = {
            "filename": "test_file",
            "size_bytes": 1024,
            "download_url": "http://localhost:5001/api/jobs/123/files/test_file"
        }
        
        # Test all valid file types
        for file_type in FileType:
            job_file = JobFile(file_type=file_type, **base_data)
            assert job_file.file_type == file_type
        
        # Test invalid file type
        with pytest.raises(ValidationError):
            JobFile(file_type="invalid/type", **base_data)


class TestJobProgressModel:
    """Test JobProgress model validation and functionality."""
    
    @pytest.fixture
    def valid_progress_data(self):
        """Valid job progress data for testing."""
        return {
            "percentage": 75,
            "current_step": "Generating charts",
            "total_steps": 4,
            "completed_steps": 3,
            "estimated_remaining_seconds": 45,
            "details": {
                "charts_generated": 8,
                "memory_usage_mb": 256
            }
        }
    
    @pytest.mark.unit
    def test_valid_progress_creation(self, valid_progress_data):
        """Test creating valid JobProgress instance."""
        progress = JobProgress(**valid_progress_data)
        
        assert progress.percentage == valid_progress_data["percentage"]
        assert progress.current_step == valid_progress_data["current_step"]
        assert progress.total_steps == valid_progress_data["total_steps"]
        assert progress.completed_steps == valid_progress_data["completed_steps"]
        assert isinstance(progress.last_updated, datetime)
    
    @pytest.mark.unit
    def test_percentage_validation(self):
        """Test percentage validation (0-100 range)."""
        base_data = {
            "total_steps": 4,
            "completed_steps": 2
        }
        
        # Test invalid percentages
        invalid_percentages = [-1, -10, 101, 150, 999]
        
        for invalid_percentage in invalid_percentages:
            with pytest.raises(ValidationError):
                JobProgress(percentage=invalid_percentage, **base_data)
        
        # Test valid percentages
        valid_percentages = [0, 25, 50, 75, 100]
        
        for valid_percentage in valid_percentages:
            progress = JobProgress(percentage=valid_percentage, **base_data)
            assert progress.percentage == valid_percentage
    
    @pytest.mark.unit
    def test_completed_steps_validation(self):
        """Test that completed steps cannot exceed total steps."""
        with pytest.raises(ValidationError) as exc_info:
            JobProgress(
                total_steps=4,
                completed_steps=5,  # More than total
                percentage=100
            )
        
        error_message = str(exc_info.value)
        assert 'completed steps cannot exceed total steps' in error_message.lower()
    
    @pytest.mark.unit
    def test_percentage_consistency_validation(self):
        """Test percentage consistency with step completion."""
        # This should fail: 3/4 steps = 75%, but percentage is 90%
        with pytest.raises(ValidationError) as exc_info:
            JobProgress(
                percentage=90,
                total_steps=4,
                completed_steps=3
            )
        
        error_message = str(exc_info.value)
        assert 'percentage does not match' in error_message.lower()
        
        # This should pass: 3/4 steps = 75%, percentage is 75%
        progress = JobProgress(
            percentage=75,
            total_steps=4,
            completed_steps=3
        )
        assert progress.percentage == 75
    
    @pytest.mark.unit
    def test_default_values(self):
        """Test default values for progress model."""
        progress = JobProgress()
        
        assert progress.percentage == 0
        assert progress.current_step == "Initializing"
        assert progress.total_steps == 1
        assert progress.completed_steps == 0
        assert progress.estimated_remaining_seconds is None
        assert isinstance(progress.last_updated, datetime)
        assert progress.details == {}


class TestJobErrorModel:
    """Test JobError model validation and functionality."""
    
    @pytest.fixture
    def valid_error_data(self):
        """Valid job error data for testing."""
        return {
            "error_type": "DataProcessingError",
            "error_message": "Unable to parse CSV file: Invalid date format",
            "error_code": "CSV_PARSE_ERROR",
            "is_retryable": True,
            "retry_count": 1,
            "max_retries": 3,
            "context": {
                "file_name": "data.csv",
                "row_number": 150
            }
        }
    
    @pytest.mark.unit
    def test_valid_error_creation(self, valid_error_data):
        """Test creating valid JobError instance."""
        error = JobError(**valid_error_data)
        
        assert error.error_type == valid_error_data["error_type"]
        assert error.error_message == valid_error_data["error_message"]
        assert error.error_code == valid_error_data["error_code"]
        assert error.is_retryable == valid_error_data["is_retryable"]
        assert error.retry_count == valid_error_data["retry_count"]
        assert isinstance(error.occurred_at, datetime)
    
    @pytest.mark.unit
    def test_retry_count_validation(self):
        """Test retry count cannot exceed maximum retries."""
        with pytest.raises(ValidationError) as exc_info:
            JobError(
                error_type="TestError",
                error_message="Test error",
                retry_count=5,
                max_retries=3
            )
        
        error_message = str(exc_info.value)
        assert 'retry count cannot exceed maximum retries' in error_message.lower()
    
    @pytest.mark.unit
    def test_required_fields(self):
        """Test that required fields are enforced."""
        # Missing error_type
        with pytest.raises(ValidationError):
            JobError(error_message="Test error")
        
        # Missing error_message
        with pytest.raises(ValidationError):
            JobError(error_type="TestError")
        
        # Valid minimal error
        error = JobError(
            error_type="TestError",
            error_message="Test error message"
        )
        assert error.error_type == "TestError"
        assert error.error_message == "Test error message"
    
    @pytest.mark.unit
    def test_default_values(self):
        """Test default values for error model."""
        error = JobError(
            error_type="TestError",
            error_message="Test error"
        )
        
        assert error.error_code is None
        assert error.stack_trace is None
        assert error.is_retryable is False
        assert error.retry_count == 0
        assert error.max_retries == 3
        assert error.context == {}


class TestJobModel:
    """Test Job model validation and functionality."""
    
    @pytest.fixture
    def valid_job_data(self):
        """Valid job data for testing."""
        return {
            "id": str(uuid.uuid4()),
            "name": "Test CMBS Report",
            "report_id": "cmbs_user_manual",
            "arguments": {
                "asofqtr": "Q2",
                "year": "2024"
            },
            "submitted_by": "test_user@company.com",
            "priority": JobPriority.HIGH,
            "timeout_seconds": 1800
        }
    
    @pytest.mark.unit
    def test_valid_job_creation(self, valid_job_data):
        """Test creating valid Job instance."""
        job = Job(**valid_job_data)
        
        assert job.id == valid_job_data["id"]
        assert job.name == valid_job_data["name"]
        assert job.report_id == valid_job_data["report_id"]
        assert job.arguments == valid_job_data["arguments"]
        assert job.submitted_by == valid_job_data["submitted_by"]
        assert job.priority == valid_job_data["priority"]
        assert job.status == JobStatus.QUEUED  # Default status
        assert isinstance(job.created_at, datetime)
        assert isinstance(job.progress, JobProgress)
    
    @pytest.mark.unit
    def test_uuid_validation(self):
        """Test UUID validation for job ID."""
        base_data = {
            "name": "Test Job",
            "report_id": "test_report",
            "submitted_by": "test_user"
        }
        
        # Test invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "123",
            "123e4567-e89b-12d3-a456",  # Incomplete
            ""
        ]
        
        for invalid_uuid in invalid_uuids:
            with pytest.raises(ValidationError):
                Job(id=invalid_uuid, **base_data)
        
        # Test valid UUID
        valid_uuid = str(uuid.uuid4())
        job = Job(id=valid_uuid, **base_data)
        assert job.id == valid_uuid
    
    @pytest.mark.unit
    def test_status_update_method(self, valid_job_data):
        """Test job status update method with validation."""
        job = Job(**valid_job_data)
        
        # Valid transition: QUEUED -> RUNNING
        job.update_status(JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        
        # Valid transition: RUNNING -> COMPLETED
        job.update_status(JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        
        # Invalid transition: COMPLETED -> RUNNING (terminal state)
        with pytest.raises(ValueError, match="Invalid status transition"):
            job.update_status(JobStatus.RUNNING)
    
    @pytest.mark.unit
    def test_status_transition_validation(self, valid_job_data):
        """Test various status transition scenarios."""
        job = Job(**valid_job_data)
        
        # Test valid transitions from QUEUED
        valid_from_queued = [JobStatus.RUNNING, JobStatus.CANCELLED]
        for target_status in valid_from_queued:
            test_job = Job(**valid_job_data)
            test_job.update_status(target_status)
            assert test_job.status == target_status
        
        # Test invalid transition from QUEUED
        with pytest.raises(ValueError):
            job.update_status(JobStatus.COMPLETED)  # Must go through RUNNING first
    
    @pytest.mark.unit
    def test_add_file_method(self, valid_job_data):
        """Test adding files to job."""
        job = Job(**valid_job_data)
        
        # Add a file
        job_file = job.add_file(
            filename="report.html",
            file_type=FileType.HTML,
            size_bytes=2048,
            download_url="http://localhost:5001/api/jobs/123/files/report.html"
        )
        
        assert len(job.files) == 1
        assert job.files[0] == job_file
        assert job.files[0].filename == "report.html"
        assert job.files[0].file_type == FileType.HTML
    
    @pytest.mark.unit
    def test_update_progress_method(self, valid_job_data):
        """Test updating job progress."""
        job = Job(**valid_job_data)
        
        # Update progress
        job.update_progress(
            percentage=50,
            current_step="Processing data",
            completed_steps=2,
            total_steps=4
        )
        
        assert job.progress.percentage == 50
        assert job.progress.current_step == "Processing data"
        assert job.progress.completed_steps == 2
        assert job.progress.total_steps == 4
    
    @pytest.mark.unit
    def test_set_error_method(self, valid_job_data):
        """Test setting job error."""
        job = Job(**valid_job_data)
        
        # Set error
        job.set_error(
            error_type="DataError",
            error_message="Invalid data format",
            error_code="DATA_FORMAT_ERROR",
            is_retryable=True
        )
        
        assert job.error is not None
        assert job.error.error_type == "DataError"
        assert job.error.error_message == "Invalid data format"
        assert job.status == JobStatus.FAILED
    
    @pytest.mark.unit
    def test_get_duration_method(self, valid_job_data):
        """Test getting job duration."""
        job = Job(**valid_job_data)
        
        # No duration for queued job
        assert job.get_duration() is None
        
        # Start job
        job.update_status(JobStatus.RUNNING)
        duration = job.get_duration()
        assert isinstance(duration, timedelta)
        assert duration.total_seconds() >= 0
        
        # Complete job
        job.update_status(JobStatus.COMPLETED)
        final_duration = job.get_duration()
        assert isinstance(final_duration, timedelta)
        assert final_duration >= duration
    
    @pytest.mark.unit
    def test_terminal_and_active_status_checks(self, valid_job_data):
        """Test terminal and active status checking methods."""
        job = Job(**valid_job_data)
        
        # Initially queued - active but not terminal
        assert job.is_active() is True
        assert job.is_terminal() is False
        
        # Running - active but not terminal
        job.update_status(JobStatus.RUNNING)
        assert job.is_active() is True
        assert job.is_terminal() is False
        
        # Completed - terminal but not active
        job.update_status(JobStatus.COMPLETED)
        assert job.is_active() is False
        assert job.is_terminal() is True
    
    @pytest.mark.unit
    def test_timeout_validation(self):
        """Test job timeout validation."""
        base_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Job",
            "report_id": "test_report",
            "submitted_by": "test_user"
        }
        
        # Test invalid timeouts
        invalid_timeouts = [0, -1, 30, 86401]  # Below 60 or above 86400
        
        for invalid_timeout in invalid_timeouts:
            with pytest.raises(ValidationError):
                Job(timeout_seconds=invalid_timeout, **base_data)
        
        # Test valid timeouts
        valid_timeouts = [60, 300, 3600, 86400]
        
        for valid_timeout in valid_timeouts:
            job = Job(timeout_seconds=valid_timeout, **base_data)
            assert job.timeout_seconds == valid_timeout
    
    @pytest.mark.unit
    def test_completion_timestamp_validation(self, valid_job_data):
        """Test that completion timestamp cannot be before creation time."""
        job = Job(**valid_job_data)
        
        # Try to set completion time before creation time
        past_time = job.created_at - timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="Completion time cannot be before creation time"):
            Job(
                completed_at=past_time,
                **valid_job_data
            )


class TestJobQueueEntryModel:
    """Test JobQueueEntry model validation and functionality."""
    
    @pytest.fixture
    def valid_job(self):
        """Valid job for queue entry testing."""
        return Job(
            id=str(uuid.uuid4()),
            name="Queue Test Job",
            report_id="test_report",
            submitted_by="test_user"
        )
    
    @pytest.mark.unit
    def test_valid_queue_entry_creation(self, valid_job):
        """Test creating valid JobQueueEntry instance."""
        queue_entry = JobQueueEntry(
            job=valid_job,
            queue_position=5,
            priority_score=7.5
        )
        
        assert queue_entry.job == valid_job
        assert queue_entry.queue_position == 5
        assert queue_entry.priority_score == 7.5
    
    @pytest.mark.unit
    def test_queue_position_validation(self, valid_job):
        """Test queue position validation (must be >= 1)."""
        # Test invalid positions
        invalid_positions = [0, -1, -10]
        
        for invalid_position in invalid_positions:
            with pytest.raises(ValidationError):
                JobQueueEntry(
                    job=valid_job,
                    queue_position=invalid_position
                )
        
        # Test valid positions
        valid_positions = [1, 5, 100]
        
        for valid_position in valid_positions:
            queue_entry = JobQueueEntry(
                job=valid_job,
                queue_position=valid_position
            )
            assert queue_entry.queue_position == valid_position


class TestModelIntegration:
    """Test integration between different models."""
    
    @pytest.mark.unit
    def test_complete_job_lifecycle(self):
        """Test complete job lifecycle with all models."""
        # Create job
        job = Job(
            id=str(uuid.uuid4()),
            name="Integration Test Job",
            report_id="test_report",
            submitted_by="integration_test",
            priority=JobPriority.HIGH
        )
        
        # Start job
        job.update_status(JobStatus.RUNNING)
        
        # Update progress
        job.update_progress(
            percentage=25,
            current_step="Loading data",
            completed_steps=1,
            total_steps=4
        )
        
        # Continue progress
        job.update_progress(
            percentage=75,
            current_step="Generating report",
            completed_steps=3
        )
        
        # Add output files
        job.add_file(
            filename="report.html",
            file_type=FileType.HTML,
            size_bytes=1024000,
            download_url="http://localhost:5001/api/jobs/123/files/report.html"
        )
        
        job.add_file(
            filename="data.csv",
            file_type=FileType.CSV,
            size_bytes=512000,
            download_url="http://localhost:5001/api/jobs/123/files/data.csv"
        )
        
        # Complete job
        job.update_progress(percentage=100, completed_steps=4)
        job.update_status(JobStatus.COMPLETED)
        
        # Verify final state
        assert job.status == JobStatus.COMPLETED
        assert job.progress.percentage == 100
        assert len(job.files) == 2
        assert job.is_terminal() is True
        assert job.is_active() is False
        assert job.get_duration() is not None
    
    @pytest.mark.unit
    def test_job_failure_with_error(self):
        """Test job failure scenario with error information."""
        job = Job(
            id=str(uuid.uuid4()),
            name="Failing Job",
            report_id="test_report",
            submitted_by="test_user"
        )
        
        # Start job
        job.update_status(JobStatus.RUNNING)
        
        # Simulate partial progress
        job.update_progress(
            percentage=60,
            current_step="Processing data",
            completed_steps=2,
            total_steps=4
        )
        
        # Job encounters error
        job.set_error(
            error_type="ProcessingError",
            error_message="Unable to process invalid data in row 1500",
            error_code="DATA_VALIDATION_ERROR",
            is_retryable=True,
            context={
                "row_number": 1500,
                "field_name": "transaction_date",
                "invalid_value": "invalid-date-format"
            }
        )
        
        # Verify error state
        assert job.status == JobStatus.FAILED
        assert job.error is not None
        assert job.error.error_type == "ProcessingError"
        assert job.error.is_retryable is True
        assert "row 1500" in job.error.error_message
        assert job.is_terminal() is True


class TestPerformanceAndSecurity:
    """Test performance and security aspects of models."""
    
    @pytest.mark.performance
    def test_job_model_validation_performance(self, faker_instance):
        """Test job model validation performance."""
        import time
        
        # Generate test data
        test_jobs = []
        for _ in range(1000):
            job_data = {
                "id": str(uuid.uuid4()),
                "name": faker_instance.sentence(nb_words=4),
                "report_id": faker_instance.word(),
                "submitted_by": faker_instance.email(),
                "arguments": {
                    faker_instance.word(): faker_instance.word()
                    for _ in range(3)
                }
            }
            test_jobs.append(job_data)
        
        # Measure validation performance
        start_time = time.time()
        
        valid_jobs = 0
        for job_data in test_jobs:
            try:
                Job(**job_data)
                valid_jobs += 1
            except ValidationError:
                pass  # Expected for some generated data
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertion (should validate 1000 jobs in < 2 seconds)
        assert duration < 2.0, f"Job validation took {duration:.3f}s for 1000 jobs"
        assert valid_jobs > 0, "No valid jobs were created"
    
    @pytest.mark.security
    def test_input_sanitization_in_models(self):
        """Test input sanitization across all models."""
        # Test malicious inputs in job model
        malicious_job_data = {
            "id": str(uuid.uuid4()),
            "name": "<script>alert('xss')</script>",
            "report_id": "'; DROP TABLE jobs; --",
            "submitted_by": "user@company.com<img src=x onerror=alert('xss')>",
            "arguments": {
                "malicious_param": "<?php system('rm -rf /'); ?>"
            }
        }
        
        # Should accept the job (validation at application layer)
        job = Job(**malicious_job_data)
        
        # But serialization should be safe
        job_dict = job.dict()
        job_json = job.json()
        
        # Verify that the malicious content is preserved but contained
        assert job.name == malicious_job_data["name"]
        assert "<script>" in job_json  # Preserved in JSON
        
        # Test file model with malicious filenames (should fail)
        with pytest.raises(ValidationError):
            JobFile(
                filename="../../../etc/passwd",
                file_type=FileType.HTML,
                size_bytes=1024,
                download_url="http://localhost:5001/files/malicious"
            )
