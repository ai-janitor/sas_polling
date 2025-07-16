"""
=============================================================================
REPORTS MODULE INITIALIZATION
=============================================================================
Purpose: Initialize the reports module and provide common imports
Usage: Import this module to access all report generators

AVAILABLE REPORT GENERATORS:
- BaseReport: Abstract base class for all reports
- CMBSUserManualReport: CMBS User Manual generator
- RMBSPerformanceReport: RMBS Performance Analysis generator
- VARDailyReport: Value at Risk Daily Report generator
- StressTestReport: Stress Test Results generator
- TradingActivityReport: Trading Activity Report generator
- AMLAlertsReport: AML Suspicious Activity Alerts generator
- FOCUSManualReport: FOCUS User Manual generator

USAGE EXAMPLE:
    from reports import BaseReport, CMBSUserManualReport
    
    config = load_config()
    report = CMBSUserManualReport(config)
    result = report.run_with_timeout(parameters)
=============================================================================
"""

from .base_report import BaseReport, ReportGenerationError

__version__ = "1.0.0"
__author__ = "DataFit Development Team"

# Export main classes
__all__ = [
    "BaseReport",
    "ReportGenerationError"
]

# Report registry for dynamic loading
REPORT_REGISTRY = {}

def register_report(report_id: str, report_class):
    """Register a report class with an ID for dynamic loading."""
    REPORT_REGISTRY[report_id] = report_class

def get_report_class(report_id: str):
    """Get a report class by ID."""
    return REPORT_REGISTRY.get(report_id)

def list_available_reports():
    """List all registered report IDs."""
    return list(REPORT_REGISTRY.keys())