# PHASE CLI DEMO: Command Line Testing & Demonstration

## PURPOSE
Complete CLI-based testing and demonstration of DataFit services using curl commands. This phase provides ready-to-use commands for testing, debugging, and demonstrating the system functionality.

## REQUIREMENTS
- Both job-submission and job-polling services running
- All endpoints accessible via HTTP
- JSON payloads for realistic testing scenarios
- Error handling validation
- File download testing

---

## DEMO SCRIPT STRUCTURE

### 1. HEALTH CHECK COMMANDS

#### Test Job Submission Service Health
```bash
# Basic health check
curl -X GET http://localhost:5000/health \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: 200 OK with service status
```

#### Test Job Polling Service Health
```bash
# Basic health check
curl -X GET http://localhost:5001/health \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: 200 OK with queue and file storage info
```

### 2. REPORT DEFINITIONS COMMANDS

#### Get Available Reports
```bash
# Fetch all available report definitions
curl -X GET http://localhost:5000/api/reports \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: JSON with categories, subcategories, and report schemas
```

#### Check Specific Report Schema
```bash
# Get reports and filter for CMBS reports
curl -X GET http://localhost:5000/api/reports \
  -H "Content-Type: application/json" \
  | jq '.categories[] | select(.id=="commercial-mortgage")'
```

### 3. JOB SUBMISSION COMMANDS

#### Submit CMBS User Manual Report Job
```bash
# Create CMBS report job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo CMBS User Manual Report",
    "jobDefinitionUri": "cmbs-user-manual",
    "arguments": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "property_type": "Office",
      "include_charts": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 5
  }' | jq '.'

# Expected Response: 201 Created with job ID and polling URL
# Save the job ID for subsequent commands: export JOB_ID="<returned-id>"
```

#### Submit RMBS Performance Report Job
```bash
# Create RMBS performance job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo RMBS Performance Report",
    "jobDefinitionUri": "rmbs-performance",
    "arguments": {
      "report_date": "2024-12-01",
      "pool_id": "POOL-2024-001",
      "loan_type": "Prime",
      "performance_metrics": "Enhanced",
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 3
  }' | jq '.'
```

#### Submit VaR Daily Report Job
```bash
# Create VaR daily report job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Daily VaR Report",
    "jobDefinitionUri": "var-daily",
    "arguments": {
      "calculation_date": "2024-12-15",
      "confidence_level": "99%",
      "portfolio": "MAIN_PORTFOLIO",
      "include_stress": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 1
  }' | jq '.'
```

#### Submit Stress Testing Report Job
```bash
# Create stress testing job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Stress Testing Report",
    "jobDefinitionUri": "stress-testing",
    "arguments": {
      "test_date": "2024-12-15",
      "scenario_type": "Severely Adverse",
      "test_horizon": "2 Years",
      "include_capital": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 2
  }' | jq '.'
```

#### Submit Trading Activity Report Job
```bash
# Create trading activity job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Trading Activity Report",
    "jobDefinitionUri": "trading-activity",
    "arguments": {
      "trade_date": "2024-12-15",
      "asset_class": "Bonds",
      "trader_id": "TRADER001",
      "include_pnl": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 4
  }' | jq '.'
```

#### Submit AML Alerts Report Job
```bash
# Create AML alerts job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo AML Alerts Report",
    "jobDefinitionUri": "aml-alerts",
    "arguments": {
      "alert_date": "2024-12-15",
      "alert_type": "Suspicious Activity",
      "risk_level": "High",
      "include_investigations": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 1
  }' | jq '.'
```

#### Submit FOCUS Manual Report Job
```bash
# Create FOCUS manual job
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo FOCUS Manual Report",
    "jobDefinitionUri": "focus-manual",
    "arguments": {
      "reporting_date": "2024-12-01",
      "report_type": "Monthly",
      "entity_type": "Broker-Dealer",
      "include_schedules": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 3
  }' | jq '.'
```

### 4. JOB STATUS MONITORING COMMANDS

#### Check Job Status
```bash
# Replace JOB_ID with actual job ID from submission response
export JOB_ID="your-job-id-here"

# Get current job status
curl -X GET "http://localhost:5001/api/jobs/${JOB_ID}/status" \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: Job status, progress, and message
```

#### Poll Job Status Until Completion
```bash
# Continuous polling script (run this in a loop)
while true; do
  STATUS=$(curl -s -X GET "http://localhost:5001/api/jobs/${JOB_ID}/status" \
    -H "Content-Type: application/json" | jq -r '.status')
  
  echo "Job Status: $STATUS"
  
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" || "$STATUS" == "cancelled" ]]; then
    echo "Job finished with status: $STATUS"
    break
  fi
  
  sleep 2
done
```

### 5. FILE MANAGEMENT COMMANDS

#### List Job Files
```bash
# List all files for a completed job
curl -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files" \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: Array of files with metadata
```

#### Download HTML Report
```bash
# Download HTML report file
curl -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files/report.html" \
  -H "Accept: text/html" \
  -o "downloaded_report.html"

echo "HTML report downloaded as downloaded_report.html"
```

#### Download CSV Data
```bash
# Download CSV data file
curl -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files/data.csv" \
  -H "Accept: text/csv" \
  -o "downloaded_data.csv"

echo "CSV data downloaded as downloaded_data.csv"
```

#### Download PDF Report
```bash
# Download PDF report file
curl -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files/report.pdf" \
  -H "Accept: application/pdf" \
  -o "downloaded_report.pdf"

echo "PDF report downloaded as downloaded_report.pdf"
```

#### Download Excel Spreadsheet
```bash
# Download Excel file
curl -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files/data.xlsx" \
  -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  -o "downloaded_data.xlsx"

echo "Excel file downloaded as downloaded_data.xlsx"
```

