#!/bin/bash
# Debug script for Internal Server Error

echo "🔍 DEBUGGING INTERNAL SERVER ERROR"
echo "=================================="
echo

# Check if we're in the right directory
if [ ! -f "run.py" ]; then
    echo "❌ Not in project directory! Please cd to nursery-website folder"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo

# Check Python version
echo "🐍 Python version:"
python3 --version 2>/dev/null || python --version
echo

# Test Flask import
echo "🧪 Testing Flask import..."
python3 -c "
try:
    import flask
    print('✅ Flask imported successfully')
    print(f'Flask version: {flask.__version__}')
except Exception as e:
    print(f'❌ Flask import error: {e}')
    exit(1)
"
echo

# Test app creation
echo "🏗️  Testing app creation..."
python3 -c "
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
echo

# Check database
echo "💾 Checking database..."
if [ -f "app/site.db" ]; then
    echo "✅ Database file exists: app/site.db"
    echo "📊 Database size: $(du -h app/site.db | cut -f1)"
else
    echo "⚠️  Database file not found, creating..."
    python3 -c "
from app import create_app
from app.models import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database created')
"
fi
echo

# Check dependencies
echo "📦 Checking critical dependencies..."
python3 -c "
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
echo

# Check for common issues
echo "🔍 Checking for common issues..."

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "⚠️  .env file not found, checking .env.production..."
    if [ -f ".env.production" ]; then
        echo "✅ .env.production exists"
    else
        echo "❌ No environment file found!"
        echo "Creating basic .env file..."
        cat > .env << EOF
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///app/site.db
EOF
        echo "✅ Basic .env file created"
    fi
fi

# Check file permissions
echo
echo "🔐 Checking file permissions..."
if [ -w "app/site.db" ] 2>/dev/null; then
    echo "✅ Database is writable"
elif [ -f "app/site.db" ]; then
    echo "❌ Database exists but not writable"
    chmod 666 app/site.db
    echo "✅ Fixed database permissions"
fi

if [ -w "app" ]; then
    echo "✅ App directory is writable"
else
    echo "❌ App directory not writable"
fi

echo
echo "🚀 Running Flask in debug mode..."
echo "If there's an error, it will show detailed traceback:"
echo "=================================="
FLASK_ENV=development FLASK_DEBUG=1 python3 run.py
