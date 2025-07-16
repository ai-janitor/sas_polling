# DataFit SAS Viya Job Execution System - Development Plan

## STRICT REQUIREMENTS

### MANDATORY RULES FOR ALL AI AGENTS
1. **NO CODE BEFORE HEADERS**: Every file MUST have detailed comment header before any code is written
2. **DOCUMENTATION FIRST**: All files must be documented with purpose and implementation details
3. **SYNCHRONIZED JSON**: GUI and job polling must use identical report definitions
4. **80% TEST COVERAGE**: Every Python file requires comprehensive unit tests
5. **CONFIG DRIVEN**: All hardcoded values MUST come from config.dev.env
6. **DEFENSIVE CODING**: All inputs must be validated, all errors handled gracefully
7. **DOCKER READY**: All services must be containerized and orchestrated

### TECHNICAL STACK REQUIREMENTS
- **Frontend**: Vanilla JavaScript SPA (NO frameworks)
- **Backend Services**: Python Flask/FastAPI
- **Data Format**: JSON for configuration, CSV for mock data
- **Containerization**: Docker with docker-compose orchestration
- **Base Images**: Amazon Linux 2023 for all services
- **Testing**: pytest with minimum 80% coverage
- **Output Formats**: HTML, PDF, CSV, XLS, Plotly charts

---

## PHASE 1: DOCUMENTATION & ARCHITECTURE
**AI Agent 1 Responsibilities**

### MANDATORY DELIVERABLES
1. Complete file structure with detailed comment headers
2. Environment configuration setup
3. Project documentation
4. API specification documentation
5. **Makefile for infrastructure management**

### FILES TO CREATE WITH HEADERS

#### Configuration Files
**File**: `Makefile`
```makefile
# =============================================================================
# DATAFIT INFRASTRUCTURE MAKEFILE  
# =============================================================================
# Purpose: Single point of control for all infrastructure operations
# Configuration: Reads all settings from config.dev.env
# 
# STRICT REQUIREMENTS:
# - NO hardcoded values anywhere in the infrastructure
# - All ports, URLs, credentials come from config.dev.env
# - Single command deployment and management
# - Environment-specific overrides supported
# - Proper cleanup and resource management
#
# AVAILABLE TARGETS:
# - build: Build all Docker images
# - deploy: Deploy all services 
# - start: Start all services
# - stop: Stop all services
# - clean: Clean up containers, images, and volumes
# - logs: Show logs from all services
# - status: Show status of all services
# - test: Run all tests
# - dev: Start in development mode
# - prod: Deploy in production mode
# =============================================================================
```

**File**: `config.dev.env`
```bash
# =============================================================================
# DATAFIT DEVELOPMENT ENVIRONMENT CONFIGURATION
# =============================================================================
# Purpose: Central configuration for all services in development environment
# Usage: Loaded by all Python, JavaScript, and Docker services
# 
# STRICT REQUIREMENTS:
# - All services MUST read configuration from this file
# - NO hardcoded values allowed in any service
# - Environment variables MUST be prefixed by service (GUI_, SUBMISSION_, POLLING_)
# - All URLs, ports, timeouts, and limits defined here
# 
# CONFIGURATION SECTIONS:
# 1. Service URLs and Ports
# 2. Database/Storage Configuration  
# 3. Job Processing Settings
# 4. File Management Settings
# 5. Security and Authentication
# 6. Logging and Monitoring
# =============================================================================
```

**File**: `project-structure.md`
```markdown
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
```

#### GUI Component Headers
**File**: `gui/index.html`
```html
<!--
=============================================================================
DATAFIT SPA - MAIN ENTRY POINT
=============================================================================
Purpose: Single Page Application for SAS Viya job execution interface
Technology: Vanilla HTML5 with semantic markup
Dependencies: app.js, main.css, Font Awesome icons

STRICT REQUIREMENTS:
- Responsive design for desktop and mobile
- Accessibility compliance (ARIA labels, semantic HTML)
- NO external JavaScript frameworks (vanilla JS only)
- Progressive enhancement approach
- Form validation and error handling

COMPONENT STRUCTURE:
1. Header with application title and navigation
2. Report selection dropdown (loads from JSON)
3. Dynamic form container (generated from report schema)
4. Job submission and status tracking
5. File download and history section

API INTEGRATION:
- GET /api/reports - Load report definitions
- POST /api/jobs - Submit job requests
- GET /api/jobs/{id}/status - Poll job status
- GET /api/jobs/{id}/files - Download results

DATA FLOW:
1. Load report definitions on page load
2. Generate form fields based on selected report schema
3. Submit job with parameters to submission service
4. Poll job status until completion
5. Display download links for generated files
=============================================================================
-->
```

