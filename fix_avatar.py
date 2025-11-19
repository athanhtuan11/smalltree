"""
Script to download avatars from R2 to local VPS storage
Converts R2 URLs to local paths to avoid loading issues
"""
from app import create_app
from app.models import db, Child
import os
import requests
from werkzeug.utils import secure_filename

app = create_app()

def download_avatars_from_r2():
    with app.app_context():
        # Find students with R2 avatar URLs
        students = Child.query.filter(Child.avatar.isnot(None)).all()
        
        downloaded_count = 0
        skipped_count = 0
        error_count = 0
        
        for student in students:
            if not student.avatar:
                continue
                
            # Check if avatar is R2 URL
            if student.avatar.startswith('http'):
                print(f"\n📥 Đang xử lý {student.name} ({student.student_code})")
                print(f"   R2 URL: {student.avatar}")
                
                try:
                    # Download from R2
                    response = requests.get(student.avatar, timeout=10)
                    if response.status_code == 200:
                        # Extract filename or create new one
                        filename = f"student_{student.student_code}_{secure_filename(student.name)}.jpg"
                        
                        # Save to local
                        save_dir = os.path.join('app', 'static', 'images', 'students')
                        os.makedirs(save_dir, exist_ok=True)
                        local_path = os.path.join(save_dir, filename)
                        
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        
                        # Update database
                        old_avatar = student.avatar
                        student.avatar = f"images/students/{filename}"
                        
                        print(f"   ✅ Downloaded: {filename}")
                        print(f"   📁 New path: {student.avatar}")
                        downloaded_count += 1
                    else:
                        print(f"   ❌ Failed to download: HTTP {response.status_code}")
                        error_count += 1
                        
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
                    error_count += 1
            else:
                # Already local, skip
                skipped_count += 1
        
        # Commit all changes
        if downloaded_count > 0:
            db.session.commit()
            print(f"\n{'='*60}")
            print(f"✅ Đã download {downloaded_count} avatars từ R2 về local")
            print(f"⏭️  Bỏ qua {skipped_count} avatars đã ở local")
            if error_count > 0:
                print(f"❌ Lỗi {error_count} avatars")
            print(f"{'='*60}")
        else:
            print(f"\n✅ Không có avatar nào từ R2. Tất cả đã ở local.")
            print(f"   (Bỏ qua {skipped_count} avatars)")

if __name__ == '__main__':
    download_avatars_from_r2()
