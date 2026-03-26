import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Select config
config_name = os.getenv("FLASK_CONFIG") or "production"

# Create Flask app
app = create_app(config_name)

# Vercel expects a variable named "app"
# Do not rename this