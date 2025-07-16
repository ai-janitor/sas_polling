"""
=============================================================================
DATAFIT JOB POLLING SERVICE
=============================================================================
Purpose: Job execution engine with FIFO queue and file management
Framework: Flask/FastAPI with background task processing
Port: Configured via config.dev.env

STRICT REQUIREMENTS:
- FIFO job queue with maximum 100 active jobs
- Asynchronous job execution with Python report generators
- File storage management with automatic cleanup
- Comprehensive job status tracking
- Thread-safe operations for concurrent access

API ENDPOINTS:
POST /api/jobs
    - Receive job from submission service
    - Add to FIFO queue
    - Return job status
    
GET /api/jobs/{job_id}/status
    - Return current job status
    - Include progress information if available
    
GET /api/jobs/{job_id}/files
    - List available files for completed job
    - Include file metadata (size, type, created)
    
GET /api/jobs/{job_id}/files/{filename}
    - Download specific file
    - Support range requests for large files
    
DELETE /api/jobs/{job_id}
    - Cancel running job
    - Clean up associated files

JOB PROCESSING:
1. Receive job from submission service
2. Add to FIFO queue (max 100 jobs)
3. Execute when worker thread available
4. Load appropriate Python report generator
5. Execute with provided parameters
6. Generate output files (HTML, PDF, CSV, XLS)
7. Update job status to completed
8. Maintain files for download

QUEUE MANAGEMENT:
- Maximum 100 jobs in queue
- FIFO processing order
- Configurable concurrent workers
- Job priority support
- Automatic cleanup of old completed jobs

FILE MANAGEMENT:
- Temporary storage for generated files
- Automatic cleanup after retention period
- File type validation and size limits
- Download logging and access control
- Support for multiple output formats

CONFIGURATION:
All settings from config.dev.env:
- POLLING_PORT: Service port
- POLLING_WORKERS: Number of concurrent workers
- POLLING_QUEUE_SIZE: Maximum queue size (100)
- FILE_RETENTION_DAYS: How long to keep files
- TEMP_STORAGE_PATH: File storage location
=============================================================================
"""

import os
import logging
import importlib.util
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

from queue_manager import JobQueueManager
from file_manager import FileManager

# Load environment configuration
load_dotenv('/home/hung/projects/datafit/config.dev.env')

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
if os.getenv('CORS_ENABLED', 'true').lower() == 'true':
    CORS(app, 
         origins=os.getenv('CORS_ORIGINS', '*').split(','),
         methods=os.getenv('CORS_METHODS', 'GET,POST,DELETE,OPTIONS').split(','),
         allow_headers=os.getenv('CORS_HEADERS', 'Content-Type,Authorization').split(','))

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger(__name__)

# Initialize managers
queue_manager = JobQueueManager()
file_manager = FileManager()

