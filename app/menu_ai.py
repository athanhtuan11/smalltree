
# Multi-AI Service as the only backend for menu AI
from .multi_ai_service import MultiAIService
from config import Config

# Global instance (reuse for all calls)
_multi_ai_service = None
def _get_multi_ai_service():
    global _multi_ai_service
    if _multi_ai_service is None:
        config = {
            "cohere": {"api_key": Config.COHERE_API_KEY, "model": "command-r"},
            "groq": {"api_key": Config.GROQ_API_KEY, "model": Config.GROQ_MODEL},
            "openai": {"api_key": Config.OPENAI_API_KEY, "model": Config.OPENAI_MODEL},
            "anthropic": {"api_key": Config.ANTHROPIC_API_KEY, "model": Config.ANTHROPIC_MODEL},
            "gemini": {"api_key": Config.GEMINI_API_KEY, "model": "gemini-1.5-pro"},
            "priority": ["cohere", "groq", "openai", "anthropic", "gemini"]
        }
        _multi_ai_service = MultiAIService(config)
    return _multi_ai_service

def get_ai_menu_suggestions(age_group="2-3 tuổi", dietary_requirements="", count=5, available_ingredients="", menu_prompt=None):
    """
    Lấy gợi ý thực đơn từ Multi-AI Service (Cohere, Groq, OpenAI, Anthropic, Gemini)
    """
    prompt = menu_prompt if menu_prompt else None
    import json
    try:
        service = _get_multi_ai_service()
        result = service.generate_text(prompt)
        if result["success"]:
            content = result["content"]
            # Nếu là string, cố gắng parse JSON
            if isinstance(content, str):
                try:
                    # Loại bỏ markdown code block nếu có
                    clean = content.strip()
                    if clean.startswith('```json'):
                        clean = clean[7:]
                    if clean.startswith('```'):
                        clean = clean[3:]
                    if clean.endswith('```'):
                        clean = clean[:-3]
                    menu_json = json.loads(clean)
                    return menu_json
                except Exception:
                    # Nếu không parse được thì trả về text như cũ
                    return [content]
            else:
                return content
        else:
            return [
                "❌ Không thể tạo menu từ AI",
                "🔄 Vui lòng kiểm tra kết nối mạng và thử lại",
                f"📝 Error: {result.get('error', 'Unknown error')} | Prompt: {prompt if prompt else '(no prompt)'}"
            ]
    except Exception as e:
        print(f"❌ [MULTI-AI] Error: {e}")
        return [
            "❌ Không thể tạo menu từ AI",
            "🔄 Vui lòng kiểm tra kết nối mạng và thử lại",
            f"📝 Error: {str(e)[:100]} | Prompt: {prompt if prompt else '(no prompt)'}"
        ]
