"""
=============================================================================
JOB SUBMISSION SERVICE UNIT TESTS
=============================================================================
Purpose: Comprehensive unit tests for job submission service
Framework: pytest with fixtures and mocking
Coverage: 80% minimum requirement

TEST CATEGORIES:
1. Health Check Tests
2. Report Definitions Tests
3. Job Submission Tests
4. Validation Tests
5. Error Handling Tests
6. Rate Limiting Tests

FIXTURES:
- app: Flask test client
- mock_polling_service: Mock polling service responses
- sample_job_request: Valid job request data
- invalid_job_request: Invalid job request data

REQUIREMENTS:
- All endpoints must be tested
- Success and failure scenarios
- Input validation coverage
- Error response validation
- Mock external dependencies
=============================================================================
"""

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from models import JobRequest, JobResponse, ValidationError

@pytest.fixture
def app():
    """Create Flask test client"""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def sample_job_request():
    """Sample valid job request data"""
    return {
        'name': 'Test CMBS Report',
        'jobDefinitionUri': 'cmbs-user-manual',
        'arguments': {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'property_type': 'Office',
            'include_charts': True
        },
        'submitted_by': 'test_user',
        'priority': 5
    }

@pytest.fixture
def invalid_job_request():
    """Sample invalid job request data"""
    return {
        'name': '',  # Invalid: empty name
        'jobDefinitionUri': 'invalid-report-id',  # Invalid: non-existent report
        'arguments': {},  # Missing required arguments
        'submitted_by': '',  # Invalid: empty submitted_by
        'priority': 15  # Invalid: out of range
    }

