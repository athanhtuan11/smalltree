#!/bin/bash

# Database Permissions Debug Script for SmallTree Academy
# Kiểm tra và fix permissions cho SQLite database

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy Database Permissions Debug ==="

# Check if we're the smalltree user
current_user=$(whoami)
echo "1. Current user: $current_user"

if [ "$current_user" != "smalltree" ]; then
    echo "Switching to smalltree user..."
    sudo -u smalltree $0
    exit $?
fi

# Navigate to project
cd $PROJECT_PATH || {
    echo "❌ Cannot access project directory: $PROJECT_PATH"
    exit 1
}

echo "2. Project directory: $(pwd)"

# Check venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

source venv/bin/activate
echo "3. Virtual environment activated"

# Check app directory
echo "4. Checking app directory..."
if [ ! -d "app" ]; then
    echo "Creating app directory..."
    mkdir -p app
fi

ls -la app/
echo "App directory permissions: $(ls -ld app/)"

# Check if we can write to app directory
if [ -w "app" ]; then
    echo "✓ App directory is writable"
else
    echo "❌ App directory is not writable"
    echo "Fixing permissions..."
    chmod 755 app
fi

# Test database file creation
echo "5. Testing database file creation..."
DB_FILE="app/site.db"

# Remove existing database for test
if [ -f "$DB_FILE" ]; then
    echo "Removing existing database for test..."
    rm -f "$DB_FILE"
fi

# Test SQLite directly
echo "6. Testing SQLite directly..."
sqlite3 "$DB_FILE" "CREATE TABLE test (id INTEGER); DROP TABLE test;" || {
    echo "❌ SQLite cannot create database file"
    echo "Checking permissions..."
    ls -la app/
    exit 1
}

if [ -f "$DB_FILE" ]; then
    echo "✓ SQLite can create database file"
    echo "Database file: $(ls -la $DB_FILE)"
    rm -f "$DB_FILE"
else
    echo "❌ Database file not created"
    exit 1
fi

# Test Python database creation
echo "7. Testing Python database creation..."
python3 -c "
import os
import sys
sys.path.insert(0, os.getcwd())

# Test environment loading
from dotenv import load_dotenv
load_dotenv()

db_url = os.environ.get('DATABASE_URL', 'NOT_SET')
print(f'DATABASE_URL from env: {db_url}')

# Test basic SQLite
import sqlite3
db_file = 'app/test_python.db'
try:
    conn = sqlite3.connect(db_file)
    conn.execute('CREATE TABLE test (id INTEGER)')
    conn.close()
    print(f'✓ Python SQLite test passed: {db_file}')
    os.remove(db_file)
except Exception as e:
    print(f'❌ Python SQLite test failed: {e}')
    sys.exit(1)

# Test Flask app
try:
    print('Testing Flask app database...')
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.models import db
        print(f'Database URI: {app.config[\"SQLALCHEMY_DATABASE_URI\"]}')
        
        # Try to create tables
        db.create_all()
        print('✓ Flask database creation successful')
        
        # Check if file was created
        import re
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        if uri.startswith('sqlite:///'):
            db_path = uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                print(f'✓ Database file created: {db_path} ({size} bytes)')
            else:
                print(f'❌ Database file not found: {db_path}')
                sys.exit(1)
        
except Exception as e:
    print(f'❌ Flask database test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "✅ Database permissions debug completed successfully!"
echo ""
echo "Directory structure:"
ls -la app/ 2>/dev/null || echo "No files in app directory"
echo ""
echo "If issues persist:"
echo "  1. Check disk space: df -h"
echo "  2. Check SELinux: getenforce"
echo "  3. Check directory ownership: ls -la"
echo ""
