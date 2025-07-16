"""
=============================================================================
JOB POLLING SERVICE UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job polling service
Framework: pytest with fixtures and mocking
Coverage: 80% minimum requirement

TEST CATEGORIES:
1. Health Check Tests
2. Job Reception Tests
3. Job Status Tests
4. File Management Tests
5. Job Cancellation Tests
6. Queue Manager Tests
7. File Manager Tests

FIXTURES:
- app: Flask test client
- sample_job_data: Valid job data
- mock_queue_manager: Mock queue manager
- mock_file_manager: Mock file manager

REQUIREMENTS:
- All endpoints must be tested
- Queue operations coverage
- File management coverage
- Error handling scenarios
- Mock external dependencies
=============================================================================
"""

import pytest
import json
import uuid
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from queue_manager import JobQueueManager
from file_manager import FileManager

@pytest.fixture
def app():
    """Create Flask test client"""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def sample_job_data():
    """Sample valid job data"""
    return {
        'id': str(uuid.uuid4()),
        'name': 'Test CMBS Report',
        'jobDefinitionUri': 'cmbs-user-manual',
        'arguments': {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'property_type': 'Office'
        },
        'submitted_by': 'test_user',
        'priority': 5,
        'submitted_at': datetime.now().isoformat(),
        'status': 'submitted'
    }

@pytest.fixture
def mock_queue_manager():
    """Mock queue manager"""
    manager = MagicMock(spec=JobQueueManager)
    manager.is_queue_full.return_value = False
    manager.get_queue_size.return_value = 5
    manager.get_active_jobs_count.return_value = 2
    manager.get_available_workers.return_value = 2
    return manager

@pytest.fixture
def mock_file_manager():
    """Mock file manager"""
    manager = MagicMock(spec=FileManager)
    manager.get_available_space.return_value = 1024 * 1024 * 1024  # 1GB
    manager.get_total_files.return_value = 10
    return manager

class TestHealthCheck:
    """Test health check endpoint"""
    
    @patch('app.queue_manager')
    @patch('app.file_manager')
    def test_health_check_success(self, mock_file_mgr, mock_queue_mgr, app):
        """Test successful health check"""
        mock_queue_mgr.get_queue_size.return_value = 5
        mock_queue_mgr.get_active_jobs_count.return_value = 2
        mock_queue_mgr.get_available_workers.return_value = 2
        mock_file_mgr.get_available_space.return_value = 1024 * 1024 * 1024
        mock_file_mgr.get_total_files.return_value = 10
        
        response = app.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service'] == 'job-polling'
        assert data['status'] == 'healthy'
        assert 'queue_info' in data
        assert 'file_storage' in data
    
    @patch('app.queue_manager')
    @patch('app.file_manager')
    def test_health_check_degraded_queue_full(self, mock_file_mgr, mock_queue_mgr, app):
        """Test health check with queue at capacity"""
        mock_queue_mgr.get_queue_size.return_value = 100  # At max capacity
        mock_queue_mgr.get_active_jobs_count.return_value = 4
        mock_queue_mgr.get_available_workers.return_value = 0
        mock_file_mgr.get_available_space.return_value = 1024 * 1024 * 1024
        mock_file_mgr.get_total_files.return_value = 10
        
        response = app.get('/health')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['status'] == 'degraded'
        assert 'warnings' in data
    
    @patch('app.queue_manager')
    @patch('app.file_manager')
    def test_health_check_degraded_low_disk(self, mock_file_mgr, mock_queue_mgr, app):
        """Test health check with low disk space"""
        mock_queue_mgr.get_queue_size.return_value = 5
        mock_queue_mgr.get_active_jobs_count.return_value = 2
        mock_queue_mgr.get_available_workers.return_value = 2
        mock_file_mgr.get_available_space.return_value = 1024 * 1024 * 50  # 50MB
        mock_file_mgr.get_total_files.return_value = 100
        
        response = app.get('/health')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['status'] == 'degraded'

