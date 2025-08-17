"""
Multi-AI Service với nhiều providers để backup và tăng quota
Hỗ trợ: Gemini, OpenAI, Anthropic Claude, Groq
"""

import json
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import AI libraries với error handling
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

class MultiAIService:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Multi-AI Service với config cho nhiều providers
        
        config format:
        {
            "cohere": {"api_key": "...", "model": "command-r"},
            "gemini": {"api_key": "...", "model": "gemini-1.5-pro"},
            "openai": {"api_key": "...", "model": "gpt-4"},
            "anthropic": {"api_key": "...", "model": "claude-3-5-sonnet-20241022"},
            "groq": {"api_key": "...", "model": "llama-3.1-70b-versatile"},
            "priority": ["cohere", "groq", "openai", "anthropic", "gemini"]  # Thứ tự ưu tiên - Gemini cuối vì hết quota
        }
        """
        self.config = config
        self.providers = {}
        self.priority = config.get("priority", ["cohere", "groq", "openai", "anthropic", "gemini"])
        
        # Initialize available providers
        self._init_providers()
        
        logger.info(f"🚀 Multi-AI Service initialized with providers: {list(self.providers.keys())}")
    
    def _init_providers(self):
        """Initialize tất cả available AI providers"""
        
        # 1. COHERE (Education-focused, try first)
        if "cohere" in self.config and self.config["cohere"].get("api_key") and COHERE_AVAILABLE:
            try:
                cohere_client = cohere.Client(api_key=self.config["cohere"]["api_key"])
                self.providers["cohere"] = {
                    "client": cohere_client,
                    "model": self.config["cohere"].get("model", "command-r"),
                    "status": "active"
                }
                logger.info("✅ Cohere AI initialized")
            except Exception as e:
                logger.error(f"❌ Cohere init failed: {e}")
        
        # 2. GEMINI
        if "gemini" in self.config and self.config["gemini"].get("api_key") and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.config["gemini"]["api_key"])
                self.providers["gemini"] = {
                    "client": genai,
                    "model": self.config["gemini"].get("model", "gemini-1.5-pro"),
                    "status": "active"
                }
                logger.info("✅ Gemini AI initialized")
            except Exception as e:
                logger.error(f"❌ Gemini init failed: {e}")
        
        # 3. GROQ (Updated to use SDK)
        if "groq" in self.config and self.config["groq"].get("api_key") and GROQ_AVAILABLE:
            try:
                groq_client = Groq(api_key=self.config["groq"]["api_key"])
                self.providers["groq"] = {
                    "client": groq_client,
                    "model": self.config["groq"].get("model", "llama-3.1-70b-versatile"),
                    "status": "active"
                }
                logger.info("✅ Groq AI initialized")
            except Exception as e:
                logger.error(f"❌ Groq init failed: {e}")
        
        # 4. OPENAI
        if "openai" in self.config and self.config["openai"].get("api_key") and OPENAI_AVAILABLE:
            try:
                openai.api_key = self.config["openai"]["api_key"]
                self.providers["openai"] = {
                    "client": openai,
                    "model": self.config["openai"].get("model", "gpt-4"),
                    "status": "active"
                }
                logger.info("✅ OpenAI initialized")
            except Exception as e:
                logger.error(f"❌ OpenAI init failed: {e}")
        
        # 4. ANTHROPIC CLAUDE
        if "anthropic" in self.config and self.config["anthropic"].get("api_key") and ANTHROPIC_AVAILABLE:
            try:
                self.providers["anthropic"] = {
                    "client": Anthropic(api_key=self.config["anthropic"]["api_key"]),
                    "model": self.config["anthropic"].get("model", "claude-3-5-sonnet-20241022"),
                    "status": "active"
                }
                logger.info("✅ Anthropic Claude initialized")
            except Exception as e:
                logger.error(f"❌ Anthropic init failed: {e}")
    
    def generate_text(self, prompt: str, max_retries: int = None) -> Dict[str, Any]:
        """
        Generate text sử dụng available providers theo thứ tự priority
        """
        if max_retries is None:
            max_retries = len(self.providers)
        
        last_error = None
        tried_providers = []
        
        for provider_name in self.priority:
            if provider_name not in self.providers:
                continue
                
            if len(tried_providers) >= max_retries:
                break
                
            provider = self.providers[provider_name]
            if provider["status"] != "active":
                continue
            
            try:
                logger.info(f"🚀 Trying {provider_name.upper()} AI...")
                result = self._call_provider(provider_name, prompt)
                
                if result["success"]:
                    logger.info(f"✅ {provider_name.upper()} AI succeeded")
                    return {
                        "success": True,
                        "content": result["content"],
                        "provider": provider_name,
                        "model": provider["model"],
                        "tried_providers": tried_providers + [provider_name]
                    }
                else:
                    tried_providers.append(provider_name)
                    last_error = result["error"]
                    logger.warning(f"⚠️ {provider_name.upper()} failed: {result['error']}")
                    
                    # Mark provider as quota exceeded if 429
                    if "429" in str(result["error"]) or "quota" in str(result["error"]).lower():
                        self.providers[provider_name]["status"] = "quota_exceeded"
                        logger.warning(f"🚫 {provider_name.upper()} marked as quota exceeded")
                        
            except Exception as e:
                tried_providers.append(provider_name)
                last_error = str(e)
                logger.error(f"❌ {provider_name.upper()} exception: {e}")
        
        # All providers failed
        return {
            "success": False,
            "error": f"All AI providers failed. Last error: {last_error}",
            "tried_providers": tried_providers,
            "available_providers": list(self.providers.keys())
        }
    
    def _call_provider(self, provider_name: str, prompt: str) -> Dict[str, Any]:
        """Call specific AI provider"""
        
        provider = self.providers[provider_name]
        
        try:
            if provider_name == "cohere":
                return self._call_cohere(provider, prompt)
            elif provider_name == "gemini":
                return self._call_gemini(provider, prompt)
            elif provider_name == "openai":
                return self._call_openai(provider, prompt)
            elif provider_name == "anthropic":
                return self._call_anthropic(provider, prompt)
            elif provider_name == "groq":
                return self._call_groq(provider, prompt)
            else:
                return {"success": False, "error": f"Unknown provider: {provider_name}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _call_cohere(self, provider: Dict, prompt: str) -> Dict[str, Any]:
        """Call Cohere AI using Chat API (Generate API deprecated)"""
        try:
            cohere_client = provider["client"]
            
            response = cohere_client.chat(
                model=provider["model"],
                message=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if response.text:
                content = response.text.strip()
                return {"success": True, "content": content}
            else:
                return {"success": False, "error": "Empty response from Cohere"}
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return {"success": False, "error": f"429 Cohere quota exceeded: {error_msg}"}
            return {"success": False, "error": f"Cohere error: {error_msg}"}
    
    def _call_gemini(self, provider: Dict, prompt: str) -> Dict[str, Any]:
        """Call Gemini AI"""
        try:
            model = provider["client"].GenerativeModel(provider["model"])
            response = model.generate_content(prompt)
            
            if response.text:
                return {"success": True, "content": response.text}
            else:
                return {"success": False, "error": "Empty response from Gemini"}
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": f"429 Gemini quota exceeded: {error_msg}"}
            return {"success": False, "error": f"Gemini error: {error_msg}"}
    
    def _call_openai(self, provider: Dict, prompt: str) -> Dict[str, Any]:
        """Call OpenAI GPT"""
        try:
            response = provider["client"].ChatCompletion.create(
                model=provider["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return {"success": True, "content": content}
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": f"429 OpenAI quota exceeded: {error_msg}"}
            return {"success": False, "error": f"OpenAI error: {error_msg}"}
    
    def _call_anthropic(self, provider: Dict, prompt: str) -> Dict[str, Any]:
        """Call Anthropic Claude"""
        try:
            response = provider["client"].messages.create(
                model=provider["model"],
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return {"success": True, "content": content}
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": f"429 Claude quota exceeded: {error_msg}"}
            return {"success": False, "error": f"Claude error: {error_msg}"}
    
    def _call_groq(self, provider: Dict, prompt: str) -> Dict[str, Any]:
        """Call Groq AI using SDK"""
        try:
            groq_client = provider["client"]
            
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=provider["model"],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return {"success": True, "content": content}
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return {"success": False, "error": f"429 Groq quota exceeded: {error_msg}"}
            return {"success": False, "error": f"Groq error: {error_msg}"}
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status của tất cả providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "model": provider["model"],
                "status": provider["status"],
                "available": provider["status"] == "active"
            }
        return status
    
    def reset_provider_status(self, provider_name: str = None):
        """Reset provider status (useful khi quota được renew)"""
        if provider_name:
            if provider_name in self.providers:
                self.providers[provider_name]["status"] = "active"
                logger.info(f"🔄 {provider_name.upper()} status reset to active")
        else:
            for name in self.providers:
                self.providers[name]["status"] = "active"
            logger.info("🔄 All provider statuses reset to active")
