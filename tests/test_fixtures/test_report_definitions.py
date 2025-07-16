"""
=============================================================================
REPORT DEFINITIONS FIXTURES UNIT TESTS
=============================================================================
Purpose: Unit tests for report definition fixtures and templates
Module: tests/fixtures/report_definitions.py

TEST CATEGORIES:
1. Report Template Validation
2. Parameter Schema Testing
3. Output Format Testing
4. Fixture Data Integrity
=============================================================================
"""

import pytest
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os
from jsonschema import validate, ValidationError

class ReportDefinition:
    """Report definition with validation and template management."""
    
    def __init__(self, report_id, name, description, category):
        self.report_id = report_id
        self.name = name
        self.description = description
        self.category = category
        self.parameters = {}
        self.output_formats = []
        self.template_config = {}
        self.validation_rules = {}
    
    def add_parameter(self, param_name, param_type, required=True, default=None, description="", validation=None):
        """Add a parameter definition to the report."""
        parameter = {
            'type': param_type,
            'required': required,
            'default': default,
            'description': description,
            'validation': validation or {}
        }
        self.parameters[param_name] = parameter
    
    def add_output_format(self, format_type, filename_template, content_type, options=None):
        """Add an output format definition."""
        output_format = {
            'type': format_type,
            'filename_template': filename_template,
            'content_type': content_type,
            'options': options or {}
        }
        self.output_formats.append(output_format)
    
    def set_template_config(self, template_path, template_engine='jinja2', options=None):
        """Set template configuration."""
        self.template_config = {
            'template_path': template_path,
            'template_engine': template_engine,
            'options': options or {}
        }
    
    def validate_parameters(self, provided_params):
        """Validate provided parameters against the definition."""
        errors = []
        
        # Check required parameters
        for param_name, param_def in self.parameters.items():
            if param_def['required'] and param_name not in provided_params:
                errors.append(f"Required parameter '{param_name}' is missing")
        
        # Validate parameter types and values
        for param_name, param_value in provided_params.items():
            if param_name not in self.parameters:
                errors.append(f"Unknown parameter '{param_name}'")
                continue
            
            param_def = self.parameters[param_name]
            validation_error = self._validate_parameter_value(param_name, param_value, param_def)
            if validation_error:
                errors.append(validation_error)
        
        return errors
    
    def _validate_parameter_value(self, param_name, value, param_def):
        """Validate a single parameter value."""
        expected_type = param_def['type']
        
        # Type validation
        if expected_type == 'string' and not isinstance(value, str):
            return f"Parameter '{param_name}' must be a string"
        elif expected_type == 'integer' and not isinstance(value, int):
            return f"Parameter '{param_name}' must be an integer"
        elif expected_type == 'number' and not isinstance(value, (int, float)):
            return f"Parameter '{param_name}' must be a number"
        elif expected_type == 'boolean' and not isinstance(value, bool):
            return f"Parameter '{param_name}' must be a boolean"
        elif expected_type == 'date' and not self._is_valid_date_string(value):
            return f"Parameter '{param_name}' must be a valid date string (YYYY-MM-DD)"
        elif expected_type == 'array' and not isinstance(value, list):
            return f"Parameter '{param_name}' must be an array"
        
        # Custom validation rules
        validation_rules = param_def.get('validation', {})
        
        if 'min_length' in validation_rules and len(str(value)) < validation_rules['min_length']:
            return f"Parameter '{param_name}' must be at least {validation_rules['min_length']} characters"
        
        if 'max_length' in validation_rules and len(str(value)) > validation_rules['max_length']:
            return f"Parameter '{param_name}' must be at most {validation_rules['max_length']} characters"
        
        if 'min_value' in validation_rules and value < validation_rules['min_value']:
            return f"Parameter '{param_name}' must be at least {validation_rules['min_value']}"
        
        if 'max_value' in validation_rules and value > validation_rules['max_value']:
            return f"Parameter '{param_name}' must be at most {validation_rules['max_value']}"
        
        if 'allowed_values' in validation_rules and value not in validation_rules['allowed_values']:
            return f"Parameter '{param_name}' must be one of: {validation_rules['allowed_values']}"
        
        if 'pattern' in validation_rules:
            import re
            if not re.match(validation_rules['pattern'], str(value)):
                return f"Parameter '{param_name}' does not match required pattern"
        
        return None
    
    def _is_valid_date_string(self, date_string):
        """Validate date string format."""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def generate_filename(self, format_type, parameters):
        """Generate filename based on template and parameters."""
        format_def = next((f for f in self.output_formats if f['type'] == format_type), None)
        if not format_def:
            raise ValueError(f"Output format '{format_type}' not defined")
        
        template = format_def['filename_template']
        
        # Simple template variable replacement
        for param_name, param_value in parameters.items():
            placeholder = f"{{{param_name}}}"
            template = template.replace(placeholder, str(param_value))
        
        # Replace common placeholders
        template = template.replace('{timestamp}', datetime.now().strftime('%Y%m%d_%H%M%S'))
        template = template.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
        
        return template
    
    def to_dict(self):
        """Convert report definition to dictionary."""
        return {
            'report_id': self.report_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'parameters': self.parameters,
            'output_formats': self.output_formats,
            'template_config': self.template_config,
            'validation_rules': self.validation_rules
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create report definition from dictionary."""
        report = cls(
            report_id=data['report_id'],
            name=data['name'],
            description=data['description'],
            category=data['category']
        )
        report.parameters = data.get('parameters', {})
        report.output_formats = data.get('output_formats', [])
        report.template_config = data.get('template_config', {})
        report.validation_rules = data.get('validation_rules', {})
        return report


class ReportDefinitionManager:
    """Manage collection of report definitions."""
    
    def __init__(self):
        self.definitions = {}
        self.categories = set()
    
    def register_definition(self, definition):
        """Register a report definition."""
        if not isinstance(definition, ReportDefinition):
            raise ValueError("Definition must be a ReportDefinition instance")
        
        self.definitions[definition.report_id] = definition
        self.categories.add(definition.category)
    
    def get_definition(self, report_id):
        """Get a report definition by ID."""
        return self.definitions.get(report_id)
    
    def get_definitions_by_category(self, category):
        """Get all definitions in a category."""
        return [defn for defn in self.definitions.values() if defn.category == category]
    
    def list_all_definitions(self):
        """List all registered definitions."""
        return list(self.definitions.values())
    
    def export_definitions(self, file_path, format='json'):
        """Export definitions to file."""
        data = {
            'definitions': [defn.to_dict() for defn in self.definitions.values()],
            'categories': list(self.categories),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            if format.lower() == 'json':
                json.dump(data, f, indent=2)
            elif format.lower() == 'yaml':
                yaml.dump(data, f, default_flow_style=False)
            else:
                raise ValueError("Format must be 'json' or 'yaml'")
    
    def import_definitions(self, file_path):
        """Import definitions from file."""
        with open(file_path, 'r') as f:
            if file_path.endswith('.json'):
                data = json.load(f)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                raise ValueError("File must be .json, .yaml, or .yml")
        
        for defn_data in data.get('definitions', []):
            definition = ReportDefinition.from_dict(defn_data)
            self.register_definition(definition)


class ReportFixtureFactory:
    """Factory for creating report test fixtures."""
    
    @staticmethod
    def create_cmbs_report_definition():
        """Create CMBS report definition fixture."""
        report = ReportDefinition(
            report_id='cmbs_user_manual',
            name='CMBS User Manual Report',
            description='Commercial Mortgage-Backed Securities analysis and user manual',
            category='RISK_MANAGEMENT'
        )
        
        # Add parameters
        report.add_parameter('analysis_date', 'date', required=True, 
                           description='Date for the analysis')
        report.add_parameter('portfolio_id', 'string', required=True,
                           description='Portfolio identifier',
                           validation={'pattern': r'^PORT\d{6}$'})
        report.add_parameter('include_stress_tests', 'boolean', required=False, default=True,
                           description='Include stress testing scenarios')
        report.add_parameter('stress_scenarios', 'array', required=False,
                           default=['mild', 'moderate', 'severe'],
                           description='List of stress test scenarios')
        
        # Add output formats
        report.add_output_format('html', 'cmbs_manual_{portfolio_id}_{date}.html', 
                               'text/html', {'charts': True, 'interactive': True})
        report.add_output_format('pdf', 'cmbs_manual_{portfolio_id}_{date}.pdf',
                               'application/pdf', {'page_size': 'A4', 'orientation': 'portrait'})
        report.add_output_format('json', 'cmbs_data_{portfolio_id}_{date}.json',
                               'application/json', {'pretty_print': True})
        
        # Set template config
        report.set_template_config('templates/cmbs_manual.html', 'jinja2',
                                 {'auto_escape': True, 'trim_blocks': True})
        
        return report
    
    @staticmethod
    def create_rmbs_performance_definition():
        """Create RMBS performance report definition fixture."""
        report = ReportDefinition(
            report_id='rmbs_performance',
            name='RMBS Performance Analysis',
            description='Residential Mortgage-Backed Securities performance analysis',
            category='PERFORMANCE_ANALYTICS'
        )
        
        # Add parameters
        report.add_parameter('analysis_date', 'date', required=True)
        report.add_parameter('portfolio_id', 'string', required=True,
                           validation={'min_length': 5, 'max_length': 20})
        report.add_parameter('benchmark', 'string', required=False, default='MBS_INDEX',
                           validation={'allowed_values': ['MBS_INDEX', 'TREASURY', 'CORPORATE']})
        report.add_parameter('lookback_months', 'integer', required=False, default=12,
                           validation={'min_value': 1, 'max_value': 60})
        
        # Add output formats
        report.add_output_format('html', 'rmbs_performance_{portfolio_id}_{timestamp}.html',
                               'text/html')
        report.add_output_format('excel', 'rmbs_performance_{portfolio_id}_{date}.xlsx',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        return report
    
    @staticmethod
    def create_var_daily_definition():
        """Create VaR daily report definition fixture."""
        report = ReportDefinition(
            report_id='var_daily',
            name='Value at Risk Daily Report',
            description='Daily Value at Risk calculation and analysis',
            category='RISK_MANAGEMENT'
        )
        
        # Add parameters
        report.add_parameter('calculation_date', 'date', required=True)
        report.add_parameter('portfolio_id', 'string', required=True)
        report.add_parameter('confidence_level', 'number', required=False, default=0.95,
                           validation={'min_value': 0.90, 'max_value': 0.99})
        report.add_parameter('method', 'string', required=False, default='HISTORICAL',
                           validation={'allowed_values': ['HISTORICAL', 'PARAMETRIC', 'MONTE_CARLO']})
        report.add_parameter('lookback_days', 'integer', required=False, default=252,
                           validation={'min_value': 30, 'max_value': 1000})
        
        # Add output formats
        report.add_output_format('json', 'var_daily_{calculation_date}.json', 'application/json')
        report.add_output_format('csv', 'var_daily_{calculation_date}.csv', 'text/csv')
        
        return report
    
    @staticmethod
    def create_aml_alerts_definition():
        """Create AML alerts report definition fixture."""
        report = ReportDefinition(
            report_id='aml_alerts',
            name='Anti-Money Laundering Alerts',
            description='AML transaction monitoring and alerts report',
            category='COMPLIANCE'
        )
        
        # Add parameters
        report.add_parameter('report_date', 'date', required=True)
        report.add_parameter('jurisdiction', 'string', required=True,
                           validation={'allowed_values': ['US', 'EU', 'UK', 'APAC', 'GLOBAL']})
        report.add_parameter('alert_severity', 'string', required=False, default='ALL',
                           validation={'allowed_values': ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'ALL']})
        report.add_parameter('include_false_positives', 'boolean', required=False, default=False)
        
        # Add output formats
        report.add_output_format('json', 'aml_alerts_{report_date}_{jurisdiction}.json',
                               'application/json')
        report.add_output_format('xml', 'aml_alerts_{report_date}_{jurisdiction}.xml',
                               'application/xml')
        
        return report


class ReportSchemaValidator:
    """Validate report definitions against JSON schemas."""
    
    PARAMETER_SCHEMA = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["string", "integer", "number", "boolean", "date", "array"]},
            "required": {"type": "boolean"},
            "default": {},
            "description": {"type": "string"},
            "validation": {
                "type": "object",
                "properties": {
                    "min_length": {"type": "integer", "minimum": 0},
                    "max_length": {"type": "integer", "minimum": 0},
                    "min_value": {"type": "number"},
                    "max_value": {"type": "number"},
                    "allowed_values": {"type": "array"},
                    "pattern": {"type": "string"}
                },
                "additionalProperties": False
            }
        },
        "required": ["type", "required"],
        "additionalProperties": False
    }
    
    OUTPUT_FORMAT_SCHEMA = {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "filename_template": {"type": "string"},
            "content_type": {"type": "string"},
            "options": {"type": "object"}
        },
        "required": ["type", "filename_template", "content_type"],
        "additionalProperties": False
    }
    
    REPORT_DEFINITION_SCHEMA = {
        "type": "object",
        "properties": {
            "report_id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "description": {"type": "string"},
            "category": {"type": "string", "minLength": 1},
            "parameters": {
                "type": "object",
                "additionalProperties": PARAMETER_SCHEMA
            },
            "output_formats": {
                "type": "array",
                "items": OUTPUT_FORMAT_SCHEMA
            },
            "template_config": {"type": "object"},
            "validation_rules": {"type": "object"}
        },
        "required": ["report_id", "name", "description", "category"],
        "additionalProperties": False
    }
    
    @classmethod
    def validate_parameter(cls, parameter_def):
        """Validate a parameter definition."""
        try:
            validate(parameter_def, cls.PARAMETER_SCHEMA)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @classmethod
    def validate_output_format(cls, output_format):
        """Validate an output format definition."""
        try:
            validate(output_format, cls.OUTPUT_FORMAT_SCHEMA)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @classmethod
    def validate_report_definition(cls, report_def_dict):
        """Validate a complete report definition."""
        try:
            validate(report_def_dict, cls.REPORT_DEFINITION_SCHEMA)
            return True, None
        except ValidationError as e:
            return False, str(e)


class TestReportDefinition:
    @pytest.fixture
    def basic_report(self):
        return ReportDefinition(
            report_id='test_report',
            name='Test Report',
            description='A test report for unit testing',
            category='TEST'
        )
    
    @pytest.mark.unit
    def test_report_creation(self, basic_report):
        assert basic_report.report_id == 'test_report'
        assert basic_report.name == 'Test Report'
        assert basic_report.category == 'TEST'
        assert len(basic_report.parameters) == 0
        assert len(basic_report.output_formats) == 0
    
    @pytest.mark.unit
    def test_add_parameter(self, basic_report):
        basic_report.add_parameter(
            'start_date', 'date', required=True, 
            description='Start date for analysis',
            validation={'pattern': r'^\d{4}-\d{2}-\d{2}$'}
        )
        
        assert 'start_date' in basic_report.parameters
        param = basic_report.parameters['start_date']
        assert param['type'] == 'date'
        assert param['required'] is True
        assert param['validation']['pattern'] == r'^\d{4}-\d{2}-\d{2}$'
    
    @pytest.mark.unit
    def test_add_output_format(self, basic_report):
        basic_report.add_output_format(
            'pdf', 'report_{date}.pdf', 'application/pdf',
            options={'page_size': 'A4'}
        )
        
        assert len(basic_report.output_formats) == 1
        format_def = basic_report.output_formats[0]
        assert format_def['type'] == 'pdf'
        assert format_def['filename_template'] == 'report_{date}.pdf'
        assert format_def['options']['page_size'] == 'A4'
    
    @pytest.mark.unit
    def test_parameter_validation_success(self, basic_report):
        basic_report.add_parameter('name', 'string', required=True)
        basic_report.add_parameter('count', 'integer', required=False, default=10)
        
        params = {'name': 'test_name', 'count': 5}
        errors = basic_report.validate_parameters(params)
        
        assert len(errors) == 0
    
    @pytest.mark.unit
    def test_parameter_validation_missing_required(self, basic_report):
        basic_report.add_parameter('required_param', 'string', required=True)
        
        params = {'optional_param': 'value'}
        errors = basic_report.validate_parameters(params)
        
        assert len(errors) > 0
        assert any('required_param' in error for error in errors)
    
    @pytest.mark.unit
    def test_parameter_validation_type_error(self, basic_report):
        basic_report.add_parameter('number_param', 'integer', required=True)
        
        params = {'number_param': 'not_a_number'}
        errors = basic_report.validate_parameters(params)
        
        assert len(errors) > 0
        assert any('must be an integer' in error for error in errors)
    
    @pytest.mark.unit
    def test_parameter_validation_custom_rules(self, basic_report):
        basic_report.add_parameter(
            'code', 'string', required=True,
            validation={'min_length': 5, 'max_length': 10, 'pattern': r'^[A-Z]+$'}
        )
        
        # Test too short
        errors = basic_report.validate_parameters({'code': 'ABC'})
        assert any('at least 5 characters' in error for error in errors)
        
        # Test too long
        errors = basic_report.validate_parameters({'code': 'ABCDEFGHIJK'})
        assert any('at most 10 characters' in error for error in errors)
        
        # Test pattern mismatch
        errors = basic_report.validate_parameters({'code': 'abc123'})
        assert any('does not match required pattern' in error for error in errors)
        
        # Test valid
        errors = basic_report.validate_parameters({'code': 'ABCDEF'})
        assert len(errors) == 0
    
    @pytest.mark.unit
    def test_filename_generation(self, basic_report):
        basic_report.add_output_format('html', 'report_{portfolio_id}_{date}.html', 'text/html')
        
        params = {'portfolio_id': 'PORT123456'}
        filename = basic_report.generate_filename('html', params)
        
        assert 'PORT123456' in filename
        assert filename.endswith('.html')
        assert '{date}' not in filename  # Should be replaced
    
    @pytest.mark.unit
    def test_to_dict_conversion(self, basic_report):
        basic_report.add_parameter('test_param', 'string', required=True)
        basic_report.add_output_format('json', 'test.json', 'application/json')
        
        report_dict = basic_report.to_dict()
        
        assert report_dict['report_id'] == 'test_report'
        assert 'test_param' in report_dict['parameters']
        assert len(report_dict['output_formats']) == 1
    
    @pytest.mark.unit
    def test_from_dict_creation(self):
        data = {
            'report_id': 'dict_report',
            'name': 'Dict Report',
            'description': 'Report from dict',
            'category': 'TEST',
            'parameters': {
                'param1': {'type': 'string', 'required': True}
            },
            'output_formats': [
                {'type': 'json', 'filename_template': 'test.json', 'content_type': 'application/json'}
            ]
        }
        
        report = ReportDefinition.from_dict(data)
        
        assert report.report_id == 'dict_report'
        assert 'param1' in report.parameters
        assert len(report.output_formats) == 1


class TestReportDefinitionManager:
    @pytest.fixture
    def manager(self):
        return ReportDefinitionManager()
    
    @pytest.fixture
    def sample_definitions(self):
        return [
            ReportFixtureFactory.create_cmbs_report_definition(),
            ReportFixtureFactory.create_rmbs_performance_definition(),
            ReportFixtureFactory.create_var_daily_definition()
        ]
    
    @pytest.mark.unit
    def test_register_definition(self, manager, sample_definitions):
        definition = sample_definitions[0]
        manager.register_definition(definition)
        
        assert definition.report_id in manager.definitions
        assert definition.category in manager.categories
    
    @pytest.mark.unit
    def test_get_definition(self, manager, sample_definitions):
        definition = sample_definitions[0]
        manager.register_definition(definition)
        
        retrieved = manager.get_definition(definition.report_id)
        assert retrieved is definition
        
        # Test non-existent
        assert manager.get_definition('nonexistent') is None
    
    @pytest.mark.unit
    def test_get_definitions_by_category(self, manager, sample_definitions):
        for definition in sample_definitions:
            manager.register_definition(definition)
        
        risk_reports = manager.get_definitions_by_category('RISK_MANAGEMENT')
        risk_report_ids = [r.report_id for r in risk_reports]
        
        assert 'cmbs_user_manual' in risk_report_ids
        assert 'var_daily' in risk_report_ids
        assert 'rmbs_performance' not in risk_report_ids  # Different category
    
    @pytest.mark.unit
    def test_export_import_definitions(self, manager, sample_definitions):
        # Register definitions
        for definition in sample_definitions:
            manager.register_definition(definition)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager.export_definitions(temp_path, format='json')
            
            # Create new manager and import
            new_manager = ReportDefinitionManager()
            new_manager.import_definitions(temp_path)
            
            # Verify import
            assert len(new_manager.definitions) == len(manager.definitions)
            for report_id in manager.definitions:
                assert report_id in new_manager.definitions
                
        finally:
            os.unlink(temp_path)


class TestReportFixtureFactory:
    @pytest.mark.unit
    def test_create_cmbs_report_definition(self):
        report = ReportFixtureFactory.create_cmbs_report_definition()
        
        assert report.report_id == 'cmbs_user_manual'
        assert report.category == 'RISK_MANAGEMENT'
        assert 'analysis_date' in report.parameters
        assert 'portfolio_id' in report.parameters
        assert len(report.output_formats) >= 2
        
        # Test parameter validation
        valid_params = {
            'analysis_date': '2024-06-30',
            'portfolio_id': 'PORT123456'
        }
        errors = report.validate_parameters(valid_params)
        assert len(errors) == 0
    
    @pytest.mark.unit
    def test_create_rmbs_performance_definition(self):
        report = ReportFixtureFactory.create_rmbs_performance_definition()
        
        assert report.report_id == 'rmbs_performance'
        assert report.category == 'PERFORMANCE_ANALYTICS'
        assert 'benchmark' in report.parameters
        
        # Test allowed values validation
        valid_params = {
            'analysis_date': '2024-06-30',
            'portfolio_id': 'RMBS_TEST',
            'benchmark': 'TREASURY'
        }
        errors = report.validate_parameters(valid_params)
        assert len(errors) == 0
        
        # Test invalid benchmark
        invalid_params = valid_params.copy()
        invalid_params['benchmark'] = 'INVALID_BENCHMARK'
        errors = report.validate_parameters(invalid_params)
        assert len(errors) > 0
    
    @pytest.mark.unit
    def test_create_var_daily_definition(self):
        report = ReportFixtureFactory.create_var_daily_definition()
        
        assert report.report_id == 'var_daily'
        assert 'confidence_level' in report.parameters
        
        # Test numeric validation
        valid_params = {
            'calculation_date': '2024-06-30',
            'portfolio_id': 'PORT123',
            'confidence_level': 0.95
        }
        errors = report.validate_parameters(valid_params)
        assert len(errors) == 0
        
        # Test out of range confidence level
        invalid_params = valid_params.copy()
        invalid_params['confidence_level'] = 1.5
        errors = report.validate_parameters(invalid_params)
        assert len(errors) > 0
    
    @pytest.mark.unit
    def test_create_aml_alerts_definition(self):
        report = ReportFixtureFactory.create_aml_alerts_definition()
        
        assert report.report_id == 'aml_alerts'
        assert report.category == 'COMPLIANCE'
        assert 'jurisdiction' in report.parameters
        
        # Test filename generation
        params = {
            'report_date': '2024-06-30',
            'jurisdiction': 'US'
        }
        filename = report.generate_filename('json', params)
        assert 'US' in filename
        assert '2024-06-30' in filename


class TestReportSchemaValidator:
    @pytest.mark.unit
    def test_validate_parameter_schema(self):
        # Valid parameter
        valid_param = {
            'type': 'string',
            'required': True,
            'default': 'test',
            'description': 'Test parameter',
            'validation': {
                'min_length': 1,
                'max_length': 100
            }
        }
        
        is_valid, error = ReportSchemaValidator.validate_parameter(valid_param)
        assert is_valid
        assert error is None
        
        # Invalid parameter (missing required field)
        invalid_param = {
            'type': 'string'
            # Missing 'required' field
        }
        
        is_valid, error = ReportSchemaValidator.validate_parameter(invalid_param)
        assert not is_valid
        assert error is not None
    
    @pytest.mark.unit
    def test_validate_output_format_schema(self):
        # Valid output format
        valid_format = {
            'type': 'pdf',
            'filename_template': 'report_{date}.pdf',
            'content_type': 'application/pdf',
            'options': {'page_size': 'A4'}
        }
        
        is_valid, error = ReportSchemaValidator.validate_output_format(valid_format)
        assert is_valid
        assert error is None
        
        # Invalid format (missing required field)
        invalid_format = {
            'type': 'pdf',
            'filename_template': 'report.pdf'
            # Missing 'content_type'
        }
        
        is_valid, error = ReportSchemaValidator.validate_output_format(invalid_format)
        assert not is_valid
        assert error is not None
    
    @pytest.mark.unit
    def test_validate_complete_report_definition(self):
        report = ReportFixtureFactory.create_cmbs_report_definition()
        report_dict = report.to_dict()
        
        is_valid, error = ReportSchemaValidator.validate_report_definition(report_dict)
        assert is_valid
        assert error is None
    
    @pytest.mark.integration
    def test_complete_fixture_workflow(self):
        """Test complete workflow of creating, validating, and using report fixtures."""
        # Create manager and add fixtures
        manager = ReportDefinitionManager()
        
        # Add all fixture definitions
        fixtures = [
            ReportFixtureFactory.create_cmbs_report_definition(),
            ReportFixtureFactory.create_rmbs_performance_definition(),
            ReportFixtureFactory.create_var_daily_definition(),
            ReportFixtureFactory.create_aml_alerts_definition()
        ]
        
        for fixture in fixtures:
            # Validate definition before registering
            report_dict = fixture.to_dict()
            is_valid, error = ReportSchemaValidator.validate_report_definition(report_dict)
            assert is_valid, f"Fixture {fixture.report_id} failed validation: {error}"
            
            # Register definition
            manager.register_definition(fixture)
        
        # Test retrieval and usage
        cmbs_report = manager.get_definition('cmbs_user_manual')
        assert cmbs_report is not None
        
        # Test parameter validation
        test_params = {
            'analysis_date': '2024-06-30',
            'portfolio_id': 'PORT123456',
            'include_stress_tests': True
        }
        
        errors = cmbs_report.validate_parameters(test_params)
        assert len(errors) == 0
        
        # Test filename generation
        filename = cmbs_report.generate_filename('html', test_params)
        assert 'PORT123456' in filename
        assert filename.endswith('.html')
        
        # Test export/import cycle
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager.export_definitions(temp_path)
            
            # Import into new manager
            new_manager = ReportDefinitionManager()
            new_manager.import_definitions(temp_path)
            
            # Verify all definitions were imported correctly
            assert len(new_manager.definitions) == len(fixtures)
            for fixture in fixtures:
                imported_def = new_manager.get_definition(fixture.report_id)
                assert imported_def is not None
                assert imported_def.name == fixture.name
                assert imported_def.category == fixture.category
                
        finally:
            os.unlink(temp_path)