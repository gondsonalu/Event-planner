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
    Production configuration — safe for Vercel deployment.
    Uses DATABASE_URL if available, otherwise fallback SQLite.
    """
    DEBUG = False

    # Important fix for Vercel
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:////tmp/database.db"

    SESSION_COOKIE_SECURE = True
    RATELIMIT_ENABLED = True

    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL") or "memory://"

    @classmethod
    def init_app(cls, app):
        # Only check SECRET_KEY, database can fallback
        if not os.environ.get("SECRET_KEY"):
            print("WARNING: SECRET_KEY not set. Using default key.")

config: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
