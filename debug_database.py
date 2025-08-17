#!/usr/bin/env python3
"""
Database debug script for SmallTree Academy
Kiểm tra kết nối database và khởi tạo schema - Compatible with optimized deployment
"""

import os
import sys
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_database():
    """Debug database configuration and connection"""
    
    print("=== SmallTree Academy Database Debug (Optimized) ===")
    
    # Load environment variables
    load_dotenv()
    
    print(f"1. Current working directory: {os.getcwd()}")
    print(f"2. Project directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Check virtual environment
    venv_path = os.path.join(os.getcwd(), 'venv')
    print(f"3. Virtual environment: {venv_path}")
    print(f"   venv exists: {os.path.exists(venv_path)}")
    if os.path.exists(venv_path):
        activate_script = os.path.join(venv_path, 'bin', 'activate')
        print(f"   activate script: {os.path.exists(activate_script)}")
    
    # Check environment variables
    database_url = os.environ.get('DATABASE_URL', 'NOT_SET')
    flask_env = os.environ.get('FLASK_ENV', 'NOT_SET')
    secret_key = os.environ.get('SECRET_KEY', 'NOT_SET')
    
    print(f"4. DATABASE_URL: {database_url}")
    print(f"5. FLASK_ENV: {flask_env}")
    print(f"6. SECRET_KEY: {'SET' if secret_key != 'NOT_SET' else 'NOT_SET'}")
    
    # Check .env file exists
    env_file = os.path.join(os.getcwd(), '.env')
    print(f"7. .env file exists: {os.path.exists(env_file)}")
    if os.path.exists(env_file):
        print(f"   .env file path: {env_file}")
        with open(env_file, 'r') as f:
            print("   .env contents:")
            for line in f:
                if 'SECRET_KEY' not in line:  # Don't show secret key
                    print(f"   {line.strip()}")
                else:
                    print(f"   SECRET_KEY=***")
    
    # Check database directory and file
    if database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        if not db_path.startswith('/'):  # Relative path
            db_path = os.path.join(os.getcwd(), db_path)
        
        db_dir = os.path.dirname(db_path)
        print(f"8. Database directory: {db_dir}")
        print(f"   Directory exists: {os.path.exists(db_dir)}")
        print(f"   Directory writable: {os.access(db_dir, os.W_OK) if os.path.exists(db_dir) else 'N/A'}")
        print(f"9. Database file: {db_path}")
        print(f"   File exists: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            print(f"   File size: {os.path.getsize(db_path)} bytes")
    
    try:
        # Import and test Flask app
        print("\n10. Testing Flask app import...")
        from app import create_app
        print("    ✓ Flask app imported successfully")
        
        app = create_app()
        print("    ✓ Flask app created successfully")
        
        with app.app_context():
            print("    ✓ Flask app context created")
            
            # Test database connection
            from app.models import db
            print("    ✓ Database models imported")
            
            # Try to create tables
            db.create_all()
            print("    ✓ Database tables created successfully")
            
            # Test basic query
            from app.models import Child
            children_count = Child.query.count()
            print(f"    ✓ Database query successful: {children_count} children in database")
            
    except Exception as e:
        print(f"\n❌ Error testing Flask app: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ Database debug completed successfully!")
    print("🚀 Ready for production deployment!")
    return True

if __name__ == '__main__':
    debug_database()