### 6. JOB CANCELLATION COMMANDS

#### Cancel Running Job
```bash
# Cancel a job (works for queued or running jobs)
curl -X DELETE "http://localhost:5001/api/jobs/${JOB_ID}" \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: 200 OK with cancellation confirmation
```

### 7. ERROR TESTING COMMANDS

#### Test Invalid Job Submission
```bash
# Submit job with missing required fields
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "jobDefinitionUri": "invalid-report",
    "arguments": {},
    "submitted_by": ""
  }' | jq '.'

# Expected Response: 422 Validation Error
```

#### Test Non-existent Report
```bash
# Submit job with non-existent report ID
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Job",
    "jobDefinitionUri": "non-existent-report",
    "arguments": {},
    "submitted_by": "test_user",
    "priority": 5
  }' | jq '.'

# Expected Response: 404 Report Not Found
```

#### Test Invalid Content Type
```bash
# Submit job with wrong content type
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: text/plain" \
  -d "not json data" \
  | jq '.'

# Expected Response: 400 Invalid Content Type
```

#### Test Non-existent Job Status
```bash
# Check status of non-existent job
curl -X GET "http://localhost:5001/api/jobs/non-existent-job-id/status" \
  -H "Content-Type: application/json" \
  | jq '.'

# Expected Response: 404 Job Not Found
```

### 8. RATE LIMITING TESTING

#### Test Rate Limiting
```bash
# Rapid fire requests to trigger rate limiting
for i in {1..25}; do
  echo "Request $i"
  curl -X GET http://localhost:5000/api/reports \
    -H "Content-Type: application/json" \
    -w "Status: %{http_code}\n" \
    -o /dev/null -s
  sleep 0.1
done

# Expected Response: Eventually 429 Rate Limit Exceeded
```

---

## COMPLETE DEMO WORKFLOW SCRIPT

### Full End-to-End Demo
```bash
#!/bin/bash

echo "=== DataFit CLI Demo Script ==="
echo ""

# 1. Health Checks
echo "1. Checking service health..."
echo "Job Submission Service:"
curl -s -X GET http://localhost:5000/health | jq '.service, .status'
echo ""
echo "Job Polling Service:"
curl -s -X GET http://localhost:5001/health | jq '.service, .status'
echo ""

# 2. Get Available Reports
echo "2. Fetching available reports..."
curl -s -X GET http://localhost:5000/api/reports | jq '.title, (.categories | length)'
echo ""

# 3. Submit a Job
echo "3. Submitting CMBS report job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo CMBS Report",
    "jobDefinitionUri": "cmbs-user-manual",
    "arguments": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "property_type": "Office",
      "include_charts": true,
      "username": "demo_user"
    },
    "submitted_by": "cli_demo",
    "priority": 5
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.id')
echo "Job submitted with ID: $JOB_ID"
echo ""

# 4. Monitor Job Status
echo "4. Monitoring job status..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "http://localhost:5001/api/jobs/${JOB_ID}/status")
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress')
  
  echo "Status: $STATUS, Progress: $PROGRESS%"
  
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" || "$STATUS" == "cancelled" ]]; then
    break
  fi
  
  sleep 3
done
echo ""

# 5. List Generated Files
if [[ "$STATUS" == "completed" ]]; then
  echo "5. Listing generated files..."
  curl -s -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files" | jq '.files[] | .filename'
  echo ""
  
  # 6. Download a File
  echo "6. Downloading HTML report..."
  curl -s -X GET "http://localhost:5001/api/jobs/${JOB_ID}/files/report.html" \
    -o "demo_report.html"
  echo "Downloaded demo_report.html"
else
  echo "5. Job did not complete successfully, skipping file operations."
fi

echo ""
echo "=== Demo Complete ==="
```

---

## TESTING CHECKLIST

### Basic Functionality
- [ ] Health checks return 200 OK
- [ ] Report definitions load successfully
- [ ] Job submission returns valid job ID
- [ ] Job status updates correctly
- [ ] Files are generated and downloadable

### Error Handling
- [ ] Invalid job data returns 422
- [ ] Non-existent report returns 404
- [ ] Wrong content type returns 400
- [ ] Non-existent job returns 404
- [ ] Rate limiting triggers 429

### All Report Types
- [ ] CMBS User Manual report
- [ ] RMBS Performance report
- [ ] VaR Daily report
- [ ] Stress Testing report
- [ ] Trading Activity report
- [ ] AML Alerts report
- [ ] FOCUS Manual report

### File Formats
- [ ] HTML report download
- [ ] PDF report download
- [ ] CSV data download
- [ ] Excel spreadsheet download

### Advanced Features
- [ ] Job cancellation works
- [ ] Multiple concurrent jobs
- [ ] File cleanup after retention
- [ ] Service communication resilience

---

## PERFORMANCE TESTING

### Load Testing Commands
```bash
# Test concurrent job submissions
for i in {1..10}; do
  (curl -X POST http://localhost:5000/api/jobs \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"Load Test Job $i\",
      \"jobDefinitionUri\": \"cmbs-user-manual\",
      \"arguments\": {
        \"start_date\": \"2024-01-01\",
        \"end_date\": \"2024-12-31\",
        \"property_type\": \"Office\",
        \"include_charts\": true,
        \"username\": \"load_test_user\"
      },
      \"submitted_by\": \"load_test\",
      \"priority\": 5
    }" | jq '.id' &)
done
wait
```

### Response Time Testing
```bash
# Measure response times
time curl -X GET http://localhost:5000/health > /dev/null 2>&1
time curl -X GET http://localhost:5000/api/reports > /dev/null 2>&1
```

This comprehensive CLI demo phase provides everything needed to test, demonstrate, and validate the DataFit system functionality through command-line interfaces.