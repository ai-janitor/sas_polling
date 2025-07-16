# SAS Viya Job Execution API - JSON Structure Examples

## Job Submission Input

```json
{
  "name": "test job submission from OIDS in ACES",
  "jobDefinitionUri": "/jobDefinitions/definitions/1969ed36-131e-46ff-a65b-736c6f9cc337",
  "arguments": {
    "_contextName": "Compute Context",
    "asofqtr": "Q1",
    "year": "2024",
    "sortorder": "Name",
    "outputtp": "XLS",
    "hidden_username": "leelam"
  }
}
```

## Job Submission Response (Initial)

```json
{
  "id": "40d707da-7f09-4723-a0bc-251bc70b8049",
  "state": "running",
  "elapsed_time": 0.235,
  "results": {}
}
```

## Job Completion Response

```json
{
  "id": "40d707da-7f09-4723-a0bc-251bc70b8049",
  "state": "completed",
  "elapsed_time": 7.232,
  "results": {
    "COMPUTE_CONTEXT": "Compute Context",
    "2AE4F0DE-6BB5-8641-A7EF-2DFB6AB950EF.log.txt": "/files/files/b3b94990-6aba-4bae-b123-c92e63022ecc",
    "_webout.xlsx": "/files/files/6931adf0-fb65-4735-b260-c3067e6b8da2",
    "COMPUTE_JOB": "5fe16b8c-90c6-4765-830f-48e08f46462b",
    "COMPUTE_SESSION": "341b4ca9-6e11-4aad-8642-6cac6c845ae4-ses0016 ended."
  }
}
```

## Report Categories Structure

```json
{
  "categories": [
    {
      "name": "datafit Help",
      "subcategories": [
        {
          "name": "Asset-Backed Securities",
          "reports": [
            {
              "name": "CMBS User Manual",
              "id": "1b2e6894-e8d4-4eba-b318-999ca330bb19",
              "prompts": [
                {
                  "hidden_username": {
                    "active": "true",
                    "hide": "true",
                    "inputType": "inputtext",
                    "label": "SEC User Name"
                  }
                }
              ]
            },
            {
              "name": "RMBS Performance Analysis",
              "id": "2c3f7895-f9e5-5fbc-c429-888db441cc28",
              "prompts": [
                {
                  "quarter": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "dropdown",
                    "label": "Quarter",
                    "options": ["Q1", "Q2", "Q3", "Q4"]
                  },
                  "year": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "inputtext",
                    "label": "Year"
                  }
                }
              ]
            }
          ]
        },
        {
          "name": "Risk Management",
          "reports": [
            {
              "name": "VAR Daily Report",
              "id": "3d4e8906-0af6-6gcd-d53a-999ec552dd39",
              "prompts": [
                {
                  "date_from": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "date",
                    "label": "From Date"
                  },
                  "date_to": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "date",
                    "label": "To Date"
                  },
                  "confidence_level": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "dropdown",
                    "label": "Confidence Level",
                    "options": ["95%", "99%", "99.9%"]
                  }
                }
              ]
            },
            {
              "name": "Stress Test Results",
              "id": "4e5f9017-1bg7-7hde-e64b-aaafdd663ee40",
              "prompts": [
                {
                  "scenario": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "dropdown",
                    "label": "Stress Scenario",
                    "options": ["Baseline", "Adverse", "Severely Adverse"]
                  },
                  "output_format": {
                    "active": "true",
                    "hide": "false",
                    "inputType": "dropdown",
                    "label": "Output Format",
                    "options": ["PDF", "XLS", "HTML"]
                  }
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "name": "Finra Data Mart",
      "reports": [
        {
          "name": "FOCUS User Manual",
          "id": "a4a3a357-b346-48a4-b7ca-24ae8f292de7",
          "prompts": []
        },
        {
          "name": "Trading Activity Report",
          "id": "b5b4b468-c457-59b5-c8db-35bf9e403ef8",
          "prompts": [
            {
              "symbol": {
                "active": "true",
                "hide": "false",
                "inputType": "inputtext",
                "label": "Stock Symbol"
              },
              "trade_date": {
                "active": "true",
                "hide": "false",
                "inputType": "date",
                "label": "Trade Date"
              }
            }
          ]
        }
      ]
    },
    {
      "name": "AML Compliance",
      "reports": [
        {
          "name": "Suspicious Activity Alerts",
          "id": "c6c5c579-d568-69c6-d9ec-46cf0f514fg9",
          "prompts": [
            {
              "alert_level": {
                "active": "true",
                "hide": "false",
                "inputType": "dropdown",
                "label": "Alert Level",
                "options": ["Low", "Medium", "High", "Critical"]
              },
              "date_range": {
                "active": "true",
                "hide": "false",
                "inputType": "dropdown",
                "label": "Date Range",
                "options": ["Last 7 days", "Last 30 days", "Last 90 days", "Custom"]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## Requirements

**1-page SPA needed:**
- Job dropdown of reports
- On report selection → expand to show other fields to select
- Submit button → POST to job submission endpoint
- Endpoint returns JSON with UUID for jobid and location of job polling endpoint
- Job polling endpoint returns null until job complete, then returns JSON with path to file download endpoint
- SPA app driven completely by JSON definition of the report
- Need config.dev.env where all scripts, Python, TS, JS files get their values from
- Need 3 Dockerfiles: GUI, job submission service, job polling service
- Reports generate: HTML, Plotly charts, PDF, CSV, XLS
- JSON examples included in this MD file
- Mock CSV data for these reports will rest in the job polling endpoint
- Job polling endpoint keeps FIFO stack of last 100 jobs and links to downloadable files
- Job polling has reports lined up with each report in JSON file that feeds GUI (both in sync)
- Reports folder with Python filename for each report
- Job submission endpoint forwards JSON payload to polling server
- Polling server parses JSON payload to load appropriate Python report with parameters

## Development Plan Summary

**DETAILED PLAN MOVED TO**: `plan-phases.md`

The comprehensive 4-phase development plan with strict requirements, technical details, and implementation guidelines has been moved to a separate file for better organization.

## API Workflow Notes

- **Job Request ID**: Used in URL path for status checking: `<base_url>/jobExecution/jobs/<job_request_id>`
- **Output Files**: Retrieved using file IDs from the results object (e.g., `_webout.xlsx` file)
- **Status States**: `running` → `completed`
- **Expected Start Date**: 23 May 2024

## Report Structure Notes

- **Categories**: Top-level groupings for reports
- **Subcategories**: Optional nested groupings within categories
- **Reports**: Individual report definitions with:
  - `name`: Display name for the report
  - `id`: Unique identifier (likely the jobDefinitionUri)
  - `prompts`: User input parameters with validation rules
- **Prompts**: Input field definitions with:
  - `active`: Whether the field is enabled
  - `hide`: Whether to hide the field from UI
  - `inputType`: Type of input control (inputtext, dropdown, etc.)
  - `label`: Display label for the field