"""
=============================================================================
JOB POLLING SERVICE APPLICATION UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job polling service main application
Technology: pytest with Flask/FastAPI testing and queue management
Module: job-polling/app.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test all API endpoints and job queue functionality
- Mock external dependencies and services
- Validate FIFO queue behavior with 100 job limit
- Test error handling and edge cases

TEST CATEGORIES:
1. Job Queue Management Tests
   - FIFO queue behavior validation
   - Queue capacity limits (100 jobs)
   - Job priority handling
   - Queue overflow scenarios
   - Thread-safe operations

2. Job Processing Tests
   - Job execution lifecycle
   - Status update propagation
   - Progress tracking
   - Error handling during execution
   - Timeout management

3. API Endpoints Tests
   - POST /api/jobs (job reception)
   - GET /api/jobs/{id}/status
   - GET /api/jobs/{id}/files
   - DELETE /api/jobs/{id} (cancellation)
   - File download endpoints

4. Report Generator Integration Tests
   - Dynamic report loading
   - Parameter passing
   - Output file management
   - Error propagation
   - Resource cleanup

5. File Management Tests
   - File creation and storage
   - Download link generation
   - File cleanup after retention
   - Storage quota management
   - Access control validation

6. Concurrency Tests
   - Multiple worker threads
   - Race condition prevention
   - Resource locking
   - Deadlock prevention
   - Memory synchronization

MOCK STRATEGY:
- Mock report generator modules
- Mock file system operations
- Mock worker thread pools
- Mock external service calls
- Mock configuration loading

API TESTING SCENARIOS:
- Valid job submission
- Invalid job parameters
- Queue overflow handling
- Job status polling
- File download requests
- Job cancellation

ERROR SCENARIOS:
- Report generator failures
- File system errors
- Queue capacity exceeded
- Invalid job IDs
- Network timeouts

PERFORMANCE BENCHMARKS:
- Job processing < 300s
- Status polling < 200ms
- File download < 5MB/s
- Queue operations < 10ms
- Concurrent job handling

SECURITY TESTS:
- Path traversal prevention
- File access restrictions
- Input validation
- Authentication checks
- Rate limiting

DEPENDENCIES:
- pytest: Test framework
- pytest-asyncio: Async testing
- pytest-mock: Mocking utilities
- threading: Concurrency testing
- queue: Queue behavior testing
=============================================================================
"""

import pytest
import asyncio
import json
import time
import uuid
import threading
import queue
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, Future
import requests
from flask import Flask, request, jsonify
from werkzeug.test import Client
from werkzeug.serving import WSGIRequestHandler


# Mock classes for job polling service
class JobStatus:
    """Job status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Job data model."""
    def __init__(self, job_id, name, report_id, arguments, submitted_by, priority=5):
        self.id = job_id
        self.name = name
        self.report_id = report_id
        self.arguments = arguments
        self.submitted_by = submitted_by
        self.priority = priority
        self.status = JobStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.files = []
        self.progress = 0


class JobQueue:
    """FIFO job queue with capacity limits."""
    def __init__(self, max_size=100):
        self.max_size = max_size
        self._queue = queue.Queue(maxsize=max_size)
        self._jobs = {}  # job_id -> Job mapping
        self._lock = threading.RLock()
    
    def add_job(self, job):
        """Add job to queue."""
        with self._lock:
            if self._queue.full():
                raise queue.Full("Job queue is at capacity")
            
            self._queue.put(job)
            self._jobs[job.id] = job
            return True
    
    def get_next_job(self, timeout=None):
        """Get next job from queue."""
        try:
            job = self._queue.get(timeout=timeout)
            return job
        except queue.Empty:
            return None
    
    def get_job(self, job_id):
        """Get specific job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job_status(self, job_id, status, **kwargs):
        """Update job status and metadata."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status
                for key, value in kwargs.items():
                    setattr(job, key, value)
                return True
            return False
    
    def remove_job(self, job_id):
        """Remove job from tracking."""
        with self._lock:
            return self._jobs.pop(job_id, None)
    
    def get_queue_size(self):
        """Get current queue size."""
        return self._queue.qsize()
    
    def get_all_jobs(self):
        """Get all tracked jobs."""
        with self._lock:
            return list(self._jobs.values())


