#!/bin/bash

# SmallTree Academy AI Services Test Script
# Test all AI services after deployment

echo "🧪 Testing SmallTree AI Services..."

PROJECT_PATH="/home/smalltree/smalltree"

if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Project path not found: $PROJECT_PATH"
    exit 1
fi

cd $PROJECT_PATH

# Test with virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Test AI packages installation
echo ""
echo "📦 Testing AI Package Installations:"

packages=("cohere" "groq" "google.generativeai" "openai" "anthropic")
for package in "${packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "   ✅ $package"
    else
        echo "   ❌ $package - NOT INSTALLED"
    fi
done

# Test AI services
echo ""
echo "🤖 Testing AI Services:"

# Run the comprehensive test
if [ -f "test_ai.py" ]; then
    python3 test_ai.py
else
    echo "⚠️ test_ai.py not found, running basic test..."
    
    python3 -c "
try:
    from config import Config
    print('✅ Config loaded')
    print(f'   COHERE: {\"✅\" if Config.COHERE_API_KEY else \"❌\"}')
    print(f'   GROQ: {\"✅\" if Config.GROQ_API_KEY else \"❌\"}')
    
    from app.ai_factory import ai_service
    result = ai_service.generate_text('Test AI generation for SmallTree Academy')
    
    if result.get('success'):
        print('✅ AI Generation Test Successful')
        print(f'   Provider: {result.get(\"provider\", \"unknown\")}')
    else:
        print('❌ AI Generation Test Failed')
        print(f'   Error: {result.get(\"error\", \"Unknown\")}')
        
except Exception as e:
    print(f'❌ AI Test Error: {e}')
    import traceback
    traceback.print_exc()
"
fi

echo ""
echo "🎯 AI Services Test Complete!"
echo ""
echo "💡 If tests fail:"
echo "   1. Check API keys in config.py"
echo "   2. Install missing packages: pip install cohere groq google-generativeai"
echo "   3. Check internet connection"
echo "   4. Review logs: sudo journalctl -u smalltree -f"