def load_report_generator(report_id: str):
    """Dynamically load report generator for the given report ID"""
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        'service': 'job-polling',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'queue_info': {
            'size': queue_manager.get_queue_size(),
            'active_jobs': queue_manager.get_active_jobs_count(),
            'workers_available': queue_manager.get_available_workers()
        },
        'file_storage': {
            'available_space': file_manager.get_available_space(),
            'total_files': file_manager.get_total_files()
        }
    }
    
    # Check if queue is at capacity
    if queue_manager.get_queue_size() >= int(os.getenv('POLLING_QUEUE_SIZE', '100')):
        health_status['status'] = 'degraded'
        health_status['warnings'] = ['Queue at maximum capacity']
    
    # Check file storage space
    if file_manager.get_available_space() < 1024 * 1024 * 100:  # Less than 100MB
        health_status['status'] = 'degraded'
        health_status['warnings'] = health_status.get('warnings', []) + ['Low disk space']
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/api/jobs', methods=['POST'])
def receive_job():
    """Receive job from submission service and add to queue"""
    try:
        # Validate JSON payload
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        job_data = request.get_json()
        if not job_data:
            return jsonify({
                'error': 'Empty request body',
                'code': 'EMPTY_PAYLOAD'
            }), 400
        
        # Validate required fields
        required_fields = ['id', 'name', 'jobDefinitionUri', 'arguments']
        for field in required_fields:
            if field not in job_data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'code': 'REQUIRED_FIELD_MISSING'
                }), 422
        
        # Check queue capacity
        if queue_manager.is_queue_full():
            return jsonify({
                'error': 'Queue is at maximum capacity',
                'code': 'QUEUE_FULL',
                'queue_size': queue_manager.get_queue_size(),
                'max_size': int(os.getenv('POLLING_QUEUE_SIZE', '100'))
            }), 503
        
        # Add job to queue
        job_id = job_data['id']
        success = queue_manager.add_job(job_data)
        
        if not success:
            return jsonify({
                'error': 'Failed to add job to queue',
                'code': 'QUEUE_ERROR'
            }), 500
        
        # Estimate duration based on report type
        estimated_duration = estimate_job_duration(job_data['jobDefinitionUri'])
        
        logger.info(f"Job {job_id} added to queue")
        return jsonify({
            'id': job_id,
            'status': os.getenv('JOB_STATUS_QUEUED', 'queued'),
            'queue_position': queue_manager.get_job_position(job_id),
            'estimated_duration': estimated_duration,
            'message': 'Job added to processing queue'
        }), 201
        
    except Exception as e:
        logger.error(f"Error receiving job: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """Get current status of a job"""
    try:
        job_status = queue_manager.get_job_status(job_id)
        if not job_status:
            return jsonify({
                'error': 'Job not found',
                'code': 'JOB_NOT_FOUND'
            }), 404
        
        # Add file information if job is completed
        if job_status['status'] == os.getenv('JOB_STATUS_COMPLETED', 'completed'):
            files = file_manager.list_job_files(job_id)
            job_status['files'] = files
        
        return jsonify(job_status), 200
        
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/jobs/<job_id>/files', methods=['GET'])
def list_job_files(job_id: str):
    """List all files for a completed job"""
    try:
        # Check if job exists and is completed
        job_status = queue_manager.get_job_status(job_id)
        if not job_status:
            return jsonify({
                'error': 'Job not found',
                'code': 'JOB_NOT_FOUND'
            }), 404
        
        if job_status['status'] != os.getenv('JOB_STATUS_COMPLETED', 'completed'):
            return jsonify({
                'error': 'Job is not completed',
                'code': 'JOB_NOT_COMPLETED',
                'current_status': job_status['status']
            }), 400
        
        files = file_manager.list_job_files(job_id)
        return jsonify({
            'job_id': job_id,
            'files': files,
            'total_files': len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing files for job {job_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/jobs/<job_id>/files/<filename>', methods=['GET'])
def download_job_file(job_id: str, filename: str):
    """Download a specific file for a job"""
    try:
        # Check if job exists
        job_status = queue_manager.get_job_status(job_id)
        if not job_status:
            return jsonify({
                'error': 'Job not found',
                'code': 'JOB_NOT_FOUND'
            }), 404
        
        # Get file path
        file_path = file_manager.get_file_path(job_id, filename)
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'error': 'File not found',
                'code': 'FILE_NOT_FOUND'
            }), 404
        
        # Log download
        logger.info(f"File download: {job_id}/{filename}")
        
        # Determine MIME type based on file extension
        mimetype = get_mimetype(filename)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {filename} for job {job_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id: str):
    """Cancel a job and clean up associated files"""
    try:
        # Check if job exists
        job_status = queue_manager.get_job_status(job_id)
        if not job_status:
            return jsonify({
                'error': 'Job not found',
                'code': 'JOB_NOT_FOUND'
            }), 404
        
        # Cancel the job
        success = queue_manager.cancel_job(job_id)
        if not success:
            return jsonify({
                'error': 'Failed to cancel job',
                'code': 'CANCEL_FAILED'
            }), 500
        
        # Clean up files
        file_manager.cleanup_job_files(job_id)
        
        logger.info(f"Job {job_id} cancelled and cleaned up")
        return jsonify({
            'id': job_id,
            'status': os.getenv('JOB_STATUS_CANCELLED', 'cancelled'),
            'message': 'Job cancelled successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

def estimate_job_duration(report_id: str) -> int:
    """Estimate job duration in seconds based on report type"""
    # Default durations for different report types
    durations = {
        'cmbs-user-manual': 120,
        'rmbs-performance': 90,
        'var-daily': 60,
        'stress-testing': 180,
        'trading-activity': 45,
        'aml-alerts': 75,
        'focus-manual': 150
    }
    return durations.get(report_id, 60)

def get_mimetype(filename: str) -> str:
    """Get MIME type based on file extension"""
    mimetypes = {
        '.html': 'text/html',
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.json': 'application/json'
    }
    
    ext = os.path.splitext(filename)[1].lower()
    return mimetypes.get(ext, 'application/octet-stream')

@app.errorhandler(404)
def not_found_handler(e):
    """Handle not found errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'code': 'ENDPOINT_NOT_FOUND'
    }), 404

@app.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('POLLING_PORT', '5001'))
    host = os.getenv('POLLING_HOST', '0.0.0.0')
    debug = os.getenv('DEV_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting job polling service on {host}:{port}")
    
    # Start background workers
    queue_manager.start_workers()
    
    # Start file cleanup process
    file_manager.start_cleanup_process()
    
    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # Cleanup on shutdown
        queue_manager.shutdown()
        file_manager.shutdown()