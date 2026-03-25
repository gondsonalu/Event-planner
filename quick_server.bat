@echo off
echo.
echo  --------------------------------------------------------------------
echo   Event Planner ^& Approval System — Phase 6: Security Hardening ^& Polish
echo  --------------------------------------------------------------------
echo.

:: ─── Preflight Checks ──────────────────────────────────────
:: Check virtual environment exists
if not exist "venv" (
    echo  [ERROR] Virtual environment not found.
    echo          Please run  run_server.bat  first to initialize the project.
    echo.
    pause
    exit /b 1
)

:: Check .env file exists
if not exist ".env" (
    echo  [WARNING] .env file is missing. Server may not start correctly.
    echo            Run  run_server.bat  to regenerate it.
    echo.
)

:: ─── Activate Environment ──────────────────────────────────
echo [1/3] Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo       Done.

:: ─── Verify Database ───────────────────────────────────────
echo.
echo [2/3] Verifying database ^& Audit logs...
if not exist "instance" mkdir instance
python -c "from app import create_app, db; from app.models.audit import AuditLog; app = create_app('default'); ctx = app.app_context(); ctx.push(); db.create_all(); print('       Tables OK.'); ctx.pop()" 2>nul
if %errorlevel% neq 0 (
    echo  [WARNING] Could not verify database. Server will attempt recovery.
)

:: ─── Launch Server ─────────────────────────────────────────
echo.
echo [3/3] Starting EventFlow server...
echo.
echo  --------------------------------------------------------------------
echo   URL:          http://127.0.0.1:5000
echo   Registration: http://127.0.0.1:5000/auth/register
echo   Dashboard:    http://127.0.0.1:5000/dashboard
echo.
echo   PHASE 6 FEATURES:
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
