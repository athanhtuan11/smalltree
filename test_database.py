"""
Script test để kiểm tra xem bảng UserActivity có tồn tại không
Chạy: python test_database.py
"""

from app import create_app, db
from app.models import UserActivity

app = create_app()

with app.app_context():
    try:
        # Thử query bảng UserActivity
        count = UserActivity.query.count()
        print(f"✅ Bảng UserActivity TỒN TẠI - Có {count} records")
        
        # Test thêm 1 record
        test_activity = UserActivity(
            user_type='test',
            user_name='Test User',
            action='test',
            description='Test migration'
        )
        db.session.add(test_activity)
        db.session.commit()
        print("✅ Có thể thêm record vào bảng UserActivity")
        
        # Xóa test record
        db.session.delete(test_activity)
        db.session.commit()
        print("✅ Database hoạt động BÌNH THƯỜNG")
        
    except Exception as e:
        print(f"❌ LỖI: Bảng UserActivity CHƯA TỒN TẠI")
        print(f"Error: {str(e)}")
        print("\n🔧 Giải pháp: Chạy migration:")
        print("   flask db upgrade")
