#!/bin/bash

# Manual installation guide for SmallTree Academy on slower servers
# Run this step by step to avoid timeout issues

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy Manual Installation Guide ==="
echo ""

echo "1. CORE PACKAGES (Install first - REQUIRED):"
echo "   cd $PROJECT_PATH && source venv/bin/activate"
echo "   pip install Flask==2.0.3"
echo "   pip install Flask-WTF==0.15.1"
echo "   pip install Flask-SQLAlchemy==2.5.1"
echo "   pip install Flask-Migrate==3.1.0"
echo "   pip install gunicorn==20.1.0"
echo "   pip install python-dotenv==0.19.2"
echo ""

echo "2. FORM VALIDATION (Install second - REQUIRED):"
echo "   pip install email_validator==1.3.1"
echo "   pip install WTForms==3.0.1"
echo ""

echo "3. OPTIONAL PACKAGES (Install if needed):"
echo "   # Document processing"
echo "   pip install python-docx==1.0.1"
echo "   pip install openpyxl"
echo ""
echo "   # Image processing (may fail on some systems)"
echo "   pip install Pillow"
echo ""

echo "4. AI SERVICES (Install if using AI features):"
echo "   pip install google-generativeai"
echo "   pip install requests"
echo ""

echo "5. TEST INSTALLATION:"
echo "   python3 -c \"from app import create_app; print('✓ Flask app import successful')\""
echo ""

echo "6. QUICK INSTALL SCRIPT (all at once - may timeout):"
echo "   pip install -r requirements_minimal.txt"
echo ""

echo "After installation, run:"
echo "   sudo bash setup_nginx_gunicorn.sh"
echo ""
