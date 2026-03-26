"""
Application Factory - Phase 6
Initializes Flask app, extensions, security middleware, and custom filters.
"""
import os
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import config
from app.utils.logger import setup_logger

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Fix for Vercel / Proxy
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Setup Logging
    setup_logger(app)

    with app.app_context():
        # Import models
        from app.models.user import User
        from app.models.config import SystemConfiguration

        @login_manager.user_loader
        def load_user(user_id):
            user = User.query.get(int(user_id))
            if user and not user.is_active:
                return None
            return user

        # Register Blueprints
        from app.blueprints.main import main_bp
        from app.blueprints.events import events_bp
        from app.blueprints.auth import auth_bp
        from app.blueprints.faculty import faculty_bp
        from app.blueprints.dept_head import dept_head_bp
        from app.blueprints.admin import admin_bp
        from app.blueprints.approvals import approvals_bp
        from app.blueprints.user import user_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(events_bp, url_prefix='/events')
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(faculty_bp, url_prefix='/faculty')
        app.register_blueprint(dept_head_bp, url_prefix='/depthead')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(approvals_bp, url_prefix='/approvals')
        app.register_blueprint(user_bp, url_prefix='/user')

        # IMPORTANT: Auto create tables (fix for Vercel serverless)
        db.create_all()

    # Error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # Template filter
    @app.template_filter('format_inr')
    def format_inr(value):
        try:
            return f"₹{float(value):,.2f}"
        except (ValueError, TypeError):
            return f"₹{value}"

    # Admin contact injector
    @app.context_processor
    def inject_admin_contact():
        from app.models.user import User, UserRole

        admin = User.query.filter_by(role=UserRole.Admin).order_by(User.id.asc()).first()
        if admin:
            return {
                'admin_email': admin.email,
                'admin_phone': admin.contact_number or 'Not provided'
            }

        return {
            'admin_email': 'admin@eventflow.jnujaipur.ac.in',
            'admin_phone': 'System Administrator'
        }

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    # Maintenance mode
    @app.before_request
    def check_maintenance_mode():
        from flask_login import current_user
        from flask import render_template, request
        from app.models.config import SystemConfiguration

        if request.endpoint and (
            'static' in request.endpoint or
            'auth.login' in request.endpoint or
            'auth.logout' in request.endpoint or
            (current_user.is_authenticated and current_user.role.name == 'Admin')
        ):
            return None

        is_maintenance = SystemConfiguration.get_setting('maintenance_mode', False)
        if is_maintenance:
            message = SystemConfiguration.get_setting(
                'maintenance_message',
                'Site is under maintenance.'
            )
            return render_template('errors/503.html', message=message), 503

    # Session lifetime
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    return app