**File**: `gui/app.js`
```javascript
/*
=============================================================================
DATAFIT SPA - MAIN APPLICATION LOGIC
=============================================================================
Purpose: Core JavaScript application for job submission and management
Technology: Vanilla ES6+ JavaScript with async/await
Dependencies: None (standalone vanilla JS)

STRICT REQUIREMENTS:
- ES6+ syntax with proper error handling
- Async/await for all API calls with timeout handling
- State management without external libraries
- Real-time job status updates with WebSocket fallback to polling
- Form validation with user-friendly error messages

CORE MODULES:
1. ReportManager - Handle report definition loading and caching
2. FormGenerator - Dynamic form creation from JSON schema
3. JobSubmitter - Job submission and validation
4. StatusTracker - Real-time job status monitoring
5. FileManager - Download management and history
6. ErrorHandler - Centralized error handling and user notification

API ENDPOINTS:
- reportDefinitionsUrl: GET /api/reports
- jobSubmissionUrl: POST /api/jobs  
- jobStatusUrl: GET /api/jobs/{id}/status
- fileDownloadUrl: GET /api/jobs/{id}/files/{filename}

CONFIGURATION:
All URLs and settings loaded from config via environment or API

STATE MANAGEMENT:
- currentReport: Selected report definition
- formData: User input parameters
- activeJobs: List of submitted jobs with status
- jobHistory: Completed jobs with download links
=============================================================================
*/
```

**File**: `gui/components/report-selector.js`
```javascript
/*
=============================================================================
REPORT SELECTOR COMPONENT
=============================================================================
Purpose: Dropdown component for report selection with category grouping
Technology: Vanilla JavaScript with event delegation
Parent: app.js

STRICT REQUIREMENTS:
- Hierarchical display of categories and subcategories
- Search/filter functionality for report names
- Keyboard navigation support (arrow keys, enter)
- Loading states and error handling
- Mobile-friendly touch interactions

COMPONENT FEATURES:
1. Grouped dropdown with categories and subcategories
2. Search functionality with fuzzy matching
3. Recent reports quick access
4. Report description tooltips
5. Keyboard accessibility

DATA STRUCTURE:
Consumes report definitions JSON with categories/subcategories/reports hierarchy

EVENTS:
- reportSelected: Fired when user selects a report
- reportChanged: Fired when selection changes
- searchUpdated: Fired when search filter changes

METHODS:
- loadReports(reportsData): Initialize component with report data
- selectReport(reportId): Programmatically select a report
- filterReports(searchTerm): Filter reports by search term
- clearSelection(): Reset to default state
=============================================================================
*/
```

**File**: `gui/components/form-generator.js`
```javascript
/*
=============================================================================
DYNAMIC FORM GENERATOR COMPONENT
=============================================================================
Purpose: Generate forms dynamically from JSON report schema
Technology: Vanilla JavaScript with template literals
Parent: app.js

STRICT REQUIREMENTS:
- Support all input types: inputtext, dropdown, date, checkbox, radio
- Real-time validation with visual feedback
- Conditional field display based on dependencies
- Accessibility compliance (labels, ARIA attributes)
- Mobile-responsive layout

INPUT TYPE SUPPORT:
1. inputtext: Text input with pattern validation
2. dropdown: Select with options from schema
3. date: Date picker with min/max constraints
4. checkbox: Boolean toggles
5. radio: Single selection from options
6. hidden: Hidden fields (e.g., username)

VALIDATION FEATURES:
- Required field validation
- Pattern matching for text inputs
- Date range validation
- Custom validation rules from schema
- Real-time feedback with error messages

FORM STRUCTURE:
Generated form includes:
- Field labels with required indicators
- Input controls based on schema
- Validation error display areas
- Submit button with loading states
- Reset functionality

METHODS:
- generateForm(reportSchema): Create form from report definition
- validateForm(): Validate all fields and return errors
- getFormData(): Extract form data as JSON
- resetForm(): Clear all fields and errors
- setFieldValue(fieldName, value): Programmatically set field values
=============================================================================
*/
```

