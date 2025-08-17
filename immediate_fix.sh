#!/bin/bash

# IMMEDIATE FIX for SmallTree Academy Database Issues
# Based on the ownership problems identified

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== IMMEDIATE DATABASE FIX ==="
echo "Identified issue: File ownership (root vs smalltree)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

cd $PROJECT_PATH

echo "1. FIXING OWNERSHIP (root cause)..."
chown -R smalltree:smalltree $PROJECT_PATH
chmod 755 $PROJECT_PATH/app

echo "2. TESTING DATABASE ACCESS..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    
    # Test directory access
    if [ ! -w app ]; then
        echo '❌ App directory still not writable after ownership fix'
        exit 1
    fi
    
    echo '✓ App directory is now writable'
    
    # Test SQLite directly
    sqlite3 app/test.db 'CREATE TABLE test (id INTEGER); DROP TABLE test;'
    rm -f app/test.db
    echo '✓ SQLite direct access works'
    
    # Test with venv
    if [ -d venv ]; then
        source venv/bin/activate
        
        # Test Flask database
        python3 -c \"
import os
import sys
sys.path.insert(0, os.getcwd())

# Use absolute path
db_path = os.path.abspath('app/site.db')
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

try:
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.models import db
        db.create_all()
        print(f'✅ DATABASE CREATED SUCCESSFULLY: {db_path}')
        
        # Test query
        from app.models import Child
        count = Child.query.count()
        print(f'✅ Database query works: {count} children')
        
except Exception as e:
    print(f'❌ Flask database failed: {e}')
    exit(1)
\"
    fi
"

echo ""
echo "3. FINAL VERIFICATION..."
ls -la $PROJECT_PATH/app/

echo ""
echo "🎉 IMMEDIATE FIX COMPLETED!"
echo ""
echo "Database should now work. Next steps:"
echo "1. sudo systemctl restart smalltree"
echo "2. Check: curl http://localhost"
echo ""
echo "If still issues, run: sudo bash quick_sqlalchemy_fix.sh"
echo ""
