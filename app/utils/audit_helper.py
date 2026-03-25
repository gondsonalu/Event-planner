"""
Audit Helper - Phase 6
Utility function to log actions to the AuditLog table.
Logs failures to app logger instead of printing to stdout.
"""
from flask import request, current_app
from flask_login import current_user
from app import db
from app.models.audit import AuditLog
from datetime import datetime, timezone


def get_client_ip():
    """
    Extract the real client IP address from the request.
    Prioritizes the X-Forwarded-For header if present (useful in production behind proxies like Render/Vercel).
    Falls back to request.remote_addr (useful for localhost).
    
    Security Note (PII): 
    Storing full IP addresses constitutes Personally Identifiable Information (PII) 
    under GDPR and similar privacy laws (as per Section 18 Limitations of project report). 
    This is suitable for internal institutional audit trails but requires care in future compliance.
    """
    if not request:
        return None
        
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For could be a comma-separated list of IPs. The first one is the original client.
        return x_forwarded_for.split(',')[0].strip()
    return request.remote_addr


def log_action(action_type, entity_type=None, entity_id=None, details=None):
    """
    Utility function to log an action to the AuditLog table.
    Silently handles failures by logging to the app logger.
    
    Args:
        action_type (str): Action type, e.g. 'CREATE', 'DELETE', 'LOGIN'
        entity_type (str): Entity type, e.g. 'EVENT', 'USER'
        entity_id (int): ID of the entity affected
        details (str): Human-readable details of the action
    """
    user_id = current_user.id if current_user.is_authenticated else None
    ip_address = get_client_ip()

    log = AuditLog(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        timestamp=datetime.now(timezone.utc),
        ip_address=ip_address,
        details=details
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Log failure to app logger — no stdout print in production
        try:
            current_app.logger.error(f"Failed to save audit log: {e}")
        except RuntimeError:
            pass  # Outside app context — silently ignore
