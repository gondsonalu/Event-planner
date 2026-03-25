"""
Security Utilities - Phase 6
XSS Prevention via bleach, CSRF token refresh helpers,
and input validation utilities.
"""
import bleach
from flask import current_app, jsonify, request
from functools import wraps


# ── Allowed HTML Tags & Attributes ──────────────────────────────────
ALLOWED_TAGS = ['b', 'i', 'u', 'ul', 'ol', 'li', 'p', 'br', 'em', 'strong']
ALLOWED_ATTRIBUTES = {}
ALLOWED_PROTOCOLS = ['http', 'https']


def sanitize_html(content):
    """
    Sanitizes HTML content using bleach.
    Allows only safe tags and strips all scripts/events.
    Used for Event Descriptions, Approver Comments, and all rich text inputs.
    
    Args:
        content (str): Raw HTML/text content from user input.
    
    Returns:
        str: Sanitized content with only allowed tags.
    """
    if not content:
        return content

    try:
        clean_content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )
        return clean_content
    except Exception as e:
        current_app.logger.error(f"Sanitization error: {str(e)}")
        # Fallback: strip ALL tags if something goes wrong
        return bleach.clean(content, tags=[], strip=True)


def sanitize_plain_text(content):
    """
    Strips ALL HTML tags, leaving only plain text.
    Use for fields like Title, Venue, etc. where no HTML is expected.
    
    Args:
        content (str): Raw user input.
    
    Returns:
        str: Plain text with all HTML removed.
    """
    if not content:
        return content
    return bleach.clean(content, tags=[], strip=True)


def sanitize_comment(content):
    """
    Sanitizes approver comments — allows minimal formatting.
    
    Args:
        content (str): Raw approver comment.
    
    Returns:
        str: Sanitized comment.
    """
    if not content:
        return content
    
    comment_tags = ['b', 'i', 'u', 'br', 'p']
    return bleach.clean(content, tags=comment_tags, attributes={}, strip=True)


def validate_no_script(content):
    """
    Returns True if the content does NOT contain script injection attempts.
    Useful as a quick pre-check before saving.
    
    Args:
        content (str): Input to validate.
    
    Returns:
        bool: True if safe, False if suspicious.
    """
    if not content:
        return True
    
    dangerous_patterns = [
        '<script', 'javascript:', 'onerror=', 'onload=',
        'onclick=', 'onmouseover=', 'onfocus=', 'eval(',
        'document.cookie', 'window.location', 'alert('
    ]
    content_lower = content.lower()
    return not any(pattern in content_lower for pattern in dangerous_patterns)