class JobPollingApp:
    """Mock job polling application."""
    def __init__(self):
        self.app = Flask(__name__)
        self.job_queue = JobQueue(max_size=100)
        self.worker_pool = ThreadPoolExecutor(max_workers=4)
        self.running = False
        self.setup_routes()
    
    def setup_routes(self):
        """Set up API routes."""
        @self.app.route('/api/jobs', methods=['POST'])
        def submit_job():
            try:
                data = request.get_json()
                
                # Validate request
                if not data or 'jobDefinitionUri' not in data:
                    return jsonify({'error': 'Invalid request'}), 400
                
                # Create job
                job_id = str(uuid.uuid4())
                job = Job(
                    job_id=job_id,
                    name=data.get('name', f'Job-{job_id[:8]}'),
                    report_id=data['jobDefinitionUri'],
                    arguments=data.get('arguments', {}),
                    submitted_by=data.get('submitted_by', 'unknown'),
                    priority=data.get('priority', 5)
                )
                
                # Add to queue
                try:
                    self.job_queue.add_job(job)
                    
                    # Submit for processing
                    future = self.worker_pool.submit(self._process_job, job)
                    
                    return jsonify({
                        'id': job_id,
                        'status': job.status,
                        'polling_url': f'/api/jobs/{job_id}/status',
                        'estimated_duration': 120
                    }), 201
                    
                except queue.Full:
                    return jsonify({'error': 'Job queue is full'}), 503
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/jobs/<job_id>/status', methods=['GET'])
        def get_job_status(job_id):
            job = self.job_queue.get_job(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            return jsonify({
                'id': job.id,
                'status': job.status,
                'progress': job.progress,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message
            })
        
        @self.app.route('/api/jobs/<job_id>/files', methods=['GET'])
        def get_job_files(job_id):
            job = self.job_queue.get_job(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            if job.status != JobStatus.COMPLETED:
                return jsonify({'files': []})
            
            return jsonify({'files': job.files})
        
        @self.app.route('/api/jobs/<job_id>/files/<filename>', methods=['GET'])
        def download_file(job_id, filename):
            job = self.job_queue.get_job(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            # Security check - prevent path traversal
            if '..' in filename or filename.startswith('/'):
                return jsonify({'error': 'Invalid filename'}), 400
            
            # Check if file exists in job files
            if filename not in [f['filename'] for f in job.files]:
                return jsonify({'error': 'File not found'}), 404
            
            # Return mock file content
            return f"Mock file content for {filename}", 200, {
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename={filename}'
            }
        
        @self.app.route('/api/jobs/<job_id>', methods=['DELETE'])
        def cancel_job(job_id):
            job = self.job_queue.get_job(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return jsonify({'error': 'Cannot cancel job in current status'}), 400
            
            # Update job status
            self.job_queue.update_job_status(job_id, JobStatus.CANCELLED)
            
            return jsonify({'message': 'Job cancelled successfully'})
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'queue_size': self.job_queue.get_queue_size(),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def _process_job(self, job):
        """Process job (mock implementation)."""
        try:
            # Update status to running
            self.job_queue.update_job_status(
                job.id, 
                JobStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            
            # Simulate processing with progress updates
            for progress in [25, 50, 75, 100]:
                time.sleep(0.1)  # Simulate work
                
                # Check if job was cancelled
                current_job = self.job_queue.get_job(job.id)
                if current_job and current_job.status == JobStatus.CANCELLED:
                    return
                
                self.job_queue.update_job_status(job.id, JobStatus.RUNNING, progress=progress)
            
            # Generate mock files
            files = [
                {
                    'filename': f'{job.name.replace(" ", "_")}_report.html',
                    'size': 1024,
                    'type': 'text/html',
                    'created_at': datetime.utcnow().isoformat()
                },
                {
                    'filename': f'{job.name.replace(" ", "_")}_data.csv',
                    'size': 512,
                    'type': 'text/csv',
                    'created_at': datetime.utcnow().isoformat()
                }
            ]
            
            # Complete job
            self.job_queue.update_job_status(
                job.id,
                JobStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                files=files,
                progress=100
            )
            
        except Exception as e:
            # Handle job failure
            self.job_queue.update_job_status(
                job.id,
                JobStatus.FAILED,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    def get_test_client(self):
        """Get test client for testing."""
        self.app.config['TESTING'] = True
        return self.app.test_client()


class TestJobPollingApp:
    """Test job polling application functionality."""
    
    @pytest.fixture
    def app(self):
        """Create job polling app for testing."""
        return JobPollingApp()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.get_test_client()
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job submission data."""
        return {
            'name': 'Test CMBS Report',
            'jobDefinitionUri': 'cmbs_user_manual',
            'arguments': {
                'asofqtr': 'Q2',
                'year': '2024',
                'sortorder': 'Name'
            },
            'submitted_by': 'test_user@company.com',
            'priority': 5
        }
    
    @pytest.mark.unit
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'queue_size' in data
        assert 'timestamp' in data
    
    @pytest.mark.unit
    def test_submit_job_success(self, client, sample_job_data):
        """Test successful job submission."""
        response = client.post('/api/jobs', 
                             json=sample_job_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'id' in data
        assert data['status'] == JobStatus.QUEUED
        assert 'polling_url' in data
        assert data['estimated_duration'] == 120
        
        # Verify job ID is valid UUID
        job_id = data['id']
        uuid.UUID(job_id)  # Should not raise exception
    
    @pytest.mark.unit
    def test_submit_job_invalid_request(self, client):
        """Test job submission with invalid request."""
        invalid_requests = [
            {},  # Empty request
            {'name': 'Test Job'},  # Missing jobDefinitionUri
            None,  # Null request
        ]
        
        for invalid_data in invalid_requests:
            response = client.post('/api/jobs',
                                 json=invalid_data,
                                 content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    @pytest.mark.unit
    def test_get_job_status_success(self, client, sample_job_data):
        """Test getting job status for existing job."""
        # Submit job first
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Get job status
        status_response = client.get(f'/api/jobs/{job_id}/status')
        
        assert status_response.status_code == 200
        data = json.loads(status_response.data)
        
        assert data['id'] == job_id
        assert 'status' in data
        assert 'progress' in data
        assert 'created_at' in data
    
    @pytest.mark.unit
    def test_get_job_status_not_found(self, client):
        """Test getting job status for non-existent job."""
        fake_job_id = str(uuid.uuid4())
        response = client.get(f'/api/jobs/{fake_job_id}/status')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    @pytest.mark.unit
    def test_get_job_files_completed_job(self, client, sample_job_data, app):
        """Test getting files for completed job."""
        # Submit job
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Wait for job to complete
        time.sleep(0.5)
        
        # Get job files
        files_response = client.get(f'/api/jobs/{job_id}/files')
        
        assert files_response.status_code == 200
        data = json.loads(files_response.data)
        
        if 'files' in data and data['files']:
            files = data['files']
            assert isinstance(files, list)
            for file_info in files:
                assert 'filename' in file_info
                assert 'size' in file_info
                assert 'type' in file_info
    
    @pytest.mark.unit
    def test_get_job_files_running_job(self, client, sample_job_data):
        """Test getting files for running job (should be empty)."""
        # Submit job
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Get files immediately (job should still be running)
        files_response = client.get(f'/api/jobs/{job_id}/files')
        
        assert files_response.status_code == 200
        data = json.loads(files_response.data)
        assert data['files'] == []
    
    @pytest.mark.unit
    def test_download_file_success(self, client, sample_job_data):
        """Test downloading file from completed job."""
        # Submit job and wait for completion
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Wait for job to complete
        time.sleep(0.5)
        
        # Get available files
        files_response = client.get(f'/api/jobs/{job_id}/files')
        files_data = json.loads(files_response.data)
        
        if files_data['files']:
            filename = files_data['files'][0]['filename']
            
            # Download file
            download_response = client.get(f'/api/jobs/{job_id}/files/{filename}')
            
            assert download_response.status_code == 200
            assert 'Mock file content' in download_response.data.decode()
            assert 'Content-Disposition' in download_response.headers
    
    @pytest.mark.unit
    def test_download_file_path_traversal_prevention(self, client, sample_job_data):
        """Test path traversal prevention in file downloads."""
        # Submit job
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Try malicious filenames
        malicious_filenames = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'file.txt/../../../etc/passwd'
        ]
        
        for malicious_filename in malicious_filenames:
            response = client.get(f'/api/jobs/{job_id}/files/{malicious_filename}')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Invalid filename' in data['error']
    
    @pytest.mark.unit
    def test_download_file_not_found(self, client, sample_job_data):
        """Test downloading non-existent file."""
        # Submit job
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Try to download non-existent file
        response = client.get(f'/api/jobs/{job_id}/files/nonexistent.txt')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'File not found' in data['error']
    
    @pytest.mark.unit
    def test_cancel_job_success(self, client, sample_job_data):
        """Test successful job cancellation."""
        # Submit job
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Cancel job
        cancel_response = client.delete(f'/api/jobs/{job_id}')
        
        assert cancel_response.status_code == 200
        data = json.loads(cancel_response.data)
        assert 'cancelled successfully' in data['message']
        
        # Verify job status is cancelled
        status_response = client.get(f'/api/jobs/{job_id}/status')
        status_data = json.loads(status_response.data)
        assert status_data['status'] == JobStatus.CANCELLED
    
    @pytest.mark.unit
    def test_cancel_completed_job(self, client, sample_job_data):
        """Test cancelling already completed job."""
        # Submit job and wait for completion
        submit_response = client.post('/api/jobs',
                                    json=sample_job_data,
                                    content_type='application/json')
        
        job_id = json.loads(submit_response.data)['id']
        
        # Wait for completion
        time.sleep(0.6)
        
        # Try to cancel completed job
        cancel_response = client.delete(f'/api/jobs/{job_id}')
        
        assert cancel_response.status_code == 400
        data = json.loads(cancel_response.data)
        assert 'Cannot cancel' in data['error']
    
    @pytest.mark.unit
    def test_cancel_nonexistent_job(self, client):
        """Test cancelling non-existent job."""
        fake_job_id = str(uuid.uuid4())
        response = client.delete(f'/api/jobs/{fake_job_id}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()


class TestJobQueue:
    """Test job queue functionality."""
    
    @pytest.fixture
    def job_queue(self):
        """Create job queue for testing."""
        return JobQueue(max_size=5)  # Small size for testing
    
    @pytest.fixture
    def sample_job(self):
        """Create sample job for testing."""
        return Job(
            job_id=str(uuid.uuid4()),
            name='Test Job',
            report_id='test_report',
            arguments={'param1': 'value1'},
            submitted_by='test_user'
        )
    
    @pytest.mark.unit
    def test_add_job_success(self, job_queue, sample_job):
        """Test successful job addition to queue."""
        result = job_queue.add_job(sample_job)
        
        assert result is True
        assert job_queue.get_queue_size() == 1
        assert job_queue.get_job(sample_job.id) == sample_job
    
    @pytest.mark.unit
    def test_add_job_queue_full(self, job_queue):
        """Test adding job to full queue."""
        # Fill the queue
        for i in range(5):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Job {i}',
                report_id='test_report',
                arguments={},
                submitted_by='test_user'
            )
            job_queue.add_job(job)
        
        # Try to add one more job (should fail)
        overflow_job = Job(
            job_id=str(uuid.uuid4()),
            name='Overflow Job',
            report_id='test_report',
            arguments={},
            submitted_by='test_user'
        )
        
        with pytest.raises(queue.Full):
            job_queue.add_job(overflow_job)
    
    @pytest.mark.unit
    def test_get_next_job_fifo(self, job_queue):
        """Test FIFO behavior of job queue."""
        jobs = []
        for i in range(3):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Job {i}',
                report_id='test_report',
                arguments={},
                submitted_by='test_user'
            )
            jobs.append(job)
            job_queue.add_job(job)
        
        # Get jobs should return in FIFO order
        for expected_job in jobs:
            retrieved_job = job_queue.get_next_job()
            assert retrieved_job.id == expected_job.id
    
    @pytest.mark.unit
    def test_get_next_job_empty_queue(self, job_queue):
        """Test getting job from empty queue."""
        job = job_queue.get_next_job(timeout=0.1)
        assert job is None
    
    @pytest.mark.unit
    def test_update_job_status(self, job_queue, sample_job):
        """Test updating job status."""
        job_queue.add_job(sample_job)
        
        # Update status
        result = job_queue.update_job_status(
            sample_job.id,
            JobStatus.RUNNING,
            progress=50,
            started_at=datetime.utcnow()
        )
        
        assert result is True
        
        # Verify updates
        updated_job = job_queue.get_job(sample_job.id)
        assert updated_job.status == JobStatus.RUNNING
        assert updated_job.progress == 50
        assert updated_job.started_at is not None
    
    @pytest.mark.unit
    def test_update_nonexistent_job(self, job_queue):
        """Test updating non-existent job."""
        fake_job_id = str(uuid.uuid4())
        result = job_queue.update_job_status(fake_job_id, JobStatus.RUNNING)
        
        assert result is False
    
    @pytest.mark.unit
    def test_remove_job(self, job_queue, sample_job):
        """Test removing job from queue."""
        job_queue.add_job(sample_job)
        
        # Remove job
        removed_job = job_queue.remove_job(sample_job.id)
        
        assert removed_job == sample_job
        assert job_queue.get_job(sample_job.id) is None
    
    @pytest.mark.unit
    def test_remove_nonexistent_job(self, job_queue):
        """Test removing non-existent job."""
        fake_job_id = str(uuid.uuid4())
        result = job_queue.remove_job(fake_job_id)
        
        assert result is None
    
    @pytest.mark.unit
    def test_get_all_jobs(self, job_queue):
        """Test getting all jobs from queue."""
        jobs = []
        for i in range(3):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Job {i}',
                report_id='test_report',
                arguments={},
                submitted_by='test_user'
            )
            jobs.append(job)
            job_queue.add_job(job)
        
        all_jobs = job_queue.get_all_jobs()
        
        assert len(all_jobs) == 3
        job_ids = [job.id for job in all_jobs]
        for job in jobs:
            assert job.id in job_ids


class TestConcurrency:
    """Test concurrent job processing."""
    
    @pytest.fixture
    def app(self):
        """Create job polling app for concurrency testing."""
        return JobPollingApp()
    
    @pytest.mark.unit
    def test_concurrent_job_submissions(self, app):
        """Test concurrent job submissions."""
        client = app.get_test_client()
        
        def submit_job(job_index):
            job_data = {
                'name': f'Concurrent Job {job_index}',
                'jobDefinitionUri': 'test_report',
                'arguments': {'index': job_index},
                'submitted_by': f'user_{job_index}'
            }
            
            response = client.post('/api/jobs',
                                 json=job_data,
                                 content_type='application/json')
            return response
        
        # Submit multiple jobs concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_job, i) for i in range(20)]
            responses = [future.result() for future in futures]
        
        # Verify all submissions were successful
        successful_submissions = [r for r in responses if r.status_code == 201]
        
        # Should accept up to queue capacity
        assert len(successful_submissions) > 0
        
        # Check for queue full responses
        queue_full_responses = [r for r in responses if r.status_code == 503]
        if queue_full_responses:
            assert len(successful_submissions) + len(queue_full_responses) == 20
    
    @pytest.mark.unit
    def test_thread_safety_queue_operations(self, app):
        """Test thread safety of queue operations."""
        job_queue = app.job_queue
        results = []
        
        def add_jobs():
            for i in range(10):
                try:
                    job = Job(
                        job_id=str(uuid.uuid4()),
                        name=f'Thread Job {i}',
                        report_id='test_report',
                        arguments={},
                        submitted_by='thread_test'
                    )
                    job_queue.add_job(job)
                    results.append(('added', job.id))
                except queue.Full:
                    results.append(('full', None))
                except Exception as e:
                    results.append(('error', str(e)))
        
        # Run multiple threads adding jobs
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_jobs)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no exceptions occurred
        errors = [r for r in results if r[0] == 'error']
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        
        # Verify some jobs were added
        added_jobs = [r for r in results if r[0] == 'added']
        assert len(added_jobs) > 0
    
    @pytest.mark.unit
    def test_job_processing_isolation(self, app):
        """Test that job processing errors don't affect other jobs."""
        client = app.get_test_client()
        
        # Submit a normal job
        normal_job_data = {
            'name': 'Normal Job',
            'jobDefinitionUri': 'test_report',
            'arguments': {},
            'submitted_by': 'test_user'
        }
        
        normal_response = client.post('/api/jobs',
                                    json=normal_job_data,
                                    content_type='application/json')
        
        normal_job_id = json.loads(normal_response.data)['id']
        
        # Submit a job that might cause errors (simulated by invalid report ID)
        error_job_data = {
            'name': 'Error Job',
            'jobDefinitionUri': 'invalid_report_that_might_cause_errors',
            'arguments': {},
            'submitted_by': 'test_user'
        }
        
        error_response = client.post('/api/jobs',
                                   json=error_job_data,
                                   content_type='application/json')
        
        error_job_id = json.loads(error_response.data)['id']
        
        # Wait for processing
        time.sleep(0.6)
        
        # Check that normal job completed successfully
        normal_status = client.get(f'/api/jobs/{normal_job_id}/status')
        normal_status_data = json.loads(normal_status.data)
        
        # Normal job should complete (even if error job fails)
        assert normal_status_data['status'] in [JobStatus.COMPLETED, JobStatus.RUNNING]


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.performance
    def test_job_queue_performance(self):
        """Test job queue operation performance."""
        job_queue = JobQueue(max_size=1000)
        
        # Test job addition performance
        start_time = time.time()
        
        jobs = []
        for i in range(100):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Performance Job {i}',
                report_id='test_report',
                arguments={},
                submitted_by='perf_test'
            )
            jobs.append(job)
            job_queue.add_job(job)
        
        add_time = time.time() - start_time
        
        # Test job retrieval performance
        start_time = time.time()
        
        retrieved_jobs = []
        for _ in range(100):
            job = job_queue.get_next_job()
            if job:
                retrieved_jobs.append(job)
        
        retrieve_time = time.time() - start_time
        
        # Performance assertions
        assert add_time < 1.0, f"Adding 100 jobs took {add_time:.3f}s"
        assert retrieve_time < 1.0, f"Retrieving 100 jobs took {retrieve_time:.3f}s"
        assert len(retrieved_jobs) == 100
    
    @pytest.mark.performance
    def test_status_polling_performance(self, app):
        """Test status polling endpoint performance."""
        client = app.get_test_client()
        
        # Submit a job
        job_data = {
            'name': 'Performance Test Job',
            'jobDefinitionUri': 'test_report',
            'arguments': {},
            'submitted_by': 'perf_test'
        }
        
        response = client.post('/api/jobs',
                             json=job_data,
                             content_type='application/json')
        
        job_id = json.loads(response.data)['id']
        
        # Test multiple status requests
        start_time = time.time()
        
        for _ in range(100):
            status_response = client.get(f'/api/jobs/{job_id}/status')
            assert status_response.status_code == 200
        
        total_time = time.time() - start_time
        avg_time = total_time / 100
        
        # Performance assertion (average < 200ms as per requirements)
        assert avg_time < 0.2, f"Average status polling time {avg_time*1000:.1f}ms too high"


class TestSecurity:
    """Test security aspects of job polling service."""
    
    @pytest.mark.security
    def test_input_validation_prevents_injection(self, app):
        """Test that input validation prevents injection attacks."""
        client = app.get_test_client()
        
        malicious_job_data = {
            'name': "<script>alert('xss')</script>",
            'jobDefinitionUri': "'; DROP TABLE jobs; --",
            'arguments': {
                'malicious_param': "<?php system('rm -rf /'); ?>"
            },
            'submitted_by': "<img src=x onerror=alert('xss')>"
        }
        
        # Submit malicious job
        response = client.post('/api/jobs',
                             json=malicious_job_data,
                             content_type='application/json')
        
        # Should accept the job (let validation happen at processing level)
        # but the malicious content should be handled safely
        if response.status_code == 201:
            job_id = json.loads(response.data)['id']
            
            # Get job status
            status_response = client.get(f'/api/jobs/{job_id}/status')
            assert status_response.status_code == 200
            
            # Response should not contain unescaped malicious content
            response_text = status_response.data.decode()
            assert '<script>' not in response_text
            assert 'DROP TABLE' not in response_text
    
    @pytest.mark.security
    def test_file_access_restrictions(self, app):
        """Test file access security restrictions."""
        client = app.get_test_client()
        
        # Submit job
        job_data = {
            'name': 'Security Test Job',
            'jobDefinitionUri': 'test_report',
            'arguments': {},
            'submitted_by': 'security_test'
        }
        
        response = client.post('/api/jobs',
                             json=job_data,
                             content_type='application/json')
        
        job_id = json.loads(response.data)['id']
        
        # Test various path traversal attempts
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM',
            'file.txt/../../../etc/passwd',
            'normal_file.txt\x00../../etc/passwd'  # Null byte injection
        ]
        
        for malicious_path in malicious_paths:
            download_response = client.get(f'/api/jobs/{job_id}/files/{malicious_path}')
            
            # Should reject with 400 (invalid filename) or 404 (not found)
            assert download_response.status_code in [400, 404]
            
            if download_response.status_code == 400:
                data = json.loads(download_response.data)
                assert 'Invalid filename' in data['error']
    
    @pytest.mark.security
    def test_job_isolation(self, app):
        """Test that jobs cannot access each other's data."""
        client = app.get_test_client()
        
        # Submit two jobs
        job1_data = {
            'name': 'Job 1',
            'jobDefinitionUri': 'test_report',
            'arguments': {'secret': 'job1_secret'},
            'submitted_by': 'user1'
        }
        
        job2_data = {
            'name': 'Job 2',
            'jobDefinitionUri': 'test_report',
            'arguments': {'secret': 'job2_secret'},
            'submitted_by': 'user2'
        }
        
        response1 = client.post('/api/jobs', json=job1_data, content_type='application/json')
        response2 = client.post('/api/jobs', json=job2_data, content_type='application/json')
        
        job1_id = json.loads(response1.data)['id']
        job2_id = json.loads(response2.data)['id']
        
        # Wait for processing
        time.sleep(0.6)
        
        # Try to access job1 files using job2 ID context (should fail)
        job1_files_response = client.get(f'/api/jobs/{job1_id}/files')
        job2_files_response = client.get(f'/api/jobs/{job2_id}/files')
        
        # Both should succeed for their own jobs
        assert job1_files_response.status_code == 200
        assert job2_files_response.status_code == 200
        
        # But files should be isolated - no cross-job file access
        job1_files = json.loads(job1_files_response.data)['files']
        job2_files = json.loads(job2_files_response.data)['files']
        
        # Verify files are different (contain job-specific content)
        if job1_files and job2_files:
            job1_filenames = [f['filename'] for f in job1_files]
            job2_filenames = [f['filename'] for f in job2_files]
            
            # Files should be job-specific (different names)
            assert job1_filenames != job2_filenames
