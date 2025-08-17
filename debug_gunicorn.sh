#!/bin/bash

# Gunicorn Debug Script for SmallTree Academy
# Kiểm tra và troubleshoot Gunicorn issues

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy Gunicorn Debug ==="

# Check if running as smalltree user
current_user=$(whoami)
echo "1. Current user: $current_user"

# Navigate to project
cd $PROJECT_PATH || {
    echo "❌ Cannot access project directory: $PROJECT_PATH"
    exit 1
}

echo "2. Project directory: $(pwd)"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

echo "3. Activating virtual environment..."
source venv/bin/activate

# Check Python packages
echo "4. Checking required packages..."
python3 -c "
import sys
required = ['flask', 'gunicorn', 'flask_sqlalchemy']
missing = []
for pkg in required:
    try:
        __import__(pkg.replace('_', '.'))
        print(f'✓ {pkg}')
    except ImportError:
        missing.append(pkg)
        print(f'❌ {pkg}')
if missing:
    print(f'Missing packages: {missing}')
    sys.exit(1)
"

# Check Flask app
echo "5. Testing Flask app import..."
python3 -c "
try:
    from app import create_app
    app = create_app()
    print('✓ Flask app import successful')
except Exception as e:
    print(f'❌ Flask app import failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

# Check run.py
echo "6. Testing run.py import..."
python3 -c "
try:
    from run import app
    print('✓ run.py import successful')
except Exception as e:
    print(f'❌ run.py import failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

# Test Gunicorn syntax
echo "7. Testing Gunicorn syntax..."
gunicorn --check-config run:app || {
    echo "❌ Gunicorn config check failed"
    exit 1
}
echo "✓ Gunicorn config OK"

# Test Gunicorn binding
echo "8. Testing Gunicorn binding..."
timeout 5 gunicorn --bind 127.0.0.1:5555 --workers 1 run:app --daemon --pid /tmp/debug_gunicorn.pid

if [ -f /tmp/debug_gunicorn.pid ]; then
    echo "✓ Gunicorn can bind and start"
    kill $(cat /tmp/debug_gunicorn.pid) 2>/dev/null
    rm -f /tmp/debug_gunicorn.pid
else
    echo "❌ Gunicorn failed to start"
    exit 1
fi

# Check log directories
echo "9. Checking log directories..."
if [ ! -d "/var/log/smalltree" ]; then
    echo "❌ Log directory missing: /var/log/smalltree"
    exit 1
fi

if [ ! -w "/var/log/smalltree" ]; then
    echo "❌ Log directory not writable: /var/log/smalltree"
    exit 1
fi

echo "✓ Log directory OK"

# Check PID directory
echo "10. Checking PID directory..."
if [ ! -d "/var/run/smalltree" ]; then
    echo "❌ PID directory missing: /var/run/smalltree"
    exit 1
fi

if [ ! -w "/var/run/smalltree" ]; then
    echo "❌ PID directory not writable: /var/run/smalltree"
    exit 1
fi

echo "✓ PID directory OK"

# Test systemd service
echo "11. Testing systemd service..."
if systemctl is-active --quiet smalltree; then
    echo "✓ SmallTree service is active"
else
    echo "⚠ SmallTree service is not active"
    echo "Service status:"
    systemctl status smalltree --no-pager -l
fi

echo ""
echo "=== Gunicorn Debug Complete ==="
echo ""
echo "Manual Gunicorn start commands:"
echo "  cd $PROJECT_PATH"
echo "  source venv/bin/activate"
echo "  gunicorn --bind 127.0.0.1:5000 run:app"
echo ""
echo "Service management:"
echo "  sudo systemctl start smalltree"
echo "  sudo systemctl status smalltree"
echo "  sudo journalctl -u smalltree -f"
echo ""
