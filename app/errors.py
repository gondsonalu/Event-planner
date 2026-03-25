"""
Error Handlers - Phase 6
Custom branded error handlers for the application.
Prevents stack trace leakage in production while logging internally.
Includes 429 rate limit handler for Flask-Limiter compatibility.
"""
import traceback
from flask import render_template, request
from flask_wtf.csrf import CSRFError


def register_error_handlers(app):
    """
    Registers custom error handlers for the Flask application.
    All errors show branded templates with no internal details exposed.
    """

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handle CSRF token expiration/invalid — show friendly refresh page."""
        app.logger.warning(
            f"CSRF Error on {request.path} from {request.remote_addr}: {e.description}"
        )
        return render_template('errors/csrf_error.html', reason=e.description), 400

    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle malformed requests."""
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle unauthorized access attempts."""
        app.logger.warning(
            f"403 Forbidden: {request.path} by {request.remote_addr}"
        )
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle pages not found."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def ratelimit_error(error):
        """
        Handle rate limit exceeded (Flask-Limiter).
        Returns a user-friendly page, NOT raw JSON.
        """
        app.logger.warning(
            f"Rate limit exceeded on {request.path} by {request.remote_addr}"
        )
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_error(error):
        """
        Handle internal server errors.
        Logs the full stack trace internally but shows
        a generic 'Something went wrong' to the user.
        """
        # Log full traceback for debugging — NEVER expose to user
        app.logger.error(
            f"500 Internal Server Error on {request.path}:\n"
            f"{traceback.format_exc()}"
        )
        return render_template('errors/500.html'), 500
