"""
Groq AI Service for SmallTree Academy
High-speed inference with open models
"""

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

import os
import logging

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self, api_key=None):
        """Initialize Groq service"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = None
        
        if self.api_key and GROQ_AVAILABLE:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("✅ Groq service initialized")
            except Exception as e:
                logger.error(f"❌ Groq initialization failed: {e}")
        else:
            logger.warning("⚠️ Groq not available (missing API key or library)")
    
    def generate_text(self, prompt, model="llama-3.1-70b-versatile", max_tokens=1024):
        """Generate text using Groq"""
        if not self.client:
            return {"error": "Groq service not available", "text": "AI service không khả dụng"}
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=model,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                "text": response.choices[0].message.content,
                "provider": "groq",
                "model": model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Groq generation failed: {e}")
            return {"error": str(e), "text": f"Lỗi Groq AI: {e}"}

# Global instance
groq_service = GroqService()