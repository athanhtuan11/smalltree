#!/usr/bin/env python3
"""
Simple Fallback Service - Templates-based menu generation
Sử dụng khi cả OpenAI và GitHub Copilot đều không available
"""

from typing import List, Dict
import random

class SimpleFallbackService:
    def __init__(self):
        self.menu_templates = {
            "6 tháng - 1 tuổi": [
                "Cháo gà xé phay nghiền mịn với cà rốt",
                "Cháo thịt heo rau cải xanh", 
                "Cháo cá hồi với bí đỏ",
                "Súp gà rau củ nghiền mịn",
                "Cháo yến mạch trứng gà"
            ],
            "1-2 tuổi": [
                "Cơm gà luộc xé nhỏ với rau muống",
                "Cháo thịt bò rau củ mềm",
                "Mì tôm rau cải",
                "Cháo cá thu với bí đỏ",
                "Súp sườn non rau củ"
            ],
            "2-3 tuổi": [
                "Cơm thịt heo xào cải thảo",
                "Mì ý sốt cà chua với thịt bò bằm",
                "Cơm gà cà ri nhẹ", 
                "Súp cá hồi rau củ",
                "Cháo đậu xanh thịt heo băm"
            ],
            "3-5 tuổi": [
                "Cơm thịt bò xào rau muống",
                "Mì udon gà nướng rau xanh",
                "Cơm chiên dương châu trẻ em",
                "Súp sườn non rau muống",
                "Cơm tấm thịt nướng nhẹ"
            ]
        }
        
        self.proteins = ["gà", "thịt heo", "cá", "tôm", "thịt bò", "trứng"]
        self.vegetables = ["brokoli", "cà rốt", "rau muống", "bina", "cải thảo", "su hào"]
        self.extras = ["khoai lang", "nấm", "đậu phụ", "bí đỏ", "cà chua"]
        
    def is_configured(self) -> bool:
        """Luôn available"""
        return True
    
    def get_service_name(self) -> str:
        return "SimpleFallbackService"
    
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Simple template-based response"""
        
        # Extract user content
        user_content = ""
        for msg in messages:
            if msg.get('role') == 'user':
                user_content = msg.get('content', '')
                break
        
        if "thực đơn" in user_content.lower() or "món ăn" in user_content.lower():
            return "Cơm gà rau củ cân bằng cho trẻ em"
        elif "dinh dưỡng" in user_content.lower():
            return '{"calories": "350 kcal", "protein_percent": "20%", "carb_percent": "55%", "fat_percent": "25%", "vitamins": "Vitamin A, C từ rau củ", "overall_score": 7, "suggestions": "Thực đơn cân bằng tốt"}'
        else:
            return "Xin chào! Tôi có thể giúp tạo thực đơn cho trẻ em."
    
    def generate_menu_suggestions(self, age_group: str, dietary_requirements: str = "", count: int = 5, available_ingredients: str = "") -> List[str]:
        """Generate menu using detailed templates"""
        
        templates = self.menu_templates.get(age_group, self.menu_templates["2-3 tuổi"])
        suggestions = []
        
        # Tạo thêm nhiều món cụ thể
        detailed_meals = [
            "Cơm thịt heo xào cải thảo",
            "Cháo gà xé phay với cà rốt",
            "Cơm cá hồi áp chảo rau muống", 
            "Bún riêu cua đồng có rau",
            "Cơm thịt bò xào đậu cove",
            "Phở gà thái nhỏ có rau thơm",
            "Cháo tôm nghiền với bí ngô",
            "Cơm sườn non hầm khoai tây",
            "Mì gà tom yum thái nhỏ",
            "Cơm thịt heo rim mắm rau lang",
            "Cháo cá thu với rau cải",
            "Cơm gà nướng rau cải xanh",
            "Bún thịt nướng rau sống",
            "Cháo yến mạch thịt bằm",
            "Cơm cá điêu hồng kho tộ"
        ]
        
        # Lấy random từ template hoặc detailed meals
        all_options = list(templates) + detailed_meals
        
        for i in range(count):
            suggestion = random.choice(all_options)
            suggestions.append(suggestion)
        
        # Make suggestions unique
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:count]
    
    def analyze_nutrition(self, food_items: List[str]) -> Dict:
        """Simple nutrition analysis"""
        
        # Count components
        has_protein = any(protein in ' '.join(food_items).lower() 
                         for protein in ['gà', 'thịt', 'cá', 'tôm', 'trứng'])
        has_carb = any(carb in ' '.join(food_items).lower() 
                      for carb in ['cơm', 'mì', 'cháo', 'bánh'])
        has_veggie = any(veggie in ' '.join(food_items).lower() 
                        for veggie in ['rau', 'cà rốt', 'brokoli', 'cải'])
        
        # Simple scoring
        score = 5  # base score
        if has_protein: score += 2
        if has_carb: score += 2
        if has_veggie: score += 1
        
        return {
            "calories": "300-400 kcal",
            "protein_percent": "20%" if has_protein else "10%",
            "carb_percent": "55%" if has_carb else "40%",
            "fat_percent": "25%",
            "vitamins": "Đa dạng vitamin từ rau củ" if has_veggie else "Cần thêm rau xanh",
            "overall_score": min(score, 10),
            "suggestions": "Thực đơn template cơ bản - cần AI service để phân tích chi tiết hơn"
        }

# Global instance
simple_fallback_service = SimpleFallbackService()
