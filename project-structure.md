# =============================================================================
# DATAFIT PROJECT STRUCTURE DOCUMENTATION
# =============================================================================
# Purpose: Complete project layout and component relationships
# Usage: Reference for all AI agents working on the project
# 
# STRICT REQUIREMENTS:
# - Every directory and file must be documented
# - Component interactions must be clearly defined
# - API contracts between services must be specified
# - Data flow diagrams must be included
# =============================================================================

## PROJECT OVERVIEW

DataFit is a microservices-based SAS Viya job execution system consisting of:
1. **GUI Service**: Single-page application for job submission
2. **Job Submission Service**: API gateway for job requests
3. **Job Polling Service**: Job execution engine with FIFO queue
4. **Report Generators**: Python modules for generating various report types

## DIRECTORY STRUCTURE

```
datafit/
├── config.dev.env                 # Central configuration file
├── docker-compose.yml             # Multi-service orchestration
├── plan-phases.md                 # Development plan and requirements
├── notes.md                       # Original requirements and notes
├── project-structure.md           # This file
├── README.md                      # Project overview and setup
├── example-reports.json           # Sample report output structure
│
├── gui/                           # Frontend SPA service
│   ├── index.html                 # Main application entry point
│   ├── app.js                     # Core application logic
│   ├── components/                # Reusable UI components
│   │   ├── report-selector.js     # Report dropdown component
│   │   ├── form-generator.js      # Dynamic form generation
│   │   └── job-status.js          # Job tracking component
│   ├── styles/                    # CSS styling
│   │   └── main.css               # Main stylesheet
│   └── Dockerfile                 # GUI container configuration
│
├── job-submission/                # Job submission microservice
│   ├── app.py                     # Flask/FastAPI application
│   ├── models.py                  # Data validation models
│   ├── utils.py                   # Utility functions
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Submission service container
│
├── job-polling/                   # Job processing microservice
│   ├── app.py                     # Main polling service
│   ├── models.py                  # Job and file models
│   ├── job_executor.py            # Report execution engine
│   ├── file_manager.py            # File storage management
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Polling service container
│
├── reports/                       # Report generator modules
│   ├── __init__.py                # Package initialization
│   ├── base_report.py             # Abstract base class
│   ├── cmbs_user_manual.py        # CMBS report generator
│   ├── rmbs_performance.py        # RMBS performance analysis
│   ├── var_daily.py               # Value at Risk reports
│   ├── stress_test.py             # Stress test results
│   ├── trading_activity.py        # Trading activity reports
│   ├── aml_alerts.py              # AML compliance reports
│   └── focus_manual.py            # FOCUS user manual
│
├── data/                          # Configuration and schema data
│   └── report-definitions.json    # Report structure definitions
│
├── mock-data/                     # Sample data for development
│   ├── aml_alerts.csv             # AML suspicious activity data
│   ├── rmbs_performance.csv       # RMBS performance metrics
│   ├── stress_test_results.csv    # Stress testing scenarios
│   ├── trading_activity.csv       # Trading transaction data
│   ├── var_daily.csv              # Value at Risk calculations
│   ├── cmbs_data.csv              # CMBS market data
│   └── focus_manual.csv           # FOCUS reporting data
│
├── templates/                     # HTML templates for reports
│   ├── base_template.html         # Base HTML template
│   ├── report_template.html       # Generic report template
│   └── chart_template.html        # Template for Plotly charts
│
└── tests/                         # Test suite
    ├── conftest.py                # pytest configuration
    ├── test_job_submission/       # Submission service tests
    │   ├── test_app.py
    │   ├── test_models.py
    │   └── test_utils.py
    ├── test_job_polling/          # Polling service tests
    │   ├── test_app.py
    │   ├── test_models.py
    │   ├── test_job_executor.py
    │   └── test_file_manager.py
    ├── test_reports/              # Report generator tests
    │   ├── test_base_report.py
    │   ├── test_cmbs_user_manual.py
    │   ├── test_rmbs_performance.py
    │   ├── test_var_daily.py
    │   ├── test_stress_test.py
    │   ├── test_trading_activity.py
    │   ├── test_aml_alerts.py
    │   └── test_focus_manual.py
    └── test_integration/          # Integration tests
        ├── test_end_to_end.py
        └── test_service_communication.py
```

## SERVICE ARCHITECTURE

### Component Relationships

```
[GUI Frontend] → [Job Submission Service] → [Job Polling Service]
      ↓                    ↓                         ↓
[User Browser]    [Request Validation]      [Job Queue & Execution]
                        ↓                         ↓
                  [Payload Forwarding]      [Report Generators]
                                                  ↓
                                            [File Management]
```

### Data Flow

1. **Job Submission Flow**:
   - GUI loads report definitions from submission service
   - User selects report and fills dynamic form
   - GUI submits job payload to submission service
   - Submission service validates and forwards to polling service
   - Polling service queues job and returns job ID

