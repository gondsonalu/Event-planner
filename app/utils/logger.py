import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """
    Configures logging for the application.
    INFO level for Development, WARNING for Production.
    """
    if not os.path.exists('instance'):
        os.makedirs('instance')

    # Log format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # File Handler
    file_handler = RotatingFileHandler(
        'instance/app.log', maxBytes=10240, backupCount=10
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

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    app.logger.info('Event Planner System Startup')

