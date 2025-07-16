"""
=============================================================================
DATAFIT JOB SUBMISSION SERVICE
=============================================================================
Purpose: REST API service for receiving job submission requests
Framework: Flask/FastAPI with async support
Port: Configured via config.dev.env

STRICT REQUIREMENTS:
- Stateless service design (no local storage)
- Request validation with detailed error responses
- Payload forwarding to polling service with correlation IDs
- Comprehensive logging with request tracing
- Health check endpoints for monitoring

API ENDPOINTS:
POST /api/jobs
    - Accepts job submission JSON payload
    - Validates request structure and parameters
    - Forwards to polling service
    - Returns job ID and polling URL
    
GET /health
    - Health check endpoint
    - Returns service status and dependencies
    
GET /api/reports
    - Returns report definitions JSON
    - Cached response with configurable TTL

REQUEST FLOW:
1. Receive job submission request
2. Validate JSON payload structure
3. Validate report ID exists in definitions
4. Validate required parameters for selected report
5. Generate unique job ID (UUID)
6. Forward payload to polling service
7. Return job ID and status polling URL

ERROR HANDLING:
- Input validation errors (400)
- Missing required fields (422)
- Invalid report ID (404)
- Polling service unavailable (503)
- Rate limiting (429)

CONFIGURATION:
All settings loaded from config.dev.env:
- SUBMISSION_PORT: Service port
- SUBMISSION_LOG_LEVEL: Logging level
- POLLING_SERVICE_URL: Target polling service
- RATE_LIMIT_REQUESTS: Max requests per minute
- REQUEST_TIMEOUT: Max request processing time
=============================================================================
"""

import os
import json
import uuid
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from models import JobRequest, JobResponse, ValidationError

# Load environment configuration
load_dotenv('/home/hung/projects/datafit/config.dev.env')

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
if os.getenv('CORS_ENABLED', 'true').lower() == 'true':
    CORS(app, 
         origins=os.getenv('CORS_ORIGINS', '*').split(','),
         methods=os.getenv('CORS_METHODS', 'GET,POST,OPTIONS').split(','),
         allow_headers=os.getenv('CORS_HEADERS', 'Content-Type,Authorization').split(','))

# Configure rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[f"{os.getenv('RATE_LIMIT_REQUESTS', '100')}/minute"]
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger(__name__)

# Global variables for cached data
report_definitions = None
report_definitions_last_loaded = None

def load_report_definitions() -> Dict[str, Any]:
    """Load report definitions from JSON file with caching"""
    global report_definitions, report_definitions_last_loaded
    
    report_file = os.getenv('REPORT_DEFINITIONS_FILE', '/app/data/report-definitions.json')
    cache_ttl = int(os.getenv('CACHE_TTL', '300'))
    
    current_time = datetime.now()
    
    # Check if cache is still valid
    if (report_definitions is not None and 
        report_definitions_last_loaded is not None and
        (current_time - report_definitions_last_loaded).seconds < cache_ttl):
        return report_definitions
    
    try:
        with open(report_file, 'r') as f:
            report_definitions = json.load(f)
            report_definitions_last_loaded = current_time
            logger.info(f"Loaded report definitions from {report_file}")
            return report_definitions
    except FileNotFoundError:
        logger.error(f"Report definitions file not found: {report_file}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in report definitions file: {e}")
        return {}

def validate_report_exists(report_id: str) -> bool:
    """Validate that the report ID exists in report definitions"""
    definitions = load_report_definitions()
    
    # Search through categories and subcategories
    for category in definitions.get('categories', []):
        for subcategory in category.get('subcategories', []):
            for report in subcategory.get('reports', []):
                if report.get('id') == report_id:
                    return True
    return False

def validate_report_parameters(report_id: str, parameters: Dict[str, Any]) -> List[ValidationError]:
    """Validate that required parameters are provided for the report"""
    definitions = load_report_definitions()
    errors = []
    
    # Find the report schema
    report_schema = None
    for category in definitions.get('categories', []):
        for subcategory in category.get('subcategories', []):
            for report in subcategory.get('reports', []):
                if report.get('id') == report_id:
                    report_schema = report.get('schema', {})
                    break
    
    if not report_schema:
        errors.append(ValidationError(
            field='jobDefinitionUri',
            message=f'Report schema not found for {report_id}',
            code='SCHEMA_NOT_FOUND'
        ))
        return errors
    
    # Validate required fields
    for field in report_schema.get('fields', []):
        field_name = field.get('name')
        field_required = field.get('required', False)
        
        if field_required and field_name not in parameters:
            errors.append(ValidationError(
                field=field_name,
                message=f'Required field {field_name} is missing',
                code='REQUIRED_FIELD_MISSING'
            ))
    
    return errors

