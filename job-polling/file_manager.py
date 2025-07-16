"""
=============================================================================
FILE MANAGER FOR JOB OUTPUTS
=============================================================================
Purpose: File storage and management for generated report outputs
Framework: OS filesystem operations with automatic cleanup

STRICT REQUIREMENTS:
- Secure file storage with access controls
- Automatic cleanup based on retention policies
- File type validation and size limits
- Download tracking and logging
- Thread-safe operations for concurrent access

FILE OPERATIONS:
- Store generated files by job ID
- List files for completed jobs
- Provide secure download paths
- Track file metadata (size, type, created)
- Automatic cleanup after retention period

STORAGE STRUCTURE:
/tmp/datafit/files/
  ├── job-{uuid}/
  │   ├── report.html
  │   ├── report.pdf
  │   ├── data.csv
  │   └── data.xlsx
  └── cleanup/

SECURITY FEATURES:
- File type validation (HTML, PDF, CSV, XLSX only)
- File size limits
- Access control by job ID
- Path traversal prevention
- Secure file naming

CONFIGURATION:
- FILE_STORAGE_PATH: Base storage directory
- FILE_RETENTION_DAYS: How long to keep files
- FILE_MAX_SIZE_MB: Maximum file size
- FILE_ALLOWED_TYPES: Allowed file extensions
=============================================================================
"""

