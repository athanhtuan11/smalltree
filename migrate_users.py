"""
Migration script: Migrate old user system to new RBAC system
Chuyển đổi từ hệ thống cũ (Child, Staff riêng) sang hệ thống mới (User unified)

CẢNH BÁO: Backup database trước khi chạy script này!
"""
from app import create_app, db
from app.models import Child, Staff, Class
from app.models_users import (
    User, TeacherProfile, StudentProfile, ParentProfile,
    create_admin, create_teacher, create_internal_student, create_parent
)
from datetime import datetime


def migrate_to_new_user_system():
    """
    Chuyển đổi data từ hệ thống cũ sang mới
    
    Steps:
    1. Migrate Staff -> User (role=teacher) + TeacherProfile
    2. Migrate Child -> User (role=student) + StudentProfile (type=internal)
    3. Create admin account
    4. Update related tables (courses, enrollments...)
    """
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("MIGRATION: Old User System -> New RBAC System")
        print("=" * 60)
        
        # Step 1: Create Admin account
        print("\n[1/4] Creating Admin account...")
        admin_email = "admin@smalltree.vn"
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if not existing_admin:
            admin = create_admin(
                email=admin_email,
                username="admin",
                password="admin123",  # CHANGE THIS!
                full_name="Administrator"
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Admin created: {admin.email}")
        else:
            print(f"⊗ Admin already exists: {existing_admin.email}")
        
        # Step 2: Migrate Staff to Teachers
        print("\n[2/4] Migrating Staff to Teachers...")
        staff_list = Staff.query.all()
        staff_mapping = {}  # old_id -> new_user_id
        
        for staff in staff_list:
            # Check if already migrated
            existing_user = User.query.filter_by(email=staff.email).first()
            if existing_user:
                print(f"⊗ Staff '{staff.name}' already migrated")
                staff_mapping[staff.id] = existing_user.id
                continue
            
            # Create username from email or name
            username = staff.email.split('@')[0] if staff.email else f"teacher_{staff.id}"
            
            # Create teacher account
            user, profile = create_teacher(
                email=staff.email or f"{username}@smalltree.vn",
                username=username,
                password="teacher123",  # Default password - should be changed
                full_name=staff.name,
                position=staff.position
            )
            
            # Copy phone
            if staff.phone:
                user.phone = staff.phone
            
            db.session.add(user)
            db.session.add(profile)
            db.session.flush()
            
            staff_mapping[staff.id] = user.id
            print(f"✓ Migrated: {staff.name} -> {user.email}")
        
        db.session.commit()
        print(f"✓ Total teachers migrated: {len(staff_mapping)}")
        
        # Step 3: Migrate Children to Students
        print("\n[3/4] Migrating Children to Internal Students...")
        children_list = Child.query.filter_by(is_active=True).all()
        child_mapping = {}  # old_id -> new_user_id
        
        for child in children_list:
            # Check if already migrated
            existing_user = User.query.filter_by(email=child.email).first()
            if existing_user:
                print(f"⊗ Student '{child.name}' already migrated")
                child_mapping[child.id] = existing_user.id
                continue
            
            # Create username from email or student_code
            if child.email:
                username = child.email.split('@')[0]
            elif child.student_code:
                username = child.student_code
            else:
                username = f"student_{child.id}"
            
            # Get class_id
            class_obj = None
            if child.class_name:
                class_obj = Class.query.filter_by(name=child.class_name).first()
            
            # Create internal student
            user, profile = create_internal_student(
                email=child.email or f"{username}@student.smalltree.vn",
                username=username,
                password="student123",  # Default password
                full_name=child.name,
                class_id=class_obj.id if class_obj else None
            )
            
            # Copy additional info
            user.phone = child.phone
            user.avatar = child.avatar
            
            profile.student_code = child.student_code
            profile.age = child.age
            profile.date_of_birth = datetime.strptime(child.birth_date, '%Y-%m-%d').date() if child.birth_date else None
            profile.father_name = child.father_name
            profile.father_phone = child.father_phone
            profile.mother_name = child.mother_name
            profile.mother_phone = child.mother_phone
            
            db.session.add(user)
            db.session.add(profile)
            db.session.flush()
            
            child_mapping[child.id] = user.id
            print(f"✓ Migrated: {child.name} (Class: {child.class_name or 'N/A'})")
        
        db.session.commit()
        print(f"✓ Total students migrated: {len(child_mapping)}")
        
        # Step 4: Update foreign keys in related tables
        print("\n[4/4] Updating foreign keys in related tables...")
        
        # Update Course.instructor_id
        from app.models_courses import Course
        courses = Course.query.all()
        for course in courses:
            if course.instructor_id in staff_mapping:
                # Get teacher profile
                new_user_id = staff_mapping[course.instructor_id]
                teacher = User.query.get(new_user_id)
                if teacher and teacher.teacher_profile:
                    course.instructor_id = teacher.teacher_profile.id
                    print(f"✓ Updated course '{course.title}' instructor")
        
        # Update Enrollment.student_id
        from app.models_courses import Enrollment
        enrollments = Enrollment.query.all()
        for enrollment in enrollments:
            if enrollment.student_id in child_mapping:
                enrollment.student_id = child_mapping[enrollment.student_id]
                print(f"✓ Updated enrollment for student")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Admin accounts: 1")
        print(f"  - Teachers migrated: {len(staff_mapping)}")
        print(f"  - Students migrated: {len(child_mapping)}")
        print(f"\nDefault passwords:")
        print(f"  - Admin: admin123")
        print(f"  - Teachers: teacher123")
        print(f"  - Students: student123")
        print(f"\n⚠️  IMPORTANT: Change all default passwords!")
        print("=" * 60)


if __name__ == '__main__':
    import sys
    
    print("\n⚠️  WARNING: This will modify your database!")
    print("Make sure you have backed up your database before proceeding.")
    response = input("\nDo you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        migrate_to_new_user_system()
    else:
        print("Migration cancelled.")
        sys.exit(0)
