"""
=============================================================================
INFRASTRUCTURE UTILITIES UNIT TESTS
=============================================================================
Purpose: Unit tests for infrastructure utility functions
Module: infrastructure/utils.py

TEST CATEGORIES:
1. File System Operations
2. Data Validation
3. Encryption/Decryption
4. Network Utilities
=============================================================================
"""

import pytest
import os
import tempfile
import json
import hashlib
import time
import socket
from unittest.mock import Mock, patch, mock_open
from datetime import datetime, timedelta
import base64
from pathlib import Path

class FileManager:
    """File system management utilities."""
    
    @staticmethod
    def ensure_directory(path):
        """Ensure directory exists, create if necessary."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError as e:
            raise FileSystemError(f"Cannot create directory {path}: {e}")
    
    @staticmethod
    def safe_write_file(filepath, content, backup=True):
        """Safely write file with optional backup."""
        filepath = Path(filepath)
        
        # Ensure parent directory exists
        FileManager.ensure_directory(filepath.parent)
        
        # Create backup if file exists and backup is requested
        if backup and filepath.exists():
            backup_path = filepath.with_suffix(f"{filepath.suffix}.backup")
            filepath.rename(backup_path)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except OSError as e:
            raise FileSystemError(f"Cannot write file {filepath}: {e}")
    
    @staticmethod
    def safe_read_file(filepath):
        """Safely read file with error handling."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileSystemError(f"File not found: {filepath}")
        except OSError as e:
            raise FileSystemError(f"Cannot read file {filepath}: {e}")
    
    @staticmethod
    def calculate_file_hash(filepath, algorithm='sha256'):
        """Calculate file hash for integrity checking."""
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except OSError as e:
            raise FileSystemError(f"Cannot calculate hash for {filepath}: {e}")
    
    @staticmethod
    def cleanup_old_files(directory, max_age_days=30, pattern="*"):
        """Clean up files older than specified age."""
        directory = Path(directory)
        if not directory.exists():
            return 0
        
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except OSError:
                    continue  # Skip files that can't be deleted
        
        return deleted_count


