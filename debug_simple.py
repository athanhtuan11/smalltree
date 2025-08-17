#!/usr/bin/env python3
"""Debug script đơn giản để kiểm tra lỗi cơ bản nhất"""

import sys
import os

print("=== QUICK DEBUG SCRIPT ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Test 1: Import cơ bản
try:
    import flask
    print(f"✅ Flask version: {flask.__version__}")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

# Test 2: App creation
try:
    from flask import Flask
    from config import Config
    
    app = Flask(__name__)
    app.config.from_object(Config)
    print("✅ Flask app created successfully")
except Exception as e:
    print(f"❌ Flask app creation failed: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Database import
try:
    from app.models import db
    print("✅ Database models imported")
except Exception as e:
    print(f"❌ Database import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Routes import
try:
    from app.routes import main
    print("✅ Routes imported successfully")
except Exception as e:
    print(f"❌ Routes import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Debug completed ===")
print("If all tests pass, run: python run.py")
