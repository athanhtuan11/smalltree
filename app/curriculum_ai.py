import json
import logging
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config import Config

logger = logging.getLogger(__name__)

class CurriculumAIService:
    def __init__(self):
        """Initialize Gemini AI service for curriculum generation"""
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            print("🚀 Curriculum AI service initialized with Gemini 1.5 Pro")
            logger.info("Curriculum AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Curriculum AI service: {e}")
            raise

    def generate_weekly_curriculum(self, age_group, week_number, themes=None, special_focus=None):
        """
        Generate comprehensive weekly curriculum for smalltree
        
        Args:
            age_group: Age group (e.g., "1-2 tuổi", "2-3 tuổi", "3-4 tuổi")
            week_number: Week number (1-53)
            themes: Optional themes/topics to focus on
            special_focus: Optional special focus areas
        """
        try:
            print(f"🎓 [CURRICULUM AI] Generating for {age_group}, week {week_number}")
            
            # Create detailed prompt for curriculum generation
            prompt = self._create_curriculum_prompt(age_group, week_number, themes, special_focus)
            
            # Configure safety settings for educational content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            print(f"🚀 [SPEED] Calling Gemini with {len(prompt)} chars prompt...")
            start_time = time.time()
            
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8000,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            elapsed = time.time() - start_time
            print(f"⏰ [TIMING] Gemini response received in {elapsed:.2f}s")
            
            if not response.text:
                raise Exception("Gemini returned empty response")
            
            # Parse the response
            curriculum_data = self._parse_curriculum_response(response.text)
            
            print(f"✅ [SUCCESS] Generated curriculum for week {week_number}")
            return curriculum_data
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [ERROR] Curriculum generation failed: {error_msg}")
            logger.error(f"Curriculum generation failed: {error_msg}")
            
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception("❌ Gemini API đã hết quota. Vui lòng: 1. Kiểm tra Google AI Studio, 2. Tạo API key mới, 3. Cập nhật vào config.py")
            else:
                raise Exception(f"❌ Lỗi tạo chương trình học: {error_msg}")

    def _create_curriculum_prompt(self, age_group, week_number, themes, special_focus):
        """Create detailed prompt for curriculum generation"""
        
        base_prompt = f"""
Tạo chương trình học chi tiết cho trẻ mầm non {age_group}, tuần số {week_number}.

KHUNG THỜI GIAN MỖI NGÀY (Thứ 2 đến Thứ 7):
**BUỔI SÁNG:**
- 7-8h: Đón trẻ
- 8h-8h30: Ăn sáng
- 8h30-9h: Hoạt động tự do
- 9h-9h40: Hoạt động học tập chính
- 9h40-10h30: Hoạt động ngoài trời/thể dục
- 10h30-14h: Ăn trưa + Nghỉ trưa

**BUỔI CHIỀU:**
- 14h-14h30: Ăn phụ chiều
- 14h30-15h30: Hoạt động học tập
- 15h30-16h: Hoạt động tự do/chơi
- 16h-16h30: Chuẩn bị về
- 16h30-17h: Đón trẻ về
- 17h-18h: Trông trẻ muộn

YÊU CÂU CONTENT:
1. **Cụ thể và phù hợp với {age_group}**
2. **Đa dạng hoạt động:** học tập, chơi, thể dục, nghệ thuật, khoa học đơn giản
3. **Phát triển toàn diện:** ngôn ngữ, vận động, nhận thức, xã hội, cảm xúc
4. **Thực tế và dễ thực hiện** tại trường mầm non
5. **Tên hoạt động cụ thể:** VD: "Học đếm từ 1-5 với trái cây", "Tô màu con vật", "Hát bài Bé làm gì"

"""

        # Add themes if specified
        if themes:
            base_prompt += f"\nCHỦ ĐỀ TUẦN: {themes}\n"
        
        # Add special focus if specified  
        if special_focus:
            base_prompt += f"\nTRỌNG TÂM ĐẶC BIỆT: {special_focus}\n"

        base_prompt += """
Trả về JSON format chính xác sau:
{
  "week_info": {
    "week_number": """ + str(week_number) + """,
    "age_group": \"""" + age_group + """\",
    "theme": "Chủ đề chính của tuần",
    "objectives": ["Mục tiêu 1", "Mục tiêu 2", "Mục tiêu 3"]
  },
  "curriculum": {
    "mon": {
      "morning_1": "Hoạt động cụ thể 7-8h",
      "morning_2": "Hoạt động cụ thể 8h-8h30", 
      "morning_3": "Hoạt động cụ thể 8h30-9h",
      "morning_4": "Hoạt động cụ thể 9h-9h40",
      "morning_5": "Hoạt động cụ thể 9h40-10h30",
      "morning_6": "Hoạt động cụ thể 10h30-14h",
      "afternoon_1": "Hoạt động cụ thể 14h-14h30",
      "afternoon_2": "Hoạt động cụ thể 14h30-15h30",
      "afternoon_3": "Hoạt động cụ thể 15h30-16h",
      "afternoon_4": "Hoạt động cụ thể 16h-16h30",
      "afternoon_5": "Hoạt động cụ thể 16h30-17h",
      "afternoon_6": "Hoạt động cụ thể 17h-18h"
    },
    "tue": { ... tương tự ... },
    "wed": { ... tương tự ... },
    "thu": { ... tương tự ... },
    "fri": { ... tương tự ... },
    "sat": { ... tương tự ... }
  },
  "materials_needed": ["Vật liệu 1", "Vật liệu 2", "Vật liệu 3"],
  "assessment_notes": "Ghi chú đánh giá và quan sát trẻ"
}

LƯU Ý: 
- Mỗi hoạt động phải CỤ THỂ, không được mơ hồ như "Hoạt động tự do"
- Phù hợp độ tuổi {age_group}
- Cân bằng giữa học và chơi
- JSON phải đúng format, không có lỗi syntax
"""
        
        return base_prompt

    def _parse_curriculum_response(self, response_text):
        """Parse Gemini response to extract curriculum data"""
        try:
            # Clean response text
            cleaned_text = response_text.strip()
            
            # Find JSON content
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise Exception("No valid JSON found in response")
            
            json_content = cleaned_text[start_idx:end_idx + 1]
            curriculum_data = json.loads(json_content)
            
            # Validate required structure
            if 'curriculum' not in curriculum_data:
                raise Exception("Missing curriculum data in response")
            
            # Validate all days and time slots exist
            required_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            required_slots = [
                'morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6',
                'afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4', 'afternoon_5', 'afternoon_6'
            ]
            
            for day in required_days:
                if day not in curriculum_data['curriculum']:
                    raise Exception(f"Missing day: {day}")
                for slot in required_slots:
                    if slot not in curriculum_data['curriculum'][day]:
                        curriculum_data['curriculum'][day][slot] = f"Hoạt động phù hợp khung giờ {slot}"
            
            print(f"✅ [PARSE] Successfully parsed curriculum with {len(required_days)} days")
            return curriculum_data
            
        except json.JSONDecodeError as e:
            print(f"🔍 [DEBUG] JSON parse error: {e}")
            print(f"🔍 [DEBUG] Response text preview: {response_text[:500]}...")
            raise Exception("❌ Gemini trả về format không hợp lệ. Vui lòng thử lại.")
        except Exception as e:
            print(f"🔍 [DEBUG] Parse error: {e}")
            raise Exception(f"❌ Lỗi xử lý dữ liệu từ AI: {str(e)}")

# Initialize service
curriculum_ai_service = CurriculumAIService()
