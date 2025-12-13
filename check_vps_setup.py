#!/usr/bin/env python3
"""
Script kiểm tra cấu hình trên VPS để debug Internal Server Error
"""
import os
import sys

def check_environment():
    """Kiểm tra biến môi trường"""
    print("=" * 60)
    print("1. KIỂM TRA BIẾN MÔI TRƯỜNG")
    print("=" * 60)
    
    env_vars = [
        'R2_ACCOUNT_ID',
        'R2_ACCESS_KEY_ID', 
        'R2_SECRET_ACCESS_KEY',
        'R2_BUCKET_NAME',
        'R2_PUBLIC_URL',
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Ẩn sensitive data
            if 'KEY' in var or 'SECRET' in var:
                display = value[:8] + '...' if len(value) > 8 else '***'
            else:
                display = value
            print(f"✅ {var}: {display}")
        else:
            print(f"❌ {var}: KHÔNG TÌM THẤY")
    print()

def check_database():
    """Kiểm tra kết nối database"""
    print("=" * 60)
    print("2. KIỂM TRA DATABASE")
    print("=" * 60)
    
    try:
        from app import create_app
        from app.models import db, Deck, Card
        
        app = create_app()
        with app.app_context():
            # Kiểm tra tables
            deck_count = Deck.query.count()
            card_count = Card.query.count()
            print(f"✅ Database kết nối thành công")
            print(f"   - Số bộ thẻ (Deck): {deck_count}")
            print(f"   - Số thẻ (Card): {card_count}")
            
    except Exception as e:
        print(f"❌ Lỗi database: {str(e)}")
        import traceback
        traceback.print_exc()
    print()

def check_r2_storage():
    """Kiểm tra R2 storage"""
    print("=" * 60)
    print("3. KIỂM TRA CLOUDFLARE R2 STORAGE")
    print("=" * 60)
    
    try:
        from r2_storage import get_r2_storage
        r2 = get_r2_storage()
        
        # Test list objects
        response = r2.s3_client.list_objects_v2(
            Bucket=r2.bucket_name,
            MaxKeys=5
        )
        
        print(f"✅ R2 Storage kết nối thành công")
        print(f"   - Bucket: {r2.bucket_name}")
        print(f"   - Public URL: {r2.public_url}")
        
        if 'Contents' in response:
            print(f"   - Số file mẫu: {len(response['Contents'])}")
            for obj in response['Contents'][:3]:
                print(f"     • {obj['Key']} ({obj['Size']} bytes)")
        else:
            print(f"   - Bucket trống hoặc không có quyền list")
            
    except ImportError:
        print(f"❌ Module r2_storage.py không tìm thấy")
    except Exception as e:
        print(f"❌ Lỗi R2 Storage: {str(e)}")
        import traceback
        traceback.print_exc()
    print()

def check_directories():
    """Kiểm tra thư mục upload"""
    print("=" * 60)
    print("4. KIỂM TRA THƯ MỤC VÀ QUYỀN")
    print("=" * 60)
    
    dirs_to_check = [
        'app/static/images',
        'app/static/flashcard/images',
        'app/static/flashcard/audio',
        'migrations/versions'
    ]
    
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            is_writable = os.access(dir_path, os.W_OK)
            status = "✅ Ghi được" if is_writable else "❌ KHÔNG ghi được"
            print(f"{status}: {dir_path}")
        else:
            print(f"❌ KHÔNG TỒN TẠI: {dir_path}")
    print()

def check_migrations():
    """Kiểm tra migrations"""
    print("=" * 60)
    print("5. KIỂM TRA DATABASE MIGRATIONS")
    print("=" * 60)
    
    versions_dir = 'migrations/versions'
    if os.path.exists(versions_dir):
        migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and f != '__pycache__']
        print(f"✅ Tìm thấy {len(migration_files)} migration files")
        
        # Liệt kê 5 file mới nhất
        migration_files.sort(reverse=True)
        for mf in migration_files[:5]:
            print(f"   - {mf}")
    else:
        print(f"❌ Thư mục migrations/versions không tồn tại")
    print()

def check_app_config():
    """Kiểm tra Flask app config"""
    print("=" * 60)
    print("6. KIỂM TRA FLASK APP CONFIG")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        
        configs = [
            'MAX_CONTENT_LENGTH',
            'SECRET_KEY',
            'SQLALCHEMY_DATABASE_URI'
        ]
        
        with app.app_context():
            for config_key in configs:
                value = app.config.get(config_key)
                if value:
                    if 'KEY' in config_key or 'URI' in config_key:
                        display = str(value)[:20] + '...' if len(str(value)) > 20 else '***'
                    else:
                        display = value
                    print(f"✅ {config_key}: {display}")
                else:
                    print(f"❌ {config_key}: KHÔNG SET")
                    
    except Exception as e:
        print(f"❌ Lỗi load app config: {str(e)}")
    print()

if __name__ == '__main__':
    print("\n🔍 BẮT ĐẦU KIỂM TRA HỆ THỐNG VPS\n")
    
    check_environment()
    check_directories()
    check_app_config()
    check_database()
    check_r2_storage()
    check_migrations()
    
    print("=" * 60)
    print("✅ HOÀN TẤT KIỂM TRA")
    print("=" * 60)
    print("\nNếu có lỗi ❌ ở trên, hãy sửa trước khi chạy app!")
    print("\nĐể xem log chi tiết trên VPS:")
    print("  • tail -f /var/log/nginx/error.log")
    print("  • tail -f /var/log/gunicorn/error.log")
    print("  • journalctl -u smalltree -f")
    print()
