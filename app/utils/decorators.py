from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to protect routes based on UserRole enum names.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role.value not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def owner_or_role_required(model, id_param, owner_field='created_by', *admin_roles):
    """
    Decorator to check if user owns the resource OR has a specific admin role.
    Assumes the route has <id_param> in kwargs, fetches the model by id_param.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            item_id = kwargs.get(id_param)
            if not item_id:
                abort(400)
                
            item = model.query.get_or_404(item_id)
            owner_id = getattr(item, owner_field)
            
            if owner_id != current_user.id and current_user.role.value not in admin_roles:
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