import os
import shutil
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FileManager:
    """File management for job outputs with cleanup and security"""
    
    def __init__(self):
        # Load configuration
        self.storage_path = os.getenv('FILE_STORAGE_PATH', '/tmp/datafit/files')
        self.retention_days = int(os.getenv('FILE_RETENTION_DAYS', '7'))
        self.max_file_size = int(os.getenv('FILE_MAX_SIZE_MB', '100')) * 1024 * 1024
        self.allowed_types = os.getenv('FILE_ALLOWED_TYPES', 'html,pdf,csv,xlsx,json').split(',')
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Cleanup thread
        self.cleanup_thread = None
        self.shutdown_event = threading.Event()
        
        # Ensure storage directory exists
        self._ensure_storage_directory()
        
        logger.info(f"FileManager initialized: storage={self.storage_path}, retention={self.retention_days}d")
    
    def _ensure_storage_directory(self):
        """Create storage directory if it doesn't exist"""
        try:
            Path(self.storage_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise
    
    def start_cleanup_process(self):
        """Start background cleanup process"""
        if self.cleanup_thread is not None:
            logger.warning("Cleanup process already started")
            return
        
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="FileCleanup",
            daemon=True
        )
        self.cleanup_thread.start()
        logger.info("File cleanup process started")
    
    def shutdown(self):
        """Shutdown file manager and cleanup process"""
        logger.info("Shutting down file manager")
        
        self.shutdown_event.set()
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        logger.info("File manager shutdown complete")
    
    def get_job_directory(self, job_id: str) -> str:
        """Get directory path for a job"""
        # Sanitize job ID to prevent path traversal
        safe_job_id = self._sanitize_filename(job_id)
        return os.path.join(self.storage_path, f"job-{safe_job_id}")
    
    def create_job_directory(self, job_id: str) -> str:
        """Create directory for job outputs"""
        job_dir = self.get_job_directory(job_id)
        
        try:
            with self.lock:
                Path(job_dir).mkdir(parents=True, exist_ok=True)
                logger.info(f"Created job directory: {job_dir}")
                return job_dir
        except Exception as e:
            logger.error(f"Failed to create job directory {job_dir}: {e}")
            raise
    
    def store_file(self, job_id: str, filename: str, content: bytes) -> str:
        """Store file for a job with validation"""
        # Validate filename
        if not self._is_valid_filename(filename):
            raise ValueError(f"Invalid filename: {filename}")
        
        # Validate file size
        if len(content) > self.max_file_size:
            raise ValueError(f"File size exceeds limit: {len(content)} > {self.max_file_size}")
        
        # Validate file type
        if not self._is_allowed_file_type(filename):
            raise ValueError(f"File type not allowed: {filename}")
        
        # Create job directory
        job_dir = self.create_job_directory(job_id)
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        file_path = os.path.join(job_dir, safe_filename)
        
        try:
            with self.lock:
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                logger.info(f"Stored file: {file_path} ({len(content)} bytes)")
                return file_path
        except Exception as e:
            logger.error(f"Failed to store file {file_path}: {e}")
            raise
    
    def store_file_from_path(self, job_id: str, source_path: str, target_filename: str) -> str:
        """Copy file from source path to job directory"""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Validate target filename
        if not self._is_valid_filename(target_filename):
            raise ValueError(f"Invalid target filename: {target_filename}")
        
        # Check file size
        file_size = os.path.getsize(source_path)
        if file_size > self.max_file_size:
            raise ValueError(f"File size exceeds limit: {file_size} > {self.max_file_size}")
        
        # Create job directory
        job_dir = self.create_job_directory(job_id)
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(target_filename)
        target_path = os.path.join(job_dir, safe_filename)
        
        try:
            with self.lock:
                shutil.copy2(source_path, target_path)
                logger.info(f"Copied file: {source_path} -> {target_path}")
                return target_path
        except Exception as e:
            logger.error(f"Failed to copy file {source_path} to {target_path}: {e}")
            raise
    
    def list_job_files(self, job_id: str) -> List[Dict[str, Any]]:
        """List all files for a job with metadata"""
        job_dir = self.get_job_directory(job_id)
        
        if not os.path.exists(job_dir):
            return []
        
        files = []
        
        try:
            with self.lock:
                for filename in os.listdir(job_dir):
                    file_path = os.path.join(job_dir, filename)
                    
                    if os.path.isfile(file_path):
                        stat_info = os.stat(file_path)
                        
                        files.append({
                            'filename': filename,
                            'size': stat_info.st_size,
                            'created_at': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                            'modified_at': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                            'content_type': self._get_content_type(filename),
                            'download_url': f"/api/jobs/{job_id}/files/{filename}"
                        })
            
            # Sort by creation time
            files.sort(key=lambda x: x['created_at'])
            
            logger.info(f"Listed {len(files)} files for job {job_id}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files for job {job_id}: {e}")
            return []
    
    def get_file_path(self, job_id: str, filename: str) -> Optional[str]:
        """Get full path to a specific file"""
        # Sanitize inputs
        safe_job_id = self._sanitize_filename(job_id)
        safe_filename = self._sanitize_filename(filename)
        
        job_dir = self.get_job_directory(safe_job_id)
        file_path = os.path.join(job_dir, safe_filename)
        
        # Verify file exists and is within job directory (security check)
        if not os.path.exists(file_path):
            return None
        
        # Ensure file is within the job directory (prevent path traversal)
        if not os.path.commonpath([job_dir, file_path]) == job_dir:
            logger.warning(f"Path traversal attempt detected: {file_path}")
            return None
        
        return file_path
    
    def cleanup_job_files(self, job_id: str) -> bool:
        """Remove all files for a job"""
        job_dir = self.get_job_directory(job_id)
        
        if not os.path.exists(job_dir):
            return True
        
        try:
            with self.lock:
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up job directory: {job_dir}")
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup job directory {job_dir}: {e}")
            return False
    
    def get_available_space(self) -> int:
        """Get available disk space in bytes"""
        try:
            stat_info = shutil.disk_usage(self.storage_path)
            return stat_info.free
        except Exception as e:
            logger.error(f"Failed to get disk space info: {e}")
            return 0
    
    def get_total_files(self) -> int:
        """Get total number of files across all jobs"""
        total = 0
        
        try:
            with self.lock:
                for job_dir in os.listdir(self.storage_path):
                    job_path = os.path.join(self.storage_path, job_dir)
                    if os.path.isdir(job_path):
                        try:
                            total += len([f for f in os.listdir(job_path) 
                                        if os.path.isfile(os.path.join(job_path, f))])
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Failed to count total files: {e}")
        
        return total
    
    def _cleanup_loop(self):
        """Background cleanup of old files"""
        logger.info("File cleanup loop started")
        
        while not self.shutdown_event.is_set():
            try:
                self._cleanup_old_files()
                
                # Sleep for 1 hour before next cleanup
                self.shutdown_event.wait(timeout=3600)
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                self.shutdown_event.wait(timeout=60)
        
        logger.info("File cleanup loop stopped")
    
    def _cleanup_old_files(self):
        """Remove files older than retention period"""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        try:
            with self.lock:
                for job_dir_name in os.listdir(self.storage_path):
                    job_dir_path = os.path.join(self.storage_path, job_dir_name)
                    
                    if not os.path.isdir(job_dir_path):
                        continue
                    
                    # Check if directory is old enough to remove
                    dir_mtime = datetime.fromtimestamp(os.path.getmtime(job_dir_path))
                    
                    if dir_mtime < cutoff_time:
                        try:
                            shutil.rmtree(job_dir_path)
                            removed_count += 1
                            logger.info(f"Removed old job directory: {job_dir_path}")
                        except Exception as e:
                            logger.error(f"Failed to remove old directory {job_dir_path}: {e}")
            
            if removed_count > 0:
                logger.info(f"Cleanup completed: removed {removed_count} old job directories")
                
        except Exception as e:
            logger.error(f"Cleanup process failed: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        # Remove path separators and other dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        sanitized = ''.join(c for c in filename if c in safe_chars)
        
        # Ensure filename is not empty and not too long
        if not sanitized:
            sanitized = "file"
        
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Validate filename"""
        if not filename or len(filename) > 255:
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for pattern in dangerous_patterns:
            if pattern in filename:
                return False
        
        return True
    
    def _is_allowed_file_type(self, filename: str) -> bool:
        """Check if file type is allowed"""
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return ext in self.allowed_types
    
    def _get_content_type(self, filename: str) -> str:
        """Get MIME type for filename"""
        content_types = {
            '.html': 'text/html',
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.json': 'application/json'
        }
        
        ext = os.path.splitext(filename)[1].lower()
        return content_types.get(ext, 'application/octet-stream')