**File**: `gui/components/job-status.js`
```javascript
/*
=============================================================================
JOB STATUS TRACKING COMPONENT
=============================================================================
Purpose: Real-time job status monitoring and file download management
Technology: Vanilla JavaScript with periodic polling
Parent: app.js

STRICT REQUIREMENTS:
- Real-time status updates with exponential backoff polling
- Progress indicators for long-running jobs
- Error handling with retry mechanisms
- File download management with progress tracking
- Job history with pagination

STATUS TRACKING:
- Poll job status every 2 seconds initially
- Exponential backoff: 2s, 4s, 8s, 16s, max 30s
- Visual indicators for: pending, running, completed, failed
- Estimated completion time display
- Cancel job functionality

FILE MANAGEMENT:
- List generated files with metadata
- Download progress tracking
- File preview for HTML/CSV reports
- Bulk download capabilities
- File cleanup after retention period

JOB HISTORY:
- FIFO list of last 100 jobs
- Filter by status, date, report type
- Search by job name or parameters
- Export history as CSV
- Detailed job information modal

METHODS:
- startPolling(jobId): Begin status polling for job
- stopPolling(jobId): Stop polling for completed/failed jobs
- downloadFile(jobId, filename): Initiate file download
- cancelJob(jobId): Cancel running job
- showJobDetails(jobId): Display detailed job information
=============================================================================
*/
```

#### Backend Service Headers
**File**: `job-submission/app.py`
```python
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
```

**File**: `job-submission/models.py`
```python
"""
=============================================================================
JOB SUBMISSION DATA MODELS
=============================================================================
Purpose: Data validation and serialization models for job requests
Framework: Pydantic for validation, dataclasses for internal models

STRICT REQUIREMENTS:
- Type hints for all fields
- Comprehensive validation rules
- Serialization to/from JSON
- Immutable data structures where possible
- Clear error messages for validation failures

MODEL CLASSES:

JobRequest:
    - name: str (job display name)
    - jobDefinitionUri: str (report ID from definitions)
    - arguments: Dict[str, Any] (report parameters)
    - submitted_by: str (user identifier)
    - priority: int (job priority, default 5)
    
JobResponse:
    - id: str (UUID job identifier)
    - status: str (initial status: 'submitted')
    - polling_url: str (status checking endpoint)
    - estimated_duration: int (estimated seconds)
    
ValidationError:
    - field: str (field name with error)
    - message: str (human-readable error message)
    - code: str (error code for programmatic handling)

VALIDATION RULES:
- Job name: 1-255 characters, alphanumeric and spaces
- Report ID: Must exist in report definitions
- Arguments: Must match report schema requirements
- Priority: Integer 1-10, default 5
- All required fields must be present

SERIALIZATION:
- to_dict(): Convert to dictionary for JSON serialization
- from_dict(): Create instance from dictionary
- to_json(): Direct JSON string serialization
- validate(): Comprehensive validation with detailed errors
=============================================================================
"""
```

**File**: `job-polling/app.py`
```python
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
```

