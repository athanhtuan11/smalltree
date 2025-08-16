from flask import current_app
from .gemini_service import gemini_service

def get_ai_menu_suggestions(age_group="2-3 tuổi", dietary_requirements="", count=5, available_ingredients=""):
    """
    Lấy gợi ý thực đơn từ Gemini AI - VERSION NHANH (không kiểm tra dinh dưỡng)
    """
    print(f"🚀 [SPEED MODE] Gemini AI for {age_group}, ingredients: {available_ingredients[:30]}...")
    
    # Convert age_group to age_months
    age_months = 24  # Default
    if "1-3" in age_group:
        age_months = 24
    elif "3-5" in age_group:
        age_months = 48
    elif "1-5" in age_group:
        age_months = 36

    try:
        # Gọi Gemini trực tiếp không qua enhancement
        result = gemini_service.generate_menu_suggestions(
            age_months=age_months,
            available_ingredients=available_ingredients,
            dietary_preferences=dietary_requirements
        )
        
        # Xử lý kết quả siêu nhanh - minimal processing
        if isinstance(result, dict) and 'weekly_menu' in result:
            suggestions = []
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
            slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
            slot_names = ['Sáng', 'Phụ sáng', 'Tráng miệng', 'Trưa', 'Xế', 'Xế chiều']
            
            # Single loop optimization
            for i, day in enumerate(days):
                suggestions.append(f"📅 **{day_names[i]}:**")
                day_menu = result['weekly_menu'][day]
                for j, slot in enumerate(slots):
                    meal = day_menu.get(slot, 'Món ăn dinh dưỡng')
                    suggestions.append(f"  • {slot_names[j]}: {meal}")
                suggestions.append("")  # Empty line
            
            # Minimal summary
            suggestions.extend([
                "📊 **Tổng kết:**",
                f"• Tổng số bữa ăn: {result.get('total_meals', 36)}",
                "• Trạng thái: Thực đơn đã tạo ✅"
            ])
            
            print(f"⚡ [SPEED MODE] Generated {len(days) * len(slots)} meals successfully!")
            return suggestions
            
        elif isinstance(result, dict) and 'meals' in result:
            # Legacy format fallback
            suggestions = [meal.get('name', f"Bữa ăn {i+1}") for i, meal in enumerate(result['meals'])]
            print(f"⚡ [SPEED MODE] Generated {len(suggestions)} suggestions")
            return suggestions
        else:
            print(f"⚡ [SPEED MODE] Unexpected format, returning as-is")
            return [str(result)]
            
    except Exception as e:
        print(f"❌ [SPEED MODE] Gemini error: {e}")
        return [
            "❌ Gemini AI không thể tạo thực đơn",
            f"🔧 Lỗi: {str(e)}",
            "💡 Kiểm tra Gemini API key trong config.py"
        ]
