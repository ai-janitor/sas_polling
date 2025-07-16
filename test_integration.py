"""
=============================================================================
DATAFIT END-TO-END INTEGRATION TESTS
=============================================================================
Purpose: Test complete workflow from job submission to file generation
Framework: pytest with service simulation
Coverage: Full workflow testing

TEST SCENARIOS:
1. Complete job submission workflow
2. Job status polling and updates
3. File generation and download
4. Error handling across services
5. Service communication validation
6. Queue management testing

REQUIREMENTS:
- Mock report generators for testing
- Simulate real service communication
- Test file creation and cleanup
- Validate API contracts between services
- Test error propagation
=============================================================================
"""

import pytest
import json
import time
import uuid
import requests
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Test configuration
SUBMISSION_BASE_URL = 'http://localhost:5000'
POLLING_BASE_URL = 'http://localhost:5001'

class MockReportGenerator:
    """Mock report generator for testing"""
    
    def __init__(self, report_id='test-report'):
        self.report_id = report_id
    
    def generate(self, arguments, job_id):
        """Generate mock report files"""
        # Create temporary files to simulate report generation
        temp_dir = tempfile.mkdtemp()
        
        files = []
        
        # Generate HTML report
        html_file = os.path.join(temp_dir, 'report.html')
        with open(html_file, 'w') as f:
            f.write(f"""
            <html>
            <head><title>Test Report {job_id}</title></head>
            <body>
                <h1>Test Report</h1>
                <p>Generated for job: {job_id}</p>
                <p>Arguments: {json.dumps(arguments)}</p>
                <p>Generated at: {datetime.now().isoformat()}</p>
            </body>
            </html>
            """)
        files.append(html_file)
        
        # Generate CSV data
        csv_file = os.path.join(temp_dir, 'data.csv')
        with open(csv_file, 'w') as f:
            f.write("id,value,timestamp\n")
            for i in range(10):
                f.write(f"{i},{i*10},{datetime.now().isoformat()}\n")
        files.append(csv_file)
        
        # Simulate processing time
        time.sleep(0.1)
        
        return files

@pytest.fixture
def sample_job_request():
    """Sample job request for testing"""
    return {
        'name': 'Integration Test Job',
        'jobDefinitionUri': 'cmbs-user-manual',
        'arguments': {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'property_type': 'Office',
            'include_charts': True
        },
        'submitted_by': 'integration_test',
        'priority': 5
    }

@pytest.fixture
def mock_services():
    """Setup mock services for testing"""
    # Mock the report generator loading
    mock_generator = MockReportGenerator()
    
    with patch('job_polling.queue_manager.importlib.util.spec_from_file_location') as mock_spec, \
         patch('job_polling.queue_manager.importlib.util.module_from_spec') as mock_module:
        
        # Setup module loading mock
        mock_spec.return_value.loader.exec_module = MagicMock()
        mock_module.return_value = MagicMock()
        
        yield mock_generator

