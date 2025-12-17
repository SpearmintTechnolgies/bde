"""
Utility functions for BDE email automation system.

This module provides helper functions used across all other modules:
- Email validation
- URL cleaning and parsing
- HTTP requests with retry logic
- Logging setup
- String formatting helpers

Usage:
    from modules.utils import validate_email, clean_url, setup_logging
"""

import re
import time
import logging
from urllib.parse import urlparse, urlunparse
from pathlib import Path


# ============================================
# EMAIL VALIDATION
# ============================================

def validate_email(email: str) -> bool:
    """
    Validate email address format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format, False otherwise
        
    Example:
        >>> validate_email("test@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False
    
    # Simple but effective email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def extract_domain(email: str) -> str:
    """
    Extract domain from email address.
    
    Args:
        email: Email address
        
    Returns:
        str: Domain part of email
        
    Example:
        >>> extract_domain("user@example.com")
        'example.com'
    """
    if not validate_email(email):
        return ""
    
    return email.split('@')[1].strip().lower()


# ============================================
# URL HANDLING
# ============================================

def clean_url(url: str) -> str:
    """
    Normalize and clean URL.
    
    - Adds https:// if no scheme
    - Removes trailing slashes
    - Strips whitespace
    - Converts to lowercase for domain
    
    Args:
        url: URL to clean
        
    Returns:
        str: Cleaned URL
        
    Example:
        >>> clean_url("example.com/path/")
        'https://example.com/path'
        >>> clean_url("  HTTP://EXAMPLE.COM  ")
        'http://example.com'
    """
    if not url:
        return ""
    
    url = url.strip()
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse and normalize
    parsed = urlparse(url)
    
    # Lowercase the domain but keep path case-sensitive
    normalized = parsed._replace(
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip('/')
    )
    
    return urlunparse(normalized)


def get_domain_from_url(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL
        
    Returns:
        str: Domain without scheme
        
    Example:
        >>> get_domain_from_url("https://www.example.com/path")
        'www.example.com'
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(clean_url(url))
        return parsed.netloc
    except:
        return ""


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid and accessible format.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid URL format
    """
    if not url:
        return False
    
    try:
        result = urlparse(clean_url(url))
        return all([result.scheme, result.netloc])
    except:
        return False


# ============================================
# HTTP REQUESTS WITH RETRY LOGIC
# ============================================

def safe_request(url: str, retries: int = 3, timeout: int = 10, headers: dict = None):
    """
    Make HTTP request with retry logic and exponential backoff.
    
    Args:
        url: URL to request
        retries: Number of retry attempts
        timeout: Request timeout in seconds
        headers: Optional custom headers
        
    Returns:
        requests.Response or None: Response object or None if all retries fail
        
    Example:
        >>> response = safe_request("https://example.com")
        >>> if response:
        ...     print(response.status_code)
    """
    import requests
    from config.settings import Config
    
    if headers is None:
        headers = {
            'User-Agent': Config.USER_AGENT
        }
    
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers=headers,
                proxies=Config.get_proxy_config()
            )
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            if attempt == retries - 1:
                # Last attempt failed
                logging.error(f"Failed to fetch {url} after {retries} attempts: {e}")
                return None
            
            # Exponential backoff: 1s, 2s, 4s
            wait_time = 2 ** attempt
            logging.warning(f"Request to {url} failed (attempt {attempt + 1}/{retries}). Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    return None


# ============================================
# LOGGING SETUP
# ============================================

def setup_logging(log_file: str = None, level: str = 'INFO', console: bool = True):
    """
    Configure logging for the application.
    
    Args:
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console: Whether to also log to console
        
    Returns:
        logging.Logger: Configured logger
        
    Example:
        >>> logger = setup_logging('data/logs/app.log', 'INFO')
        >>> logger.info("Application started")
    """
    from config.settings import Config
    
    # Use config values if not provided
    if log_file is None:
        log_file = Config.LOG_FILE
    if level is None:
        level = Config.LOG_LEVEL
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Create handlers
    handlers = []
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    return logging.getLogger(__name__)


# ============================================
# STRING FORMATTING
# ============================================

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
        
    Example:
        >>> truncate_text("This is a very long text", 10)
        'This is...'
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters.
    
    Args:
        text: Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_first_name(full_name: str) -> str:
    """
    Extract first name from full name.
    
    Args:
        full_name: Full name
        
    Returns:
        str: First name
        
    Example:
        >>> extract_first_name("John Smith")
        'John'
        >>> extract_first_name("there")
        'there'
    """
    if not full_name:
        return "there"
    
    name = full_name.strip()
    
    # If name is generic placeholder, return it
    if name.lower() in ['there', 'investor', 'recipient']:
        return name
    
    # Return first word
    return name.split()[0] if name else "there"


# ============================================
# DATA FORMATTING
# ============================================

def format_currency(amount: float) -> str:
    """
    Format number as currency.
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted currency string
        
    Example:
        >>> format_currency(0.03)
        '$0.03'
        >>> format_currency(1234.56)
        '$1,234.56'
    """
    return f"${amount:,.2f}"


def format_list(items: list, max_items: int = 5, separator: str = ', ') -> str:
    """
    Format list as string with optional truncation.
    
    Args:
        items: List to format
        max_items: Maximum items to show
        separator: Separator between items
        
    Returns:
        str: Formatted string
        
    Example:
        >>> format_list(['A', 'B', 'C'], max_items=2)
        'A, B, and 1 more'
    """
    if not items:
        return ""
    
    if len(items) <= max_items:
        return separator.join(str(item) for item in items)
    
    shown = items[:max_items]
    remaining = len(items) - max_items
    
    result = separator.join(str(item) for item in shown)
    result += f"{separator}and {remaining} more"
    
    return result


# ============================================
# TIME HELPERS
# ============================================

def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        str: ISO formatted timestamp
        
    Example:
        >>> get_timestamp()
        '2025-12-16T10:30:45'
    """
    from datetime import datetime
    return datetime.now().isoformat()


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
        
    Example:
        >>> format_duration(125)
        '2m 5s'
        >>> format_duration(3665)
        '1h 1m 5s'
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return ' '.join(parts)


# ============================================
# ERROR HANDLING
# ============================================

def safe_get(dictionary: dict, key: str, default=None):
    """
    Safely get value from dictionary with default.
    
    Args:
        dictionary: Dictionary to access
        key: Key to retrieve
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    try:
        return dictionary.get(key, default) if dictionary else default
    except:
        return default


def handle_exception(e: Exception, context: str = "") -> str:
    """
    Format exception for logging.
    
    Args:
        e: Exception object
        context: Optional context description
        
    Returns:
        str: Formatted error message
    """
    error_msg = f"{type(e).__name__}: {str(e)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    
    return error_msg


# ============================================
# VALIDATION HELPERS
# ============================================

def is_empty(value) -> bool:
    """
    Check if value is empty (None, empty string, empty list, etc).
    
    Args:
        value: Value to check
        
    Returns:
        bool: True if empty
    """
    if value is None:
        return True
    if isinstance(value, str):
        return len(value.strip()) == 0
    if isinstance(value, (list, dict, tuple)):
        return len(value) == 0
    return False


def ensure_string(value, default: str = "") -> str:
    """
    Ensure value is a string.
    
    Args:
        value: Value to convert
        default: Default if value is None
        
    Returns:
        str: String value
    """
    if value is None:
        return default
    return str(value).strip()