2. **Job Processing Flow**:
   - Polling service processes jobs in FIFO order
   - Job executor loads appropriate report generator
   - Report generator executes with provided parameters
   - Generated files stored with file manager
   - Job status updated to completed

3. **Status Tracking Flow**:
   - GUI polls job status endpoint periodically
   - Polling service returns current status and progress
   - When completed, file download links provided
   - Files auto-cleaned after retention period

## API CONTRACTS

### Job Submission Service APIs

```
GET /api/reports
Response: Report definitions JSON structure
Status: 200 OK

POST /api/jobs
Request: Job submission payload
Response: Job ID and polling URL
Status: 201 Created

GET /health
Response: Service health status
Status: 200 OK
```

### Job Polling Service APIs

```
POST /api/jobs
Request: Job payload from submission service
Response: Job status
Status: 201 Created

GET /api/jobs/{job_id}/status
Response: Current job status and progress
Status: 200 OK

GET /api/jobs/{job_id}/files
Response: List of available files
Status: 200 OK

GET /api/jobs/{job_id}/files/{filename}
Response: File download
Status: 200 OK

DELETE /api/jobs/{job_id}
Request: Cancel job
Status: 204 No Content
```

## DATA MODELS

### Job Request Model
```json
{
  "name": "string",
  "jobDefinitionUri": "string",
  "arguments": {
    "parameter_name": "value"
  },
  "priority": "integer",
  "submitted_by": "string"
}
```

### Job Status Model
```json
{
  "id": "uuid",
  "status": "enum[submitted,queued,running,completed,failed,cancelled]",
  "progress": "integer[0-100]",
  "created_at": "datetime",
  "started_at": "datetime",
  "completed_at": "datetime",
  "error_message": "string",
  "files": ["array of file objects"]
}
```

### Report Definition Model
```json
{
  "categories": [
    {
      "name": "string",
      "subcategories": [
        {
          "name": "string",
          "reports": [
            {
              "name": "string",
              "id": "uuid",
              "description": "string",
              "estimated_duration": "integer",
              "output_formats": ["array"],
              "prompts": [
                {
                  "field_name": {
                    "active": "boolean",
                    "hide": "boolean",
                    "inputType": "enum",
                    "label": "string",
                    "required": "boolean",
                    "options": ["array"],
                    "validation": "object"
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## DEPLOYMENT ARCHITECTURE

### Docker Services

1. **GUI Service** (Port 3000)
   - Nginx serving static files
   - Environment variables from config.dev.env
   - Volume mount for development hot reload

2. **Job Submission Service** (Port 5001)
   - Python Flask/FastAPI application
   - Health check endpoint
   - Log volume for monitoring

3. **Job Polling Service** (Port 5002)
   - Python Flask/FastAPI with background workers
   - File storage volume
   - Queue persistence volume

### Network Communication

- Services communicate via Docker internal network
- GUI accesses backend through exposed ports
- Inter-service communication uses service names
- All external traffic through reverse proxy

### Volume Management

- **Config Volume**: Shared config.dev.env
- **Data Volume**: Report definitions and mock data
- **File Storage**: Generated report files
- **Logs Volume**: Application logs
- **Templates Volume**: HTML templates

## SECURITY CONSIDERATIONS

### Input Validation
- All user inputs validated at API gateway
- SQL injection prevention (when database added)
- XSS protection in frontend
- File type validation for uploads

### Access Control
- CORS configured for frontend domain
- Rate limiting on API endpoints
- File access control with time-limited URLs
- Service-to-service authentication

### Data Security
- No sensitive data in logs
- Temporary file cleanup
- Secure file storage permissions
- Environment variable protection

## MONITORING AND LOGGING

### Log Structure
- Structured JSON logging
- Request correlation IDs
- Performance metrics
- Error tracking with stack traces

### Health Checks
- Service availability endpoints
- Database connectivity (future)
- File system health
- Queue status monitoring

### Metrics Collection
- Request/response times
- Queue depth and processing time
- File generation success rates
- Error rates by service

## DEVELOPMENT WORKFLOW

### Phase Dependencies
1. **Phase 1**: Documentation and file headers (this phase)
2. **Phase 2**: Infrastructure setup (Docker, config loading)
3. **Phase 3**: Backend services implementation
4. **Phase 4**: Frontend and report generators

### Testing Strategy
- Unit tests for all Python modules
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Performance tests for queue processing

### Code Quality
- Type hints for all Python code
- ESLint for JavaScript
- Black formatting for Python
- Pre-commit hooks for quality checks

## FUTURE ENHANCEMENTS

### Planned Features
- User authentication and authorization
- Database persistence for job history
- WebSocket real-time updates
- Advanced queue management
- Horizontal scaling support

### Scalability Considerations
- Stateless service design
- Database abstraction layer
- Container orchestration ready
- Load balancer configuration
- Caching strategies implemented