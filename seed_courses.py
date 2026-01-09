"""
Script to seed database with sample courses
"""
from app import create_app, db
from app.models_courses import Course, CourseSection, Lesson
from app.models import Staff
from datetime import datetime
import json

app = create_app()

with app.app_context():
    # Get first staff member to be instructor
    instructor = Staff.query.first()
    if not instructor:
        print("No staff found! Please create a staff member first.")
        exit(1)
    
    print(f"Using instructor: {instructor.name} (ID: {instructor.id})")
    
    # Create sample courses
    courses_data = [
        {
            'title': 'Complete Python Programming',
            'slug': 'complete-python-programming',
            'short_description': 'Master Python from basics to advanced with hands-on projects',
            'description': '''Học Python từ cơ bản đến nâng cao với các dự án thực tế. 
            
Khóa học này bao gồm:
- Python cơ bản: biến, kiểu dữ liệu, control flow
- Functions và OOP
- Working with files và databases
- Web scraping với BeautifulSoup
- Data analysis với Pandas
- API development với Flask

Phù hợp cho người mới bắt đầu muốn học lập trình hoặc người muốn chuyển sang Data Science/ML.''',
            'category': 'Programming',
            'level': 'Beginner',
            'price': 399000,
            'status': 'published',
            'total_duration': 2520,  # 42 hours
            'total_lessons': 156,
            'what_you_learn': json.dumps([
                'Học Python 3 từ cơ bản đến nâng cao',
                'Xây dựng được các ứng dụng thực tế',
                'Hiểu về Object-Oriented Programming',
                'Làm việc với files, databases, và APIs',
                'Sử dụng các thư viện phổ biến như NumPy, Pandas',
                'Chuẩn bị cho Data Science và Machine Learning'
            ]),
            'requirements': json.dumps([
                'Không cần kinh nghiệm lập trình trước đó',
                'Máy tính Windows/Mac/Linux',
                'Kết nối internet để xem video'
            ])
        },
        {
            'title': 'Web Development Bootcamp',
            'slug': 'web-development-bootcamp',
            'short_description': 'HTML, CSS, JavaScript, React, Node.js - Complete web development',
            'description': '''Khóa học toàn diện về phát triển web từ Frontend đến Backend.

Nội dung khóa học:
- HTML5 & CSS3 cơ bản và nâng cao
- JavaScript ES6+ và DOM manipulation
- Responsive design với Bootstrap
- React.js cho Frontend
- Node.js và Express cho Backend
- MongoDB database
- Authentication và Authorization
- Deploy lên Heroku và Netlify

Sau khóa học bạn có thể xây dựng website hoàn chỉnh.''',
            'category': 'Web Development',
            'level': 'All Levels',
            'price': 499000,
            'status': 'published',
            'total_duration': 3780,  # 63 hours
            'total_lessons': 234,
            'what_you_learn': json.dumps([
                'HTML5, CSS3, và JavaScript hiện đại',
                'Responsive design với Bootstrap và Flexbox',
                'React.js cho single-page applications',
                'Node.js và Express framework',
                'MongoDB và Mongoose',
                'RESTful APIs và Authentication',
                'Deploy ứng dụng lên production'
            ]),
            'requirements': json.dumps([
                'Hiểu biết cơ bản về máy tính và internet',
                'Không cần kinh nghiệm lập trình',
                'Máy tính với internet ổn định'
            ])
        },
        {
            'title': 'Machine Learning A-Z',
            'slug': 'machine-learning-a-z',
            'short_description': 'Learn ML algorithms from theory to practice with Python',
            'description': '''Khóa học Machine Learning từ lý thuyết đến thực hành với Python.

Topics:
- Regression: Linear, Polynomial, SVR
- Classification: Logistic Regression, KNN, SVM, Random Forest
- Clustering: K-Means, Hierarchical
- Deep Learning: Neural Networks, CNN
- Natural Language Processing
- Reinforcement Learning basics

Bao gồm cả lý thuyết toán học và code thực tế với scikit-learn, TensorFlow.''',
            'category': 'Data Science',
            'level': 'Intermediate',
            'price': 599000,
            'status': 'published',
            'total_duration': 2640,  # 44 hours
            'total_lessons': 289,
            'what_you_learn': json.dumps([
                'Các thuật toán ML cơ bản và nâng cao',
                'Preprocessing và feature engineering',
                'Model evaluation và tuning',
                'Deep Learning với TensorFlow',
                'Natural Language Processing',
                'Computer Vision với CNN',
                'Deploy ML models'
            ]),
            'requirements': json.dumps([
                'Kiến thức Python cơ bản',
                'Toán học cấp 3 (algebra, calculus)',
                'Hiểu biết về statistics cơ bản'
            ])
        }
    ]
    
    for course_data in courses_data:
        # Check if course exists
        existing = Course.query.filter_by(slug=course_data['slug']).first()
        if existing:
            print(f"Course '{course_data['title']}' already exists. Skipping.")
            continue
        
        # Create course
        course = Course(
            title=course_data['title'],
            slug=course_data['slug'],
            short_description=course_data['short_description'],
            description=course_data['description'],
            instructor_id=instructor.id,
            category=course_data['category'],
            level=course_data['level'],
            language='Vietnamese',
            price=course_data['price'],
            status=course_data['status'],
            total_duration=course_data['total_duration'],
            total_lessons=course_data['total_lessons'],
            what_you_learn=course_data['what_you_learn'],
            requirements=course_data['requirements'],
            rating_avg=4.5 + (hash(course_data['title']) % 5) / 10,  # Random rating 4.5-4.9
            rating_count=50 + (hash(course_data['title']) % 150),  # Random 50-200 reviews
            enrolled_count=30 + (hash(course_data['title']) % 100),  # Random 30-130 students
            created_at=datetime.now(),
            updated_at=datetime.now(),
            published_at=datetime.now()
        )
        
        db.session.add(course)
        db.session.flush()  # Get course.id
        
        # Add sample sections
        section1 = CourseSection(
            course_id=course.id,
            title='Introduction',
            order=1
        )
        db.session.add(section1)
        db.session.flush()
        
        # Add sample lessons
        lesson1 = Lesson(
            section_id=section1.id,
            title='Welcome to the Course',
            order=1,
            duration=330,  # 5:30
            is_preview=True
        )
        lesson2 = Lesson(
            section_id=section1.id,
            title='Course Overview',
            order=2,
            duration=480,  # 8:00
            is_preview=True
        )
        db.session.add_all([lesson1, lesson2])
        
        print(f"✓ Created course: {course.title}")
    
    db.session.commit()
    print("\n✓ Database seeded successfully!")
    print(f"Total courses: {Course.query.count()}")