class DataValidator:
    """Data validation utilities."""
    
    @staticmethod
    def validate_email(email):
        """Validate email address format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format."""
        import re
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it's a valid length (10-15 digits)
        return 10 <= len(digits_only) <= 15
    
    @staticmethod
    def validate_ssn(ssn):
        """Validate Social Security Number format."""
        import re
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', ssn)
        # Should be exactly 9 digits
        return len(digits_only) == 9 and not digits_only.startswith('000')
    
    @staticmethod
    def validate_json_schema(data, schema):
        """Validate JSON data against schema."""
        try:
            import jsonschema
            jsonschema.validate(data, schema)
            return True, None
        except ImportError:
            # Fallback basic validation if jsonschema not available
            return DataValidator._basic_schema_validation(data, schema)
        except jsonschema.ValidationError as e:
            return False, str(e)
    
    @staticmethod
    def _basic_schema_validation(data, schema):
        """Basic schema validation fallback."""
        required = schema.get('required', [])
        properties = schema.get('properties', {})
        
        # Check required fields
        for field in required:
            if field not in data:
                return False, f"Required field '{field}' is missing"
        
        # Check field types
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get('type')
                if expected_type == 'string' and not isinstance(data[field], str):
                    return False, f"Field '{field}' must be a string"
                elif expected_type == 'integer' and not isinstance(data[field], int):
                    return False, f"Field '{field}' must be an integer"
                elif expected_type == 'number' and not isinstance(data[field], (int, float)):
                    return False, f"Field '{field}' must be a number"
        
        return True, None
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe file system usage."""
        import re
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\.\.', '_', filename)  # Remove directory traversal
        filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def validate_financial_amount(amount, min_value=0, max_value=None):
        """Validate financial amount."""
        try:
            amount = float(amount)
            if amount < min_value:
                return False, f"Amount must be at least {min_value}"
            if max_value is not None and amount > max_value:
                return False, f"Amount cannot exceed {max_value}"
            # Check for reasonable decimal places (max 2 for currency)
            if round(amount, 2) != amount:
                return False, "Amount cannot have more than 2 decimal places"
            return True, None
        except (ValueError, TypeError):
            return False, "Amount must be a valid number"


class CryptoUtils:
    """Cryptographic utilities for security operations."""
    
    @staticmethod
    def generate_salt():
        """Generate a random salt for password hashing."""
        import secrets
        return secrets.token_hex(16)
    
    @staticmethod
    def hash_password(password, salt):
        """Hash password with salt using PBKDF2."""
        import hashlib
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    @staticmethod
    def verify_password(password, salt, hashed_password):
        """Verify password against hash."""
        return CryptoUtils.hash_password(password, salt) == hashed_password
    
    @staticmethod
    def encrypt_sensitive_data(data, key):
        """Encrypt sensitive data (simplified implementation)."""
        # In production, use proper encryption libraries like cryptography
        import base64
        # This is a simplified example - use proper encryption in production
        encoded_data = base64.b64encode(data.encode()).decode()
        return encoded_data
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data, key):
        """Decrypt sensitive data (simplified implementation)."""
        import base64
        try:
            decoded_data = base64.b64decode(encrypted_data).decode()
            return decoded_data
        except Exception:
            raise CryptoError("Failed to decrypt data")
    
    @staticmethod
    def generate_api_key():
        """Generate a secure API key."""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_session_token():
        """Generate a session token."""
        import secrets
        import time
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(16)
        return f"{timestamp}_{random_part}"


class NetworkUtils:
    """Network-related utilities."""
    
    @staticmethod
    def is_port_open(host, port, timeout=3):
        """Check if a port is open on a host."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error):
            return False
    
    @staticmethod
    def get_local_ip():
        """Get local IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    @staticmethod
    def validate_ip_address(ip):
        """Validate IP address format."""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    @staticmethod
    def ping_host(host, count=1):
        """Ping a host (cross-platform)."""
        import subprocess
        import platform
        
        # Determine ping command based on OS
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False


class DateTimeUtils:
    """Date and time utilities."""
    
    @staticmethod
    def parse_iso_datetime(datetime_str):
        """Parse ISO format datetime string."""
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValidationError(f"Invalid datetime format: {e}")
    
    @staticmethod
    def format_datetime_for_db(dt):
        """Format datetime for database storage."""
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_business_days_between(start_date, end_date):
        """Calculate business days between two dates."""
        business_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday is 0, Friday is 4
                business_days += 1
            current_date += timedelta(days=1)
        
        return business_days
    
    @staticmethod
    def is_market_hours(dt=None):
        """Check if given time is during market hours (9:30 AM - 4:00 PM ET)."""
        if dt is None:
            dt = datetime.now()
        
        # This is simplified - in production, consider time zones and holidays
        if dt.weekday() >= 5:  # Weekend
            return False
        
        market_open = dt.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = dt.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= dt <= market_close


# Custom exceptions
class FileSystemError(Exception):
    """File system operation error."""
    pass

class ValidationError(Exception):
    """Data validation error."""
    pass

class CryptoError(Exception):
    """Cryptographic operation error."""
    pass


class TestFileManager:
    def test_ensure_directory_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, 'new_dir', 'nested_dir')
            
            result = FileManager.ensure_directory(test_path)
            
            assert result is True
            assert os.path.exists(test_path)
            assert os.path.isdir(test_path)
    
    def test_ensure_directory_existing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = FileManager.ensure_directory(temp_dir)
            assert result is True
    
    def test_safe_write_and_read_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test.txt')
            test_content = "Hello, World!"
            
            # Write file
            result = FileManager.safe_write_file(test_file, test_content)
            assert result is True
            assert os.path.exists(test_file)
            
            # Read file
            read_content = FileManager.safe_read_file(test_file)
            assert read_content == test_content
    
    def test_safe_write_with_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test.txt')
            original_content = "Original content"
            new_content = "New content"
            
            # Write original file
            FileManager.safe_write_file(test_file, original_content, backup=False)
            
            # Write with backup
            FileManager.safe_write_file(test_file, new_content, backup=True)
            
            # Check new content
            assert FileManager.safe_read_file(test_file) == new_content
            
            # Check backup exists
            backup_file = test_file + ".backup"
            assert os.path.exists(backup_file)
            assert FileManager.safe_read_file(backup_file) == original_content
    
    def test_calculate_file_hash(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content for hashing")
            temp_path = f.name
        
        try:
            hash_value = FileManager.calculate_file_hash(temp_path)
            assert len(hash_value) == 64  # SHA256 produces 64-character hex string
            assert isinstance(hash_value, str)
            
            # Test different algorithm
            md5_hash = FileManager.calculate_file_hash(temp_path, algorithm='md5')
            assert len(md5_hash) == 32  # MD5 produces 32-character hex string
        finally:
            os.unlink(temp_path)
    
    def test_cleanup_old_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with different ages
            old_file = os.path.join(temp_dir, 'old_file.txt')
            new_file = os.path.join(temp_dir, 'new_file.txt')
            
            # Create files
            with open(old_file, 'w') as f:
                f.write("old")
            with open(new_file, 'w') as f:
                f.write("new")
            
            # Make old file appear old by modifying its timestamp
            old_time = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
            os.utime(old_file, (old_time, old_time))
            
            # Clean up files older than 30 days
            deleted_count = FileManager.cleanup_old_files(temp_dir, max_age_days=30)
            
            assert deleted_count == 1
            assert not os.path.exists(old_file)
            assert os.path.exists(new_file)
    
    def test_file_not_found_error(self):
        with pytest.raises(FileSystemError):
            FileManager.safe_read_file("/nonexistent/file.txt")


class TestDataValidator:
    def test_validate_email(self):
        # Valid emails
        assert DataValidator.validate_email("user@example.com")
        assert DataValidator.validate_email("test.email+tag@domain.co.uk")
        
        # Invalid emails
        assert not DataValidator.validate_email("invalid-email")
        assert not DataValidator.validate_email("@domain.com")
        assert not DataValidator.validate_email("user@")
    
    def test_validate_phone(self):
        # Valid phone numbers
        assert DataValidator.validate_phone("1234567890")
        assert DataValidator.validate_phone("(123) 456-7890")
        assert DataValidator.validate_phone("+1-123-456-7890")
        
        # Invalid phone numbers
        assert not DataValidator.validate_phone("123")
        assert not DataValidator.validate_phone("abcdefghij")
        assert not DataValidator.validate_phone("12345678901234567")  # Too long
    
    def test_validate_ssn(self):
        # Valid SSNs
        assert DataValidator.validate_ssn("123456789")
        assert DataValidator.validate_ssn("123-45-6789")
        
        # Invalid SSNs
        assert not DataValidator.validate_ssn("000123456")  # Starts with 000
        assert not DataValidator.validate_ssn("12345678")   # Too short
        assert not DataValidator.validate_ssn("1234567890") # Too long
    
    def test_validate_json_schema(self):
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        # Valid data
        valid_data = {"name": "John", "age": 30}
        is_valid, error = DataValidator.validate_json_schema(valid_data, schema)
        assert is_valid
        assert error is None
        
        # Invalid data - missing required field
        invalid_data = {"name": "John"}
        is_valid, error = DataValidator.validate_json_schema(invalid_data, schema)
        assert not is_valid
        assert "age" in error
    
    def test_sanitize_filename(self):
        # Test dangerous characters
        assert DataValidator.sanitize_filename("file<name>.txt") == "file_name_.txt"
        assert DataValidator.sanitize_filename("../../../etc/passwd") == "_.._.._.._etc_passwd"
        assert DataValidator.sanitize_filename("  .hidden  ") == "hidden"
        
        # Test length limitation
        long_name = "a" * 300 + ".txt"
        sanitized = DataValidator.sanitize_filename(long_name)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".txt")
    
    def test_validate_financial_amount(self):
        # Valid amounts
        is_valid, error = DataValidator.validate_financial_amount(100.50)
        assert is_valid
        assert error is None
        
        is_valid, error = DataValidator.validate_financial_amount("250.75")
        assert is_valid
        
        # Invalid amounts
        is_valid, error = DataValidator.validate_financial_amount(-10)
        assert not is_valid
        assert "at least 0" in error
        
        is_valid, error = DataValidator.validate_financial_amount(100.123)  # Too many decimals
        assert not is_valid
        assert "decimal places" in error


class TestCryptoUtils:
    def test_generate_salt(self):
        salt1 = CryptoUtils.generate_salt()
        salt2 = CryptoUtils.generate_salt()
        
        assert len(salt1) == 32  # 16 bytes * 2 (hex)
        assert len(salt2) == 32
        assert salt1 != salt2  # Should be different
    
    def test_password_hashing_and_verification(self):
        password = "test_password_123"
        salt = CryptoUtils.generate_salt()
        
        # Hash password
        hashed = CryptoUtils.hash_password(password, salt)
        assert len(hashed) == 64  # SHA256 hex length
        
        # Verify correct password
        assert CryptoUtils.verify_password(password, salt, hashed)
        
        # Verify incorrect password
        assert not CryptoUtils.verify_password("wrong_password", salt, hashed)
    
    def test_encrypt_decrypt_data(self):
        data = "sensitive information"
        key = "encryption_key"
        
        # Encrypt
        encrypted = CryptoUtils.encrypt_sensitive_data(data, key)
        assert encrypted != data
        
        # Decrypt
        decrypted = CryptoUtils.decrypt_sensitive_data(encrypted, key)
        assert decrypted == data
    
    def test_generate_api_key(self):
        key1 = CryptoUtils.generate_api_key()
        key2 = CryptoUtils.generate_api_key()
        
        assert len(key1) > 30  # Should be reasonably long
        assert key1 != key2   # Should be unique
        assert key1.replace('-', '').replace('_', '').isalnum()  # URL-safe characters
    
    def test_generate_session_token(self):
        token1 = CryptoUtils.generate_session_token()
        token2 = CryptoUtils.generate_session_token()
        
        assert '_' in token1  # Should contain timestamp separator
        assert token1 != token2
        
        # Check timestamp part
        timestamp_part = token1.split('_')[0]
        assert timestamp_part.isdigit()


class TestNetworkUtils:
    def test_validate_ip_address(self):
        # Valid IPs
        assert NetworkUtils.validate_ip_address("192.168.1.1")
        assert NetworkUtils.validate_ip_address("127.0.0.1")
        assert NetworkUtils.validate_ip_address("255.255.255.255")
        
        # Invalid IPs
        assert not NetworkUtils.validate_ip_address("256.1.1.1")
        assert not NetworkUtils.validate_ip_address("not.an.ip.address")
        assert not NetworkUtils.validate_ip_address("192.168.1")
    
    def test_get_local_ip(self):
        ip = NetworkUtils.get_local_ip()
        assert NetworkUtils.validate_ip_address(ip)
        assert ip != "0.0.0.0"
    
    @pytest.mark.slow
    def test_is_port_open(self):
        # Test with a commonly closed port
        assert not NetworkUtils.is_port_open("127.0.0.1", 99999, timeout=1)
        
        # Test with invalid host
        assert not NetworkUtils.is_port_open("invalid-host-name", 80, timeout=1)
    
    @pytest.mark.slow  
    def test_ping_host(self):
        # Test with localhost (should usually work)
        result = NetworkUtils.ping_host("127.0.0.1", count=1)
        assert isinstance(result, bool)
        
        # Test with invalid host
        result = NetworkUtils.ping_host("invalid-host-12345", count=1)
        assert result is False


class TestDateTimeUtils:
    def test_parse_iso_datetime(self):
        # Test valid ISO formats
        dt1 = DateTimeUtils.parse_iso_datetime("2024-06-30T15:30:00")
        assert dt1.year == 2024
        assert dt1.month == 6
        assert dt1.day == 30
        
        dt2 = DateTimeUtils.parse_iso_datetime("2024-06-30T15:30:00Z")
        assert dt2.year == 2024
        
        # Test invalid format
        with pytest.raises(ValidationError):
            DateTimeUtils.parse_iso_datetime("invalid-datetime")
    
    def test_format_datetime_for_db(self):
        dt = datetime(2024, 6, 30, 15, 30, 45)
        formatted = DateTimeUtils.format_datetime_for_db(dt)
        assert formatted == "2024-06-30 15:30:45"
    
    def test_get_business_days_between(self):
        # Test Monday to Friday (5 business days)
        start = datetime(2024, 6, 3)   # Monday
        end = datetime(2024, 6, 7)     # Friday
        business_days = DateTimeUtils.get_business_days_between(start, end)
        assert business_days == 5
        
        # Test including weekend
        start = datetime(2024, 6, 7)   # Friday  
        end = datetime(2024, 6, 10)    # Monday
        business_days = DateTimeUtils.get_business_days_between(start, end)
        assert business_days == 2  # Friday and Monday only
    
    def test_is_market_hours(self):
        # Test during market hours (weekday, 10 AM)
        market_time = datetime(2024, 6, 5, 10, 0)  # Wednesday 10 AM
        assert DateTimeUtils.is_market_hours(market_time)
        
        # Test outside market hours (weekday, 8 AM)
        early_time = datetime(2024, 6, 5, 8, 0)   # Wednesday 8 AM
        assert not DateTimeUtils.is_market_hours(early_time)
        
        # Test weekend
        weekend_time = datetime(2024, 6, 8, 10, 0)  # Saturday 10 AM
        assert not DateTimeUtils.is_market_hours(weekend_time)