class TestJobReception:
    """Test job reception endpoint"""
    
    @patch('app.queue_manager')
    def test_receive_job_success(self, mock_queue_mgr, app, sample_job_data):
        """Test successful job reception"""
        mock_queue_mgr.is_queue_full.return_value = False
        mock_queue_mgr.add_job.return_value = True
        mock_queue_mgr.get_job_position.return_value = 1
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_data),
                          content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['id'] == sample_job_data['id']
        assert data['status'] == 'queued'
        assert 'queue_position' in data
        assert 'estimated_duration' in data
    
    def test_receive_job_invalid_content_type(self, app, sample_job_data):
        """Test job reception with invalid content type"""
        response = app.post('/api/jobs',
                          data='not json',
                          content_type='text/plain')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['code'] == 'INVALID_CONTENT_TYPE'
    
    def test_receive_job_empty_payload(self, app):
        """Test job reception with empty payload"""
        response = app.post('/api/jobs',
                          data='',
                          content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['code'] == 'EMPTY_PAYLOAD'
    
    def test_receive_job_missing_fields(self, app):
        """Test job reception with missing required fields"""
        incomplete_job = {'name': 'Test Job'}  # Missing required fields
        
        response = app.post('/api/jobs',
                          data=json.dumps(incomplete_job),
                          content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data['code'] == 'REQUIRED_FIELD_MISSING'
    
    @patch('app.queue_manager')
    def test_receive_job_queue_full(self, mock_queue_mgr, app, sample_job_data):
        """Test job reception when queue is full"""
        mock_queue_mgr.is_queue_full.return_value = True
        mock_queue_mgr.get_queue_size.return_value = 100
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_data),
                          content_type='application/json')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['code'] == 'QUEUE_FULL'
    
    @patch('app.queue_manager')
    def test_receive_job_queue_error(self, mock_queue_mgr, app, sample_job_data):
        """Test job reception with queue error"""
        mock_queue_mgr.is_queue_full.return_value = False
        mock_queue_mgr.add_job.return_value = False
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_data),
                          content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['code'] == 'QUEUE_ERROR'

