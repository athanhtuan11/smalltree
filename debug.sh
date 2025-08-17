#!/bin/bash

# Simple Debug Script for SmallTree Academy
# Quick troubleshooting tool

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy Debug ==="

# Check user
echo "1. Current user: $(whoami)"

# Check project
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Project directory not found: $PROJECT_PATH"
    exit 1
fi

cd $PROJECT_PATH
echo "2. Project directory: $(pwd)"

# Check ownership
echo "3. Key file ownership:"
ls -la run.py .env app/ 2>/dev/null || echo "Some files missing"

# Check venv
if [ -d "venv" ]; then
    echo "4. Virtual environment: ✓"
    if [ "$(whoami)" = "smalltree" ]; then
        source venv/bin/activate
        echo "   Python: $(python3 --version)"
        echo "   Flask: $(python3 -c 'import flask; print(flask.__version__)' 2>/dev/null || echo 'Not installed')"
        echo "   Gunicorn: $(gunicorn --version 2>/dev/null || echo 'Not installed')"
    fi
else
    echo "4. Virtual environment: ❌"
fi

# Check database
if [ -f "app/site.db" ]; then
    echo "5. Database: ✓ ($(du -h app/site.db | cut -f1))"
else
    echo "5. Database: ❌"
fi

# Check services (if root)
if [ "$EUID" -eq 0 ]; then
    echo "6. Services:"
    systemctl is-active smalltree && echo "   SmallTree: ✓" || echo "   SmallTree: ❌"
    systemctl is-active nginx && echo "   Nginx: ✓" || echo "   Nginx: ❌"
fi

# Quick test
if [ "$(whoami)" = "smalltree" ] && [ -d "venv" ]; then
    echo "7. Quick Flask test:"
    source venv/bin/activate
    python3 -c "
try:
    from app import create_app
    app = create_app()
    print('   Flask import: ✓')
except Exception as e:
    print(f'   Flask import: ❌ {e}')
" 2>/dev/null
fi

echo ""
echo "=== Debug Complete ==="

# Show next steps
if [ "$EUID" -eq 0 ]; then
    echo "Commands to try:"
    echo "  sudo systemctl restart smalltree"
    echo "  sudo journalctl -u smalltree -f"
    echo "  curl http://localhost"
fi
