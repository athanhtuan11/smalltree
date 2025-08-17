#!/usr/bin/env python3
"""
Test AI Services for SmallTree Academy
Test Cohere and Groq after Gemini quota exceeded
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_services():
    print("🧪 Testing AI Services...")
    
    # Test 1: Config loading
    try:
        from config import Config
        print(f"✅ Config loaded")
        print(f"   COHERE: {'✅' if Config.COHERE_API_KEY else '❌'}")
        print(f"   GROQ: {'✅' if Config.GROQ_API_KEY else '❌'}")
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return
    
    # Test 2: Multi-AI Service
    try:
        from app.multi_ai_service import MultiAIService
        config = {
            "cohere": {"api_key": Config.COHERE_API_KEY, "model": "command-r"},
            "groq": {"api_key": Config.GROQ_API_KEY, "model": "llama-3.1-8b-instant"},
            "priority": ["cohere", "groq"]
        }
        
        ai_service = MultiAIService(config)
        print(f"✅ Multi-AI Service initialized")
        print(f"   Providers: {list(ai_service.providers.keys())}")
        
        # Test simple generation
        result = ai_service.generate_text("Xin chào! Bạn có thể giúp tôi tạo thực đơn cho trẻ mầm non không?")
        
        if result.get("success"):
            print(f"✅ AI Generation successful")
            print(f"   Provider: {result.get('provider', 'unknown')}")
            print(f"   Text (first 100 chars): {result.get('text', '')[:100]}...")
        else:
            print(f"❌ AI Generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Multi-AI Service failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: AI Factory
    try:
        from app.ai_factory import get_ai_menu_suggestions
        result = get_ai_menu_suggestions("2-3 tuổi", 3, "không cay")
        print(f"✅ AI Factory menu test")
        print(f"   Result: {str(result)[:100]}...")
    except Exception as e:
        print(f"❌ AI Factory failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_services()
