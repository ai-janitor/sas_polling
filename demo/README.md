# DataFit CLI Demo & Testing Framework

## Overview
This directory contains a comprehensive CLI testing and demonstration framework for the DataFit SAS Viya Job Execution System. The framework provides automated testing, performance validation, and interactive demonstrations using curl commands.

## Directory Structure
```
demo/
├── Makefile                 # Main automation for demo execution
├── README.md               # This file - demo instructions
├── PHASE-CLI-DEMO.md       # Detailed CLI commands and procedures
├── scripts/                # Individual test scripts
├── configs/                # Test data and configuration files
└── outputs/                # Generated reports and test results
    └── temp/               # Temporary files during execution
```

## Prerequisites
- DataFit services running (job-submission on port 5000, job-polling on port 5001)
- curl command-line tool installed
- jq JSON processor installed (for formatted output)
- make utility available

## Quick Start

### 1. Check Service Health
```bash
make health
```
This verifies that both job-submission and job-polling services are running and healthy.

### 2. Run Complete Demonstration
```bash
make demo
```
This executes a full end-to-end workflow demonstration including job submission, status monitoring, and file download.

### 3. Run All Tests
```bash
make test-all
```
This runs the complete test suite including basic functionality, error handling, all report types, and performance tests.

## Available Make Targets

### Core Demo Commands
- `make demo` - Run complete end-to-end demonstration
- `make health` - Check service health and readiness
- `make help` - Show all available targets with descriptions

### Test Categories
- `make test-basic` - Run basic functionality tests
- `make test-errors` - Run error handling tests
- `make test-reports` - Test all 7 report types
- `make test-performance` - Run performance and load tests
- `make test-all` - Run complete test suite

### Utility Commands
- `make setup` - Create demo directory structure
- `make clean` - Clean up demo outputs and temporary files
- `make logs` - Show service logs (if running in Docker)
- `make report` - Generate demo execution report
- `make validate-config` - Validate configuration settings

## Test Categories

### Basic Functionality Tests
- Service health endpoints
- Report definitions loading
- Simple job submission and status checking

### Error Handling Tests
- Invalid job submissions
- Nonexistent resource requests
- Malformed request handling

### Report Type Tests
Tests all 7 supported report types:
- CMBS User Manual Report
- RMBS Performance Report
- VaR Daily Report
- Stress Testing Report
- Trading Activity Report
- AML Alerts Report
- FOCUS Manual Report

### Performance Tests
- Response time measurement
- Concurrent job submission
- Rate limiting validation

## Configuration

The demo framework reads all configuration from `../config.dev.env`. Key settings include:
- `SUBMISSION_PORT` - Job submission service port
- `POLLING_PORT` - Job polling service port
- Service URLs are automatically constructed from these ports

## Output Files

All demo outputs are stored in the `outputs/` directory:
- `demo-job-id.txt` - Last submitted job ID
- `demo-report.html` - Downloaded sample report
- `demo-report.md` - Execution summary report
- `temp/` - Temporary files from test execution

## Troubleshooting

### Services Not Responding
1. Check if services are running:
   ```bash
   curl http://localhost:5000/health
   curl http://localhost:5001/health
   ```

2. Verify configuration in `../config.dev.env`

3. Check service logs:
   ```bash
   make logs
   ```

### Test Failures
1. Run health check first: `make health`
2. Check individual test categories: `make test-basic`
3. Review outputs in `outputs/temp/` for detailed error information

### Permission Issues
Ensure the demo directory is writable:
```bash
chmod +w demo/outputs/
```

## Manual Testing

For manual testing outside of the Makefile automation, see `PHASE-CLI-DEMO.md` for detailed curl commands and procedures.

## Performance Expectations

- Health checks: < 500ms response time
- Job submission: < 1 second
- Status polling: < 200ms per request
- File downloads: Depends on file size

## Demo Flow

The complete demo (`make demo`) follows this workflow:

1. **Health Check** - Verify services are operational
2. **Report Discovery** - Load available report definitions
3. **Job Submission** - Submit a CMBS report job
4. **Status Monitoring** - Poll job status until completion
5. **File Management** - List and download generated files

This demonstrates the complete DataFit workflow from job submission to file delivery.

## Integration with CI/CD

The demo framework can be integrated into CI/CD pipelines:

```bash
# In your CI/CD script
cd demo
make validate-config
make health
make test-all
make report
```

The exit codes follow standard conventions (0 = success, non-zero = failure).

## Support

For issues with the demo framework:
1. Check service health with `make health`
2. Review the detailed commands in `PHASE-CLI-DEMO.md`
3. Examine output files in `outputs/temp/` for debugging information