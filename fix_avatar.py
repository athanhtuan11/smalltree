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
        fixed_path_count = 0
        
        for student in students:
            if not student.avatar:
                continue
            
            # Extract R2 URL from broken path like "images/students/https://..."
            r2_url = None
            if 'http' in student.avatar:
                if student.avatar.startswith('images/students/http'):
                    # Broken path: extract R2 URL
                    r2_url = student.avatar.replace('images/students/', '')
                    print(f"\n🔧 Fix broken path: {student.name} ({student.student_code})")
                    print(f"   Before: {student.avatar}")
                    print(f"   R2 URL: {r2_url}")
                elif student.avatar.startswith('http'):
                    # Direct R2 URL
                    r2_url = student.avatar
                    print(f"\n📥 Đang xử lý {student.name} ({student.student_code})")
                    print(f"   R2 URL: {r2_url}")
            
            if r2_url:
                try:
                    # Download from R2
                    response = requests.get(r2_url, timeout=10)
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
                        
                        if 'images/students/http' in old_avatar:
                            fixed_path_count += 1
                        else:
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
        total_changes = downloaded_count + fixed_path_count
        if total_changes > 0:
            db.session.commit()
            print(f"\n{'='*60}")
            if fixed_path_count > 0:
                print(f"🔧 Đã fix {fixed_path_count} avatars có path lỗi")
            if downloaded_count > 0:
                print(f"✅ Đã download {downloaded_count} avatars từ R2 về local")
            print(f"⏭️  Bỏ qua {skipped_count} avatars đã ở local")
            if error_count > 0:
                print(f"❌ Lỗi {error_count} avatars")
            print(f"{'='*60}")
        else:
            print(f"\n✅ Không có avatar nào cần xử lý. Tất cả đã ở local.")
            print(f"   (Bỏ qua {skipped_count} avatars)")

if __name__ == '__main__':
    download_avatars_from_r2()