class TestJobStatus:
    """Test job status endpoint"""
    
    @patch('app.queue_manager')
    def test_get_job_status_success(self, mock_queue_mgr, app):
        """Test successful job status retrieval"""
        job_id = str(uuid.uuid4())
        mock_status = {
            'id': job_id,
            'status': 'running',
            'progress': 50,
            'message': 'Processing...'
        }
        mock_queue_mgr.get_job_status.return_value = mock_status
        
        response = app.get(f'/api/jobs/{job_id}/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == job_id
        assert data['status'] == 'running'
        assert data['progress'] == 50
    
    @patch('app.file_manager')
    @patch('app.queue_manager')
    def test_get_job_status_completed_with_files(self, mock_queue_mgr, mock_file_mgr, app):
        """Test job status for completed job with files"""
        job_id = str(uuid.uuid4())
        mock_status = {
            'id': job_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Completed'
        }
        mock_files = [
            {'filename': 'report.html', 'size': 1024},
            {'filename': 'data.csv', 'size': 512}
        ]
        mock_queue_mgr.get_job_status.return_value = mock_status
        mock_file_mgr.list_job_files.return_value = mock_files
        
        response = app.get(f'/api/jobs/{job_id}/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'completed'
        assert 'files' in data
        assert len(data['files']) == 2
    
    @patch('app.queue_manager')
    def test_get_job_status_not_found(self, mock_queue_mgr, app):
        """Test job status for non-existent job"""
        job_id = str(uuid.uuid4())
        mock_queue_mgr.get_job_status.return_value = None
        
        response = app.get(f'/api/jobs/{job_id}/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['code'] == 'JOB_NOT_FOUND'

class TestFileManagement:
    """Test file management endpoints"""
    
    @patch('app.file_manager')
    @patch('app.queue_manager')
    def test_list_job_files_success(self, mock_queue_mgr, mock_file_mgr, app):
        """Test successful file listing"""
        job_id = str(uuid.uuid4())
        mock_status = {'status': 'completed'}
        mock_files = [
            {'filename': 'report.html', 'size': 1024},
            {'filename': 'data.csv', 'size': 512}
        ]
        mock_queue_mgr.get_job_status.return_value = mock_status
        mock_file_mgr.list_job_files.return_value = mock_files
        
        response = app.get(f'/api/jobs/{job_id}/files')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['job_id'] == job_id
        assert len(data['files']) == 2
        assert data['total_files'] == 2
    
    @patch('app.queue_manager')
    def test_list_job_files_not_found(self, mock_queue_mgr, app):
        """Test file listing for non-existent job"""
        job_id = str(uuid.uuid4())
        mock_queue_mgr.get_job_status.return_value = None
        
        response = app.get(f'/api/jobs/{job_id}/files')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['code'] == 'JOB_NOT_FOUND'
    
    @patch('app.queue_manager')
    def test_list_job_files_not_completed(self, mock_queue_mgr, app):
        """Test file listing for non-completed job"""
        job_id = str(uuid.uuid4())
        mock_status = {'status': 'running'}
        mock_queue_mgr.get_job_status.return_value = mock_status
        
        response = app.get(f'/api/jobs/{job_id}/files')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['code'] == 'JOB_NOT_COMPLETED'
    
    @patch('os.path.exists')
    @patch('app.file_manager')
    @patch('app.queue_manager')
    def test_download_job_file_success(self, mock_queue_mgr, mock_file_mgr, mock_exists, app):
        """Test successful file download"""
        job_id = str(uuid.uuid4())
        filename = 'report.html'
        file_path = f'/tmp/job-{job_id}/{filename}'
        
        mock_queue_mgr.get_job_status.return_value = {'status': 'completed'}
        mock_file_mgr.get_file_path.return_value = file_path
        mock_exists.return_value = True
        
        with patch('flask.send_file') as mock_send:
            mock_send.return_value = 'file_content'
            response = app.get(f'/api/jobs/{job_id}/files/{filename}')
            mock_send.assert_called_once()
    
    @patch('app.file_manager')
    @patch('app.queue_manager')
    def test_download_job_file_not_found(self, mock_queue_mgr, mock_file_mgr, app):
        """Test file download for non-existent file"""
        job_id = str(uuid.uuid4())
        filename = 'nonexistent.html'
        
        mock_queue_mgr.get_job_status.return_value = {'status': 'completed'}
        mock_file_mgr.get_file_path.return_value = None
        
        response = app.get(f'/api/jobs/{job_id}/files/{filename}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['code'] == 'FILE_NOT_FOUND'

class TestJobCancellation:
    """Test job cancellation endpoint"""
    
    @patch('app.file_manager')
    @patch('app.queue_manager')
    def test_cancel_job_success(self, mock_queue_mgr, mock_file_mgr, app):
        """Test successful job cancellation"""
        job_id = str(uuid.uuid4())
        mock_queue_mgr.get_job_status.return_value = {'status': 'running'}
        mock_queue_mgr.cancel_job.return_value = True
        mock_file_mgr.cleanup_job_files.return_value = True
        
        response = app.delete(f'/api/jobs/{job_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == job_id
        assert data['status'] == 'cancelled'
        assert 'message' in data
    
    @patch('app.queue_manager')
    def test_cancel_job_not_found(self, mock_queue_mgr, app):
        """Test cancellation of non-existent job"""
        job_id = str(uuid.uuid4())
        mock_queue_mgr.get_job_status.return_value = None
        
        response = app.delete(f'/api/jobs/{job_id}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['code'] == 'JOB_NOT_FOUND'
    
    @patch('app.queue_manager')
    def test_cancel_job_failure(self, mock_queue_mgr, app):
        """Test job cancellation failure"""
        job_id = str(uuid.uuid4())
        mock_queue_mgr.get_job_status.return_value = {'status': 'running'}
        mock_queue_mgr.cancel_job.return_value = False
        
        response = app.delete(f'/api/jobs/{job_id}')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['code'] == 'CANCEL_FAILED'

class TestQueueManager:
    """Test JobQueueManager functionality"""
    
    def test_queue_manager_initialization(self):
        """Test queue manager initialization"""
        with patch.dict(os.environ, {
            'POLLING_QUEUE_SIZE': '50',
            'POLLING_WORKERS': '2',
            'POLLING_JOB_TIMEOUT': '120'
        }):
            manager = JobQueueManager()
            assert manager.max_queue_size == 50
            assert manager.num_workers == 2
            assert manager.job_timeout == 120
    
    def test_add_job_success(self):
        """Test successful job addition to queue"""
        manager = JobQueueManager()
        job_data = {
            'id': str(uuid.uuid4()),
            'name': 'Test Job',
            'jobDefinitionUri': 'test-report',
            'arguments': {}
        }
        
        result = manager.add_job(job_data)
        assert result is True
        assert manager.get_queue_size() > 0
    
    def test_get_job_status(self):
        """Test job status retrieval"""
        manager = JobQueueManager()
        job_id = str(uuid.uuid4())
        job_data = {
            'id': job_id,
            'name': 'Test Job',
            'jobDefinitionUri': 'test-report',
            'arguments': {}
        }
        
        manager.add_job(job_data)
        status = manager.get_job_status(job_id)
        
        assert status is not None
        assert status['id'] == job_id
        assert status['status'] == 'queued'
    
    def test_cancel_job(self):
        """Test job cancellation"""
        manager = JobQueueManager()
        job_id = str(uuid.uuid4())
        job_data = {
            'id': job_id,
            'name': 'Test Job',
            'jobDefinitionUri': 'test-report',
            'arguments': {}
        }
        
        manager.add_job(job_data)
        result = manager.cancel_job(job_id)
        
        assert result is True
        status = manager.get_job_status(job_id)
        assert status['status'] == 'cancelled'

class TestFileManager:
    """Test FileManager functionality"""
    
    def test_file_manager_initialization(self):
        """Test file manager initialization"""
        with patch.dict(os.environ, {
            'FILE_STORAGE_PATH': '/tmp/test',
            'FILE_RETENTION_DAYS': '3',
            'FILE_MAX_SIZE_MB': '50'
        }):
            with patch('pathlib.Path.mkdir'):
                manager = FileManager()
                assert manager.storage_path == '/tmp/test'
                assert manager.retention_days == 3
                assert manager.max_file_size == 50 * 1024 * 1024
    
    def test_create_job_directory(self):
        """Test job directory creation"""
        manager = FileManager()
        job_id = str(uuid.uuid4())
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            job_dir = manager.create_job_directory(job_id)
            assert f'job-{job_id}' in job_dir
            mock_mkdir.assert_called()
    
    def test_store_file_success(self):
        """Test successful file storage"""
        manager = FileManager()
        job_id = str(uuid.uuid4())
        filename = 'test.html'
        content = b'<html><body>Test</body></html>'
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file:
            file_path = manager.store_file(job_id, filename, content)
            assert filename in file_path
            mock_file.assert_called()
    
    def test_store_file_invalid_type(self):
        """Test file storage with invalid file type"""
        manager = FileManager()
        job_id = str(uuid.uuid4())
        filename = 'test.exe'  # Not allowed type
        content = b'executable content'
        
        with pytest.raises(ValueError, match='File type not allowed'):
            manager.store_file(job_id, filename, content)
    
    def test_store_file_too_large(self):
        """Test file storage with file too large"""
        manager = FileManager()
        job_id = str(uuid.uuid4())
        filename = 'large.html'
        content = b'x' * (manager.max_file_size + 1)  # Exceed size limit
        
        with pytest.raises(ValueError, match='File size exceeds limit'):
            manager.store_file(job_id, filename, content)
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        manager = FileManager()
        
        # Test dangerous filename
        dangerous = '../../../etc/passwd'
        safe = manager._sanitize_filename(dangerous)
        assert '..' not in safe
        assert '/' not in safe
        
        # Test normal filename
        normal = 'report_2024-01-01.html'
        safe = manager._sanitize_filename(normal)
        assert safe == 'report_2024-01-01.html'

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_estimate_job_duration(self):
        """Test job duration estimation"""
        from app import estimate_job_duration
        
        # Test known report types
        assert estimate_job_duration('cmbs-user-manual') == 120
        assert estimate_job_duration('var-daily') == 60
        assert estimate_job_duration('stress-testing') == 180
        
        # Test unknown report type
        assert estimate_job_duration('unknown-report') == 60  # Default
    
    def test_get_mimetype(self):
        """Test MIME type detection"""
        from app import get_mimetype
        
        assert get_mimetype('report.html') == 'text/html'
        assert get_mimetype('data.csv') == 'text/csv'
        assert get_mimetype('document.pdf') == 'application/pdf'
        assert get_mimetype('spreadsheet.xlsx') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert get_mimetype('unknown.xyz') == 'application/octet-stream'

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=app', '--cov=queue_manager', '--cov=file_manager', '--cov-report=term-missing'])