@pytest.fixture
def mock_report_definitions():
    """Mock report definitions data"""
    return {
        'title': 'Test Report Definitions',
        'categories': [
            {
                'id': 'test-category',
                'subcategories': [
                    {
                        'id': 'test-subcategory',
                        'reports': [
                            {
                                'id': 'cmbs-user-manual',
                                'name': 'Test CMBS Report',
                                'schema': {
                                    'fields': [
                                        {
                                            'name': 'start_date',
                                            'required': True
                                        },
                                        {
                                            'name': 'end_date',
                                            'required': True
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_success(self, app):
        """Test successful health check"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'status': 'healthy'}
            
            response = app.get('/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['service'] == 'job-submission'
            assert 'timestamp' in data
            assert 'dependencies' in data
    
    def test_health_check_degraded(self, app):
        """Test health check with degraded dependencies"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception('Connection failed')
            
            response = app.get('/health')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert data['status'] == 'degraded'

class TestReportDefinitions:
    """Test report definitions endpoint"""
    
    @patch('app.load_report_definitions')
    def test_get_reports_success(self, mock_load, app, mock_report_definitions):
        """Test successful report definitions retrieval"""
        mock_load.return_value = mock_report_definitions
        
        response = app.get('/api/reports')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'Test Report Definitions'
        assert 'categories' in data
    
    @patch('app.load_report_definitions')
    def test_get_reports_not_found(self, mock_load, app):
        """Test report definitions not found"""
        mock_load.return_value = {}
        
        response = app.get('/api/reports')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['code'] == 'DEFINITIONS_NOT_FOUND'
    
    @patch('app.load_report_definitions')
    def test_get_reports_error(self, mock_load, app):
        """Test report definitions loading error"""
        mock_load.side_effect = Exception('File error')
        
        response = app.get('/api/reports')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['code'] == 'INTERNAL_ERROR'

class TestJobSubmission:
    """Test job submission endpoint"""
    
    @patch('app.forward_to_polling_service')
    @patch('app.validate_report_parameters')
    @patch('app.validate_report_exists')
    def test_submit_job_success(self, mock_validate_exists, mock_validate_params, 
                               mock_forward, app, sample_job_request):
        """Test successful job submission"""
        # Setup mocks
        mock_validate_exists.return_value = True
        mock_validate_params.return_value = []
        mock_forward.return_value = {'estimated_duration': 120}
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_request),
                          content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'id' in data
        assert data['status'] == 'submitted'
        assert 'polling_url' in data
        assert data['estimated_duration'] == 120
    
    def test_submit_job_invalid_content_type(self, app, sample_job_request):
        """Test job submission with invalid content type"""
        response = app.post('/api/jobs',
                          data='not json',
                          content_type='text/plain')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['code'] == 'INVALID_CONTENT_TYPE'
    
    def test_submit_job_empty_payload(self, app):
        """Test job submission with empty payload"""
        response = app.post('/api/jobs',
                          data='',
                          content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['code'] == 'EMPTY_PAYLOAD'
    
    @patch('app.validate_report_exists')
    def test_submit_job_invalid_structure(self, mock_validate, app):
        """Test job submission with invalid structure"""
        invalid_request = {'invalid': 'structure'}
        
        response = app.post('/api/jobs',
                          data=json.dumps(invalid_request),
                          content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data['code'] == 'VALIDATION_ERROR'
    
    @patch('app.validate_report_exists')
    def test_submit_job_report_not_found(self, mock_validate, app, sample_job_request):
        """Test job submission with non-existent report"""
        mock_validate.return_value = False
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_request),
                          content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['code'] == 'REPORT_NOT_FOUND'
    
    @patch('app.validate_report_parameters')
    @patch('app.validate_report_exists')
    def test_submit_job_parameter_validation_error(self, mock_validate_exists, 
                                                  mock_validate_params, app, sample_job_request):
        """Test job submission with parameter validation errors"""
        mock_validate_exists.return_value = True
        mock_validate_params.return_value = [
            ValidationError('start_date', 'Start date is required', 'REQUIRED_FIELD_MISSING')
        ]
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_request),
                          content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data['code'] == 'PARAMETER_VALIDATION_ERROR'
        assert 'details' in data
    
    @patch('app.forward_to_polling_service')
    @patch('app.validate_report_parameters')
    @patch('app.validate_report_exists')
    def test_submit_job_polling_service_unavailable(self, mock_validate_exists, 
                                                   mock_validate_params, mock_forward, 
                                                   app, sample_job_request):
        """Test job submission when polling service is unavailable"""
        mock_validate_exists.return_value = True
        mock_validate_params.return_value = []
        mock_forward.return_value = None
        
        response = app.post('/api/jobs',
                          data=json.dumps(sample_job_request),
                          content_type='application/json')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['code'] == 'POLLING_SERVICE_ERROR'

class TestValidation:
    """Test validation functions"""
    
    @patch('app.load_report_definitions')
    def test_validate_report_exists_true(self, mock_load, mock_report_definitions):
        """Test report validation - report exists"""
        from app import validate_report_exists
        
        mock_load.return_value = mock_report_definitions
        
        result = validate_report_exists('cmbs-user-manual')
        assert result is True
    
    @patch('app.load_report_definitions')
    def test_validate_report_exists_false(self, mock_load, mock_report_definitions):
        """Test report validation - report does not exist"""
        from app import validate_report_exists
        
        mock_load.return_value = mock_report_definitions
        
        result = validate_report_exists('non-existent-report')
        assert result is False
    
    @patch('app.load_report_definitions')
    def test_validate_report_parameters_success(self, mock_load, mock_report_definitions):
        """Test parameter validation - all required parameters present"""
        from app import validate_report_parameters
        
        mock_load.return_value = mock_report_definitions
        
        parameters = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        }
        
        errors = validate_report_parameters('cmbs-user-manual', parameters)
        assert len(errors) == 0
    
    @patch('app.load_report_definitions')
    def test_validate_report_parameters_missing_required(self, mock_load, mock_report_definitions):
        """Test parameter validation - missing required parameters"""
        from app import validate_report_parameters
        
        mock_load.return_value = mock_report_definitions
        
        parameters = {
            'start_date': '2024-01-01'
            # Missing end_date
        }
        
        errors = validate_report_parameters('cmbs-user-manual', parameters)
        assert len(errors) > 0
        assert any(error.field == 'end_date' for error in errors)

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_handler(self, app):
        """Test 404 error handler"""
        response = app.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['code'] == 'ENDPOINT_NOT_FOUND'
    
    def test_rate_limit_handler(self, app):
        """Test rate limit error handler"""
        # This test would require actually hitting the rate limit
        # For now, we'll test the handler function exists
        from app import rate_limit_handler
        
        mock_error = MagicMock()
        mock_error.description = 'Rate limit exceeded'
        
        response, status_code = rate_limit_handler(mock_error)
        
        assert status_code == 429
        data = json.loads(response.data)
        assert data['code'] == 'RATE_LIMIT_EXCEEDED'

class TestModels:
    """Test data models"""
    
    def test_job_request_valid(self, sample_job_request):
        """Test JobRequest with valid data"""
        job_request = JobRequest.from_dict(sample_job_request)
        
        assert job_request.name == sample_job_request['name']
        assert job_request.jobDefinitionUri == sample_job_request['jobDefinitionUri']
        assert job_request.arguments == sample_job_request['arguments']
        assert job_request.submitted_by == sample_job_request['submitted_by']
        assert job_request.priority == sample_job_request['priority']
    
    def test_job_request_invalid(self, invalid_job_request):
        """Test JobRequest with invalid data"""
        with pytest.raises(ValueError):
            JobRequest.from_dict(invalid_job_request)
    
    def test_job_request_validation_errors(self):
        """Test JobRequest validation error details"""
        job_request_data = {
            'name': '',
            'jobDefinitionUri': '',
            'arguments': 'not_a_dict',
            'submitted_by': '',
            'priority': 15
        }
        
        try:
            JobRequest.from_dict(job_request_data)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_message = str(e)
            assert 'Job name' in error_message
            assert 'Report ID' in error_message
    
    def test_job_response_valid(self):
        """Test JobResponse with valid data"""
        job_response = JobResponse(
            id=str(uuid.uuid4()),
            status='submitted',
            polling_url='http://localhost:5001/api/jobs/123/status',
            estimated_duration=120
        )
        
        assert job_response.status == 'submitted'
        assert job_response.estimated_duration == 120
        assert 'polling_url' in job_response.to_dict()
    
    def test_job_response_invalid(self):
        """Test JobResponse with invalid data"""
        with pytest.raises(ValueError):
            JobResponse(
                id='',  # Invalid: empty ID
                status='invalid_status',  # Invalid: not in allowed statuses
                polling_url='not_a_url',  # Invalid: not a valid URL
                estimated_duration=-1  # Invalid: negative duration
            )
    
    def test_validation_error(self):
        """Test ValidationError model"""
        error = ValidationError(
            field='test_field',
            message='Test error message',
            code='TEST_ERROR'
        )
        
        error_dict = error.to_dict()
        assert error_dict['field'] == 'test_field'
        assert error_dict['message'] == 'Test error message'
        assert error_dict['code'] == 'TEST_ERROR'

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=app', '--cov=models', '--cov-report=term-missing'])