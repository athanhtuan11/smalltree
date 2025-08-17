#!/bin/bash
# Quick test script for requirements.txt

echo "🧪 Testing Requirements Installation"
echo "==================================="

# Check if conda environment exists
if conda info --envs | grep -q "flaskenv"; then
    echo "✅ Conda environment 'flaskenv' found"
    conda activate flaskenv
else
    echo "⚠️  Conda environment 'flaskenv' not found"
    echo "Creating new environment..."
    conda create -n flaskenv python=3.9 -y
    conda activate flaskenv
fi

echo
echo "📦 Installing requirements..."
pip install -r requirements.txt

echo
echo "🧪 Testing imports..."
python -c "
import sys
print(f'Python: {sys.version}')

packages = [
    'flask', 'flask_wtf', 'flask_sqlalchemy', 'flask_migrate',
    'werkzeug', 'jinja2', 'gunicorn', 'PIL', 'openpyxl',
    'docx', 'email_validator', 'wtforms', 'dotenv'
]

failed = []
for package in packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError as e:
        print(f'❌ {package}: {e}')
        failed.append(package)

if failed:
    print(f'\n⚠️  Failed packages: {failed}')
    sys.exit(1)
else:
    print('\n🎉 All packages imported successfully!')
"

echo
echo "🚀 Testing Flask app creation..."
python -c "
try:
    from flask import Flask
    from config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    print('✅ Flask app created successfully')
except Exception as e:
    print(f'❌ Flask app creation failed: {e}')
    exit(1)
"

echo
echo "✅ Requirements test completed successfully!"
echo "You can now run: python run.py"
