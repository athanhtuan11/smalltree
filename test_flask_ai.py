#!/usr/bin/env python3
"""
Test Flask App with AI Services
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def test_flask_ai():
    print("🧪 Testing Flask App with AI Services...")
    
    try:
        # Test Flask app creation
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        with app.app_context():
            print("✅ Flask app context activated")
            
            # Test AI routes import
            try:
                from app.routes import ai_menu_fallback, ai_curriculum_fallback
                print("✅ AI routes imported successfully")
            except Exception as e:
                print(f"❌ AI routes failed: {e}")
            
            # Test AI factory
            try:
                from app.ai_factory import get_ai_menu_suggestions, get_ai_curriculum_suggestions
                print("✅ AI Factory imported successfully")
                
                # Test menu generation
                print("🔄 Testing menu generation...")
                menu_result = get_ai_menu_suggestions("2-3 tuổi", 3, "không cay")
                print(f"✅ Menu AI: {str(menu_result)[:100]}...")
                
                # Test curriculum generation
                print("🔄 Testing curriculum generation...")
                curriculum_result = get_ai_curriculum_suggestions("2-3 tuổi", "toán học", 30)
                print(f"✅ Curriculum AI: {str(curriculum_result)[:100]}...")
                
            except Exception as e:
                print(f"❌ AI Factory failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Test Multi-AI service directly
            try:
                from app.multi_ai_service import MultiAIService
                from config import Config
                
                config = {
                    "cohere": {"api_key": Config.COHERE_API_KEY, "model": "command-r"},
                    "groq": {"api_key": Config.GROQ_API_KEY, "model": "llama-3.1-8b-instant"},
                    "priority": ["cohere", "groq"]
                }
                
                ai_service = MultiAIService(config)
                print(f"✅ Multi-AI Service: {list(ai_service.providers.keys())}")
                
                # Test generation
                result = ai_service.generate_text("Tạo thực đơn cho trẻ mầm non 2-3 tuổi")
                if result.get("success"):
                    print(f"✅ AI Generation: {result.get('provider')} - {result.get('text', '')[:50]}...")
                else:
                    print(f"❌ AI Generation failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Multi-AI Service failed: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flask_ai()
