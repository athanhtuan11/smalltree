#!/usr/bin/env python3
"""
Utility script để cấu hình số học sinh cho tính toán khối lượng thực phẩm
"""

from app import create_app
from app.models import db
import json
import os

def set_student_count(count):
    """Thiết lập số học sinh trong config"""
    config_file = 'student_config.json'
    config = {}
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    config['student_count'] = count
    config['last_updated'] = str(datetime.now())
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Đã cập nhật số học sinh: {count}")

def get_student_count():
    """Lấy số học sinh từ config"""
    config_file = 'student_config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('student_count', 25)
    
    return 25  # Mặc định

if __name__ == '__main__':
    import sys
    from datetime import datetime
    
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count > 0:
                set_student_count(count)
            else:
                print("❌ Số học sinh phải lớn hơn 0")
        except ValueError:
            print("❌ Vui lòng nhập số hợp lệ")
    else:
        current_count = get_student_count()
        print(f"📊 Số học sinh hiện tại: {current_count}")
        print("\nCách sử dụng:")
        print(f"  python {sys.argv[0]} <số_học_sinh>")
        print("\nVí dụ:")
        print(f"  python {sys.argv[0]} 30")
