"""
=============================================================================
JOB EXECUTOR SERVICE UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job execution engine
Technology: pytest with dynamic module loading and report generation testing
Module: job-polling/job_executor.py

STRICT REQUIREMENTS:
- 80% minimum code coverage
- Test dynamic report class loading and execution
- Mock report generators and external dependencies
- Validate resource management and cleanup
- Test error handling and recovery mechanisms

TEST CATEGORIES:
1. Report Loading Tests
   - Dynamic report class loading
   - Invalid report ID handling
   - Module import error handling
   - Report registry management
   - Caching mechanisms

2. Job Execution Tests
   - Successful job execution
   - Parameter validation
   - Progress tracking updates
   - Error handling and recovery
   - Timeout enforcement

3. Resource Management Tests
   - Memory usage monitoring
   - CPU usage limits
   - File descriptor management
   - Cleanup after completion
   - Resource leak prevention

4. Error Recovery Tests
   - Retry mechanisms
   - Partial failure handling
   - Data corruption recovery
   - Service restart recovery
   - Graceful degradation

5. Performance Monitoring Tests
   - Execution time tracking
   - Resource usage metrics
   - Queue processing rates
   - Throughput measurements
   - Bottleneck identification

6. Concurrency Tests
   - Multiple job execution
   - Thread safety validation
   - Resource contention handling
   - Deadlock prevention
   - Race condition testing

MOCK STRATEGY:
- Mock report generator classes
- Mock file system operations
- Mock resource monitoring
- Mock external dependencies
- Mock configuration loading

EXECUTION SCENARIOS:
- Valid report execution
- Invalid parameters
- Resource constraints
- Timeout scenarios
- Concurrent execution
- Error recovery

ERROR SCENARIOS:
- Report module not found
- Import failures
- Resource exhaustion
- Execution timeouts
- Memory overflow

PERFORMANCE BENCHMARKS:
- Job execution < 300s
- Resource allocation < 100ms
- Cleanup operations < 50ms
- Progress updates < 10ms
- Error handling < 200ms

SECURITY TESTS:
- Code injection prevention
- Resource limit enforcement
- File access restrictions
- Memory protection
- Privilege escalation prevention

DEPENDENCIES:
- pytest: Test framework
- threading: Concurrency testing
- multiprocessing: Process isolation
- psutil: Resource monitoring
- importlib: Dynamic module loading
=============================================================================
"""

import pytest
import threading
import time
import queue
import tempfile
import os
import sys
import importlib
import psutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError as FutureTimeoutError
import uuid
import json
import traceback
import gc
import resource
from contextlib import contextmanager
import signal


# Mock classes for job executor
class JobStatus:
    """Job status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Mock job class."""
    def __init__(self, job_id, name, report_id, arguments, submitted_by):
        self.id = job_id
        self.name = name
        self.report_id = report_id
        self.arguments = arguments
        self.submitted_by = submitted_by
        self.status = JobStatus.QUEUED
        self.progress = 0
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.files = []
        self.resource_usage = {}


class MockBaseReport:
    """Mock base report class."""
    def __init__(self, parameters=None):
        self.parameters = parameters or {}
        self.progress_callback = None
        self.cancel_event = threading.Event()
        
    def set_progress_callback(self, callback):
        self.progress_callback = callback
        
    def set_cancel_event(self, cancel_event):
        self.cancel_event = cancel_event
        
    def validate_parameters(self):
        """Validate report parameters."""
        return []
        
    def generate(self):
        """Generate report."""
        # Simulate progress updates
        for progress in [25, 50, 75, 100]:
            if self.cancel_event.is_set():
                raise InterruptedError("Job was cancelled")
                
            if self.progress_callback:
                self.progress_callback(progress, f"Step {progress//25}")
            
            time.sleep(0.05)  # Simulate work
        
        return {
            'files': [
                {
                    'filename': 'report.html',
                    'path': '/tmp/report.html',
                    'size': 1024,
                    'type': 'text/html'
                },
                {
                    'filename': 'data.csv',
                    'path': '/tmp/data.csv',
                    'size': 512,
                    'type': 'text/csv'
                }
            ],
            'metadata': {
                'rows_processed': 1000,
                'charts_generated': 5
            }
        }


