"""
Script to check all avatar paths in database
"""
from app import create_app
from app.models import db, Child

app = create_app()

def check_avatars():
    with app.app_context():
        students = Child.query.filter(Child.avatar.isnot(None)).all()
        
        print(f"\n{'='*80}")
        print(f"KIỂM TRA AVATAR PATHS - Tổng {len(students)} học sinh có avatar")
        print(f"{'='*80}\n")
        
        local_count = 0
        r2_count = 0
        broken_count = 0
        
        for student in students:
            if not student.avatar:
                continue
            
            status = ""
            if student.avatar.startswith('images/students/http'):
                status = "❌ BROKEN PATH"
                broken_count += 1
            elif student.avatar.startswith('http'):
                status = "🌐 R2 URL"
                r2_count += 1
            elif student.avatar.startswith('images/students/'):
                status = "✅ LOCAL"
                local_count += 1
            else:
                status = "⚠️  UNKNOWN"
            
            print(f"{status:15} | {student.student_code:10} | {student.name:20} | {student.avatar}")
        
        print(f"\n{'='*80}")
        print(f"TỔNG KẾT:")
        print(f"  ✅ Local paths:   {local_count}")
        print(f"  🌐 R2 URLs:       {r2_count}")
        print(f"  ❌ Broken paths:  {broken_count}")
        print(f"{'='*80}\n")
        
        if broken_count > 0 or r2_count > 0:
            print("⚠️  CẦN CHẠY: python fix_avatar.py để fix các avatars trên")
        else:
            print("✅ Tất cả avatars đều OK!")

if __name__ == '__main__':
    check_avatars()
