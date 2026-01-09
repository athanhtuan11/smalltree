"""
Models cho hệ thống Courses (tương tự Udemy)
"""
from app.models import db
from datetime import datetime


class Course(db.Model):
    """Khóa học - Course"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)  # URL-friendly
    description = db.Column(db.Text)
    short_description = db.Column(db.String(500))
    
    # Thông tin giảng viên
    instructor_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    instructor = db.relationship('Staff', backref=db.backref('courses', lazy=True))
    
    # Thumbnail và media
    thumbnail = db.Column(db.String(500))  # URL ảnh thumbnail
    intro_video = db.Column(db.String(500))  # URL video giới thiệu
    
    # Phân loại
    category = db.Column(db.String(100))  # Ví dụ: "Toán học", "Tiếng Anh", "STEAM"
    level = db.Column(db.String(50))  # Beginner, Intermediate, Advanced
    language = db.Column(db.String(50), default='Tiếng Việt')
    
    # Trạng thái và giá
    price = db.Column(db.Float, default=0)  # Giá khóa học (0 = miễn phí)
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    is_featured = db.Column(db.Boolean, default=False)  # Khóa học nổi bật
    
    # Thống kê
    total_duration = db.Column(db.Integer, default=0)  # Tổng thời lượng (phút)
    total_lessons = db.Column(db.Integer, default=0)  # Tổng số bài học
    enrolled_count = db.Column(db.Integer, default=0)  # Số học viên đã đăng ký
    rating_avg = db.Column(db.Float, default=0)  # Điểm đánh giá trung bình
    rating_count = db.Column(db.Integer, default=0)  # Số lượt đánh giá
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Requirements và outcomes
    requirements = db.Column(db.Text)  # JSON array: ["Yêu cầu 1", "Yêu cầu 2"]
    what_you_learn = db.Column(db.Text)  # JSON array: ["Học được 1", "Học được 2"]
    
    def __repr__(self):
        return f'<Course {self.title}>'


class CourseSection(db.Model):
    """Chương/Section trong khóa học"""
    __tablename__ = 'course_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    course = db.relationship('Course', backref=db.backref('sections', lazy=True, order_by='CourseSection.order'))
    
    def __repr__(self):
        return f'<CourseSection {self.title}>'


class Lesson(db.Model):
    """Bài học trong section"""
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('course_sections.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    
    # Loại bài học
    lesson_type = db.Column(db.String(20), default='video')  # video, text, quiz, assignment
    
    # Nội dung
    video_url = db.Column(db.String(500))  # URL video (YouTube, Vimeo, hoặc local)
    content = db.Column(db.Text)  # Nội dung text (HTML)
    duration = db.Column(db.Integer, default=0)  # Thời lượng (giây)
    
    # Tài liệu đính kèm
    attachments = db.Column(db.Text)  # JSON array: [{"name": "", "url": ""}]
    
    # Settings
    is_preview = db.Column(db.Boolean, default=False)  # Cho phép xem trước miễn phí
    is_published = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    section = db.relationship('CourseSection', backref=db.backref('lessons', lazy=True, order_by='Lesson.order'))
    
    def __repr__(self):
        return f'<Lesson {self.title}>'


class Enrollment(db.Model):
    """Đăng ký khóa học"""
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)  # Học sinh
    
    # Trạng thái
    status = db.Column(db.String(20), default='active')  # active, completed, dropped
    progress = db.Column(db.Float, default=0)  # Tiến độ % (0-100)
    
    # Thời gian
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    last_accessed_at = db.Column(db.DateTime)
    
    # Certificate
    certificate_issued = db.Column(db.Boolean, default=False)
    certificate_url = db.Column(db.String(500))
    
    course = db.relationship('Course', backref=db.backref('enrollments', lazy=True))
    student = db.relationship('Child', backref=db.backref('enrollments', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='unique_enrollment'),)
    
    def __repr__(self):
        return f'<Enrollment course={self.course_id} student={self.student_id}>'


class LessonProgress(db.Model):
    """Tiến độ học của từng bài học"""
    __tablename__ = 'lesson_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    
    # Trạng thái
    is_completed = db.Column(db.Boolean, default=False)
    watched_duration = db.Column(db.Integer, default=0)  # Thời lượng đã xem (giây)
    completion_percentage = db.Column(db.Float, default=0)  # % hoàn thành
    
    # Notes của học viên
    notes = db.Column(db.Text)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    enrollment = db.relationship('Enrollment', backref=db.backref('lesson_progress', lazy=True))
    lesson = db.relationship('Lesson', backref=db.backref('progress', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('enrollment_id', 'lesson_id', name='unique_lesson_progress'),)
    
    def __repr__(self):
        return f'<LessonProgress enrollment={self.enrollment_id} lesson={self.lesson_id}>'


class CourseReview(db.Model):
    """Đánh giá khóa học"""
    __tablename__ = 'course_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    
    # Đánh giá
    rating = db.Column(db.Integer, nullable=False)  # 1-5 sao
    review_text = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    
    course = db.relationship('Course', backref=db.backref('reviews', lazy=True))
    student = db.relationship('Child', backref=db.backref('course_reviews', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='unique_course_review'),)
    
    def __repr__(self):
        return f'<CourseReview course={self.course_id} rating={self.rating}>'