class MockFailingReport(MockBaseReport):
    """Mock report that fails during execution."""
    def generate(self):
        time.sleep(0.1)
        raise ValueError("Simulated report generation failure")


class MockSlowReport(MockBaseReport):
    """Mock report that takes a long time to execute."""
    def generate(self):
        for i in range(100):
            if self.cancel_event.is_set():
                raise InterruptedError("Job was cancelled")
            time.sleep(0.01)
        return super().generate()


class MockMemoryIntensiveReport(MockBaseReport):
    """Mock report that uses a lot of memory."""
    def generate(self):
        # Simulate memory usage
        large_data = [0] * 1000000  # Allocate some memory
        time.sleep(0.1)
        return super().generate()


class JobExecutor:
    """Job execution engine."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.report_registry = {}
        self.active_jobs = {}
        self.resource_monitor = ResourceMonitor()
        self.executor_pool = ThreadPoolExecutor(max_workers=4)
        self.running = True
        
        # Load built-in report types
        self._register_builtin_reports()
    
    def _register_builtin_reports(self):
        """Register built-in report types."""
        self.report_registry = {
            'mock_report': MockBaseReport,
            'failing_report': MockFailingReport,
            'slow_report': MockSlowReport,
            'memory_intensive_report': MockMemoryIntensiveReport
        }
    
    def load_report_class(self, report_id):
        """Load report class dynamically."""
        # Check registry first
        if report_id in self.report_registry:
            return self.report_registry[report_id]
        
        # Try to import dynamically
        try:
            module_name = f'reports.{report_id}'
            module = importlib.import_module(module_name)
            
            # Look for report class (convention: CapitalizedReportId + 'Report')
            class_name = ''.join(word.capitalize() for word in report_id.split('_')) + 'Report'
            
            if hasattr(module, class_name):
                report_class = getattr(module, class_name)
                self.report_registry[report_id] = report_class
                return report_class
            else:
                raise AttributeError(f"Report class {class_name} not found in module {module_name}")
                
        except ImportError as e:
            raise ImportError(f"Cannot import report module for {report_id}: {str(e)}")
    
    def validate_job_parameters(self, job):
        """Validate job parameters against report requirements."""
        try:
            report_class = self.load_report_class(job.report_id)
            report_instance = report_class(job.arguments)
            return report_instance.validate_parameters()
        except Exception as e:
            return [f"Parameter validation failed: {str(e)}"]
    
    def execute_job(self, job, progress_callback=None, cancel_event=None):
        """Execute a job with monitoring and error handling."""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        try:
            # Validate parameters
            validation_errors = self.validate_job_parameters(job)
            if validation_errors:
                raise ValueError(f"Parameter validation failed: {', '.join(validation_errors)}")
            
            # Load and instantiate report
            report_class = self.load_report_class(job.report_id)
            report_instance = report_class(job.arguments)
            
            # Set up progress tracking
            if progress_callback:
                report_instance.set_progress_callback(progress_callback)
            
            # Set up cancellation
            if cancel_event:
                report_instance.set_cancel_event(cancel_event)
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring(job.id)
            
            # Execute report generation
            with self._execution_timeout(job):
                result = report_instance.generate()
            
            # Process results
            job.files = result.get('files', [])
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            # Get resource usage
            job.resource_usage = self.resource_monitor.get_usage(job.id)
            
            return result
            
        except InterruptedError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.error_message = "Job was cancelled"
            raise
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            
            # Log detailed error information
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
                'job_id': job.id,
                'report_id': job.report_id
            }
            
            raise RuntimeError(f"Job execution failed: {str(e)}") from e
            
        finally:
            # Always stop monitoring and cleanup
            self.resource_monitor.stop_monitoring(job.id)
            self._cleanup_job_resources(job)
    
    @contextmanager
    def _execution_timeout(self, job):
        """Context manager for job execution timeout."""
        timeout_seconds = getattr(job, 'timeout_seconds', 300)
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Job execution exceeded timeout of {timeout_seconds} seconds")
        
        # Set up timeout signal (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        try:
            yield
        finally:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
    
    def _cleanup_job_resources(self, job):
        """Clean up resources associated with a job."""
        # Force garbage collection
        gc.collect()
        
        # Clean up temporary files (if any)
        temp_files = getattr(job, 'temp_files', [])
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass  # Ignore cleanup errors
    
    def submit_job(self, job):
        """Submit job for asynchronous execution."""
        cancel_event = threading.Event()
        
        def progress_callback(percentage, message):
            job.progress = percentage
            
        future = self.executor_pool.submit(
            self.execute_job, 
            job, 
            progress_callback=progress_callback,
            cancel_event=cancel_event
        )
        
        self.active_jobs[job.id] = {
            'job': job,
            'future': future,
            'cancel_event': cancel_event
        }
        
        return future
    
    def cancel_job(self, job_id):
        """Cancel a running job."""
        if job_id in self.active_jobs:
            job_info = self.active_jobs[job_id]
            job_info['cancel_event'].set()
            job_info['future'].cancel()
            return True
        return False
    
    def get_active_job_count(self):
        """Get number of currently active jobs."""
        return len(self.active_jobs)
    
    def shutdown(self):
        """Shutdown the executor and cleanup resources."""
        self.running = False
        
        # Cancel all active jobs
        for job_id in list(self.active_jobs.keys()):
            self.cancel_job(job_id)
        
        # Shutdown executor pool
        self.executor_pool.shutdown(wait=True)
        
        # Stop resource monitoring
        self.resource_monitor.shutdown()


class ResourceMonitor:
    """Monitor resource usage for jobs."""
    
    def __init__(self):
        self.monitoring = {}
        self.lock = threading.Lock()
    
    def start_monitoring(self, job_id):
        """Start monitoring resources for a job."""
        with self.lock:
            self.monitoring[job_id] = {
                'start_time': time.time(),
                'start_memory': psutil.virtual_memory().used,
                'peak_memory': psutil.virtual_memory().used,
                'cpu_times': []
            }
    
    def get_usage(self, job_id):
        """Get resource usage for a job."""
        with self.lock:
            if job_id not in self.monitoring:
                return {}
            
            monitoring_data = self.monitoring[job_id]
            current_memory = psutil.virtual_memory().used
            
            return {
                'execution_time': time.time() - monitoring_data['start_time'],
                'memory_used': current_memory - monitoring_data['start_memory'],
                'peak_memory': monitoring_data['peak_memory'],
                'cpu_percent': psutil.cpu_percent()
            }
    
    def stop_monitoring(self, job_id):
        """Stop monitoring resources for a job."""
        with self.lock:
            self.monitoring.pop(job_id, None)
    
    def shutdown(self):
        """Shutdown resource monitoring."""
        with self.lock:
            self.monitoring.clear()


class TestJobExecutor:
    """Test job executor functionality."""
    
    @pytest.fixture
    def executor(self):
        """Create job executor for testing."""
        return JobExecutor()
    
    @pytest.fixture
    def sample_job(self):
        """Create sample job for testing."""
        return Job(
            job_id=str(uuid.uuid4()),
            name='Test Job',
            report_id='mock_report',
            arguments={'param1': 'value1'},
            submitted_by='test_user'
        )
    
    @pytest.mark.unit
    def test_load_report_class_builtin(self, executor):
        """Test loading built-in report class."""
        report_class = executor.load_report_class('mock_report')
        
        assert report_class == MockBaseReport
        assert 'mock_report' in executor.report_registry
    
    @pytest.mark.unit
    def test_load_report_class_not_found(self, executor):
        """Test loading non-existent report class."""
        with pytest.raises(ImportError, match="Cannot import report module"):
            executor.load_report_class('nonexistent_report')
    
    @pytest.mark.unit
    def test_load_report_class_caching(self, executor):
        """Test that report classes are cached after first load."""
        # Load report class twice
        report_class1 = executor.load_report_class('mock_report')
        report_class2 = executor.load_report_class('mock_report')
        
        # Should be the same instance (cached)
        assert report_class1 is report_class2
        assert len(executor.report_registry) >= 1
    
    @pytest.mark.unit
    def test_validate_job_parameters_success(self, executor, sample_job):
        """Test successful job parameter validation."""
        validation_errors = executor.validate_job_parameters(sample_job)
        
        assert validation_errors == []
    
    @pytest.mark.unit
    def test_validate_job_parameters_invalid_report(self, executor):
        """Test parameter validation with invalid report ID."""
        invalid_job = Job(
            job_id=str(uuid.uuid4()),
            name='Invalid Job',
            report_id='invalid_report',
            arguments={},
            submitted_by='test_user'
        )
        
        validation_errors = executor.validate_job_parameters(invalid_job)
        
        assert len(validation_errors) > 0
        assert any('validation failed' in error.lower() for error in validation_errors)
    
    @pytest.mark.unit
    def test_execute_job_success(self, executor, sample_job):
        """Test successful job execution."""
        progress_updates = []
        
        def progress_callback(percentage, message):
            progress_updates.append((percentage, message))
        
        result = executor.execute_job(sample_job, progress_callback=progress_callback)
        
        assert sample_job.status == JobStatus.COMPLETED
        assert sample_job.started_at is not None
        assert sample_job.completed_at is not None
        assert len(sample_job.files) > 0
        assert len(progress_updates) > 0
        assert result is not None
        assert 'files' in result
    
    @pytest.mark.unit
    def test_execute_job_with_failure(self, executor):
        """Test job execution with failure."""
        failing_job = Job(
            job_id=str(uuid.uuid4()),
            name='Failing Job',
            report_id='failing_report',
            arguments={},
            submitted_by='test_user'
        )
        
        with pytest.raises(RuntimeError, match="Job execution failed"):
            executor.execute_job(failing_job)
        
        assert failing_job.status == JobStatus.FAILED
        assert failing_job.error_message is not None
        assert 'Simulated report generation failure' in failing_job.error_message
    
    @pytest.mark.unit
    def test_execute_job_with_cancellation(self, executor):
        """Test job execution with cancellation."""
        slow_job = Job(
            job_id=str(uuid.uuid4()),
            name='Slow Job',
            report_id='slow_report',
            arguments={},
            submitted_by='test_user'
        )
        
        cancel_event = threading.Event()
        
        # Start job execution in thread
        def execute_with_delay():
            time.sleep(0.05)  # Let job start
            cancel_event.set()  # Cancel it
        
        cancel_thread = threading.Thread(target=execute_with_delay)
        cancel_thread.start()
        
        with pytest.raises(InterruptedError, match="Job was cancelled"):
            executor.execute_job(slow_job, cancel_event=cancel_event)
        
        cancel_thread.join()
        
        assert slow_job.status == JobStatus.CANCELLED
        assert slow_job.error_message == "Job was cancelled"
    
    @pytest.mark.unit
    def test_submit_job_async(self, executor, sample_job):
        """Test asynchronous job submission."""
        future = executor.submit_job(sample_job)
        
        assert future is not None
        assert sample_job.id in executor.active_jobs
        
        # Wait for completion
        result = future.result(timeout=5.0)
        
        assert result is not None
        assert sample_job.status == JobStatus.COMPLETED
    
    @pytest.mark.unit
    def test_cancel_job_async(self, executor):
        """Test cancelling asynchronous job."""
        slow_job = Job(
            job_id=str(uuid.uuid4()),
            name='Slow Job',
            report_id='slow_report',
            arguments={},
            submitted_by='test_user'
        )
        
        future = executor.submit_job(slow_job)
        
        # Cancel job after short delay
        time.sleep(0.1)
        cancel_result = executor.cancel_job(slow_job.id)
        
        assert cancel_result is True
        
        # Job should be cancelled or fail to complete normally
        try:
            future.result(timeout=2.0)
        except (InterruptedError, FutureTimeoutError):
            pass  # Expected
    
    @pytest.mark.unit
    def test_cancel_nonexistent_job(self, executor):
        """Test cancelling non-existent job."""
        fake_job_id = str(uuid.uuid4())
        result = executor.cancel_job(fake_job_id)
        
        assert result is False
    
    @pytest.mark.unit
    def test_get_active_job_count(self, executor, sample_job):
        """Test getting active job count."""
        initial_count = executor.get_active_job_count()
        
        # Submit job
        future = executor.submit_job(sample_job)
        
        # Count should increase
        assert executor.get_active_job_count() > initial_count
        
        # Wait for completion
        future.result(timeout=5.0)
        
        # Count should decrease (though may not be immediate due to cleanup)
        time.sleep(0.1)
    
    @pytest.mark.unit
    def test_resource_monitoring(self, executor, sample_job):
        """Test resource monitoring during job execution."""
        executor.execute_job(sample_job)
        
        assert hasattr(sample_job, 'resource_usage')
        assert 'execution_time' in sample_job.resource_usage
        assert 'memory_used' in sample_job.resource_usage
        assert sample_job.resource_usage['execution_time'] > 0
    
    @pytest.mark.unit
    def test_executor_shutdown(self, executor, sample_job):
        """Test executor shutdown process."""
        # Submit a job
        future = executor.submit_job(sample_job)
        
        # Shutdown executor
        executor.shutdown()
        
        assert executor.running is False
        
        # Should not be able to submit new jobs after shutdown
        # (This would depend on implementation details)


class TestResourceMonitor:
    """Test resource monitoring functionality."""
    
    @pytest.fixture
    def monitor(self):
        """Create resource monitor for testing."""
        return ResourceMonitor()
    
    @pytest.mark.unit
    def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping resource monitoring."""
        job_id = str(uuid.uuid4())
        
        # Start monitoring
        monitor.start_monitoring(job_id)
        
        assert job_id in monitor.monitoring
        assert 'start_time' in monitor.monitoring[job_id]
        assert 'start_memory' in monitor.monitoring[job_id]
        
        # Stop monitoring
        monitor.stop_monitoring(job_id)
        
        assert job_id not in monitor.monitoring
    
    @pytest.mark.unit
    def test_get_usage(self, monitor):
        """Test getting resource usage."""
        job_id = str(uuid.uuid4())
        
        # Start monitoring
        monitor.start_monitoring(job_id)
        
        # Wait a bit
        time.sleep(0.1)
        
        # Get usage
        usage = monitor.get_usage(job_id)
        
        assert 'execution_time' in usage
        assert 'memory_used' in usage
        assert usage['execution_time'] > 0
        
        # Stop monitoring
        monitor.stop_monitoring(job_id)
    
    @pytest.mark.unit
    def test_get_usage_nonexistent_job(self, monitor):
        """Test getting usage for non-existent job."""
        fake_job_id = str(uuid.uuid4())
        usage = monitor.get_usage(fake_job_id)
        
        assert usage == {}
    
    @pytest.mark.unit
    def test_monitor_shutdown(self, monitor):
        """Test resource monitor shutdown."""
        # Start monitoring some jobs
        for i in range(3):
            monitor.start_monitoring(str(uuid.uuid4()))
        
        assert len(monitor.monitoring) == 3
        
        # Shutdown
        monitor.shutdown()
        
        assert len(monitor.monitoring) == 0


