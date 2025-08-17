"""
AI Service Factory cho SmallTree Academy
Tự động khởi tạo Multi-AI với config từ config.py
"""

from app.multi_ai_service import MultiAIService
from config import Config

def create_ai_service():
    """Create Multi-AI service với config từ Config class"""
    config = {
        "cohere": {
            "api_key": Config.COHERE_API_KEY,
            "model": "command-r"
        },
        "groq": {
            "api_key": Config.GROQ_API_KEY,
            "model": Config.GROQ_MODEL
        },
        "openai": {
            "api_key": Config.OPENAI_API_KEY,
            "model": Config.OPENAI_MODEL
        },
        "anthropic": {
            "api_key": Config.ANTHROPIC_API_KEY,
            "model": Config.ANTHROPIC_MODEL
        },
        "gemini": {
            "api_key": Config.GEMINI_API_KEY,
            "model": "gemini-1.5-pro"
        },
        "priority": ["cohere", "groq", "openai", "anthropic", "gemini"]  # Cohere và Groq đầu tiên
    }
    
    return MultiAIService(config)

# Global AI service instance
ai_service = create_ai_service()

def get_ai_menu_suggestions(age_group, meal_count, dietary_requirements=""):
    """Tạo gợi ý thực đơn sử dụng Multi-AI"""
    prompt = f"""
    Tạo thực đơn dinh dương cho trẻ mầm non:
    
    🎯 Độ tuổi: {age_group}
    🍽️ Số bữa ăn: {meal_count}
    🥗 Yêu cầu đặc biệt: {dietary_requirements or "Không có"}
    
    Vui lòng tạo thực đơn chi tiết với:
    - Món ăn phù hợp với độ tuổi
    - Cân bằng dinh dưỡng
    - Dễ tiêu hóa cho trẻ nhỏ
    - Nguyên liệu dễ tìm tại Việt Nam
    
    Format: JSON với các bữa ăn và món ăn cụ thể.
    """
    
    result = ai_service.generate_text(prompt)
    return result.get("text", "Không thể tạo thực đơn AI")

def get_ai_curriculum_suggestions(age_group, activity_type, duration_minutes=30):
    """Tạo gợi ý chương trình học sử dụng Multi-AI"""
    prompt = f"""
    Tạo chương trình học cho trẻ mầm non:
    
    🎯 Độ tuổi: {age_group}
    📚 Loại hoạt động: {activity_type}
    ⏰ Thời gian: {duration_minutes} phút
    
    Vui lòng tạo chương trình chi tiết với:
    - Mục tiêu học tập rõ ràng
    - Hoạt động phù hợp độ tuổi
    - Phương pháp dạy học tích cực
    - Đánh giá kết quả học tập
    
    Thiết kế theo phương pháp Montessori và Reggio Emilia.
    """
    
    result = ai_service.generate_text(prompt)
    return result.get("text", "Không thể tạo chương trình học AI")
