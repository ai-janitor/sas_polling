"""
=============================================================================
INFRASTRUCTURE CONFIGURATION UNIT TESTS
=============================================================================
Purpose: Unit tests for system configuration management
Module: infrastructure/config.py

TEST CATEGORIES:
1. Configuration Loading
2. Environment Variable Handling
3. Configuration Validation
4. Security Settings
=============================================================================
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

class ConfigManager:
    """Configuration management system."""
    
    def __init__(self, config_path=None):
        self.config_path = config_path or "config/app_config.json"
        self.config_data = {}
        self.env_overrides = {}
        self.required_keys = [
            'database.host', 'database.port', 'database.name',
            'redis.host', 'redis.port',
            'app.secret_key', 'app.debug_mode',
            'logging.level', 'logging.file_path'
        ]
    
    def load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
        
        return self.config_data
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.name',
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            'SECRET_KEY': 'app.secret_key',
            'DEBUG_MODE': 'app.debug_mode',
            'LOG_LEVEL': 'logging.level'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_key, self._convert_env_value(env_value))
                self.env_overrides[config_key] = env_value
    
    def _set_nested_value(self, key_path, value):
        """Set a nested configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.config_data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _convert_env_value(self, value):
        """Convert environment variable string to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_config(self):
        """Validate required configuration keys."""
        missing_keys = []
        
        for required_key in self.required_keys:
            if not self._has_nested_key(required_key):
                missing_keys.append(required_key)
        
        if missing_keys:
            raise ConfigurationError(f"Missing required configuration keys: {', '.join(missing_keys)}")
        
        # Validate specific values
        self._validate_database_config()
        self._validate_security_config()
        self._validate_logging_config()
    
    def _has_nested_key(self, key_path):
        """Check if a nested key exists using dot notation."""
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return True
        except (KeyError, TypeError):
            return False
    
    def _validate_database_config(self):
        """Validate database configuration."""
        db_config = self.config_data.get('database', {})
        
        # Validate port range
        port = db_config.get('port')
        if not isinstance(port, int) or not (1 <= port <= 65535):
            raise ConfigurationError(f"Invalid database port: {port}")
        
        # Validate host format
        host = db_config.get('host', '')
        if not host or len(host.strip()) == 0:
            raise ConfigurationError("Database host cannot be empty")
    
    def _validate_security_config(self):
        """Validate security configuration."""
        app_config = self.config_data.get('app', {})
        
        # Validate secret key
        secret_key = app_config.get('secret_key', '')
        if len(secret_key) < 32:
            raise ConfigurationError("Secret key must be at least 32 characters long")
        
        # Check for debug mode in production
        debug_mode = app_config.get('debug_mode', False)
        env = app_config.get('environment', 'development')
        if debug_mode and env == 'production':
            raise ConfigurationError("Debug mode should not be enabled in production")
    
    def _validate_logging_config(self):
        """Validate logging configuration."""
        logging_config = self.config_data.get('logging', {})
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = logging_config.get('level', '').upper()
        if log_level not in valid_levels:
            raise ConfigurationError(f"Invalid log level: {log_level}. Must be one of {valid_levels}")
        
        # Validate log file path
        log_path = logging_config.get('file_path', '')
        if log_path:
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except OSError as e:
                    raise ConfigurationError(f"Cannot create log directory: {e}")
    
    def get(self, key_path, default=None):
        """Get a configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_database_url(self):
        """Generate database connection URL."""
        db_config = self.config_data.get('database', {})
        
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 5432)
        name = db_config.get('name', 'datafit')
        user = db_config.get('user', 'datafit_user')
        password = db_config.get('password', '')
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            return f"postgresql://{user}@{host}:{port}/{name}"
    
    def get_redis_url(self):
        """Generate Redis connection URL."""
        redis_config = self.config_data.get('redis', {})
        
        host = redis_config.get('host', 'localhost')
        port = redis_config.get('port', 6379)
        db = redis_config.get('db', 0)
        password = redis_config.get('password', '')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"
    
    def is_production(self):
        """Check if running in production environment."""
        return self.get('app.environment', 'development') == 'production'
    
    def is_debug_enabled(self):
        """Check if debug mode is enabled."""
        return self.get('app.debug_mode', False)
    
    def get_env_overrides(self):
        """Get dictionary of environment variable overrides."""
        return self.env_overrides.copy()


class ConfigurationError(Exception):
    """Configuration-related error."""
    pass


