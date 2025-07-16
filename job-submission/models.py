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

import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationError:
    """Validation error model for detailed error reporting"""
    field: str
    message: str
    code: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization"""
        return {
            'field': self.field,
            'message': self.message,
            'code': self.code
        }

class JobRequest:
    """Job submission request model with validation"""
    
    def __init__(self, name: str, jobDefinitionUri: str, arguments: Dict[str, Any], 
                 submitted_by: str, priority: int = 5):
        self.name = name
        self.jobDefinitionUri = jobDefinitionUri
        self.arguments = arguments or {}
        self.submitted_by = submitted_by
        self.priority = priority
        
        # Validate on initialization
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation failed: {[e.message for e in errors]}")
    
    def validate(self) -> List[ValidationError]:
        """Comprehensive validation with detailed error messages"""
        errors = []
        
        # Validate job name
        if not self.name:
            errors.append(ValidationError(
                field='name',
                message='Job name is required',
                code='REQUIRED_FIELD_MISSING'
            ))
        elif not isinstance(self.name, str):
            errors.append(ValidationError(
                field='name',
                message='Job name must be a string',
                code='INVALID_TYPE'
            ))
        elif len(self.name.strip()) == 0:
            errors.append(ValidationError(
                field='name',
                message='Job name cannot be empty',
                code='EMPTY_VALUE'
            ))
        elif len(self.name) > 255:
            errors.append(ValidationError(
                field='name',
                message='Job name cannot exceed 255 characters',
                code='VALUE_TOO_LONG'
            ))
        elif not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', self.name):
            errors.append(ValidationError(
                field='name',
                message='Job name contains invalid characters (only alphanumeric, spaces, hyphens, underscores, and dots allowed)',
                code='INVALID_FORMAT'
            ))
        
        # Validate jobDefinitionUri
        if not self.jobDefinitionUri:
            errors.append(ValidationError(
                field='jobDefinitionUri',
                message='Report ID is required',
                code='REQUIRED_FIELD_MISSING'
            ))
        elif not isinstance(self.jobDefinitionUri, str):
            errors.append(ValidationError(
                field='jobDefinitionUri',
                message='Report ID must be a string',
                code='INVALID_TYPE'
            ))
        elif len(self.jobDefinitionUri.strip()) == 0:
            errors.append(ValidationError(
                field='jobDefinitionUri',
                message='Report ID cannot be empty',
                code='EMPTY_VALUE'
            ))
        
        # Validate arguments
        if not isinstance(self.arguments, dict):
            errors.append(ValidationError(
                field='arguments',
                message='Arguments must be a dictionary',
                code='INVALID_TYPE'
            ))
        
        # Validate submitted_by
        if not self.submitted_by:
            errors.append(ValidationError(
                field='submitted_by',
                message='Submitted by field is required',
                code='REQUIRED_FIELD_MISSING'
            ))
        elif not isinstance(self.submitted_by, str):
            errors.append(ValidationError(
                field='submitted_by',
                message='Submitted by must be a string',
                code='INVALID_TYPE'
            ))
        elif len(self.submitted_by.strip()) == 0:
            errors.append(ValidationError(
                field='submitted_by',
                message='Submitted by cannot be empty',
                code='EMPTY_VALUE'
            ))
        
        # Validate priority
        if not isinstance(self.priority, int):
            errors.append(ValidationError(
                field='priority',
                message='Priority must be an integer',
                code='INVALID_TYPE'
            ))
        elif self.priority < 1 or self.priority > 10:
            errors.append(ValidationError(
                field='priority',
                message='Priority must be between 1 and 10',
                code='VALUE_OUT_OF_RANGE'
            ))
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'jobDefinitionUri': self.jobDefinitionUri,
            'arguments': self.arguments,
            'submitted_by': self.submitted_by,
            'priority': self.priority
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobRequest':
        """Create instance from dictionary"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        return cls(
            name=data.get('name', ''),
            jobDefinitionUri=data.get('jobDefinitionUri', ''),
            arguments=data.get('arguments', {}),
            submitted_by=data.get('submitted_by', ''),
            priority=data.get('priority', 5)
        )

class JobResponse:
    """Job submission response model"""
    
    def __init__(self, id: str, status: str, polling_url: str, estimated_duration: int = 60):
        self.id = id
        self.status = status
        self.polling_url = polling_url
        self.estimated_duration = estimated_duration
        self.created_at = datetime.now().isoformat()
        
        # Validate on initialization
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation failed: {[e.message for e in errors]}")
    
    def validate(self) -> List[ValidationError]:
        """Validate response data"""
        errors = []
        
        # Validate ID
        if not self.id:
            errors.append(ValidationError(
                field='id',
                message='Job ID is required',
                code='REQUIRED_FIELD_MISSING'
            ))
        elif not isinstance(self.id, str):
            errors.append(ValidationError(
                field='id',
                message='Job ID must be a string',
                code='INVALID_TYPE'
            ))
        
        # Validate status
        valid_statuses = ['submitted', 'queued', 'running', 'completed', 'failed', 'cancelled']
        if not self.status:
            errors.append(ValidationError(
                field='status',
                message='Status is required',
                code='REQUIRED_FIELD_MISSING'
            ))
        elif self.status not in valid_statuses:
            errors.append(ValidationError(
                field='status',
                message=f'Status must be one of: {", ".join(valid_statuses)}',
                code='INVALID_VALUE'
            ))
        
        # Validate polling_url
        if not self.polling_url:
            errors.append(ValidationError(
                field='polling_url',
                message='Polling URL is required',
                code='REQUIRED_FIELD_MISSING'
            ))
        elif not isinstance(self.polling_url, str):
            errors.append(ValidationError(
                field='polling_url',
                message='Polling URL must be a string',
                code='INVALID_TYPE'
            ))
        elif not self.polling_url.startswith(('http://', 'https://')):
            errors.append(ValidationError(
                field='polling_url',
                message='Polling URL must be a valid HTTP/HTTPS URL',
                code='INVALID_FORMAT'
            ))
        
        # Validate estimated_duration
        if not isinstance(self.estimated_duration, int):
            errors.append(ValidationError(
                field='estimated_duration',
                message='Estimated duration must be an integer',
                code='INVALID_TYPE'
            ))
        elif self.estimated_duration < 0:
            errors.append(ValidationError(
                field='estimated_duration',
                message='Estimated duration must be non-negative',
                code='VALUE_OUT_OF_RANGE'
            ))
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'status': self.status,
            'polling_url': self.polling_url,
            'estimated_duration': self.estimated_duration,
            'created_at': self.created_at
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobResponse':
        """Create instance from dictionary"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        return cls(
            id=data.get('id', ''),
            status=data.get('status', ''),
            polling_url=data.get('polling_url', ''),
            estimated_duration=data.get('estimated_duration', 60)
        )

class JobStatus:
    """Job status model for polling responses"""
    
    def __init__(self, id: str, status: str, progress: int = 0, 
                 message: str = '', estimated_completion: Optional[str] = None,
                 files: Optional[List[Dict[str, Any]]] = None):
        self.id = id
        self.status = status
        self.progress = progress
        self.message = message
        self.estimated_completion = estimated_completion
        self.files = files or []
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'estimated_completion': self.estimated_completion,
            'files': self.files,
            'last_updated': self.last_updated
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobStatus':
        """Create instance from dictionary"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        return cls(
            id=data.get('id', ''),
            status=data.get('status', ''),
            progress=data.get('progress', 0),
            message=data.get('message', ''),
            estimated_completion=data.get('estimated_completion'),
            files=data.get('files', [])
        )