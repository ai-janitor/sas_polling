"""
=============================================================================
JOB QUEUE MANAGER
=============================================================================
Purpose: Thread-safe FIFO job queue with worker management
Framework: Threading with Queue for concurrent processing

STRICT REQUIREMENTS:
- FIFO queue implementation with maximum capacity
- Thread-safe operations for concurrent access
- Worker thread management with graceful shutdown
- Job status tracking and progress updates
- Priority support and automatic timeout handling

QUEUE FEATURES:
- Maximum 100 jobs capacity (configurable)
- FIFO processing order with priority override
- Concurrent worker threads for job execution
- Job status tracking: queued, running, completed, failed, cancelled
- Automatic timeout and cleanup for stuck jobs

WORKER MANAGEMENT:
- Configurable number of worker threads
- Graceful startup and shutdown
- Job execution with error handling and logging
- Progress tracking and status updates
- Resource cleanup on job completion

JOB LIFECYCLE:
1. Job added to queue with status 'queued'
2. Worker picks up job and sets status to 'running'
3. Worker executes report generator
4. Job completed with status 'completed' or 'failed'
5. Files generated and stored for download
6. Job cleanup after retention period

CONFIGURATION:
- POLLING_QUEUE_SIZE: Maximum queue capacity
- POLLING_WORKERS: Number of worker threads
- POLLING_JOB_TIMEOUT: Maximum job execution time
- JOB_STATUS_*: Status constants from config
=============================================================================
"""

import os
import time
import uuid
import logging
import threading
from queue import Queue, Empty, Full
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, Future
import importlib.util

logger = logging.getLogger(__name__)