class TestConfigManager:
    @pytest.fixture
    def sample_config(self):
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "datafit",
                "user": "datafit_user",
                "password": "secure_password"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "app": {
                "secret_key": "a_very_long_and_secure_secret_key_that_is_at_least_32_chars",
                "debug_mode": False,
                "environment": "development"
            },
            "logging": {
                "level": "INFO",
                "file_path": "/var/log/datafit/app.log"
            }
        }
    
    @pytest.fixture
    def config_manager(self):
        return ConfigManager()
    
    @pytest.fixture
    def temp_config_file(self, sample_config):
        """Create a temporary configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f, indent=2)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_load_valid_config(self, config_manager, temp_config_file, sample_config):
        config_manager.config_path = temp_config_file
        loaded_config = config_manager.load_config()
        
        assert loaded_config == sample_config
        assert config_manager.config_data == sample_config
    
    @pytest.mark.unit
    def test_load_nonexistent_config(self, config_manager):
        config_manager.config_path = "/nonexistent/path.json"
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.load_config()
        
        assert "Configuration file not found" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_load_invalid_json(self, config_manager):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            invalid_config_path = f.name
        
        try:
            config_manager.config_path = invalid_config_path
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.load_config()
            
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            os.unlink(invalid_config_path)
    
    @pytest.mark.unit
    def test_environment_variable_overrides(self, config_manager, temp_config_file):
        config_manager.config_path = temp_config_file
        
        # Set environment variables
        with patch.dict(os.environ, {
            'DB_HOST': 'production-db.example.com',
            'DB_PORT': '5433',
            'DEBUG_MODE': 'false',
            'LOG_LEVEL': 'WARNING'
        }):
            config_manager.load_config()
        
        # Check overrides were applied
        assert config_manager.get('database.host') == 'production-db.example.com'
        assert config_manager.get('database.port') == 5433  # Should be converted to int
        assert config_manager.get('app.debug_mode') is False
        assert config_manager.get('logging.level') == 'WARNING'
        
        # Check env_overrides tracking
        overrides = config_manager.get_env_overrides()
        assert 'database.host' in overrides
        assert overrides['database.host'] == 'production-db.example.com'
    
    @pytest.mark.unit
    def test_missing_required_keys(self, config_manager):
        incomplete_config = {
            "database": {
                "host": "localhost"
                # Missing port, name
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(incomplete_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.load_config()
            
            assert "Missing required configuration keys" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_database_validation_invalid_port(self, config_manager, sample_config):
        sample_config['database']['port'] = 70000  # Invalid port
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.load_config()
            
            assert "Invalid database port" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_security_validation_short_secret_key(self, config_manager, sample_config):
        sample_config['app']['secret_key'] = 'short'  # Too short
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.load_config()
            
            assert "Secret key must be at least 32 characters" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_security_validation_debug_in_production(self, config_manager, sample_config):
        sample_config['app']['debug_mode'] = True
        sample_config['app']['environment'] = 'production'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.load_config()
            
            assert "Debug mode should not be enabled in production" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_logging_validation_invalid_level(self, config_manager, sample_config):
        sample_config['logging']['level'] = 'INVALID_LEVEL'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.load_config()
            
            assert "Invalid log level" in str(exc_info.value)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_get_nested_values(self, config_manager, temp_config_file):
        config_manager.config_path = temp_config_file
        config_manager.load_config()
        
        assert config_manager.get('database.host') == 'localhost'
        assert config_manager.get('database.port') == 5432
        assert config_manager.get('nonexistent.key', 'default') == 'default'
        assert config_manager.get('database.nonexistent') is None
    
    @pytest.mark.unit
    def test_database_url_generation(self, config_manager, temp_config_file):
        config_manager.config_path = temp_config_file
        config_manager.load_config()
        
        db_url = config_manager.get_database_url()
        expected = "postgresql://datafit_user:secure_password@localhost:5432/datafit"
        assert db_url == expected
    
    @pytest.mark.unit
    def test_database_url_without_password(self, config_manager, sample_config):
        # Remove password
        del sample_config['database']['password']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            config_manager.load_config()
            
            db_url = config_manager.get_database_url()
            expected = "postgresql://datafit_user@localhost:5432/datafit"
            assert db_url == expected
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.unit
    def test_redis_url_generation(self, config_manager, temp_config_file):
        config_manager.config_path = temp_config_file
        config_manager.load_config()
        
        redis_url = config_manager.get_redis_url()
        expected = "redis://localhost:6379/0"
        assert redis_url == expected
    
    @pytest.mark.unit
    def test_environment_detection(self, config_manager, temp_config_file):
        config_manager.config_path = temp_config_file
        config_manager.load_config()
        
        assert not config_manager.is_production()
        assert not config_manager.is_debug_enabled()
    
    @pytest.mark.unit
    def test_convert_env_value_types(self, config_manager):
        assert config_manager._convert_env_value('true') is True
        assert config_manager._convert_env_value('false') is False
        assert config_manager._convert_env_value('123') == 123
        assert config_manager._convert_env_value('123.45') == 123.45
        assert config_manager._convert_env_value('string_value') == 'string_value'
    
    @pytest.mark.unit
    def test_nested_key_operations(self, config_manager):
        config_manager.config_data = {
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        }
        
        # Test has_nested_key
        assert config_manager._has_nested_key('level1.level2.level3')
        assert not config_manager._has_nested_key('level1.level2.nonexistent')
        
        # Test set_nested_value
        config_manager._set_nested_value('level1.level2.new_key', 'new_value')
        assert config_manager.config_data['level1']['level2']['new_key'] == 'new_value'
        
        # Test creating new nested structure
        config_manager._set_nested_value('new_level1.new_level2.key', 'value')
        assert config_manager.config_data['new_level1']['new_level2']['key'] == 'value'
    
    @pytest.mark.integration
    def test_full_configuration_workflow(self, config_manager, sample_config):
        """Test complete configuration loading and validation workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        try:
            config_manager.config_path = temp_path
            
            # Test with environment overrides
            with patch.dict(os.environ, {
                'DB_HOST': 'env-host',
                'LOG_LEVEL': 'DEBUG'
            }):
                loaded_config = config_manager.load_config()
            
            # Verify configuration was loaded and overridden
            assert loaded_config is not None
            assert config_manager.get('database.host') == 'env-host'
            assert config_manager.get('logging.level') == 'DEBUG'
            
            # Test utility methods
            assert 'env-host' in config_manager.get_database_url()
            assert not config_manager.is_production()
            
            # Test env overrides tracking
            overrides = config_manager.get_env_overrides()
            assert len(overrides) == 2
            
        finally:
            os.unlink(temp_path)