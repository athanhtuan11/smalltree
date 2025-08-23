import json
import logging
import time  # Move to top for faster import
import hashlib  # For caching
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config import Config

# Simple in-memory cache for speed
_menu_cache = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key=None):
        """
        Initialize Gemini service
        """
        try:
            # Debug API key loading
            if api_key:
                print(f"🔧 [DEBUG] Using provided API key")
                self.api_key = api_key
            else:
                api_key_from_config = getattr(Config, 'GEMINI_API_KEY', None)
                print(f"🔑 [DEBUG] Gemini API key from config: {api_key_from_config[:10] if api_key_from_config else None}...")
                
                if not api_key_from_config:
                    # Hardcoded API key for testing - temporary measure
                    print(f"🔧 [DEBUG] Using hardcoded API key for testing")
                    api_key_from_config = "AIzaSyC5F9JQiQJUQcQQWm9Qcy_ZGOzqZz_Bfeg"
                    
                self.api_key = api_key_from_config
            
            if self.api_key:
                genai.configure(api_key=self.api_key)
                
                # Use Gemini Pro model - try multiple versions for compatibility
                try:
                    self.model = genai.GenerativeModel(
                        model_name="gemini-1.5-pro",  # Stable Pro model
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    print(f"🚀 Gemini service initialized with STABLE PRO model: gemini-1.5-pro")
                except Exception as model_error:
                    print(f"⚠️ Pro model failed, falling back to Flash: {model_error}")
                    self.model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    print(f"✅ Fallback to Flash model successful")
                logger.info("Gemini service initialized successfully")
            else:
                print("⚠️ Gemini API key not configured")
                logger.warning("Gemini API key not configured")
                self.model = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.model = None

    def is_configured(self):
        """Check if Gemini service is properly configured"""
        return self.model is not None

    def init_app(self, app):
        """Initialize with Flask app (for compatibility)"""
        pass

    def calculate_meal_count(self, available_ingredients):
        """
        Calculate number of meals based on available ingredients
        Enhanced logic for better variation
        """
        if not available_ingredients or available_ingredients.strip() == "":
            return 3  # Default if no ingredients specified
            
        # Count ingredients by splitting on comma and filtering non-empty
        ingredients = [x.strip() for x in available_ingredients.split(',') if x.strip()]
        ingredient_count = len(ingredients)
        
        print(f"🧮 [DEBUG] Ingredient count: {ingredient_count}")
        
        # Smart calculation based on ingredient diversity
        if ingredient_count <= 3:
            return 2  # Few ingredients = fewer but focused meals
        elif ingredient_count <= 6:
            return 3  # Medium ingredients = moderate variety  
        elif ingredient_count <= 9:
            return 4  # Many ingredients = good variety
        else:
            return 5  # Lots of ingredients = maximum variety

    def generate_menu_suggestions(self, age_group=None, available_ingredients=None, special_requirements=None, 
                                age_months=None, dietary_preferences=None, menu_prompt=None):
        """
        Generate menu suggestions using Gemini AI with dynamic meal counting
        Supports both new (age_group) and legacy (age_months) signatures
        """
        if not self.is_configured():
            logger.error("Gemini service not configured")
            raise Exception("Gemini API chưa được cấu hình")
        
        # Handle legacy parameters
        if age_months is not None:
            # Convert age_months to age_group
            if age_months <= 12:
                age_group = "6-12 tháng"
            elif age_months <= 24:
                age_group = "1-2 tuổi"
            elif age_months <= 36:
                age_group = "2-3 tuổi"
            elif age_months <= 48:
                age_group = "3-4 tuổi"
            else:
                age_group = "4-5 tuổi"
        
        if dietary_preferences is not None:
            special_requirements = dietary_preferences
            
        # Ensure we have age_group
        if age_group is None:
            age_group = "2-3 tuổi"  # Default

        # Calculate dynamic meal count
        num_meals = self.calculate_meal_count(available_ingredients)
        print(f"📊 [DEBUG] Expected meals count: {num_meals}")

        ingredients_text = available_ingredients if available_ingredients else "không có nguyên liệu cụ thể"
        requirements_text = special_requirements if special_requirements else "không có yêu cầu đặc biệt"

        print(f"🤖 [DEBUG] Calling Gemini AI for {age_group}, ingredients: {ingredients_text[:50]}...")

        # Cache key for avoiding duplicate calls
        cache_key = hashlib.md5(f"{age_group}_{ingredients_text}_{requirements_text}".encode()).hexdigest()
        if cache_key in _menu_cache:
            print(f"⚡ [CACHE HIT] Returning cached result")
            return _menu_cache[cache_key]

        # Nếu có menu_prompt thì dùng luôn prompt này, không tự tạo prompt mặc định
        if menu_prompt:
            prompt = menu_prompt
        else:
            # 🚀 GEMINI 2.5 PRO OPTIMIZED PROMPT - Chi tiết và cụ thể hơn
            prompt = f"""Tạo thực đơn tuần cân bằng dinh dưỡng cho trẻ {age_group}.
Nguyên liệu có sẵn: {ingredients_text}
Yêu cầu đặc biệt: {requirements_text}

Lưu ý: Tên món ăn phải CỤ THỂ và CHI TIẾT. Ví dụ:
- Thay vì \"Cơm thịt rau\" → \"Cơm thịt heo xào cải thảo\"
- Thay vì \"Cháo gà\" → \"Cháo gà xé phay với cà rốt\"
- Thay vì \"Canh rau\" → \"Canh bí đỏ thịt bằm\"

Trả về JSON format:
{{
    \"weekly_menu\": {{
        \"mon\": {{\"morning\": \"Cháo gà xé phay với cà rốt\", \"snack\": \"Sữa chua có đường\", \"dessert\": \"Chuối nghiền mật ong\", \"lunch\": \"Cơm thịt bò xào đậu cove\", \"afternoon\": \"Bánh quy sữa dinh dưỡng\", \"lateafternoon\": \"Sữa tươi không đường\"}},
        \"tue\": {{\"morning\": \"Phở bò thái nhỏ có rau thơm\", \"snack\": \"Bánh crackers nguyên cám\", \"dessert\": \"Cam vắt tươi\", \"lunch\": \"Cơm gà luộc với bí đỏ\", \"afternoon\": \"Chè đậu xanh nước cốt dừa\", \"lateafternoon\": \"Nước ép táo\"}},
        \"wed\": {{\"morning\": \"Cháo thịt heo bằm rau cải\", \"snack\": \"Kẹo dẻo vitamin C\", \"dessert\": \"Táo nghiền có quế\", \"lunch\": \"Cơm cá hồi áp chảo rau muống\", \"afternoon\": \"Bánh bao nhân thịt nhỏ\", \"lateafternoon\": \"Sữa đậu nành\"}},
        \"thu\": {{\"morning\": \"Bún riêu cua đồng có rau\", \"snack\": \"Bánh su kem nhỏ\", \"dessert\": \"Nho tách hạt tươi\", \"lunch\": \"Cơm sườn non hầm khoai tây\", \"afternoon\": \"Chè cung đình hạt sen\", \"lateafternoon\": \"Nước lọc\"}},
        \"fri\": {{\"morning\": \"Cháo tôm nghiền với bí ngô\", \"snack\": \"Yogurt tự nhiên\", \"dessert\": \"Lê nghiền có mật ong\", \"lunch\": \"Cơm gà nướng rau cải xanh\", \"afternoon\": \"Bánh flan caramen\", \"lateafternoon\": \"Sữa đậu nành vani\"}},
        \"sat\": {{\"morning\": \"Mì gà tom yum thái nhỏ\", \"snack\": \"Bánh quy yến mạch\", \"dessert\": \"Dưa hấu cắt nhỏ\", \"lunch\": \"Cơm thịt heo rim mắm rau lang\", \"afternoon\": \"Chè thái hạt lựu\", \"lateafternoon\": \"Sữa tươi có canxi\"}}
    }},
    \"total_meals\": 36,
    \"nutrition_notes\": \"Thực đơn cân bằng protein, vitamin, khoáng chất phù hợp độ tuổi với tên món cụ thể\"
}}"""

        print(f"🚀 [SPEED] Calling Gemini with {len(prompt)} chars prompt...")
        
        start_time = time.time()  # Use pre-imported time

        try:
            # Add timeout and better error handling
            print(f"⏰ [DEBUG] Starting Gemini API call...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,  # Pro model can handle more efficiently
                    temperature=0.3,         # Slightly higher for better quality
                    top_p=0.9,              # Better coherence in Pro model
                    top_k=40                # More vocab options for Pro
                ),
                request_options={'timeout': 30}  # 30 second timeout
            )
            print(f"✅ [DEBUG] Gemini API call completed")
            
            api_time = time.time() - start_time
            print(f"⚡ [SPEED] Gemini API took {api_time:.2f} seconds")
            
            if response and response.text:
                response_text = response.text.strip()
                print(f"📝 [SPEED] Response: {len(response_text)} chars")
                print(f"🔍 [DEBUG] First 200 chars: {response_text[:200]}...")
                
                # Fast JSON parsing - try direct first
                try:
                    result = json.loads(response_text)
                    print(f"✅ [SPEED] Direct JSON parse successful")
                    # Cache successful result
                    _menu_cache[cache_key] = result
                    return result
                except json.JSONDecodeError as je:
                    print(f"⚠️ [DEBUG] JSON decode error: {je}")
                    # Quick cleanup only if direct fails
                    clean_text = response_text.replace('```json', '').replace('```', '').strip()
                    try:
                        result = json.loads(clean_text)
                        print(f"✅ [SPEED] Cleaned JSON parse successful")
                        # Cache successful result
                        _menu_cache[cache_key] = result
                        return result
                    except json.JSONDecodeError as je2:
                        # No fallback - raise error for AI-only mode
                        print(f"❌ [ERROR] JSON parsing failed completely: {je2}")
                        print(f"🔍 [DEBUG] Raw response: {response_text}")
                        raise Exception("Gemini AI trả về dữ liệu không hợp lệ")
            else:
                print(f"❌ [ERROR] Gemini returned empty response")
                raise Exception("Gemini không trả về kết quả")
                
        except Exception as e:
            api_time = time.time() - start_time
            print(f"❌ [ERROR] Gemini API failed after {api_time:.2f}s: {e}")
            print(f"🔍 [DEBUG] Error type: {type(e).__name__}")
            print(f"🔍 [DEBUG] Error details: {str(e)}")
            logger.error(f"Gemini menu generation failed: {e}")
            
            # Raise exception instead of fallback - user wants AI only
            if "quota" in str(e).lower():
                raise Exception("❌ Gemini API đã hết quota. Vui lòng:\n1. Kiểm tra Google AI Studio (https://aistudio.google.com/)\n2. Tạo API key mới\n3. Cập nhật vào config.py")
            else:
                raise Exception(f"Gemini AI không thể tạo thực đơn: {str(e)}")

    def _convert_to_weekly_format(self, legacy_result, age_group, available_ingredients):
        """Convert legacy meal format to weekly menu format"""
        meals = legacy_result.get('meals', [])
        
        # Create weekly menu structure
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
        
        weekly_menu = {}
        meal_index = 0
        
        for day in days:
            weekly_menu[day] = {}
            for slot in slots:
                if meal_index < len(meals):
                    meal = meals[meal_index]
                    weekly_menu[day][slot] = f"{meal.get('name', 'Món ăn dinh dưỡng')} - {meal.get('description', '')}"
                    meal_index += 1
                else:
                    # No fallback - raise error for AI-only mode
                    raise Exception(f"❌ Gemini API đã hết quota. Vui lòng: 1. Kiểm tra Google AI Studio, 2. Tạo API key mới, 3. Cập nhật vào config.py")
        
        return {
            "weekly_menu": weekly_menu,
            "nutrition_analysis": legacy_result.get('overall_nutrition_analysis', 'Thực đơn cân bằng dinh dưỡng'),
            "recommendations": legacy_result.get('recommendations', 'Đảm bảo vệ sinh thực phẩm'),
            "total_meals": 36,
            "week_summary": f"Thực đơn tuần cho trẻ {age_group}"
        }

# Create global instance
try:
    gemini_service = GeminiService()
except Exception as e:
    logger.error(f"Failed to create gemini_service instance: {e}")
    gemini_service = None