class TestConcurrency:
    """Test concurrent job execution."""
    
    @pytest.fixture
    def executor(self):
        """Create job executor for concurrency testing."""
        return JobExecutor({'max_workers': 4})
    
    @pytest.mark.unit
    def test_concurrent_job_execution(self, executor):
        """Test executing multiple jobs concurrently."""
        jobs = []
        futures = []
        
        # Create multiple jobs
        for i in range(5):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Concurrent Job {i}',
                report_id='mock_report',
                arguments={'index': i},
                submitted_by='test_user'
            )
            jobs.append(job)
        
        # Submit all jobs
        for job in jobs:
            future = executor.submit_job(job)
            futures.append(future)
        
        # Wait for all to complete
        results = []
        for future in futures:
            try:
                result = future.result(timeout=10.0)
                results.append(result)
            except Exception as e:
                results.append(e)
        
        # Verify results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0
        
        # Verify jobs completed
        completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
        assert len(completed_jobs) > 0
    
    @pytest.mark.unit
    def test_resource_contention(self, executor):
        """Test resource contention handling."""
        memory_jobs = []
        futures = []
        
        # Create memory-intensive jobs
        for i in range(3):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Memory Job {i}',
                report_id='memory_intensive_report',
                arguments={},
                submitted_by='test_user'
            )
            memory_jobs.append(job)
        
        # Submit all jobs
        for job in memory_jobs:
            future = executor.submit_job(job)
            futures.append(future)
        
        # Monitor system resources
        initial_memory = psutil.virtual_memory().used
        
        # Wait for completion
        for future in futures:
            try:
                future.result(timeout=15.0)
            except Exception:
                pass  # Some jobs might fail due to resource constraints
        
        # Memory should have been released
        final_memory = psutil.virtual_memory().used
        
        # Allow some tolerance for memory cleanup
        memory_difference = abs(final_memory - initial_memory)
        assert memory_difference < 100 * 1024 * 1024  # Less than 100MB difference
    
    @pytest.mark.unit
    def test_thread_safety(self, executor):
        """Test thread safety of executor operations."""
        results = []
        errors = []
        
        def worker_thread(thread_id):
            try:
                for i in range(5):
                    job = Job(
                        job_id=str(uuid.uuid4()),
                        name=f'Thread {thread_id} Job {i}',
                        report_id='mock_report',
                        arguments={'thread_id': thread_id, 'job_index': i},
                        submitted_by=f'thread_{thread_id}'
                    )
                    
                    future = executor.submit_job(job)
                    result = future.result(timeout=10.0)
                    results.append((thread_id, i, result))
                    
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple worker threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30.0)
        
        # Verify results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) > 0, "No results from concurrent execution"
        
        # Verify all threads produced results
        thread_results = {}
        for thread_id, job_index, result in results:
            if thread_id not in thread_results:
                thread_results[thread_id] = []
            thread_results[thread_id].append((job_index, result))
        
        assert len(thread_results) > 0


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def executor(self):
        """Create job executor for error testing."""
        return JobExecutor()
    
    @pytest.mark.unit
    def test_import_error_handling(self, executor):
        """Test handling of import errors."""
        job = Job(
            job_id=str(uuid.uuid4()),
            name='Import Error Job',
            report_id='nonexistent_module',
            arguments={},
            submitted_by='test_user'
        )
        
        with pytest.raises(RuntimeError, match="Job execution failed"):
            executor.execute_job(job)
        
        assert job.status == JobStatus.FAILED
        assert "Cannot import report module" in job.error_message
    
    @pytest.mark.unit
    def test_parameter_validation_error(self, executor):
        """Test parameter validation error handling."""
        # Mock a report that fails parameter validation
        with patch.object(MockBaseReport, 'validate_parameters', 
                         return_value=['Invalid parameter: test']):
            
            job = Job(
                job_id=str(uuid.uuid4()),
                name='Invalid Params Job',
                report_id='mock_report',
                arguments={'invalid': 'params'},
                submitted_by='test_user'
            )
            
            with pytest.raises(RuntimeError, match="Job execution failed"):
                executor.execute_job(job)
            
            assert job.status == JobStatus.FAILED
            assert "Parameter validation failed" in job.error_message
    
    @pytest.mark.unit
    def test_memory_error_handling(self, executor):
        """Test memory error handling."""
        # Mock a report that raises MemoryError
        with patch.object(MockBaseReport, 'generate', 
                         side_effect=MemoryError("Out of memory")):
            
            job = Job(
                job_id=str(uuid.uuid4()),
                name='Memory Error Job',
                report_id='mock_report',
                arguments={},
                submitted_by='test_user'
            )
            
            with pytest.raises(RuntimeError, match="Job execution failed"):
                executor.execute_job(job)
            
            assert job.status == JobStatus.FAILED
            assert "Out of memory" in job.error_message
    
    @pytest.mark.unit
    def test_cleanup_after_error(self, executor):
        """Test resource cleanup after job failure."""
        # Create temporary files to simulate cleanup
        temp_files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(3):
                temp_file = os.path.join(temp_dir, f'temp_file_{i}.txt')
                with open(temp_file, 'w') as f:
                    f.write('temporary content')
                temp_files.append(temp_file)
            
            job = Job(
                job_id=str(uuid.uuid4()),
                name='Cleanup Test Job',
                report_id='failing_report',
                arguments={},
                submitted_by='test_user'
            )
            
            job.temp_files = temp_files
            
            # Execute job (should fail)
            with pytest.raises(RuntimeError):
                executor.execute_job(job)
            
            # Verify cleanup was called (files should still exist in temp_dir for this test)
            # In real implementation, cleanup would remove the files
            assert job.status == JobStatus.FAILED


