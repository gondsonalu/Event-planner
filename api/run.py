import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create Flask app
app = create_app(os.getenv("FLASK_CONFIG") or "production")

# Vercel serverless entry point
application = app

# Local development ke liye
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)