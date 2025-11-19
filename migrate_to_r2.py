"""
Script migrate ảnh từ VPS sang Cloudflare R2
Chạy 1 lần hoặc setup cronjob để tự động migrate
"""

import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Activity, ActivityImage, Child, StudentAlbum, StudentAlbumImage
from r2_storage import get_r2_storage
from config_r2 import MIGRATION_CONFIG

def migrate_activity_images(r2, batch_size=50):
    """Migrate ảnh hoạt động"""
    app = create_app()
    with app.app_context():
        # Lấy ảnh chưa migrate (local path)
        images = ActivityImage.query.filter(
            ~ActivityImage.filepath.like('http%')
        ).limit(batch_size).all()
        
        migrated = 0
        failed = 0
        
        for img in images:
            try:
                # Đường dẫn local
                local_path = os.path.join('app/static', img.filepath)
                
                if not os.path.exists(local_path):
                    print(f"⚠️  File không tồn tại: {local_path}")
                    continue
                
                # Kiểm tra tuổi file
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(local_path))
                if file_age.days < MIGRATION_CONFIG['min_age_days']:
                    continue
                
                # Upload lên R2
                filename = os.path.basename(local_path)
                with open(local_path, 'rb') as f:
                    r2_url = r2.upload_file(f, filename, folder='activities')
                
                if r2_url:
                    # Cập nhật database
                    old_path = img.filepath
                    img.filepath = r2_url
                    db.session.commit()
                    
                    # Xóa file local
                    try:
                        os.remove(local_path)
                        print(f"✅ Migrated: {filename}")
                    except:
                        print(f"⚠️  Không thể xóa local: {local_path}")
                    
                    migrated += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Lỗi migrate {img.id}: {str(e)}")
                db.session.rollback()
                failed += 1
        
        print(f"\n📊 Ảnh hoạt động: {migrated} thành công, {failed} thất bại")
        return migrated

def migrate_student_images(r2, batch_size=50):
    """Migrate ảnh học sinh"""
    app = create_app()
    with app.app_context():
        students = Child.query.filter(
            Child.image.isnot(None),
            ~Child.image.like('http%')
        ).limit(batch_size).all()
        
        migrated = 0
        failed = 0
        
        for student in students:
            try:
                local_path = os.path.join('app/static', student.image)
                
                if not os.path.exists(local_path):
                    continue
                
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(local_path))
                if file_age.days < MIGRATION_CONFIG['min_age_days']:
                    continue
                
                filename = os.path.basename(local_path)
                with open(local_path, 'rb') as f:
                    r2_url = r2.upload_file(f, filename, folder='students')
                
                if r2_url:
                    student.image = r2_url
                    db.session.commit()
                    
                    try:
                        os.remove(local_path)
                    except:
                        pass
                    
                    migrated += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Lỗi migrate student {student.id}: {str(e)}")
                db.session.rollback()
                failed += 1
        
        print(f"📊 Ảnh học sinh: {migrated} thành công, {failed} thất bại")
        return migrated

def migrate_album_images(r2, batch_size=50):
    """Migrate ảnh album"""
    app = create_app()
    with app.app_context():
        albums = StudentAlbumImage.query.filter(
            ~StudentAlbumImage.filepath.like('http%')
        ).limit(batch_size).all()
        
        migrated = 0
        failed = 0
        
        for img in albums:
            try:
                local_path = os.path.join('app/static', img.filepath)
                
                if not os.path.exists(local_path):
                    continue
                
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(local_path))
                if file_age.days < MIGRATION_CONFIG['min_age_days']:
                    continue
                
                filename = os.path.basename(local_path)
                with open(local_path, 'rb') as f:
                    r2_url = r2.upload_file(f, filename, folder='albums')
                
                if r2_url:
                    img.filepath = r2_url
                    db.session.commit()
                    
                    try:
                        os.remove(local_path)
                    except:
                        pass
                    
                    migrated += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Lỗi migrate album {img.id}: {str(e)}")
                db.session.rollback()
                failed += 1
        
        print(f"📊 Ảnh album: {migrated} thành công, {failed} thất bại")
        return migrated

def cleanup_empty_dirs():
    """Xóa các thư mục rỗng"""
    dirs_to_check = [
        'app/static/images/activities',
        'app/static/images/students',
        'app/static/student_albums'
    ]
    
    for base_dir in dirs_to_check:
        if not os.path.exists(base_dir):
            continue
        
        for root, dirs, files in os.walk(base_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"🗑️  Đã xóa thư mục rỗng: {dir_path}")
                except:
                    pass

def main():
    print("="*70)
    print("🚀 MIGRATE ẢNH TỪ VPS → CLOUDFLARE R2")
    print("="*70)
    print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📦 Batch size: {MIGRATION_CONFIG['batch_size']}")
    print(f"⏳ Chỉ migrate ảnh cũ hơn {MIGRATION_CONFIG['min_age_days']} ngày")
    print("-"*70)
    
    # Khởi tạo R2
    r2 = get_r2_storage()
    if not r2.enabled:
        print("❌ R2 chưa được cấu hình. Vui lòng cấu hình trong config_r2.py")
        return
    
    try:
        # Migrate từng loại
        total_migrated = 0
        batch_size = MIGRATION_CONFIG['batch_size']
        
        total_migrated += migrate_activity_images(r2, batch_size)
        total_migrated += migrate_student_images(r2, batch_size)
        total_migrated += migrate_album_images(r2, batch_size)
        
        # Dọn dẹp thư mục rỗng
        cleanup_empty_dirs()
        
        # Thống kê R2
        stats = r2.get_storage_stats()
        
        print("\n" + "="*70)
        print(f"✅ HOÀN THÀNH - Đã migrate {total_migrated} ảnh")
        print(f"📊 Dung lượng R2: {stats.get('total_size_gb', 0):.2f} GB")
        print(f"📁 Tổng số file: {stats.get('total_files', 0)}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
