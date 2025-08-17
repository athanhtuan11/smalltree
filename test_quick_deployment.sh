#!/bin/bash

# Quick test deployment script for SmallTree Academy
# Kiểm tra nhanh mọi thứ có hoạt động không

PROJECT_PATH="/home/smalltree/smalltree"
VENV_PATH="$PROJECT_PATH/venv"

echo "=== SmallTree Academy Quick Test ==="

# Test 1: Check project structure
echo "1. Checking project structure..."
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Project directory not found: $PROJECT_PATH"
    exit 1
fi

if [ ! -f "$PROJECT_PATH/run.py" ]; then
    echo "❌ run.py not found"
    exit 1
fi

if [ ! -d "$PROJECT_PATH/app" ]; then
    echo "❌ app directory not found"
    exit 1
fi

echo "✓ Project structure OK"

# Test 2: Check virtual environment
echo "2. Checking virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found: $VENV_PATH"
    exit 1
fi

if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "❌ Virtual environment activation script not found"
    exit 1
fi

echo "✓ Virtual environment OK"

# Test 3: Check .env file
echo "3. Checking environment configuration..."
if [ ! -f "$PROJECT_PATH/.env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

echo "✓ Environment file OK"

# Test 4: Test Flask app
echo "4. Testing Flask application..."
cd $PROJECT_PATH
source $VENV_PATH/bin/activate

export FLASK_APP=run.py
export FLASK_ENV=production

# Test database debug
echo "Running database debug..."
python3 debug_database.py || {
    echo "❌ Database debug failed"
    exit 1
}

echo "✓ Database OK"

# Test 5: Quick app startup test
echo "5. Testing app startup..."
timeout 10 python3 -c "
from app import create_app
import sys
try:
    app = create_app()
    with app.app_context():
        from app.models import db, Child
        db.create_all()
        count = Child.query.count()
        print(f'✓ App startup successful: {count} children in database')
except Exception as e:
    print(f'❌ App startup failed: {e}')
    sys.exit(1)
" || {
    echo "❌ App startup test failed"
    exit 1
}

# Test 6: Check if Gunicorn can start (improved)
echo "6. Testing Gunicorn startup..."

# Test Gunicorn import first
cd $PROJECT_PATH
source $VENV_PATH/bin/activate
python3 -c "
try:
    from run import app
    print('✓ App import for Gunicorn OK')
except Exception as e:
    print(f'❌ App import failed: {e}')
    exit(1)
" || {
    echo "❌ Gunicorn app import test failed"
    exit 1
}

# Test Gunicorn syntax
gunicorn --check-config run:app || {
    echo "❌ Gunicorn config check failed"
    exit 1
}

# Test Gunicorn binding
timeout 10 gunicorn --bind 127.0.0.1:5001 --workers 1 --timeout 30 run:app --daemon --pid /tmp/test_gunicorn.pid || {
    echo "❌ Gunicorn startup failed"
    exit 1
}

# Check if Gunicorn actually started
if [ -f /tmp/test_gunicorn.pid ]; then
    kill $(cat /tmp/test_gunicorn.pid) 2>/dev/null
    rm -f /tmp/test_gunicorn.pid
    echo "✓ Gunicorn startup OK"
else
    echo "❌ Gunicorn PID file not created"
    exit 1
fi

# Test 7: Check permissions
echo "7. Checking file permissions..."
if [ ! -w "$PROJECT_PATH/app" ]; then
    echo "❌ App directory not writable"
    exit 1
fi

echo "✓ Permissions OK"

echo ""
echo "🎉 All tests passed! SmallTree Academy deployment is ready."
echo ""
echo "Next steps:"
echo "1. sudo systemctl start smalltree"
echo "2. sudo systemctl start nginx"
echo "3. Visit http://$(hostname -I | cut -d' ' -f1) to test"
echo ""
