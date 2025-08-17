#!/usr/bin/env python3
# Quick test for SmallTree Flask app

try:
    print("🧪 Testing SmallTree Flask app...")
    
    from app import create_app
    app = create_app()
    
    print("✅ SmallTree Flask app created successfully!")
    print(f"📊 App name: {app.name}")
    print(f"🔧 Debug mode: {app.debug}")
    print(f"🌐 Instance path: {app.instance_path}")
    
    # Test basic route
    with app.test_client() as client:
        response = client.get('/')
        print(f"🌍 Home page status: {response.status_code}")
        
    print("🚀 SmallTree is ready for Linux deployment!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Run: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
