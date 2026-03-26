import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Flask config select
config_name = os.getenv("FLASK_CONFIG") or "production"

# Create app
app = create_app(config_name)

# Vercel expects this variable
application = app

# Local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=(config_name == "development"))