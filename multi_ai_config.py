# AI Configuration cho Multi-AI Service
# Cấu hình nhiều AI providers để backup và tăng quota

from config import Config

# ==============================================
# MULTI-AI CONFIGURATION
# ==============================================

class MultiAIConfig:
    """Configuration cho Multi-AI Service"""
    
    # Thứ tự ưu tiên các AI providers
    # Provider đầu tiên sẽ được thử trước
    PRIORITY_ORDER = [
        "cohere",    # Cohere (excellent for education + 1000 calls/month) - TRY FIRST!
        "groq",      # Groq (free tier generous + fast)
        "gemini",    # Gemini 1.5 Pro (current but quota limited)
        "openai",    # OpenAI GPT-4 (high quality)
        "anthropic"  # Claude (safety focused)
    ]
    
    # ==============================================
    # GET KEYS FROM CONFIG.PY
    # ==============================================
    COHERE_API_KEY = getattr(Config, 'COHERE_API_KEY', None)
    COHERE_MODEL = "command-r"  # Best Cohere model for text generation
    
    GEMINI_API_KEY = Config.GEMINI_API_KEY
    GEMINI_MODEL = "gemini-1.5-pro"
    
    GROQ_API_KEY = Config.GROQ_API_KEY
    GROQ_MODEL = "llama-3.1-8b-instant"  # Updated active model
    
    OPENAI_API_KEY = Config.OPENAI_API_KEY
    OPENAI_MODEL = Config.OPENAI_MODEL
    
    ANTHROPIC_API_KEY = Config.ANTHROPIC_API_KEY
    ANTHROPIC_MODEL = Config.ANTHROPIC_MODEL
    
    @classmethod
    def get_config(cls):
        """Return config dictionary cho Multi-AI Service"""
        config = {}
        
        # Cohere - TRY FIRST (excellent for education)
        if cls.COHERE_API_KEY and cls.COHERE_API_KEY != "YOUR_COHERE_API_KEY_HERE":
            config["cohere"] = {
                "api_key": cls.COHERE_API_KEY,
                "model": cls.COHERE_MODEL
            }
        
        # Groq - SECOND (free + fast)
        if cls.GROQ_API_KEY and cls.GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE":
            config["groq"] = {
                "api_key": cls.GROQ_API_KEY,
                "model": cls.GROQ_MODEL
            }
        
        # Gemini - BACKUP
        if cls.GEMINI_API_KEY:
            config["gemini"] = {
                "api_key": cls.GEMINI_API_KEY,
                "model": cls.GEMINI_MODEL
            }
        
        # OpenAI - PAID BACKUP
        if cls.OPENAI_API_KEY:
            config["openai"] = {
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_MODEL
            }
        
        # Anthropic - FINAL BACKUP
        if cls.ANTHROPIC_API_KEY:
            config["anthropic"] = {
                "api_key": cls.ANTHROPIC_API_KEY,
                "model": cls.ANTHROPIC_MODEL
            }
        
        return config

# ==============================================
# QUICK SETUP GUIDE
# ==============================================

"""
🚀 GROQ SETUP ĐÃ SẴN SÀNG!

Chỉ cần:
1. Copy Groq API key của bạn
2. Paste vào config.py tại dòng: GROQ_API_KEY = 'PASTE_HERE'
3. Test: python demo_multi_ai.py

Groq sẽ được thử FIRST (fastest + free 5000 requests/day)
Gemini sẽ là backup nếu Groq fail.

HƯỚNG DẪN NHANH:
1. Vào: https://console.groq.com/ 
2. Login → API Keys → Create API Key
3. Copy key (format: gsk_...)
4. Paste vào config.py
5. python demo_multi_ai.py để test
"""