def forward_to_polling_service(job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Forward job request to polling service"""
    polling_url = os.getenv('SUBMISSION_TO_POLLING_URL', 'http://job-polling:5001')
    timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
    
    try:
        response = requests.post(
            f"{polling_url}/api/jobs",
            json=job_data,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to forward job to polling service: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    polling_url = os.getenv('SUBMISSION_TO_POLLING_URL', 'http://job-polling:5001')
    
    health_status = {
        'service': 'job-submission',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'dependencies': {}
    }
    
    # Check polling service health
    try:
        response = requests.get(f"{polling_url}/health", timeout=5)
        if response.status_code == 200:
            health_status['dependencies']['polling_service'] = 'healthy'
        else:
            health_status['dependencies']['polling_service'] = 'unhealthy'
            health_status['status'] = 'degraded'
    except requests.exceptions.RequestException:
        health_status['dependencies']['polling_service'] = 'unreachable'
        health_status['status'] = 'degraded'
    
    # Check report definitions
    try:
        definitions = load_report_definitions()
        if definitions:
            health_status['dependencies']['report_definitions'] = 'loaded'
        else:
            health_status['dependencies']['report_definitions'] = 'not_found'
            health_status['status'] = 'degraded'
    except Exception:
        health_status['dependencies']['report_definitions'] = 'error'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/api/reports', methods=['GET'])
@limiter.limit("50/minute")
def get_reports():
    """Get report definitions"""
    try:
        definitions = load_report_definitions()
        if not definitions:
            return jsonify({
                'error': 'Report definitions not available',
                'code': 'DEFINITIONS_NOT_FOUND'
            }), 503
        
        return jsonify(definitions), 200
    except Exception as e:
        logger.error(f"Error loading report definitions: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/jobs', methods=['POST'])
@limiter.limit("20/minute")
def submit_job():
    """Submit a new job"""
    try:
        # Validate JSON payload
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        payload = request.get_json()
        if not payload:
            return jsonify({
                'error': 'Empty request body',
                'code': 'EMPTY_PAYLOAD'
            }), 400
        
        # Validate request structure
        try:
            job_request = JobRequest.from_dict(payload)
        except Exception as e:
            return jsonify({
                'error': f'Invalid request structure: {str(e)}',
                'code': 'VALIDATION_ERROR'
            }), 422
        
        # Validate report exists
        if not validate_report_exists(job_request.jobDefinitionUri):
            return jsonify({
                'error': f'Report not found: {job_request.jobDefinitionUri}',
                'code': 'REPORT_NOT_FOUND'
            }), 404
        
        # Validate report parameters
        validation_errors = validate_report_parameters(
            job_request.jobDefinitionUri, 
            job_request.arguments
        )
        if validation_errors:
            return jsonify({
                'error': 'Parameter validation failed',
                'code': 'PARAMETER_VALIDATION_ERROR',
                'details': [error.to_dict() for error in validation_errors]
            }), 422
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Prepare job data for polling service
        job_data = {
            'id': job_id,
            'name': job_request.name,
            'jobDefinitionUri': job_request.jobDefinitionUri,
            'arguments': job_request.arguments,
            'submitted_by': job_request.submitted_by,
            'priority': job_request.priority,
            'submitted_at': datetime.now().isoformat(),
            'status': os.getenv('JOB_STATUS_SUBMITTED', 'submitted')
        }
        
        # Forward to polling service
        polling_response = forward_to_polling_service(job_data)
        if not polling_response:
            return jsonify({
                'error': 'Polling service unavailable',
                'code': 'POLLING_SERVICE_ERROR'
            }), 503
        
        # Create response
        polling_base_url = os.getenv('POLLING_BASE_URL', 'http://localhost:5001')
        response = JobResponse(
            id=job_id,
            status=os.getenv('JOB_STATUS_SUBMITTED', 'submitted'),
            polling_url=f"{polling_base_url}/api/jobs/{job_id}/status",
            estimated_duration=polling_response.get('estimated_duration', 60)
        )
        
        logger.info(f"Job submitted successfully: {job_id}")
        return jsonify(response.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in job submission: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.errorhandler(429)
def rate_limit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'code': 'RATE_LIMIT_EXCEEDED',
        'message': str(e.description)
    }), 429

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
    port = int(os.getenv('SUBMISSION_PORT', '5000'))
    host = os.getenv('SUBMISSION_HOST', '0.0.0.0')
    debug = os.getenv('DEV_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting job submission service on {host}:{port}")
    app.run(host=host, port=port, debug=debug)