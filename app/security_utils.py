"""
Security utility functions for input validation và sanitization
"""
import re
import html

def sanitize_input(text, max_length=1000, allow_html=False):
    """
    Sanitize user input để prevent XSS và injection attacks
    
    Args:
        text (str): Input text to sanitize
        max_length (int): Maximum allowed length
        allow_html (bool): Whether to allow safe HTML tags
    
    Returns:
        str: Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes và control characters
    text = text.replace('\x00', '')
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    if not allow_html:
        # Escape HTML entities
        text = html.escape(text)
    else:
        # Allow only safe HTML tags
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'br']
        # Simple whitelist approach - remove script, style, etc.
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def validate_age_group(age_group):
    """Validate age group input"""
    valid_ages = ['6-12-months', '1-2-years', '2-3-years', '3-5-years', 'all-ages']
    return age_group if age_group in valid_ages else 'all-ages'

def validate_menu_count(count_str):
    """Validate menu count input"""
    try:
        count = int(count_str)
        return max(1, min(count, 50))  # Limit between 1-50
    except (ValueError, TypeError):
        return 10  # Default value

def validate_ip_address(ip):
    """Simple IP validation"""
    if not ip:
        return "unknown"
    
    # Basic IPv4 validation
    parts = ip.split('.')
    if len(parts) == 4:
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return "invalid"
            return ip
        except ValueError:
            pass
    
    return "unknown"

def is_sql_injection_attempt(text):
    """Detect potential SQL injection attempts"""
    if not text:
        return False
    
    text_lower = text.lower()
    sql_keywords = [
        'union', 'select', 'insert', 'update', 'delete', 'drop', 
        'create', 'alter', 'exec', 'execute', 'sp_', 'xp_',
        'script', 'javascript', 'vbscript'
    ]
    
    suspicious_patterns = [
        r'[\'\"]\s*;\s*',  # Quote followed by semicolon
        r'--\s*',          # SQL comments
        r'/\*.*?\*/',      # Block comments
        r'0x[0-9a-f]+',    # Hex values
    ]
    
    # Check for SQL keywords
    for keyword in sql_keywords:
        if keyword in text_lower:
            return True
    
    # Check for suspicious patterns
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False

def log_security_event(event_type, details, ip_address="unknown"):
    """Log security events for monitoring"""
    timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚨 [SECURITY] {timestamp} - {event_type} from {ip_address}: {details}")

# Rate limiting storage (in-memory - use Redis in production)
_rate_limit_storage = {}

def check_rate_limit(identifier, limit_seconds=10):
    """
    Check if request is within rate limit
    
    Args:
        identifier (str): Unique identifier (IP, user ID, etc.)
        limit_seconds (int): Minimum seconds between requests
    
    Returns:
        tuple: (is_allowed, seconds_remaining)
    """
    import time
    
    current_time = time.time()
    
    if identifier in _rate_limit_storage:
        last_request = _rate_limit_storage[identifier]
        elapsed = current_time - last_request
        
        if elapsed < limit_seconds:
            remaining = limit_seconds - elapsed
            return False, int(remaining) + 1
    
    _rate_limit_storage[identifier] = current_time
    return True, 0

def clean_rate_limit_storage():
    """Clean old entries from rate limit storage"""
    import time
    
    current_time = time.time()
    expired_keys = []
    
    for identifier, timestamp in _rate_limit_storage.items():
        if current_time - timestamp > 3600:  # Remove entries older than 1 hour
            expired_keys.append(identifier)
    
    for key in expired_keys:
        del _rate_limit_storage[key]
