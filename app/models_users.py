"""
New User Management System with RBAC
Hệ thống quản lý người dùng mới với phân quyền rõ ràng
"""
from app.models import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    Bảng User chung cho tất cả người dùng
    Thay thế việc dùng Child, Staff riêng biệt
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Thông tin cá nhân
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(300))
    
    # Role & Status
    role = db.Column(db.String(20), nullable=False, index=True)  # admin, teacher, parent, student, public_student
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)  # Xác thực email
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Relationships
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, lazy=True)
    student_profile = db.relationship('StudentProfile', 
                                      foreign_keys='StudentProfile.user_id',
                                      backref='user', 
                                      uselist=False, 
                                      lazy=True)
    parent_profile = db.relationship('ParentProfile', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        """Hash password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def __repr__(self):
        return f'<User {self.username} - {self.role}>'


class TeacherProfile(db.Model):
    """Thông tin chi tiết giáo viên"""
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Thông tin nghề nghiệp
    position = db.Column(db.String(100))  # Vị trí: Giáo viên chính, Phụ trách,...
    subject = db.Column(db.String(100))  # Môn dạy chính
    bio = db.Column(db.Text)  # Giới thiệu bản thân
    experience_years = db.Column(db.Integer, default=0)
    
    # Thông tin quản lý
    employee_code = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    
    # Statistics
    total_students = db.Column(db.Integer, default=0)
    total_courses = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TeacherProfile {self.user.full_name}>'


class StudentProfile(db.Model):
    """Thông tin chi tiết học sinh"""
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Phân loại học sinh
    student_type = db.Column(db.String(20), nullable=False)  # 'internal' hoặc 'public'
    # internal: học sinh trong trường (có lớp, được quản lý)
    # public: học sinh đăng ký từ bên ngoài (chỉ học online)
    
    # Thông tin học sinh nội bộ (internal)
    student_code = db.Column(db.String(20), unique=True, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    class_obj = db.relationship('Class', backref='students', lazy=True)
    
    # Thông tin cá nhân
    date_of_birth = db.Column(db.Date)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(500))
    
    # Thông tin phụ huynh
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Link to parent user
    father_name = db.Column(db.String(100))
    father_phone = db.Column(db.String(20))
    mother_name = db.Column(db.String(100))
    mother_phone = db.Column(db.String(20))
    
    # Trạng thái
    enrollment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, graduated, dropout
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentProfile {self.user.full_name} - {self.student_type}>'


class ParentProfile(db.Model):
    """Thông tin chi tiết phụ huynh"""
    __tablename__ = 'parent_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Thông tin liên hệ khẩn cấp
    emergency_contact = db.Column(db.String(100))
    address = db.Column(db.String(500))
    
    # Danh sách con - relationship through parent_id in StudentProfile
    # Note: SQLAlchemy sẽ tự động match parent_id với user_id của ParentProfile
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def children(self):
        """Get all children of this parent"""
        return StudentProfile.query.filter_by(parent_id=self.user_id).all()
    
    def __repr__(self):
        return f'<ParentProfile {self.user.full_name}>'


# ==================== PERMISSIONS ====================
# Định nghĩa quyền cho từng role
ROLE_PERMISSIONS = {
    'admin': [
        'manage_users',
        'manage_classes',
        'manage_all_courses',
        'manage_activities',
        'manage_attendance',
        'manage_finance',
        'view_analytics',
        'manage_system'
    ],
    'teacher': [
        'manage_own_courses',
        'view_own_classes',
        'manage_attendance',
        'view_own_students',
        'grade_students',
        'create_activities',
        'manage_curriculum'
    ],
    'parent': [
        'view_children_info',
        'view_children_attendance',
        'view_children_grades',
        'pay_tuition',
        'enroll_courses',
        'view_activities'
    ],
    'student': [
        'view_own_profile',
        'view_own_grades',
        'view_own_attendance',
        'access_courses',
        'submit_assignments',
        'view_activities'
    ],
    'public_student': [
        'view_own_profile',
        'purchase_courses',
        'access_enrolled_courses',
        'submit_assignments',
        'view_certificates'
    ]
}


# ==================== HELPER FUNCTIONS ====================
def create_admin(email, username, password, full_name):
    """Tạo admin account"""
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        role='admin',
        is_active=True,
        is_verified=True
    )
    user.set_password(password)
    return user


def create_teacher(email, username, password, full_name, position=None):
    """Tạo teacher account với profile"""
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        role='teacher',
        is_active=True,
        is_verified=True
    )
    user.set_password(password)
    
    profile = TeacherProfile(
        user=user,
        position=position or 'Giáo viên'
    )
    
    return user, profile


def create_internal_student(email, username, password, full_name, class_id, parent_user=None):
    """Tạo học sinh nội bộ (có lớp học)"""
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        role='student',
        is_active=True,
        is_verified=True
    )
    user.set_password(password)
    
    profile = StudentProfile(
        user=user,
        student_type='internal',
        class_id=class_id,
        parent_id=parent_user.id if parent_user else None
    )
    
    return user, profile


def create_public_student(email, username, password, full_name):
    """Tạo học sinh công khai (đăng ký từ bên ngoài)"""
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        role='public_student',
        is_active=True,
        is_verified=False  # Cần xác thực email
    )
    user.set_password(password)
    
    profile = StudentProfile(
        user=user,
        student_type='public'
    )
    
    return user, profile


def create_parent(email, username, password, full_name):
    """Tạo parent account"""
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        role='parent',
        is_active=True,
        is_verified=True
    )
    user.set_password(password)
    
    profile = ParentProfile(user=user)
    
    return user, profile
