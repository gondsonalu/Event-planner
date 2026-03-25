@echo off
setlocal enabledelayedexpansion

echo.
echo  --------------------------------------------------------------------
echo   Event Planner ^& Approval System — Phase 6: Security Hardening ^& Polish
echo  --------------------------------------------------------------------
echo.

:: ─── Step 1: Check Python Installation ──────────────────────
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo          Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        Found: %%v

:: ─── Step 2: Create Virtual Environment ─────────────────────
echo.
echo [2/7] Setting up virtual environment...
if not exist "venv" (
    echo        Creating new virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo        Virtual environment created successfully.
) else (
    echo        Virtual environment already exists. Skipping.
)

:: ─── Step 3: Activate Virtual Environment ───────────────────
echo.
echo [3/7] Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo        Environment activated.

:: ─── Step 4: Install Dependencies ───────────────────────────
echo.
echo [4/7] Installing / updating dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Dependency installation failed.
    echo          Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo        All dependencies installed.

:: ─── Step 5: Configure Environment Variables ────────────────
echo.
echo [5/7] Configuring environment...
if not exist ".env" (
    echo        .env file not found — generating secure defaults...
    for /f "tokens=*" %%a in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET=%%a
    (
        echo SECRET_KEY=!SECRET!
        echo FLASK_APP=run.py
        echo FLASK_CONFIG=development
        echo FLASK_DEBUG=1
    ) > .env
    echo        .env file created with a secure SECRET_KEY.
) else (
    echo        .env file found. Using existing configuration.
)

:: ─── Step 6: Initialize Database ────────────────────────────
echo.
echo [6/7] Initializing database ^& Audit logs...
if not exist "instance" mkdir instance
python -c "from app import create_app, db; from app.models.audit import AuditLog; app = create_app('default'); ctx = app.app_context(); ctx.push(); db.create_all(); print('        Database tables created / verified.'); ctx.pop()" 2>nul
if %errorlevel% neq 0 (
    echo  [WARNING] Database initialization encountered an issue.
    echo            The server will attempt to create tables on startup.
)

:: ─── Step 7: Seed Sample Data ───────────────────────────────
echo.
echo [7/7] Seeding sample data...
python seed_phase5.py
if %errorlevel% neq 0 (
    echo  [WARNING] Seeding failed. You may need to create users manually.
) else (
    echo        Seed data injected successfully.
)

:: ─── Step 8: Launch Server ──────────────────────────────────
echo.
echo  --------------------------------------------------------------------
echo   [SUCCESS] Phase 6 Environment Ready!
echo  --------------------------------------------------------------------
echo.
echo   Starting EventFlow server...
echo   URL:          http://127.0.0.1:5000
echo   Registration: http://127.0.0.1:5000/auth/register
echo   Dashboard:    http://127.0.0.1:5000/dashboard
echo.
echo   FEATURE UPDATES:
echo   - XSS Protection ^& Rate Limiting
echo   - Session Security ^& CSRF Auto-Refresh
echo   - Workflow Edge Cases ^& Reassignments
echo   - Custom Branded Error Pages
echo.
echo   Press Ctrl+C to stop the server.
echo  --------------------------------------------------------------------
echo.

:: Open browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000/dashboard"

:: Start Flask development server
python run.py

echo.
echo  Server stopped.
pause
