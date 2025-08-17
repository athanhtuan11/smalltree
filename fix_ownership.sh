#!/bin/bash

# Fix Ownership Issues for SmallTree Academy
# Run as root to fix file ownership problems

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy Ownership Fix ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

cd $PROJECT_PATH || {
    echo "❌ Cannot access project directory: $PROJECT_PATH"
    exit 1
}

echo "1. Current ownership issues:"
ls -la | grep -E "(root|smalltree)" | head -10

echo ""
echo "2. Fixing ownership for all files..."
chown -R smalltree:smalltree $PROJECT_PATH

echo "3. Setting proper permissions..."
# Fix directory permissions
find $PROJECT_PATH -type d -exec chmod 755 {} \;

# Fix file permissions (readable for owner and group)
find $PROJECT_PATH -type f -exec chmod 644 {} \;

# Fix executable scripts
chmod +x $PROJECT_PATH/*.sh
chmod +x $PROJECT_PATH/venv/bin/*

# Ensure app directory is writable
mkdir -p $PROJECT_PATH/app
chmod 755 $PROJECT_PATH/app

# Ensure .env is secure but readable
if [ -f "$PROJECT_PATH/.env" ]; then
    chmod 600 $PROJECT_PATH/.env
fi

echo "4. Verifying ownership..."
echo "Project directory:"
ls -ld $PROJECT_PATH

echo ""
echo "Key files:"
ls -la $PROJECT_PATH | grep -E "(run.py|.env|app)" | head -5

echo ""
echo "App directory:"
ls -la $PROJECT_PATH/app/

echo ""
echo "✅ Ownership fix completed!"
echo ""
echo "Now run database test:"
echo "  sudo -u smalltree bash test_db_permissions.sh"
echo ""
