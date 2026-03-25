"""
Application Configuration - Phase 6
Production-ready configuration with distinct Development and Production classes.
All secrets are loaded from Environment Variables in production.
"""
import os
from typing import Dict, Type
from datetime import timedelta


class Config:
    """
    Base configuration class.
    Shared settings across all environments.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session Security (Section 12 - Security Design) ─────────────
    SESSION_COOKIE_HTTPONLY = True       # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SECURE = True        # HTTPS only (overridden in dev)
    SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection via SameSite
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # 30 min inactivity timeout

    # ── Flask-Limiter Configuration ─────────────────────────────────
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_HEADERS_ENABLED = True

    # ── Content Security ────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # ── Rate Limit Tiers (used in blueprints) ───────────────────────
    # Students: strict limits on submissions
    STUDENT_SUBMIT_LIMIT = "5 per day"
    # Approvers/Admins: higher ceilings for bulk reviews
    APPROVER_ACTION_LIMIT = "100 per day"
    ADMIN_ACTION_LIMIT = "200 per day"


class DevelopmentConfig(Config):
    """Development configuration — relaxed security for local testing."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'dev.db')

    # Allow HTTP in development
    SESSION_COOKIE_SECURE = False
    # Disable rate limiting in dev for testing ease
    RATELIMIT_ENABLED = False


class TestingConfig(Config):
    """Testing configuration — for automated tests."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """
    Production configuration — maximum security.
    All secrets MUST come from environment variables.
    """
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Strict security in production
    SESSION_COOKIE_SECURE = True
    RATELIMIT_ENABLED = True

    # Use Redis for rate limiting in production (if available)
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL') or "memory://"

    @classmethod
    def init_app(cls, app):
        """Validate critical environment variables on startup."""
        assert os.environ.get('SECRET_KEY'), \
            "CRITICAL: SECRET_KEY must be set in environment for Production!"
        assert os.environ.get('DATABASE_URL'), \
            "CRITICAL: DATABASE_URL must be set in environment for Production!"


config: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