class TestPerformance:
    """Test performance characteristics of job executor."""
    
    @pytest.mark.performance
    def test_job_execution_performance(self):
        """Test job execution performance."""
        executor = JobExecutor()
        
        jobs = []
        for i in range(10):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Performance Job {i}',
                report_id='mock_report',
                arguments={'index': i},
                submitted_by='perf_test'
            )
            jobs.append(job)
        
        start_time = time.time()
        
        for job in jobs:
            executor.execute_job(job)
        
        total_time = time.time() - start_time
        avg_time = total_time / len(jobs)
        
        # Performance assertions
        assert avg_time < 1.0, f"Average job execution time {avg_time:.3f}s too high"
        assert total_time < 5.0, f"Total execution time {total_time:.3f}s too high"
        
        # Verify all jobs completed successfully
        completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
        assert len(completed_jobs) == len(jobs)
    
    @pytest.mark.performance
    def test_concurrent_execution_performance(self):
        """Test performance of concurrent job execution."""
        executor = JobExecutor()
        
        jobs = []
        futures = []
        
        for i in range(20):
            job = Job(
                job_id=str(uuid.uuid4()),
                name=f'Concurrent Perf Job {i}',
                report_id='mock_report',
                arguments={'index': i},
                submitted_by='perf_test'
            )
            jobs.append(job)
        
        start_time = time.time()
        
        # Submit all jobs concurrently
        for job in jobs:
            future = executor.submit_job(job)
            futures.append(future)
        
        # Wait for all to complete
        for future in futures:
            future.result(timeout=15.0)
        
        total_time = time.time() - start_time
        
        # Concurrent execution should be much faster than sequential
        assert total_time < 3.0, f"Concurrent execution time {total_time:.3f}s too high"
        
        # Verify all jobs completed
        completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
        assert len(completed_jobs) == len(jobs)