#### Report Generator Headers
**File**: `reports/base_report.py`
```python
"""
=============================================================================
BASE REPORT GENERATOR CLASS
=============================================================================
Purpose: Abstract base class for all report generators
Framework: ABC (Abstract Base Classes) with common functionality

STRICT REQUIREMENTS:
- Abstract methods that all reports must implement
- Common utility functions for file generation
- Standardized parameter validation
- Consistent output format handling
- Error handling and logging patterns

ABSTRACT METHODS (must be implemented by subclasses):
- generate(): Main report generation logic
- validate_parameters(): Validate input parameters
- get_output_formats(): Return supported output formats
- get_estimated_duration(): Return estimated processing time

COMMON FUNCTIONALITY:
- Parameter loading and validation
- Output file generation (HTML, PDF, CSV, XLS)
- Error handling with detailed messages
- Progress tracking for long-running reports
- Temporary file management

OUTPUT FORMAT SUPPORT:
- HTML: Interactive reports with Plotly charts
- PDF: Print-ready formatted documents
- CSV: Raw data export
- XLS: Excel-compatible spreadsheets
- JSON: Structured data output

UTILITY METHODS:
- load_mock_data(): Load CSV data for report
- generate_html(): Create HTML output with templates
- generate_pdf(): Convert HTML to PDF
- generate_csv(): Export data as CSV
- generate_xls(): Create Excel files
- create_plotly_chart(): Generate interactive charts

ERROR HANDLING:
- Parameter validation errors
- Data loading failures
- File generation errors
- Timeout handling for long reports
- Resource cleanup on failures

CONFIGURATION:
- REPORTS_DATA_PATH: Path to mock data files
- REPORTS_TEMPLATE_PATH: Path to HTML templates
- REPORTS_OUTPUT_PATH: Temporary output directory
- REPORT_TIMEOUT: Maximum execution time
=============================================================================
"""
```

### STRICT DOCUMENTATION REQUIREMENTS
Each file header must include:
1. **Purpose**: Exact function and responsibility
2. **Technology**: Specific technologies and frameworks used
3. **Dependencies**: All external dependencies listed
4. **Requirements**: Strict implementation requirements
5. **API/Methods**: All public interfaces documented
6. **Configuration**: All configurable parameters
7. **Error Handling**: Expected errors and responses
8. **Data Flow**: Input/output and processing flow

---

## PHASE 2: CORE INFRASTRUCTURE
**AI Agent 2 Responsibilities**

### MANDATORY DELIVERABLES
1. Complete config.dev.env with all environment variables
2. Docker containers for all three services (NO hardcoded values)
3. docker-compose.yml for orchestration (using config variables)
4. Base report class implementation
5. Mock data CSV files for all reports
6. **Makefile integration and hardcoded value elimination**

### DOCKER REQUIREMENTS
Each Dockerfile must:
- **Use Amazon Linux 2023 base images for all services**
- Multi-stage builds for production optimization
- Non-root user for security
- Health checks for all services
- Proper signal handling for graceful shutdown
- **NO hardcoded ports, URLs, or configuration values**
- **All configuration via ARG and ENV from config files**
- Install Python 3.11+ and Node.js 18+ on Amazon Linux 2023

### AMAZON LINUX 2023 REQUIREMENTS
All Docker containers MUST use Amazon Linux 2023 as the base image:

**GUI Service Dockerfile:**
```dockerfile
FROM amazonlinux:2023 AS base
RUN dnf update -y && dnf install -y \
    nodejs npm \
    nginx \
    curl
```

**Job Submission Service Dockerfile:**
```dockerfile
FROM amazonlinux:2023 AS base
RUN dnf update -y && dnf install -y \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    gcc \
    curl
```

**Job Polling Service Dockerfile:**
```dockerfile
FROM amazonlinux:2023 AS base
RUN dnf update -y && dnf install -y \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    gcc \
    curl
```

**CRITICAL**: No Alpine, Ubuntu, or other base images allowed. Amazon Linux 2023 provides:
- AWS optimized performance
- Enterprise security compliance
- Long-term support and updates
- Consistent with AWS deployment environment

### MOCK DATA REQUIREMENTS
CSV files for each report in mock-data/:
- cmbs_data.csv (CMBS User Manual data)
- rmbs_performance.csv (RMBS performance metrics)
- var_daily.csv (Value at Risk calculations)
- stress_test_results.csv (Stress testing scenarios)
- trading_activity.csv (Trading transaction data)
- aml_alerts.csv (AML suspicious activity data)
- focus_manual.csv (FOCUS reporting data)

---

## PHASE 3: SERVICES IMPLEMENTATION
**AI Agent 3 Responsibilities**

### MANDATORY DELIVERABLES
1. Complete job submission service with all endpoints (Amazon Linux 2023)
2. Complete job polling service with FIFO queue (Amazon Linux 2023)
3. Job execution engine with Python report loading
4. File management system with cleanup
5. Inter-service communication with error handling

