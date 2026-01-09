"""
Seed data cho Course với Sections và Lectures đầy đủ
Tạo một khóa học Python hoàn chỉnh giống Udemy
"""
from app import create_app, db
from app.models_courses import Course, CourseSection, Lesson
from datetime import datetime
import json

app = create_app()

def seed_complete_course():
    """Tạo 1 khóa học Python đầy đủ với curriculum"""
    
    with app.app_context():
        print("🌱 Seeding complete course data...")
        
        # Check if course already exists
        existing = Course.query.filter_by(slug='complete-python-bootcamp').first()
        if existing:
            print("⚠️  Course 'Complete Python Bootcamp' already exists. Skipping...")
            return
        
        # 1. Create Course
        course = Course(
            title='Complete Python Bootcamp: Zero to Hero in Python',
            slug='complete-python-bootcamp',
            description='Learn Python like a Professional! Start from the basics and go all the way to creating your own applications and games!',
            short_description='Go from zero to hero with Python 3. Learn Python programming from scratch and build real projects.',
            instructor_id=1,  # Admin/Teacher
            thumbnail='https://img-c.udemycdn.com/course/480x270/567828_67d0.jpg',
            intro_video='https://www.youtube.com/watch?v=rfscVS0vtbw',
            category='Programming',
            level='All Levels',
            language='Tiếng Việt',
            price=499000,
            status='published',
            is_featured=True,
            total_duration=1200,  # 20 hours
            total_lessons=0,  # Will update
            enrolled_count=156,
            rating_avg=4.7,
            rating_count=42,
            published_at=datetime.utcnow(),
            requirements=json.dumps([
                'Access to a computer with an internet connection',
                'No prior programming experience needed',
                'Desire to learn Python programming'
            ]),
            what_you_learn=json.dumps([
                'Learn to use Python professionally, learning both Python 2 and Python 3!',
                'Create games with Python, like Tic Tac Toe and Blackjack',
                'Learn advanced Python features, like the collections module',
                'Learn to use Object Oriented Programming with classes',
                'Understand complex topics, like decorators',
                'Understand how to use both the Jupyter Notebook and create .py files',
                'Build a complete understanding of Python from the ground up'
            ])
        )
        
        db.session.add(course)
        db.session.flush()  # Get course.id
        
        print(f"✅ Created course: {course.title}")
        
        # 2. Create Sections and Lectures
        sections_data = [
            {
                'title': 'Course Introduction',
                'description': 'Welcome to the course! Let\'s get started.',
                'lectures': [
                    {
                        'title': 'Welcome to the Course!',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=rfscVS0vtbw',
                        'duration': 180,  # 3 minutes
                        'is_preview': True,
                        'description': 'Welcome video introducing the course structure and what you will learn.'
                    },
                    {
                        'title': 'Course Curriculum Overview',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example2',
                        'duration': 300,  # 5 minutes
                        'is_preview': True,
                        'description': 'Overview of all sections and learning path.'
                    },
                    {
                        'title': 'Course FAQs',
                        'lesson_type': 'text',
                        'content': '<h3>Frequently Asked Questions</h3><p><strong>Q: Do I need prior experience?</strong><br>A: No! This course starts from scratch.</p><p><strong>Q: What version of Python?</strong><br>A: We teach both Python 2 and Python 3.</p>',
                        'duration': 0,
                        'is_preview': True
                    }
                ]
            },
            {
                'title': 'Python Setup',
                'description': 'Install Python and set up your development environment.',
                'lectures': [
                    {
                        'title': 'Installing Python on Windows',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example3',
                        'duration': 480,  # 8 minutes
                        'is_preview': False,
                        'description': 'Step-by-step guide to install Python 3 on Windows.'
                    },
                    {
                        'title': 'Installing Python on Mac/Linux',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example4',
                        'duration': 420,  # 7 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Running Python Code',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example5',
                        'duration': 360,  # 6 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Introduction to Jupyter Notebook',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example6',
                        'duration': 600,  # 10 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Setup Quiz',
                        'lesson_type': 'quiz',
                        'duration': 0,
                        'is_preview': False,
                        'description': 'Test your knowledge about Python installation.'
                    }
                ]
            },
            {
                'title': 'Python Basics',
                'description': 'Learn the fundamental building blocks of Python programming.',
                'lectures': [
                    {
                        'title': 'Numbers in Python',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example7',
                        'duration': 720,  # 12 minutes
                        'is_preview': False,
                        'description': 'Learn about integers, floats, and basic math operations.'
                    },
                    {
                        'title': 'Variables and Assignments',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example8',
                        'duration': 540,  # 9 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Strings in Python',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example9',
                        'duration': 900,  # 15 minutes
                        'is_preview': False,
                        'description': 'Working with text: string methods, indexing, and slicing.'
                    },
                    {
                        'title': 'String Formatting',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example10',
                        'duration': 480,  # 8 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Lists in Python',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example11',
                        'duration': 840,  # 14 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Dictionaries in Python',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example12',
                        'duration': 720,  # 12 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Python Basics - Practice Assignment',
                        'lesson_type': 'assignment',
                        'duration': 0,
                        'is_preview': False,
                        'description': 'Complete 10 coding exercises to test your understanding of Python basics.'
                    }
                ]
            },
            {
                'title': 'Control Flow',
                'description': 'Learn if statements, loops, and control flow in Python.',
                'lectures': [
                    {
                        'title': 'If, Elif, and Else Statements',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example13',
                        'duration': 600,  # 10 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'For Loops',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example14',
                        'duration': 720,  # 12 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'While Loops',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example15',
                        'duration': 540,  # 9 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Useful Operators',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example16',
                        'duration': 420,  # 7 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'List Comprehensions',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example17',
                        'duration': 480,  # 8 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Control Flow Quiz',
                        'lesson_type': 'quiz',
                        'duration': 0,
                        'is_preview': False
                    }
                ]
            },
            {
                'title': 'Functions',
                'description': 'Master functions, lambda expressions, and scope.',
                'lectures': [
                    {
                        'title': 'Introduction to Functions',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example18',
                        'duration': 660,  # 11 minutes
                        'is_preview': False
                    },
                    {
                        'title': '*args and **kwargs',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example19',
                        'duration': 540,  # 9 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Lambda Expressions',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example20',
                        'duration': 420,  # 7 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Nested Functions and Scope',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example21',
                        'duration': 600,  # 10 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Functions Practice Assignment',
                        'lesson_type': 'assignment',
                        'duration': 0,
                        'is_preview': False
                    }
                ]
            },
            {
                'title': 'Object Oriented Programming',
                'description': 'Learn classes, objects, and OOP principles.',
                'lectures': [
                    {
                        'title': 'Introduction to OOP',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example22',
                        'duration': 720,  # 12 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Classes and Objects',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example23',
                        'duration': 900,  # 15 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Inheritance and Polymorphism',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example24',
                        'duration': 840,  # 14 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'Special Methods',
                        'lesson_type': 'video',
                        'video_url': 'https://www.youtube.com/watch?v=example25',
                        'duration': 600,  # 10 minutes
                        'is_preview': False
                    },
                    {
                        'title': 'OOP Challenge Project',
                        'lesson_type': 'assignment',
                        'duration': 0,
                        'is_preview': False,
                        'description': 'Build a complete Card Game using OOP principles.'
                    }
                ]
            }
        ]
        
        total_lectures = 0
        
        for idx, section_data in enumerate(sections_data, 1):
            section = CourseSection(
                course_id=course.id,
                title=section_data['title'],
                description=section_data['description'],
                order=idx
            )
            db.session.add(section)
            db.session.flush()
            
            print(f"  📁 Section {idx}: {section.title}")
            
            for lecture_idx, lecture_data in enumerate(section_data['lectures'], 1):
                lecture = Lesson(
                    section_id=section.id,
                    title=lecture_data['title'],
                    lesson_type=lecture_data['lesson_type'],
                    video_url=lecture_data.get('video_url', ''),
                    content=lecture_data.get('content', ''),
                    duration=lecture_data['duration'],
                    description=lecture_data.get('description', ''),
                    is_preview=lecture_data.get('is_preview', False),
                    order=lecture_idx
                )
                db.session.add(lecture)
                total_lectures += 1
                
                icon = {'video': '🎥', 'text': '📄', 'quiz': '❓', 'assignment': '📝'}.get(lecture.lesson_type, '📌')
                print(f"    {icon} Lecture {lecture_idx}: {lecture.title}")
        
        # Update course stats
        course.total_lessons = total_lectures
        
        db.session.commit()
        
        print(f"\n✅ Successfully created:")
        print(f"   - 1 Course: {course.title}")
        print(f"   - {len(sections_data)} Sections")
        print(f"   - {total_lectures} Lectures")
        print(f"\n🌐 Access curriculum builder at:")
        print(f"   http://localhost:5000/courses/{course.id}/curriculum")


if __name__ == '__main__':
    seed_complete_course()
    print("\n🎉 Seeding complete!")