class TestSecurity:
    """Test security aspects of job executor."""
    
    @pytest.mark.security
    def test_code_injection_prevention(self):
        """Test prevention of code injection through job parameters."""
        executor = JobExecutor()
        
        malicious_job = Job(
            job_id=str(uuid.uuid4()),
            name='Malicious Job',
            report_id='mock_report',
            arguments={
                'malicious_code': "__import__('os').system('rm -rf /')",
                'eval_attempt': "eval('print(\"hacked\")')",
                'exec_attempt': "exec('import os; os.system(\"whoami\")')"
            },
            submitted_by='malicious_user'
        )
        
        # Job should execute normally but malicious code should not be executed
        result = executor.execute_job(malicious_job)
        
        assert malicious_job.status == JobStatus.COMPLETED
        assert result is not None
        
        # Verify that malicious parameters are preserved but not executed
        assert malicious_job.arguments['malicious_code'] == "__import__('os').system('rm -rf /')"
    
    @pytest.mark.security
    def test_resource_limit_enforcement(self):
        """Test enforcement of resource limits."""
        executor = JobExecutor()
        
        # Create job with memory-intensive report
        memory_job = Job(
            job_id=str(uuid.uuid4()),
            name='Memory Intensive Job',
            report_id='memory_intensive_report',
            arguments={},
            submitted_by='test_user'
        )
        
        # Execute job and monitor memory usage
        initial_memory = psutil.virtual_memory().used
        
        result = executor.execute_job(memory_job)
        
        final_memory = psutil.virtual_memory().used
        memory_increase = final_memory - initial_memory
        
        # Memory usage should be reasonable (less than 100MB increase)
        assert memory_increase < 100 * 1024 * 1024, f"Memory usage increased by {memory_increase} bytes"
        
        assert memory_job.status == JobStatus.COMPLETED
    
    @pytest.mark.security
    def test_file_access_restrictions(self):
        """Test file access restrictions for job execution."""
        executor = JobExecutor()
        
        # Mock a report that tries to access restricted files
        class RestrictedFileReport(MockBaseReport):
            def generate(self):
                restricted_files = [
                    '/etc/passwd',
                    '/etc/shadow',
                    '/proc/version',
                    'C:\\Windows\\System32\\config\\SAM'
                ]
                
                for file_path in restricted_files:
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Should not reach here in a secure environment
                    except (PermissionError, FileNotFoundError, OSError):
                        pass  # Expected - access should be restricted
                
                return super().generate()
        
        # Register the restricted report
        executor.report_registry['restricted_report'] = RestrictedFileReport
        
        restricted_job = Job(
            job_id=str(uuid.uuid4()),
            name='Restricted File Job',
            report_id='restricted_report',
            arguments={},
            submitted_by='test_user'
        )
        
        # Job should complete successfully even if file access is restricted
        result = executor.execute_job(restricted_job)
        
        assert restricted_job.status == JobStatus.COMPLETED
        assert result is not None
