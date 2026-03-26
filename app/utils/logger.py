import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """
    Configures logging for the application.
    INFO level for Development, WARNING for Production.
    Works on Vercel serverless (uses /tmp instead of instance folder).
    """

    # Vercel serverless writable directory
    log_dir = "/tmp"

    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        log_dir = "/tmp"

    log_file = os.path.join(log_dir, "app.log")

    # Log format
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # File Handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Set log level based on environment
    if app.debug:
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
    else:
        app.logger.setLevel(logging.WARNING)
        file_handler.setLevel(logging.WARNING)
        console_handler.setLevel(logging.WARNING)

    # Avoid duplicate handlers on reload
    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)

    app.logger.info("Event Planner System Startup")