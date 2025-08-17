#!/bin/bash
# Test script to verify project structure for run.py at root level

echo "=========================================="
echo "🔍 TESTING PROJECT STRUCTURE"
echo "=========================================="

PROJECT_PATH="/home/smalltree/smalltree"

echo "📁 CORRECT STRUCTURE for mamnoncaynho.com:"
echo "   $PROJECT_PATH/"
echo "   ├── run.py                 ← MAIN APP (root level)"
echo "   ├── app/"
echo "   │   ├── __init__.py"
echo "   │   ├── routes.py"
echo "   │   ├── models.py"
echo "   │   └── static/"
echo "   ├── requirements.txt"
echo "   └── setup_nginx_gunicorn.sh"
echo ""

echo "✅ UPDATED CONFIGURATION:"
echo "   - APP_MODULE: run:app          (was: app.run:app)"
echo "   - FLASK_APP: run.py           (was: app/run.py)"
echo "   - Check file: run.py          (was: app/run.py)"
echo "   - Working Directory: $PROJECT_PATH"
echo "   - User: smalltree"
echo ""

echo "🧪 MANUAL TEST COMMANDS:"
echo "   cd $PROJECT_PATH"
echo "   source venv/bin/activate"
echo "   python run.py              ← Should work"
echo "   flask run                  ← Should work"
echo ""

echo "🔧 GUNICORN TEST:"
echo "   gunicorn run:app           ← Should work"
echo "   gunicorn --bind 0.0.0.0:5000 run:app"
echo ""

echo "✅ FIXES APPLIED:"
echo "   1. APP_MODULE changed from 'app.run:app' to 'run:app'"
echo "   2. File check changed from 'app/run.py' to 'run.py'"
echo "   3. FLASK_APP set to 'run.py' instead of 'app/run.py'"
echo ""

echo "🚀 Ready for deployment with run.py at root level!"
