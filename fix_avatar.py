"""
Script to fix avatar paths in database
Remove duplicate prefix "images/students/" from R2 URLs
"""
from app import create_app
from app.models import db, Child

app = create_app()

def fix_avatar_paths():
    with app.app_context():
        # Find students with broken avatar paths
        students = Child.query.filter(Child.avatar.isnot(None)).all()
        
        fixed_count = 0
        for student in students:
            if student.avatar and 'http' in student.avatar:
                # Check if path has duplicate prefix
                if student.avatar.startswith('images/students/http'):
                    # Extract just the R2 URL
                    r2_url = student.avatar.replace('images/students/', '')
                    print(f"Fixing {student.name} ({student.student_code})")
                    print(f"  Before: {student.avatar}")
                    print(f"  After:  {r2_url}")
                    student.avatar = r2_url
                    fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ Đã fix {fixed_count} avatar paths!")
        else:
            print("\n✅ Không có avatar nào cần fix.")

if __name__ == '__main__':
    fix_avatar_paths()
