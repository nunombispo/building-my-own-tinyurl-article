import string
from typing import Optional
from user_agents import parse

# Base62 alphabet: 0-9, a-z, A-Z
BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode_id(num: int, min_length: int = 6) -> str:
    """
    Convert a number to a base62 string, padded to minimum length.
    
    Args:
        num: Integer ID to encode
        min_length: Minimum length of the output string (default: 6)
        
    Returns:
        Base62 encoded string, padded with leading zeros to min_length
        
    Note:
        With 6 characters and base62, you can encode up to 56.8 billion URLs
    """
    if num == 0:
        return BASE62[0].zfill(min_length)
    
    result = []
    while num:
        result.append(BASE62[num % 62])
        num //= 62
    
    encoded = ''.join(reversed(result))
    
    # Pad with leading zeros to meet minimum length
    if len(encoded) < min_length:
        encoded = BASE62[0] * (min_length - len(encoded)) + encoded
    
    return encoded

def decode_slug(slug: str) -> Optional[int]:
    """
    Convert a base62 string back to a number.
    
    Args:
        slug: Base62 encoded string
        
    Returns:
        Decoded integer, or None if invalid characters
    """
    try:
        num = 0
        for char in slug:
            num = num * 62 + BASE62.index(char)
        return num
    except ValueError:
        # Character not in BASE62 alphabet
        return None

def parse_user_agent(user_agent_string: Optional[str]) -> dict:
    """
    Parse user agent string to extract device info.
    
    Args:
        user_agent_string: User agent string from request
        
    Returns:
        Dictionary with device_type, browser, and os
    """
    if not user_agent_string:
        return {
            "device_type": "unknown",
            "browser": "unknown",
            "os": "unknown"
        }
    
    user_agent = parse(user_agent_string)
    
    # Determine device type
    if user_agent.is_mobile:
        device_type = "mobile"
    elif user_agent.is_tablet:
        device_type = "tablet"
    elif user_agent.is_pc:
        device_type = "desktop"
    else:
        device_type = "bot" if user_agent.is_bot else "unknown"
    
    return {
        "device_type": device_type,
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}"
    }

def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or len(url) > 2048:  # Max URL length
        return False
    
    if not url.startswith(("http://", "https://")):
        return False
    
    # Basic check for valid URL structure
    if len(url) < 10:  # http://a.b is minimum valid URL
        return False
    
    return True

def validate_custom_slug(slug: str) -> bool:
    """
    Validate custom slug format.
    Only allows alphanumeric characters and hyphens.
    
    Args:
        slug: Custom slug to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not slug:
        return False
    
    # Only allow alphanumeric and hyphens, 3-50 characters
    if len(slug) < 3 or len(slug) > 50:
        return False
    
    allowed_chars = set(string.ascii_letters + string.digits + '-_')
    return all(char in allowed_chars for char in slug)
