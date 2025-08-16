import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB, tăng giới hạn upload file
    
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