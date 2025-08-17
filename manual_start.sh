#!/bin/bash

# Manual SmallTree Academy Startup Script
# Để troubleshoot và start manual khi systemd service có vấn đề

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy Manual Startup ==="

# Check if we're the smalltree user
if [ "$(whoami)" != "smalltree" ]; then
    echo "⚠ Running as $(whoami), switching to smalltree user..."
    sudo -u smalltree $0
    exit $?
fi

# Navigate to project
cd $PROJECT_PATH || {
    echo "❌ Cannot access project directory: $PROJECT_PATH"
    exit 1
}

echo "✓ Project directory: $(pwd)"

# Activate virtual environment
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source venv/bin/activate
echo "✓ Virtual environment activated"

# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=production
echo "✓ Environment variables set"

# Create log directories if needed
sudo mkdir -p /var/log/smalltree /var/run/smalltree
sudo chown smalltree:smalltree /var/log/smalltree /var/run/smalltree

# Test Flask app
echo "Testing Flask app..."
python3 -c "
from app import create_app
app = create_app()
print('✓ Flask app test successful')
"

# Kill any existing Gunicorn processes
echo "Cleaning up existing processes..."
pkill -f "gunicorn.*run:app" 2>/dev/null || true
sleep 2

# Start Gunicorn in foreground for debugging
echo "Starting Gunicorn (foreground mode for debugging)..."
echo "Press Ctrl+C to stop"
echo ""

gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 2 \
    --worker-class sync \
    --timeout 60 \
    --keepalive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    run:app
