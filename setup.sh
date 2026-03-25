#!/bin/bash

# Event Planner & Approval System - Phase 1 Setup Script
# Target: Kali Linux / Ubuntu

echo "Initializing Event Planner Phase 1..."

# 1. Update and install dependencies
sudo apt update
sudo apt install -y python3-venv python3-pip sqlite3

# 2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize .env file
if [ ! -f .env ]; then
    echo "Creating .env template..."
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
    echo "FLASK_APP=run.py" >> .env
    echo "FLASK_CONFIG=development" >> .env
    echo "PORT=5000" >> .env
fi

# 5. Verify Setup
echo "Verifying installation..."
python3 -m flask --version

echo "Setup Complete! Use 'source venv/bin/activate' and 'python run.py' to start."