class JobQueueManager:
    """Thread-safe job queue manager with worker management"""
    
    def __init__(self):
        # Load configuration
        self.max_queue_size = int(os.getenv('POLLING_QUEUE_SIZE', '100'))
        self.num_workers = int(os.getenv('POLLING_WORKERS', '4'))
        self.job_timeout = int(os.getenv('POLLING_JOB_TIMEOUT', '300'))
        
        # Initialize queue and storage
        self.job_queue = Queue(maxsize=self.max_queue_size)
        self.job_status = {}  # job_id -> status dict
        self.active_jobs = {}  # job_id -> Future object
        
        # Thread safety
        self.status_lock = threading.RLock()
        self.queue_lock = threading.RLock()
        
        # Worker management
        self.executor = None
        self.shutdown_event = threading.Event()
        self.cleanup_thread = None
        
        logger.info(f"JobQueueManager initialized with {self.num_workers} workers, max queue size: {self.max_queue_size}")
    
    def start_workers(self):
        """Start worker threads for job processing"""
        if self.executor is not None:
            logger.warning("Workers already started")
            return
        
        self.executor = ThreadPoolExecutor(
            max_workers=self.num_workers,
            thread_name_prefix="JobWorker"
        )
        
        # Start queue processing threads
        for i in range(self.num_workers):
            self.executor.submit(self._worker_loop, f"worker-{i}")
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="QueueCleanup",
            daemon=True
        )
        self.cleanup_thread.start()
        
        logger.info(f"Started {self.num_workers} worker threads")
    
    def shutdown(self):
        """Gracefully shutdown all workers"""
        logger.info("Shutting down job queue manager")
        
        self.shutdown_event.set()
        
        # Cancel all active jobs
        with self.status_lock:
            for job_id, future in self.active_jobs.items():
                if not future.done():
                    future.cancel()
                    self._update_job_status(job_id, {
                        'status': os.getenv('JOB_STATUS_CANCELLED', 'cancelled'),
                        'message': 'Service shutdown',
                        'completed_at': datetime.now().isoformat()
                    })
        
        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=True, timeout=30)
        
        # Wait for cleanup thread
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        logger.info("Job queue manager shutdown complete")
    
    def add_job(self, job_data: Dict[str, Any]) -> bool:
        """Add job to queue"""
        job_id = job_data['id']
        
        try:
            with self.queue_lock:
                # Check if queue is full
                if self.job_queue.full():
                    logger.warning(f"Queue is full, cannot add job {job_id}")
                    return False
                
                # Add to queue
                self.job_queue.put(job_data, block=False)
            
            # Initialize job status
            with self.status_lock:
                self.job_status[job_id] = {
                    'id': job_id,
                    'status': os.getenv('JOB_STATUS_QUEUED', 'queued'),
                    'progress': 0,
                    'message': 'Job queued for processing',
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'job_data': job_data
                }
            
            logger.info(f"Job {job_id} added to queue")
            return True
            
        except Full:
            logger.error(f"Queue full, cannot add job {job_id}")
            return False
        except Exception as e:
            logger.error(f"Error adding job {job_id} to queue: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        with self.status_lock:
            if job_id not in self.job_status:
                return None
            
            status = self.job_status[job_id].copy()
            # Remove internal job_data from response
            status.pop('job_data', None)
            return status
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        with self.status_lock:
            if job_id not in self.job_status:
                return False
            
            current_status = self.job_status[job_id]['status']
            
            # Can only cancel queued or running jobs
            if current_status in [os.getenv('JOB_STATUS_COMPLETED', 'completed'),
                                os.getenv('JOB_STATUS_FAILED', 'failed'),
                                os.getenv('JOB_STATUS_CANCELLED', 'cancelled')]:
                return False
            
            # Cancel running job
            if job_id in self.active_jobs:
                future = self.active_jobs[job_id]
                if not future.done():
                    future.cancel()
            
            # Update status
            self._update_job_status(job_id, {
                'status': os.getenv('JOB_STATUS_CANCELLED', 'cancelled'),
                'message': 'Job cancelled by user',
                'completed_at': datetime.now().isoformat()
            })
            
            logger.info(f"Job {job_id} cancelled")
            return True
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.job_queue.qsize()
    
    def get_active_jobs_count(self) -> int:
        """Get number of active (running) jobs"""
        with self.status_lock:
            return len(self.active_jobs)
    
    def get_available_workers(self) -> int:
        """Get number of available workers"""
        return self.num_workers - self.get_active_jobs_count()
    
    def is_queue_full(self) -> bool:
        """Check if queue is at maximum capacity"""
        return self.job_queue.full()
    
    def get_job_position(self, job_id: str) -> int:
        """Get position of job in queue (approximate)"""
        # This is an approximation since Queue doesn't provide exact position
        return self.job_queue.qsize()
    
    def _worker_loop(self, worker_name: str):
        """Main worker loop for processing jobs"""
        logger.info(f"Worker {worker_name} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get job from queue with timeout
                job_data = self.job_queue.get(timeout=1.0)
                job_id = job_data['id']
                
                logger.info(f"Worker {worker_name} processing job {job_id}")
                
                # Submit job for execution
                future = self.executor.submit(self._execute_job, job_data, worker_name)
                
                # Track active job
                with self.status_lock:
                    self.active_jobs[job_id] = future
                
                # Wait for completion or timeout
                try:
                    future.result(timeout=self.job_timeout)
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    self._update_job_status(job_id, {
                        'status': os.getenv('JOB_STATUS_FAILED', 'failed'),
                        'message': f'Job execution failed: {str(e)}',
                        'completed_at': datetime.now().isoformat()
                    })
                finally:
                    # Remove from active jobs
                    with self.status_lock:
                        self.active_jobs.pop(job_id, None)
                
                # Mark task as done in queue
                self.job_queue.task_done()
                
            except Empty:
                # No job available, continue loop
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                continue
        
        logger.info(f"Worker {worker_name} stopped")
    
    def _execute_job(self, job_data: Dict[str, Any], worker_name: str):
        """Execute a single job"""
        job_id = job_data['id']
        
        try:
            # Update status to running
            self._update_job_status(job_id, {
                'status': os.getenv('JOB_STATUS_RUNNING', 'running'),
                'progress': 0,
                'message': f'Job started on {worker_name}',
                'started_at': datetime.now().isoformat()
            })
            
            # Load and execute report generator
            report_generator = self._load_report_generator(job_data['jobDefinitionUri'])
            
            # Update progress
            self._update_job_status(job_id, {
                'progress': 25,
                'message': 'Report generator loaded'
            })
            
            # Execute report generation
            output_files = report_generator.generate(job_data['arguments'], job_id)
            
            # Update progress
            self._update_job_status(job_id, {
                'progress': 100,
                'status': os.getenv('JOB_STATUS_COMPLETED', 'completed'),
                'message': 'Report generation completed',
                'completed_at': datetime.now().isoformat(),
                'output_files': output_files
            })
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} execution failed: {e}")
            self._update_job_status(job_id, {
                'status': os.getenv('JOB_STATUS_FAILED', 'failed'),
                'message': f'Execution failed: {str(e)}',
                'completed_at': datetime.now().isoformat()
            })
            raise
    
    def _load_report_generator(self, report_id: str):
        """Load report generator for the given report ID"""
        try:
            # Map report IDs to Python modules
            report_mapping = {
                'cmbs-user-manual': 'cmbs_report',
                'rmbs-performance': 'rmbs_report',
                'var-daily': 'var_report', 
                'stress-testing': 'stress_report',
                'trading-activity': 'trading_report',
                'aml-alerts': 'aml_report',
                'focus-manual': 'focus_report'
            }
            
            module_name = report_mapping.get(report_id)
            if not module_name:
                raise ValueError(f"No report generator found for {report_id}")
            
            # Import the module dynamically
            module_path = f"/home/hung/projects/datafit/reports/{module_name}.py"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                raise ImportError(f"Could not load module {module_name}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the report class (assumes class name follows pattern like CmbsReport)
            class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            report_class = getattr(module, class_name)
            
            return report_class()
            
        except Exception as e:
            logger.error(f"Failed to load report generator for {report_id}: {e}")
            raise
    
    def _update_job_status(self, job_id: str, updates: Dict[str, Any]):
        """Update job status with thread safety"""
        with self.status_lock:
            if job_id in self.job_status:
                self.job_status[job_id].update(updates)
                self.job_status[job_id]['last_updated'] = datetime.now().isoformat()
    
    def _cleanup_loop(self):
        """Background cleanup of old completed jobs"""
        logger.info("Cleanup thread started")
        
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()
                retention_hours = 24  # Keep job status for 24 hours
                
                jobs_to_remove = []
                
                with self.status_lock:
                    for job_id, job_info in self.job_status.items():
                        # Check if job is completed and old enough to remove
                        if job_info['status'] in [
                            os.getenv('JOB_STATUS_COMPLETED', 'completed'),
                            os.getenv('JOB_STATUS_FAILED', 'failed'),
                            os.getenv('JOB_STATUS_CANCELLED', 'cancelled')
                        ]:
                            completed_at = job_info.get('completed_at')
                            if completed_at:
                                completed_time = datetime.fromisoformat(completed_at)
                                if current_time - completed_time > timedelta(hours=retention_hours):
                                    jobs_to_remove.append(job_id)
                
                # Remove old jobs
                for job_id in jobs_to_remove:
                    with self.status_lock:
                        self.job_status.pop(job_id, None)
                    logger.info(f"Cleaned up old job status: {job_id}")
                
                # Sleep for 1 hour before next cleanup
                self.shutdown_event.wait(timeout=3600)
                
            except Exception as e:
                logger.error(f"Cleanup thread error: {e}")
                self.shutdown_event.wait(timeout=60)
        
        logger.info("Cleanup thread stopped")