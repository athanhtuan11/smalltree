#!/usr/bin/env python3
"""
Test AI Services for SmallTree Academy - COMPLETE CHECK
Test Cohere and Groq after Gemini quota exceeded
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_services():
    print("🧪 Testing AI Services - COMPLETE CHECK...")
    
    # Test 1: Config loading
    try:
        from config import Config
        print(f"✅ Config loaded")
        print(f"   COHERE: {'✅' if Config.COHERE_API_KEY else '❌'}")
        print(f"   GROQ: {'✅' if Config.GROQ_API_KEY else '❌'}")
        print(f"   GEMINI: {'✅' if Config.GEMINI_API_KEY else '❌'}")
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return
    
    # Test 2: Package installations
    print("\n📦 Testing AI Package Installations:")
    packages = [
        ("cohere", "Cohere AI"),
        ("groq", "Groq AI"), 
        ("google.generativeai", "Google Gemini"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic Claude")
    ]
    
    for package, name in packages:
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - NOT INSTALLED")
    
    # Test 3: Multi-AI Service
    print("\n🤖 Testing Multi-AI Service:")
    try:
        from app.multi_ai_service import MultiAIService
        config = {
            "cohere": {"api_key": Config.COHERE_API_KEY, "model": "command-r"},
            "groq": {"api_key": Config.GROQ_API_KEY, "model": "llama-3.1-8b-instant"},
            "priority": ["cohere", "groq"]
        }
        
        ai_service = MultiAIService(config)
        print(f"   ✅ Multi-AI Service initialized")
        print(f"   📋 Providers: {list(ai_service.providers.keys())}")
        
        # Test simple generation
        print("   🔄 Testing AI generation...")
        result = ai_service.generate_text("Xin chào! Bạn có thể giúp tôi tạo thực đơn cho trẻ mầm non không?")
        
        if result.get("success"):
            print(f"   ✅ AI Generation successful")
            print(f"   🎯 Provider: {result.get('provider', 'unknown')}")
            print(f"   💬 Text: {result.get('text', '')[:100]}...")
        else:
            print(f"   ❌ AI Generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Multi-AI Service failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: AI Factory
    print("\n🏭 Testing AI Factory:")
    try:
        from app.ai_factory import get_ai_menu_suggestions, get_ai_curriculum_suggestions
        
        # Test menu suggestions
        print("   🔄 Testing menu suggestions...")
        menu_result = get_ai_menu_suggestions("2-3 tuổi", 3, "không cay")
        print(f"   ✅ Menu AI: {str(menu_result)[:100]}...")
        
        # Test curriculum suggestions  
        print("   🔄 Testing curriculum suggestions...")
        curriculum_result = get_ai_curriculum_suggestions("2-3 tuổi", "toán học", 30)
        print(f"   ✅ Curriculum AI: {str(curriculum_result)[:100]}...")
        
    except Exception as e:
        print(f"   ❌ AI Factory failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Enhanced AI Services
    print("\n⚡ Testing Enhanced AI Services:")
    try:
        from app.enhanced_menu_ai import get_ai_menu_suggestions_enhanced
        print("   ✅ Enhanced Menu AI imported")
    except Exception as e:
        print(f"   ❌ Enhanced Menu AI failed: {e}")
        
    try:
        from app.enhanced_curriculum_ai import get_ai_curriculum_suggestions_enhanced
        print("   ✅ Enhanced Curriculum AI imported")
    except Exception as e:
        print(f"   ❌ Enhanced Curriculum AI failed: {e}")
    
    # Test 6: Routes AI import
    print("\n🛣️  Testing Routes AI Integration:")
    try:
        from app.routes import ai_menu_fallback, ai_curriculum_fallback
        print("   ✅ AI fallback functions imported")
    except Exception as e:
        print(f"   ❌ Routes AI integration failed: {e}")
    
    print("\n🎯 AI Services Test Complete!")

if __name__ == "__main__":
    test_ai_services()
