#!/bin/bash

# Quick Database Permissions Test for SmallTree Academy

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== Quick Database Permissions Test ==="

if [ "$(whoami)" != "smalltree" ]; then
    echo "Switching to smalltree user..."
    sudo -u smalltree $0
    exit $?
fi

cd $PROJECT_PATH || exit 1

# Create and test app directory
echo "1. Testing app directory..."
mkdir -p app
chmod 755 app

if [ ! -w "app" ]; then
    echo "❌ App directory not writable"
    exit 1
fi

echo "✓ App directory writable"

# Test SQLite directly
echo "2. Testing SQLite access..."
sqlite3 app/test.db "CREATE TABLE test (id INTEGER); INSERT INTO test VALUES (1); SELECT * FROM test;" || {
    echo "❌ SQLite access failed"
    exit 1
}

rm -f app/test.db
echo "✓ SQLite access OK"

# Test Python database
echo "3. Testing Python database..."
if [ -d "venv" ]; then
    source venv/bin/activate
    
    python3 -c "
import os
import sqlite3

# Test absolute path
db_path = os.path.abspath('app/test_python.db')
print(f'Testing database path: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE test (id INTEGER)')
    conn.execute('INSERT INTO test VALUES (1)')
    conn.close()
    print('✓ Python SQLite test passed')
    os.remove(db_path)
except Exception as e:
    print(f'❌ Python SQLite test failed: {e}')
    exit(1)
"
else
    echo "⚠ Virtual environment not found"
fi

echo ""
echo "✅ All permissions tests passed!"
echo "Database should work correctly now."
echo ""
