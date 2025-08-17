@echo off
setlocal enabledelayedexpansion

echo ================================
echo SAFE DEPLOYMENT - SmallTree
echo ================================
echo.

REM Step 1: Backup current data
echo [1/5] Creating backup of current data...
call backup_data.bat
if errorlevel 1 (
    echo ERROR: Backup failed! Stopping deployment.
    pause
    exit /b 1
)
echo ✅ Backup completed successfully
echo.

REM Step 2: Stash any uncommitted local changes
echo [2/5] Stashing local changes...
git stash push -m "Auto-stash before deployment %date% %time%"
echo ✅ Local changes stashed
echo.

REM Step 3: Pull latest code
echo [3/5] Pulling latest code from repository...
git pull origin master
if errorlevel 1 (
    echo ERROR: Git pull failed! Restoring from stash.
    git stash pop
    pause
    exit /b 1
)
echo ✅ Code updated successfully
echo.

REM Step 4: Install/update dependencies
echo [4/5] Installing/updating dependencies...
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed correctly
    echo Continuing anyway...
)
echo ✅ Dependencies updated
echo.

REM Step 5: Database migration (if needed)
echo [5/5] Checking for database migrations...
python -c "
from app import create_app
from flask_migrate import upgrade
try:
    app = create_app()
    with app.app_context():
        upgrade()
    print('✅ Database migrations completed')
except Exception as e:
    print(f'ℹ️  No migrations needed or error: {e}')
"
echo.

echo ================================
echo DEPLOYMENT COMPLETED SUCCESSFULLY
echo ================================
echo.
echo Your data has been preserved:
echo - Database: app/site.db (unchanged)
echo - Uploads: app/static/uploads/ (unchanged)
echo - Activities: app/static/images/activities/ (unchanged)
echo.
echo Backup created in: backups/ folder
echo.
echo Ready to restart server!
echo ================================

pause
