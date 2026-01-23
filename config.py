import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    
    # Database configuration: ưu tiên DATABASE_URL (PostgreSQL hoặc SQLite)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "app", "site.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB cho 100 ảnh @ 2MB/ảnh
    
    # LLM Farm API Configuration - Bosch GenAI Platform
    LLM_FARM_API_KEY = os.environ.get('LLM_FARM_API_KEY') or '5707f722220e48a889aecccce0406a74'
    LLM_FARM_BASE_URL = os.environ.get('LLM_FARM_BASE_URL') or 'https://aoai-farm.bosch-temp.com'
    LLM_FARM_MODEL = os.environ.get('LLM_FARM_MODEL') or 'askbosch-prod-farm-openai-gpt-4o-mini-2024-07-18'
    LLM_FARM_API_VERSION = os.environ.get('LLM_FARM_API_VERSION') or '2024-08-01-preview'
      
    # Google Gemini API Configuration
    # ⚠️ API KEY HIỆN TẠI ĐÃ HẾT QUOTA! Cần thay đổi:
    # 1. Truy cập: https://ai.google.dev/gemini-api
    # 2. Tạo API key mới  
    # 3. Thay thế key bên dưới
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSyChKUMAlHaOj29YXh4POZbgzPRvCmCa9pQ'
    
    # 🎯 COHERE AI Configuration (Excellent for Education)
    # Cohere API Key từ: https://dashboard.cohere.ai/
    # Free tier: 1,000 calls/month, quality tốt cho educational content
    # PASTE COHERE API KEY CỦA BẠN VÀO ĐÂY ⬇️
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY') or 'J4NQeZN0iLquKjAJnOsEd0pjLbS0hGKPsmFaE4C3'
    
    # YouTube Data API v3 Configuration
    # Get your API key from: https://console.cloud.google.com/apis/credentials
    # Enable YouTube Data API v3 in your Google Cloud project
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY') or 'YOUR_YOUTUBE_API_KEY_HERE'
    
    # Email Configuration for Gmail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'mamnoncaynho@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''  # App Password from Google
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'mamnoncaynho@gmail.com'
    ENROLLMENT_NOTIFICATION_EMAIL = 'mamnoncaynho@gmail.com'
    
    # 🚀 GROQ AI Configuration (Free + Fast)
    # Groq API Key từ: https://console.groq.com/
    # Free tier: 5,000 requests/day, tốc độ cực nhanh
    # PASTE GROQ API KEY CỦA BẠN VÀO ĐÂY ⬇️
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY') or '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'
    GROQ_MODEL = os.environ.get('GROQ_MODEL') or 'llama-3.1-8b-instant'  # Updated model
    
    # 🤖 OpenAI Configuration (Optional - High Quality)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or ''
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL') or 'gpt-4o-mini'
    
    # 🛡️ Anthropic Claude Configuration (Optional - Safety Focused)  
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') or ''
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL') or 'claude-3-5-sonnet-20241022'