### API CONTRACT REQUIREMENTS
All endpoints must:
- Follow RESTful conventions
- Return consistent JSON responses
- Include proper HTTP status codes
- Implement request/response logging
- Support CORS for frontend integration

### QUEUE IMPLEMENTATION REQUIREMENTS
- Thread-safe FIFO queue implementation
- Maximum 100 jobs capacity
- Graceful handling of queue overflow
- Job priority support
- Automatic job timeout and cleanup

---

## PHASE 4: CLI DEMO & TESTING
**AI Agent 4 Responsibilities**

### MANDATORY DELIVERABLES
1. Complete CLI testing framework with curl commands
2. End-to-end workflow demonstration scripts
3. Error handling validation commands
4. Performance testing procedures
5. Service startup and demo automation
6. Demo Makefile for automated testing and demonstration

### CLI DEMO REQUIREMENTS
- **Demo Directory Structure**: `/demo/` with organized scripts and outputs
- **Makefile Integration**: Automated demo execution and service management
- **Comprehensive Testing**: All endpoints, error scenarios, and file downloads
- **Documentation**: Clear instructions for running demos and interpreting results
- **Performance Validation**: Load testing and response time measurement
- **Service Health**: Automated health checks and dependency validation

### DEMO DELIVERABLES
- `demo/Makefile`: Complete automation for demo execution
- `demo/scripts/`: Individual test scripts for each scenario
- `demo/configs/`: Test data and configuration files
- `demo/outputs/`: Generated reports and test results
- `demo/README.md`: Demo execution instructions and troubleshooting

---

## PHASE 5: FRONTEND & REPORTS
**AI Agent 5 Responsibilities**

### MANDATORY DELIVERABLES
1. Complete SPA with all components (Amazon Linux 2023 + Nginx)
2. All 7 report generators implemented
3. Dynamic form generation from JSON schema
4. Real-time job status tracking
5. File download and management

### FRONTEND REQUIREMENTS
- Responsive design (mobile, tablet, desktop)
- Accessibility compliance (WCAG 2.1 AA)
- Progressive enhancement
- Error handling with user-friendly messages
- Performance optimization (lazy loading, caching)

### REPORT GENERATOR REQUIREMENTS
Each report must:
- Inherit from base_report.py
- Support all output formats (HTML, PDF, CSV, XLS)
- Include Plotly charts where appropriate
- Validate all input parameters
- Handle missing data gracefully

---

## TESTING REQUIREMENTS

### UNIT TEST STANDARDS
- Minimum 80% code coverage for all Python files
- Test file naming: test_{module_name}.py
- Use pytest framework with fixtures
- Mock all external dependencies
- Test both success and failure scenarios

### INTEGRATION TEST REQUIREMENTS
- End-to-end workflow testing
- Service communication testing
- File upload/download testing
- Queue behavior validation
- Error propagation testing

### TEST DATA REQUIREMENTS
- Separate test data from mock data
- Fixtures for all test scenarios
- Test database/storage isolation
- Automated test execution in CI/CD

---

## QUALITY STANDARDS

### CODE QUALITY
- Type hints for all Python code
- ESLint configuration for JavaScript
- Black code formatting for Python
- Comprehensive error handling
- Security best practices

### DOCUMENTATION QUALITY
- All public APIs documented
- README with setup instructions
- Architecture decision records
- Deployment documentation
- Troubleshooting guides

### PERFORMANCE REQUIREMENTS
- Job submission response < 500ms
- Status polling response < 200ms
- File generation timeout < 300 seconds
- Frontend page load < 2 seconds
- Support 50 concurrent users

---

## SECURITY REQUIREMENTS

### INPUT VALIDATION
- Sanitize all user inputs
- Validate file uploads
- Parameter injection prevention
- XSS protection
- CSRF protection

### FILE SECURITY
- Validate file types and sizes
- Secure file storage location
- Access control for downloads
- Automatic file cleanup
- No execution of uploaded files

### SERVICE SECURITY
- Authentication between services
- Request rate limiting
- Error message sanitization
- Secure configuration management
- Network segmentation in Docker