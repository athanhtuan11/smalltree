#!/bin/bash

# SQLAlchemy Version Fix Script for SmallTree Academy
# Fixes Flask-SQLAlchemy compatibility issues

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SQLAlchemy Version Fix ==="

# Check if we're in the right directory
if [ ! -f "$PROJECT_PATH/run.py" ]; then
    echo "❌ Please run this from the project directory: $PROJECT_PATH"
    exit 1
fi

cd $PROJECT_PATH

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "1. Checking current SQLAlchemy version..."
python3 -c "
try:
    import sqlalchemy
    print(f'Current SQLAlchemy version: {sqlalchemy.__version__}')
except ImportError:
    print('SQLAlchemy not installed')
"

echo "2. Checking Flask-SQLAlchemy version..."
python3 -c "
try:
    import flask_sqlalchemy
    print(f'Current Flask-SQLAlchemy version: {flask_sqlalchemy.__version__}')
except ImportError:
    print('Flask-SQLAlchemy not installed')
"

echo "3. Installing compatible versions..."
pip install --upgrade "SQLAlchemy>=1.4,<2.0" "Flask-SQLAlchemy==2.5.1"

echo "4. Testing compatibility..."
python3 -c "
try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    class TestModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)
    
    with app.app_context():
        db.create_all()
        print('✓ SQLAlchemy compatibility test passed')
        
    import os
    if os.path.exists('test.db'):
        os.remove('test.db')
        
except Exception as e:
    print(f'❌ Compatibility test failed: {e}')
    exit(1)
"

echo "5. Testing SmallTree app..."
python3 -c "
try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import db
        db.create_all()
        print('✓ SmallTree app database test passed')
except Exception as e:
    print(f'❌ SmallTree app test failed: {e}')
    print('You may need to check your app configuration')
    exit(1)
"

echo ""
echo "✅ SQLAlchemy version fix completed successfully!"
echo ""
echo "Installed versions:"
python3 -c "
import sqlalchemy, flask_sqlalchemy
print(f'SQLAlchemy: {sqlalchemy.__version__}')
print(f'Flask-SQLAlchemy: {flask_sqlalchemy.__version__}')
"
echo ""
