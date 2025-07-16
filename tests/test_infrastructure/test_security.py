"""
=============================================================================
INFRASTRUCTURE SECURITY UNIT TESTS
=============================================================================
Purpose: Unit tests for security infrastructure components
Module: infrastructure/security.py

TEST CATEGORIES:
1. Authentication & Authorization
2. Input Sanitization
3. API Security
4. Audit Logging
=============================================================================
"""

import pytest
import jwt
import time
import hashlib
import secrets
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import re
import json

class AuthenticationManager:
    """Authentication and authorization management."""
    
    def __init__(self, secret_key, token_expiry_hours=24):
        self.secret_key = secret_key
        self.token_expiry_hours = token_expiry_hours
        self.failed_attempts = {}  # Track failed login attempts
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes in seconds
    
    def authenticate_user(self, username, password, user_store):
        """Authenticate user credentials."""
        # Check if user is locked out
        if self._is_user_locked_out(username):
            raise AuthenticationError("Account temporarily locked due to failed attempts")
        
        # Get user from store
        user = user_store.get(username)
        if not user:
            self._record_failed_attempt(username)
            raise AuthenticationError("Invalid credentials")
        
        # Verify password
        if not self._verify_password(password, user['password_hash'], user['salt']):
            self._record_failed_attempt(username)
            raise AuthenticationError("Invalid credentials")
        
        # Clear failed attempts on successful login
        self._clear_failed_attempts(username)
        
        return user
    
    def generate_jwt_token(self, user_id, username, roles=None):
        """Generate JWT token for authenticated user."""
        if roles is None:
            roles = []
        
        payload = {
            'user_id': user_id,
            'username': username,
            'roles': roles,
            'iat': int(time.time()),
            'exp': int(time.time()) + (self.token_expiry_hours * 3600)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_jwt_token(self, token):
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def _verify_password(self, password, password_hash, salt):
        """Verify password against stored hash."""
        computed_hash = self._hash_password(password, salt)
        return computed_hash == password_hash
    
    def _hash_password(self, password, salt):
        """Hash password with salt using PBKDF2."""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _is_user_locked_out(self, username):
        """Check if user is currently locked out."""
        if username not in self.failed_attempts:
            return False
        
        attempts_data = self.failed_attempts[username]
        if attempts_data['count'] < self.max_attempts:
            return False
        
        # Check if lockout period has expired
        time_since_last_attempt = time.time() - attempts_data['last_attempt']
        return time_since_last_attempt < self.lockout_duration
    
    def _record_failed_attempt(self, username):
        """Record a failed login attempt."""
        current_time = time.time()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {'count': 0, 'last_attempt': 0}
        
        attempts_data = self.failed_attempts[username]
        
        # Reset count if last attempt was more than lockout duration ago
        if current_time - attempts_data['last_attempt'] > self.lockout_duration:
            attempts_data['count'] = 0
        
        attempts_data['count'] += 1
        attempts_data['last_attempt'] = current_time
    
    def _clear_failed_attempts(self, username):
        """Clear failed attempts for user."""
        if username in self.failed_attempts:
            del self.failed_attempts[username]


class InputSanitizer:
    """Input sanitization and validation for security."""
    
    @staticmethod
    def sanitize_sql_input(input_string):
        """Sanitize input to prevent SQL injection."""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Remove or escape dangerous SQL characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_html_input(input_string):
        """Sanitize HTML input to prevent XSS attacks."""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Remove potentially dangerous HTML tags and attributes
        html_tags = re.compile(r'<[^>]+>')
        sanitized = html_tags.sub('', input_string)
        
        # Escape remaining HTML entities
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        for char, escape in html_escape_table.items():
            sanitized = sanitized.replace(char, escape)
        
        return sanitized
    
    @staticmethod
    def validate_file_upload(filename, content, allowed_extensions=None, max_size_mb=10):
        """Validate file upload for security."""
        if allowed_extensions is None:
            allowed_extensions = ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx']
        
        errors = []
        
        # Check filename
        if not filename or len(filename.strip()) == 0:
            errors.append("Filename cannot be empty")
        
        # Check file extension
        if allowed_extensions:
            file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
            if file_ext not in allowed_extensions:
                errors.append(f"File type {file_ext} not allowed")
        
        # Check file size
        if content:
            size_mb = len(content) / (1024 * 1024)
            if size_mb > max_size_mb:
                errors.append(f"File size {size_mb:.1f}MB exceeds limit of {max_size_mb}MB")
        
        # Check for dangerous filenames
        dangerous_patterns = [r'\.\.', r'[<>:"/\\|?*]', r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$']
        for pattern in dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                errors.append("Filename contains dangerous characters")
                break
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_api_parameters(params):
        """Sanitize API parameters."""
        sanitized = {}
        
        for key, value in params.items():
            # Sanitize key
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '', str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                clean_value = InputSanitizer.sanitize_html_input(value)
                # Additional length limit
                clean_value = clean_value[:1000]  # Limit to 1000 chars
            elif isinstance(value, (int, float)):
                clean_value = value
            elif isinstance(value, list):
                clean_value = [InputSanitizer.sanitize_html_input(str(v)) for v in value[:100]]  # Limit list size
            else:
                clean_value = str(value)[:1000]
            
            sanitized[clean_key] = clean_value
        
        return sanitized


class APISecurityManager:
    """API security management including rate limiting and validation."""
    
    def __init__(self):
        self.rate_limits = {}  # Track API calls per client
        self.api_keys = {}     # Valid API keys
        self.blocked_ips = set()  # Blocked IP addresses
    
    def validate_api_key(self, api_key, required_permissions=None):
        """Validate API key and permissions."""
        if not api_key or api_key not in self.api_keys:
            raise SecurityError("Invalid API key")
        
        key_data = self.api_keys[api_key]
        
        # Check if key is active
        if not key_data.get('active', True):
            raise SecurityError("API key is inactive")
        
        # Check expiration
        if 'expires_at' in key_data:
            if datetime.now() > key_data['expires_at']:
                raise SecurityError("API key has expired")
        
        # Check permissions
        if required_permissions:
            key_permissions = key_data.get('permissions', [])
            for permission in required_permissions:
                if permission not in key_permissions:
                    raise SecurityError(f"Insufficient permissions: {permission}")
        
        return key_data
    
    def check_rate_limit(self, client_id, limit_per_hour=1000):
        """Check if client has exceeded rate limit."""
        current_time = time.time()
        current_hour = int(current_time // 3600)
        
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = {}
        
        client_limits = self.rate_limits[client_id]
        
        # Clean old hour data
        old_hours = [hour for hour in client_limits.keys() if hour < current_hour - 1]
        for old_hour in old_hours:
            del client_limits[old_hour]
        
        # Check current hour limit
        current_count = client_limits.get(current_hour, 0)
        if current_count >= limit_per_hour:
            raise SecurityError("Rate limit exceeded")
        
        # Increment count
        client_limits[current_hour] = current_count + 1
        
        return True
    
    def validate_request_headers(self, headers):
        """Validate security-related request headers."""
        required_headers = ['User-Agent', 'Content-Type']
        security_issues = []
        
        for header in required_headers:
            if header not in headers:
                security_issues.append(f"Missing required header: {header}")
        
        # Check for suspicious user agents
        user_agent = headers.get('User-Agent', '').lower()
        suspicious_patterns = ['bot', 'crawler', 'scanner', 'sqlmap', 'nikto']
        for pattern in suspicious_patterns:
            if pattern in user_agent:
                security_issues.append(f"Suspicious user agent detected: {pattern}")
        
        # Validate Content-Type for POST/PUT requests
        content_type = headers.get('Content-Type', '')
        if content_type and 'script' in content_type.lower():
            security_issues.append("Dangerous content type detected")
        
        return len(security_issues) == 0, security_issues
    
    def is_ip_blocked(self, ip_address):
        """Check if IP address is blocked."""
        return ip_address in self.blocked_ips
    
    def block_ip(self, ip_address, reason="Security violation"):
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        return True
    
    def generate_api_key(self, client_name, permissions=None, expires_days=365):
        """Generate a new API key."""
        if permissions is None:
            permissions = []
        
        api_key = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=expires_days)
        
        self.api_keys[api_key] = {
            'client_name': client_name,
            'permissions': permissions,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'active': True
        }
        
        return api_key


class AuditLogger:
    """Security audit logging system."""
    
    def __init__(self):
        self.log_entries = []  # In production, this would write to a secure log file/database
    
    def log_authentication_event(self, username, event_type, ip_address, success=True, details=None):
        """Log authentication-related events."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': f"AUTH_{event_type.upper()}",
            'username': username,
            'ip_address': ip_address,
            'success': success,
            'details': details or {},
            'category': 'AUTHENTICATION'
        }
        
        self.log_entries.append(entry)
        return entry
    
    def log_api_access(self, api_key, endpoint, method, ip_address, status_code, response_time=None):
        """Log API access events."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'API_ACCESS',
            'api_key': api_key[:8] + '...' if api_key else None,  # Partial key for security
            'endpoint': endpoint,
            'method': method,
            'ip_address': ip_address,
            'status_code': status_code,
            'response_time': response_time,
            'category': 'API'
        }
        
        self.log_entries.append(entry)
        return entry
    
    def log_security_event(self, event_type, severity, description, ip_address=None, user_id=None):
        """Log security-related events."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': f"SECURITY_{event_type.upper()}",
            'severity': severity.upper(),
            'description': description,
            'ip_address': ip_address,
            'user_id': user_id,
            'category': 'SECURITY'
        }
        
        self.log_entries.append(entry)
        return entry
    
    def log_data_access(self, user_id, resource_type, resource_id, action, success=True):
        """Log data access events."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'DATA_ACCESS',
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action.upper(),
            'success': success,
            'category': 'DATA'
        }
        
        self.log_entries.append(entry)
        return entry
    
    def get_security_summary(self, hours=24):
        """Get security events summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_entries = [
            entry for entry in self.log_entries
            if datetime.fromisoformat(entry['timestamp']) > cutoff_time
        ]
        
        summary = {
            'total_events': len(recent_entries),
            'authentication_events': len([e for e in recent_entries if e['category'] == 'AUTHENTICATION']),
            'security_events': len([e for e in recent_entries if e['category'] == 'SECURITY']),
            'failed_logins': len([e for e in recent_entries if e['category'] == 'AUTHENTICATION' and not e['success']]),
            'api_calls': len([e for e in recent_entries if e['category'] == 'API']),
            'data_access_events': len([e for e in recent_entries if e['category'] == 'DATA'])
        }
        
        return summary


# Custom exceptions
class AuthenticationError(Exception):
    """Authentication-related error."""
    pass

class SecurityError(Exception):
    """General security error."""
    pass


class TestAuthenticationManager:
    @pytest.fixture
    def auth_manager(self):
        return AuthenticationManager(secret_key="test_secret_key_12345")
    
    @pytest.fixture
    def user_store(self):
        salt = "test_salt"
        password_hash = hashlib.pbkdf2_hmac('sha256', 'password123'.encode(), salt.encode(), 100000).hex()
        
        return {
            'testuser': {
                'user_id': 1,
                'username': 'testuser',
                'password_hash': password_hash,
                'salt': salt,
                'roles': ['user']
            }
        }
    
    @pytest.mark.unit
    def test_successful_authentication(self, auth_manager, user_store):
        user = auth_manager.authenticate_user('testuser', 'password123', user_store)
        
        assert user['username'] == 'testuser'
        assert user['user_id'] == 1
    
    @pytest.mark.unit
    def test_failed_authentication_invalid_user(self, auth_manager, user_store):
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.authenticate_user('nonexistent', 'password123', user_store)
        
        assert "Invalid credentials" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_failed_authentication_wrong_password(self, auth_manager, user_store):
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.authenticate_user('testuser', 'wrongpassword', user_store)
        
        assert "Invalid credentials" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_account_lockout_after_failed_attempts(self, auth_manager, user_store):
        # Make multiple failed attempts
        for _ in range(5):
            with pytest.raises(AuthenticationError):
                auth_manager.authenticate_user('testuser', 'wrongpassword', user_store)
        
        # Next attempt should result in lockout
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.authenticate_user('testuser', 'password123', user_store)
        
        assert "temporarily locked" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_jwt_token_generation_and_verification(self, auth_manager):
        user_id = 1
        username = "testuser"
        roles = ["user", "admin"]
        
        # Generate token
        token = auth_manager.generate_jwt_token(user_id, username, roles)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = auth_manager.verify_jwt_token(token)
        assert payload['user_id'] == user_id
        assert payload['username'] == username
        assert payload['roles'] == roles
    
    @pytest.mark.unit
    def test_jwt_token_expiry(self, auth_manager):
        # Create auth manager with very short expiry
        short_auth = AuthenticationManager("test_secret", token_expiry_hours=0.001)  # ~3.6 seconds
        
        token = short_auth.generate_jwt_token(1, "testuser")
        
        # Wait for token to expire
        time.sleep(4)
        
        with pytest.raises(AuthenticationError) as exc_info:
            short_auth.verify_jwt_token(token)
        
        assert "expired" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_jwt_token(self, auth_manager):
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.verify_jwt_token("invalid.token.here")
        
        assert "Invalid token" in str(exc_info.value)


class TestInputSanitizer:
    @pytest.mark.unit
    def test_sql_injection_sanitization(self):
        malicious_input = "'; DROP TABLE users; --"
        sanitized = InputSanitizer.sanitize_sql_input(malicious_input)
        
        assert "DROP TABLE" not in sanitized
        assert ";" not in sanitized
        assert "--" not in sanitized
    
    @pytest.mark.unit
    def test_html_xss_sanitization(self):
        malicious_input = "<script>alert('XSS')</script><img src=x onerror=alert(1)>"
        sanitized = InputSanitizer.sanitize_html_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "<img" not in sanitized
        assert "&lt;" in sanitized or "&gt;" in sanitized  # HTML entities
    
    @pytest.mark.unit
    def test_file_upload_validation_success(self):
        filename = "document.pdf"
        content = b"PDF content here"
        allowed_extensions = ['.pdf', '.doc']
        
        is_valid, errors = InputSanitizer.validate_file_upload(
            filename, content, allowed_extensions, max_size_mb=1
        )
        
        assert is_valid
        assert len(errors) == 0
    
    @pytest.mark.unit
    def test_file_upload_validation_failures(self):
        # Test invalid extension
        is_valid, errors = InputSanitizer.validate_file_upload(
            "malware.exe", b"content", ['.pdf'], max_size_mb=1
        )
        assert not is_valid
        assert any("not allowed" in error for error in errors)
        
        # Test file too large
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        is_valid, errors = InputSanitizer.validate_file_upload(
            "large.pdf", large_content, ['.pdf'], max_size_mb=10
        )
        assert not is_valid
        assert any("exceeds limit" in error for error in errors)
        
        # Test dangerous filename
        is_valid, errors = InputSanitizer.validate_file_upload(
            "../../../etc/passwd", b"content", ['.txt'], max_size_mb=1
        )
        assert not is_valid
        assert any("dangerous characters" in error for error in errors)
    
    @pytest.mark.unit
    def test_api_parameter_sanitization(self):
        params = {
            'user_input': '<script>alert("xss")</script>',
            'number_param': 123,
            'list_param': ['item1', '<script>bad</script>', 'item3'],
            'special_chars!!!': 'value'
        }
        
        sanitized = InputSanitizer.sanitize_api_parameters(params)
        
        assert '<script>' not in sanitized['user_input']
        assert sanitized['number_param'] == 123
        assert len(sanitized['list_param']) == 3
        assert 'specialchars' in sanitized  # Special chars removed from key


class TestAPISecurityManager:
    @pytest.fixture
    def api_security(self):
        manager = APISecurityManager()
        # Add a test API key
        test_key = manager.generate_api_key("test_client", ["read", "write"])
        manager.test_key = test_key  # Store for test access
        return manager
    
    @pytest.mark.unit
    def test_api_key_validation_success(self, api_security):
        key_data = api_security.validate_api_key(api_security.test_key, ["read"])
        
        assert key_data['client_name'] == "test_client"
        assert "read" in key_data['permissions']
    
    @pytest.mark.unit
    def test_api_key_validation_failures(self, api_security):
        # Invalid key
        with pytest.raises(SecurityError) as exc_info:
            api_security.validate_api_key("invalid_key")
        assert "Invalid API key" in str(exc_info.value)
        
        # Insufficient permissions
        with pytest.raises(SecurityError) as exc_info:
            api_security.validate_api_key(api_security.test_key, ["admin"])
        assert "Insufficient permissions" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_rate_limiting(self, api_security):
        client_id = "test_client"
        
        # Should succeed within limit
        for _ in range(10):
            result = api_security.check_rate_limit(client_id, limit_per_hour=20)
            assert result is True
        
        # Should fail when limit exceeded
        for _ in range(15):  # Exceed the limit
            api_security.check_rate_limit(client_id, limit_per_hour=20)
        
        with pytest.raises(SecurityError) as exc_info:
            api_security.check_rate_limit(client_id, limit_per_hour=20)
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_request_header_validation(self, api_security):
        # Valid headers
        valid_headers = {
            'User-Agent': 'Mozilla/5.0 (legitimate browser)',
            'Content-Type': 'application/json'
        }
        
        is_valid, issues = api_security.validate_request_headers(valid_headers)
        assert is_valid
        assert len(issues) == 0
        
        # Invalid headers
        invalid_headers = {
            'User-Agent': 'sqlmap/1.0 (bot scanner)',
            'Content-Type': 'text/javascript'  # Suspicious
        }
        
        is_valid, issues = api_security.validate_request_headers(invalid_headers)
        assert not is_valid
        assert len(issues) > 0
    
    @pytest.mark.unit
    def test_ip_blocking(self, api_security):
        ip_address = "192.168.1.100"
        
        # Should not be blocked initially
        assert not api_security.is_ip_blocked(ip_address)
        
        # Block IP
        api_security.block_ip(ip_address, "Suspicious activity")
        
        # Should now be blocked
        assert api_security.is_ip_blocked(ip_address)
    
    @pytest.mark.unit
    def test_api_key_generation(self, api_security):
        key = api_security.generate_api_key("new_client", ["read"], expires_days=30)
        
        assert isinstance(key, str)
        assert len(key) > 30  # Should be reasonably long
        assert key in api_security.api_keys
        
        key_data = api_security.api_keys[key]
        assert key_data['client_name'] == "new_client"
        assert key_data['permissions'] == ["read"]
        assert key_data['active'] is True


class TestAuditLogger:
    @pytest.fixture
    def audit_logger(self):
        return AuditLogger()
    
    @pytest.mark.unit
    def test_authentication_event_logging(self, audit_logger):
        entry = audit_logger.log_authentication_event(
            username="testuser",
            event_type="login",
            ip_address="192.168.1.1",
            success=True,
            details={"method": "password"}
        )
        
        assert entry['event_type'] == "AUTH_LOGIN"
        assert entry['username'] == "testuser"
        assert entry['success'] is True
        assert entry['category'] == 'AUTHENTICATION'
        assert len(audit_logger.log_entries) == 1
    
    @pytest.mark.unit
    def test_api_access_logging(self, audit_logger):
        entry = audit_logger.log_api_access(
            api_key="test_key_12345",
            endpoint="/api/users",
            method="GET",
            ip_address="192.168.1.1",
            status_code=200,
            response_time=0.45
        )
        
        assert entry['event_type'] == "API_ACCESS"
        assert entry['api_key'].startswith("test_key")
        assert entry['endpoint'] == "/api/users"
        assert entry['status_code'] == 200
        assert entry['category'] == 'API'
    
    @pytest.mark.unit
    def test_security_event_logging(self, audit_logger):
        entry = audit_logger.log_security_event(
            event_type="suspicious_activity",
            severity="high",
            description="Multiple failed login attempts",
            ip_address="192.168.1.100",
            user_id=123
        )
        
        assert entry['event_type'] == "SECURITY_SUSPICIOUS_ACTIVITY"
        assert entry['severity'] == "HIGH"
        assert entry['category'] == 'SECURITY'
    
    @pytest.mark.unit
    def test_data_access_logging(self, audit_logger):
        entry = audit_logger.log_data_access(
            user_id=123,
            resource_type="customer_data",
            resource_id="CUST001",
            action="read",
            success=True
        )
        
        assert entry['event_type'] == "DATA_ACCESS"
        assert entry['resource_type'] == "customer_data"
        assert entry['action'] == "READ"
        assert entry['category'] == 'DATA'
    
    @pytest.mark.unit
    def test_security_summary(self, audit_logger):
        # Log various events
        audit_logger.log_authentication_event("user1", "login", "192.168.1.1", True)
        audit_logger.log_authentication_event("user2", "login", "192.168.1.2", False)
        audit_logger.log_api_access("key1", "/api/data", "GET", "192.168.1.1", 200)
        audit_logger.log_security_event("brute_force", "high", "Attack detected", "192.168.1.3")
        audit_logger.log_data_access(123, "customer", "C001", "read", True)
        
        summary = audit_logger.get_security_summary(hours=24)
        
        assert summary['total_events'] == 5
        assert summary['authentication_events'] == 2
        assert summary['failed_logins'] == 1
        assert summary['api_calls'] == 1
        assert summary['security_events'] == 1
        assert summary['data_access_events'] == 1