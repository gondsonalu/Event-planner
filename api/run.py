import os
from dotenv import load_dotenv

load_dotenv()

try:
    from app import create_app

    config_name = os.getenv("FLASK_CONFIG") or "production"
    app = create_app(config_name)

except Exception as e:
    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def error():
        return f"""
        <h1>App Failed to Start</h1>
        <pre>{str(e)}</pre>
        """