class TestEndToEndWorkflow:
    """Test complete end-to-end workflow"""
    
    def test_submit_job_to_completion(self, sample_job_request, mock_services):
        """Test complete job submission to completion workflow"""
        
        # Step 1: Submit job to submission service
        with patch('job_submission.app.forward_to_polling_service') as mock_forward, \
             patch('job_submission.app.validate_report_exists') as mock_validate, \
             patch('job_submission.app.validate_report_parameters') as mock_validate_params:
            
            # Setup mocks
            mock_validate.return_value = True
            mock_validate_params.return_value = []
            mock_forward.return_value = {'estimated_duration': 120}
            
            # Import and create submission app
            from job_submission.app import app as submission_app
            submission_client = submission_app.test_client()
            
            # Submit job
            response = submission_client.post('/api/jobs',
                                            data=json.dumps(sample_job_request),
                                            content_type='application/json')
            
            assert response.status_code == 201
            job_data = json.loads(response.data)
            job_id = job_data['id']
            
            assert 'id' in job_data
            assert job_data['status'] == 'submitted'
            assert 'polling_url' in job_data
    
    def test_job_status_progression(self):
        """Test job status progression through states"""
        from job_polling.queue_manager import JobQueueManager
        
        manager = JobQueueManager()
        
        # Create test job
        job_id = str(uuid.uuid4())
        job_data = {
            'id': job_id,
            'name': 'Status Test Job',
            'jobDefinitionUri': 'test-report',
            'arguments': {'test': 'value'},
            'submitted_by': 'test_user',
            'priority': 5
        }
        
        # Test initial queued status
        success = manager.add_job(job_data)
        assert success is True
        
        status = manager.get_job_status(job_id)
        assert status['status'] == 'queued'
        assert status['progress'] == 0
        
        # Test status update to running
        manager._update_job_status(job_id, {
            'status': 'running',
            'progress': 25,
            'message': 'Processing started'
        })
        
        status = manager.get_job_status(job_id)
        assert status['status'] == 'running'
        assert status['progress'] == 25
        
        # Test status update to completed
        manager._update_job_status(job_id, {
            'status': 'completed',
            'progress': 100,
            'message': 'Processing completed',
            'output_files': ['report.html', 'data.csv']
        })
        
        status = manager.get_job_status(job_id)
        assert status['status'] == 'completed'
        assert status['progress'] == 100
        assert 'output_files' in status
    
    def test_file_generation_and_storage(self):
        """Test file generation and storage workflow"""
        from job_polling.file_manager import FileManager
        
        manager = FileManager()
        job_id = str(uuid.uuid4())
        
        # Test file storage
        filename = 'test_report.html'
        content = b'<html><body>Test Report Content</body></html>'
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True) as mock_open:
            
            file_path = manager.store_file(job_id, filename, content)
            assert filename in file_path
            assert f'job-{job_id}' in file_path
        
        # Test file listing
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=['test_report.html']), \
             patch('os.path.isfile', return_value=True), \
             patch('os.stat') as mock_stat:
            
            # Mock stat info
            mock_stat.return_value.st_size = len(content)
            mock_stat.return_value.st_ctime = time.time()
            mock_stat.return_value.st_mtime = time.time()
            
            files = manager.list_job_files(job_id)
            assert len(files) == 1
            assert files[0]['filename'] == 'test_report.html'
            assert files[0]['size'] == len(content)
    
    def test_job_cancellation_workflow(self):
        """Test job cancellation workflow"""
        from job_polling.queue_manager import JobQueueManager
        from job_polling.file_manager import FileManager
        
        queue_manager = JobQueueManager()
        file_manager = FileManager()
        
        # Create and queue job
        job_id = str(uuid.uuid4())
        job_data = {
            'id': job_id,
            'name': 'Cancellation Test Job',
            'jobDefinitionUri': 'test-report',
            'arguments': {},
            'submitted_by': 'test_user'
        }
        
        queue_manager.add_job(job_data)
        
        # Verify job is queued
        status = queue_manager.get_job_status(job_id)
        assert status['status'] == 'queued'
        
        # Cancel job
        success = queue_manager.cancel_job(job_id)
        assert success is True
        
        # Verify job is cancelled
        status = queue_manager.get_job_status(job_id)
        assert status['status'] == 'cancelled'
        
        # Test file cleanup
        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree:
            
            file_manager.cleanup_job_files(job_id)
            mock_rmtree.assert_called_once()
    
    def test_error_handling_workflow(self):
        """Test error handling across the workflow"""
        
        # Test invalid job request
        invalid_request = {
            'name': '',  # Invalid name
            'jobDefinitionUri': 'non-existent-report',
            'arguments': {},
            'submitted_by': ''
        }
        
        from job_submission.app import app as submission_app
        client = submission_app.test_client()
        
        response = client.post('/api/jobs',
                              data=json.dumps(invalid_request),
                              content_type='application/json')
        
        assert response.status_code == 422
        error_data = json.loads(response.data)
        assert error_data['code'] == 'VALIDATION_ERROR'
        
        # Test queue full scenario
        from job_polling.queue_manager import JobQueueManager
        
        manager = JobQueueManager()
        
        # Fill queue to capacity
        with patch.object(manager, 'job_queue') as mock_queue:
            mock_queue.full.return_value = True
            
            job_data = {
                'id': str(uuid.uuid4()),
                'name': 'Test Job',
                'jobDefinitionUri': 'test-report',
                'arguments': {}
            }
            
            success = manager.add_job(job_data)
            assert success is False
    
    def test_service_communication(self):
        """Test communication between services"""
        
        # Test submission service to polling service communication
        job_data = {
            'id': str(uuid.uuid4()),
            'name': 'Communication Test',
            'jobDefinitionUri': 'test-report',
            'arguments': {},
            'submitted_by': 'test_user'
        }
        
        # Mock successful communication
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'status': 'received'}
            mock_post.return_value = mock_response
            
            from job_submission.app import forward_to_polling_service
            
            result = forward_to_polling_service(job_data)
            assert result is not None
            assert result['status'] == 'received'
        
        # Test communication failure
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError('Service unavailable')
            
            result = forward_to_polling_service(job_data)
            assert result is None
    
    def test_concurrent_job_processing(self):
        """Test concurrent job processing"""
        from job_polling.queue_manager import JobQueueManager
        
        manager = JobQueueManager()
        
        # Create multiple jobs
        job_ids = []
        for i in range(5):
            job_id = str(uuid.uuid4())
            job_data = {
                'id': job_id,
                'name': f'Concurrent Job {i}',
                'jobDefinitionUri': 'test-report',
                'arguments': {'index': i},
                'submitted_by': 'test_user'
            }
            
            success = manager.add_job(job_data)
            assert success is True
            job_ids.append(job_id)
        
        # Verify all jobs are queued
        for job_id in job_ids:
            status = manager.get_job_status(job_id)
            assert status is not None
            assert status['status'] == 'queued'
        
        # Test queue size
        assert manager.get_queue_size() == 5
    
    def test_file_retention_and_cleanup(self):
        """Test file retention and cleanup policies"""
        from job_polling.file_manager import FileManager
        from datetime import datetime, timedelta
        
        manager = FileManager()
        
        # Mock old files for cleanup
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.isdir', return_value=True), \
             patch('os.path.getmtime') as mock_getmtime, \
             patch('shutil.rmtree') as mock_rmtree:
            
            # Setup old directory
            old_time = (datetime.now() - timedelta(days=8)).timestamp()
            mock_listdir.return_value = ['job-old-123', 'job-recent-456']
            mock_getmtime.side_effect = lambda path: old_time if 'old' in path else time.time()
            
            # Run cleanup
            manager._cleanup_old_files()
            
            # Verify old files were removed
            mock_rmtree.assert_called_once()
    
    def test_api_contract_validation(self):
        """Test API contracts between services"""
        
        # Test job submission API contract
        from job_submission.models import JobRequest, JobResponse
        
        # Valid request
        valid_data = {
            'name': 'API Test Job',
            'jobDefinitionUri': 'test-report',
            'arguments': {'test': 'value'},
            'submitted_by': 'api_test',
            'priority': 5
        }
        
        job_request = JobRequest.from_dict(valid_data)
        assert job_request.name == valid_data['name']
        
        # Valid response
        job_response = JobResponse(
            id=str(uuid.uuid4()),
            status='submitted',
            polling_url='http://localhost:5001/api/jobs/123/status',
            estimated_duration=120
        )
        
        response_dict = job_response.to_dict()
        assert 'id' in response_dict
        assert 'status' in response_dict
        assert 'polling_url' in response_dict
        
        # Test validation errors
        invalid_data = {'name': ''}  # Missing required fields
        
        with pytest.raises(ValueError):
            JobRequest.from_dict(invalid_data)

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])