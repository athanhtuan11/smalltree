"""
Seed script để tạo dữ liệu mẫu cho Task Tracking module
"""
from app import create_app, db
from app.models_tasks import Project, Task, TaskComment
from app.models import Staff
from datetime import datetime

def seed_task_tracking():
    app = create_app()
    
    with app.app_context():
        print("🌱 Seeding Task Tracking data...")
        
        # Get or create a staff member as owner
        staff = Staff.query.filter_by(is_active=True).first()
        if not staff:
            print("⚠️  No active staff found. Please create a staff member first.")
            return
        
        print(f"✓ Using staff: {staff.name} (ID: {staff.id})")
        
        # Check if projects already exist
        existing_projects = Project.query.count()
        if existing_projects > 0:
            print(f"⚠️  Found {existing_projects} existing projects. Skipping project creation.")
            print("   Delete existing projects if you want to recreate them.")
            return
        
        # Create Project 1: Course Development
        project1 = Project(
            name='Course Development',
            key='COURSE',
            description='Phát triển các khóa học mới cho hệ thống',
            owner_id=staff.id,
            project_type='kanban',
            status='active',
            color='#43a047'
        )
        db.session.add(project1)
        db.session.flush()  # Get ID
        
        print(f"✓ Created project: {project1.name} ({project1.key})")
        
        # Create tasks for Project 1
        tasks_p1 = [
            Task(
                project_id=project1.id,
                task_key='COURSE-1',
                title='Thiết kế curriculum cho khóa Python cơ bản',
                description='Tạo outline chi tiết cho khóa học Python từ cơ bản đến nâng cao\n\nAcceptance Criteria:\n- 10+ sections\n- 50+ lectures\n- Bài tập thực hành',
                task_type='story',
                priority='high',
                status='in_progress',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=8
            ),
            Task(
                project_id=project1.id,
                task_key='COURSE-2',
                title='Quay video bài 1: Giới thiệu Python',
                description='Quay và edit video giới thiệu về ngôn ngữ Python',
                task_type='task',
                priority='high',
                status='todo',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=5
            ),
            Task(
                project_id=project1.id,
                task_key='COURSE-3',
                title='Viết bài tập thực hành về Variables',
                description='Tạo 10 bài tập về biến, kiểu dữ liệu',
                task_type='task',
                priority='medium',
                status='todo',
                reporter_id=staff.id,
                story_points=3
            ),
            Task(
                project_id=project1.id,
                task_key='COURSE-4',
                title='Review nội dung bài Introduction to Python',
                description='Kiểm tra lại nội dung, cấu trúc, và chất lượng video',
                task_type='task',
                priority='medium',
                status='review',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=2
            ),
            Task(
                project_id=project1.id,
                task_key='COURSE-5',
                title='Setup môi trường phát triển',
                description='Cài đặt Python, VSCode, extensions cần thiết',
                task_type='task',
                priority='low',
                status='done',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=1
            )
        ]
        
        for task in tasks_p1:
            db.session.add(task)
        
        print(f"✓ Created {len(tasks_p1)} tasks for {project1.key}")
        
        # Create Project 2: Content Creation
        project2 = Project(
            name='Content Creation',
            key='CONTENT',
            description='Tạo nội dung bài giảng và tài liệu học tập',
            owner_id=staff.id,
            project_type='kanban',
            status='active',
            color='#2196F3'
        )
        db.session.add(project2)
        db.session.flush()
        
        print(f"✓ Created project: {project2.name} ({project2.key})")
        
        # Create tasks for Project 2
        tasks_p2 = [
            Task(
                project_id=project2.id,
                task_key='CONTENT-1',
                title='Thiết kế slide bài giảng về OOP',
                description='Tạo slide PowerPoint về Object-Oriented Programming',
                task_type='story',
                priority='high',
                status='in_progress',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=5
            ),
            Task(
                project_id=project2.id,
                task_key='CONTENT-2',
                title='Viết bài blog: Top 10 Python Tips',
                description='Viết bài blog chia sẻ 10 tips hữu ích khi học Python',
                task_type='task',
                priority='medium',
                status='todo',
                reporter_id=staff.id,
                story_points=3
            ),
            Task(
                project_id=project2.id,
                task_key='CONTENT-3',
                title='Tạo infographic về Python Data Types',
                description='Thiết kế infographic trực quan về các kiểu dữ liệu trong Python',
                task_type='task',
                priority='low',
                status='done',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=2
            )
        ]
        
        for task in tasks_p2:
            db.session.add(task)
        
        print(f"✓ Created {len(tasks_p2)} tasks for {project2.key}")
        
        # Create Project 3: System Development
        project3 = Project(
            name='System Development',
            key='SYS',
            description='Phát triển và cải thiện hệ thống SmallTree',
            owner_id=staff.id,
            project_type='scrum',
            status='active',
            color='#9c27b0'
        )
        db.session.add(project3)
        db.session.flush()
        
        print(f"✓ Created project: {project3.name} ({project3.key})")
        
        # Create tasks for Project 3
        tasks_p3 = [
            Task(
                project_id=project3.id,
                task_key='SYS-1',
                title='Fix bug: Video upload không hiển thị progress',
                description='Người dùng không thấy progress bar khi upload video lớn',
                task_type='bug',
                priority='urgent',
                status='in_progress',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=3
            ),
            Task(
                project_id=project3.id,
                task_key='SYS-2',
                title='Implement course curriculum builder',
                description='Tạo giao diện quản lý sections và lectures cho khóa học',
                task_type='story',
                priority='high',
                status='done',
                reporter_id=staff.id,
                assignee_id=staff.id,
                story_points=13
            ),
            Task(
                project_id=project3.id,
                task_key='SYS-3',
                title='Add email notification cho task assignments',
                description='Gửi email thông báo khi được assign task mới',
                task_type='story',
                priority='medium',
                status='todo',
                reporter_id=staff.id,
                story_points=5
            )
        ]
        
        for task in tasks_p3:
            db.session.add(task)
        
        print(f"✓ Created {len(tasks_p3)} tasks for {project3.key}")
        
        # Add some comments to tasks
        db.session.flush()  # Ensure tasks have IDs
        
        comment1 = TaskComment(
            task_id=Task.query.filter_by(task_key='COURSE-1').first().id,
            author_id=staff.id,
            content='Đã hoàn thành phần outline cơ bản, đang review chi tiết.'
        )
        db.session.add(comment1)
        
        comment2 = TaskComment(
            task_id=Task.query.filter_by(task_key='SYS-1').first().id,
            author_id=staff.id,
            content='Root cause: Missing event listener cho upload progress. Đang fix.'
        )
        db.session.add(comment2)
        
        print("✓ Created sample comments")
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Task Tracking seeding completed!")
        print(f"   - Created 3 projects")
        print(f"   - Created {len(tasks_p1) + len(tasks_p2) + len(tasks_p3)} tasks")
        print(f"   - Created 2 comments")
        print("\n📌 Access at: http://localhost:5000/tasks")

if __name__ == '__main__':
    seed_task_tracking()
