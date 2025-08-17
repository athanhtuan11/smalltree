@echo off
setlocal enabledelayedexpansion

echo 🔍 DEBUGGING INTERNAL SERVER ERROR
echo ==================================
echo.

REM Check if we're in the right directory
if not exist "run.py" (
    echo ❌ Not in project directory! Please cd to nursery-website folder
    pause
    exit /b 1
)

echo 📁 Current directory: %cd%
echo.

REM Check Python version
echo 🐍 Python version:
python --version
echo.

REM Test Flask import
echo 🧪 Testing Flask import...
python -c "
try:
    import flask
    print('✅ Flask imported successfully')
    print(f'Flask version: {flask.__version__}')
except Exception as e:
    print(f'❌ Flask import error: {e}')
    exit(1)
"
echo.

REM Test app creation
echo 🏗️  Testing app creation...
python -c "
try:
    from app import create_app
    app = create_app()
    print('✅ App created successfully')
except Exception as e:
    print(f'❌ App creation error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
if errorlevel 1 (
    echo.
    echo ❌ App creation failed! Check the error above.
    pause
    exit /b 1
)
echo.

REM Check database
echo 💾 Checking database...
if exist "app\site.db" (
    echo ✅ Database file exists: app\site.db
) else (
    echo ⚠️  Database file not found, creating...
    python -c "
from app import create_app
from app.models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database created')
"
)
echo.

REM Check dependencies
echo 📦 Checking critical dependencies...
python -c "
import sys
critical_packages = [
    'flask', 'flask_sqlalchemy', 'flask_migrate', 
    'flask_wtf', 'werkzeug', 'jinja2'
]

for package in critical_packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - MISSING!')
        sys.exit(1)
"
if errorlevel 1 (
    echo.
    echo ❌ Missing dependencies! Installing...
    pip install -r requirements.txt
)
echo.

REM Check for common issues
echo 🔍 Checking for common issues...

REM Check if .env file exists
if exist ".env" (
    echo ✅ .env file exists
) else (
    echo ⚠️  .env file not found, checking .env.production...
    if exist ".env.production" (
        echo ✅ .env.production exists
    ) else (
        echo ❌ No environment file found!
        echo Creating basic .env file...
        echo SECRET_KEY=dev-secret-key-change-in-production > .env
        echo FLASK_ENV=development >> .env
        echo FLASK_DEBUG=1 >> .env
        echo DATABASE_URL=sqlite:///app/site.db >> .env
        echo ✅ Basic .env file created
    )
)

echo.
echo 🚀 Running Flask in debug mode...
echo If there's an error, it will show detailed traceback:
echo ==================================
set FLASK_ENV=development
set FLASK_DEBUG=1
python run.py
pause
