"""
Authentication and Authorization Decorators
Decorators và functions để xác thực và phân quyền
"""
from functools import wraps
from flask import session, redirect, url_for, flash, abort
from app.models_users import User, ROLE_PERMISSIONS


def login_required(f):
    """
    Decorator yêu cầu đăng nhập
    Usage: @login_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục!', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorator yêu cầu role cụ thể
    Usage: @role_required('admin', 'teacher')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vui lòng đăng nhập để tiếp tục!', 'warning')
                return redirect(url_for('main.login'))
            
            user_role = session.get('role')
            if user_role not in roles:
                flash('Bạn không có quyền truy cập trang này!', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission):
    """
    Decorator yêu cầu permission cụ thể
    Usage: @permission_required('manage_courses')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vui lòng đăng nhập để tiếp tục!', 'warning')
                return redirect(url_for('main.login'))
            
            user_role = session.get('role')
            permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            if permission not in permissions:
                flash('Bạn không có quyền thực hiện hành động này!', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_only(f):
    """
    Decorator chỉ cho phép admin
    Usage: @admin_only
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục!', 'warning')
            return redirect(url_for('main.login'))
        
        if session.get('role') != 'admin':
            flash('Chỉ admin mới có quyền truy cập!', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_or_admin(f):
    """
    Decorator cho phép teacher hoặc admin
    Usage: @teacher_or_admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục!', 'warning')
            return redirect(url_for('main.login'))
        
        user_role = session.get('role')
        if user_role not in ['admin', 'teacher']:
            flash('Chỉ giáo viên và admin mới có quyền truy cập!', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== HELPER FUNCTIONS ====================

def current_user():
    """Lấy thông tin user hiện tại từ session"""
    user_id = session.get('user_id')
    if user_id:
        from app.models_users import User
        return User.query.get(user_id)
    return None


def has_permission(permission):
    """Check xem user hiện tại có permission không"""
    user_role = session.get('role')
    if not user_role:
        return False
    return permission in ROLE_PERMISSIONS.get(user_role, [])


def is_admin():
    """Check xem user hiện tại có phải admin không"""
    return session.get('role') == 'admin'


def is_teacher():
    """Check xem user hiện tại có phải teacher không"""
    return session.get('role') == 'teacher'


def is_student():
    """Check xem user hiện tại có phải student không"""
    return session.get('role') in ['student', 'public_student']


def is_parent():
    """Check xem user hiện tại có phải parent không"""
    return session.get('role') == 'parent'


def can_access_course(course_id):
    """
    Check xem user có thể truy cập khóa học không
    
    Rules:
    - Admin: Truy cập tất cả
    - Teacher: Truy cập khóa học của mình
    - Student (internal): Truy cập khóa học miễn phí + khóa đã đăng ký
    - Student (public): Chỉ truy cập khóa đã mua
    - Parent: Truy cập khóa học con đã đăng ký
    """
    from app.models_courses import Course, Enrollment
    
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if not user_id:
        return False
    
    course = Course.query.get(course_id)
    if not course:
        return False
    
    # Admin xem tất cả
    if user_role == 'admin':
        return True
    
    # Teacher xem khóa học của mình
    if user_role == 'teacher':
        # Cần lấy teacher_id từ profile
        user = current_user()
        if user and user.teacher_profile:
            return course.instructor_id == user.teacher_profile.id
        return False
    
    # Student: check enrollment
    if user_role in ['student', 'public_student']:
        # Học sinh nội bộ có thể xem khóa miễn phí
        if user_role == 'student' and course.price == 0:
            return True
        
        # Check xem đã đăng ký chưa
        enrollment = Enrollment.query.filter_by(
            course_id=course_id,
            student_id=user_id,
            status='active'
        ).first()
        return enrollment is not None
    
    # Parent: check xem con có đăng ký không
    if user_role == 'parent':
        user = current_user()
        if user and user.parent_profile:
            for child in user.parent_profile.children:
                enrollment = Enrollment.query.filter_by(
                    course_id=course_id,
                    student_id=child.user_id,
                    status='active'
                ).first()
                if enrollment:
                    return True
        return False
    
    return False


def can_manage_course(course_id):
    """
    Check xem user có thể quản lý (edit/delete) khóa học không
    
    Rules:
    - Admin: Quản lý tất cả
    - Teacher: Chỉ quản lý khóa học của mình
    """
    user_role = session.get('role')
    
    if user_role == 'admin':
        return True
    
    if user_role == 'teacher':
        from app.models_courses import Course
        course = Course.query.get(course_id)
        if course:
            user = current_user()
            if user and user.teacher_profile:
                return course.instructor_id == user.teacher_profile.id
    
    return False


def can_view_student(student_id):
    """
    Check xem user có thể xem thông tin học sinh không
    
    Rules:
    - Admin: Xem tất cả
    - Teacher: Xem học sinh trong lớp của mình
    - Parent: Xem con của mình
    - Student: Chỉ xem thông tin của chính mình
    """
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    if user_role == 'admin':
        return True
    
    if user_role == 'teacher':
        # Check xem học sinh có trong lớp của giáo viên không
        from app.models_users import StudentProfile
        from app.models import Class
        
        student = StudentProfile.query.filter_by(user_id=student_id).first()
        if student and student.class_id:
            # TODO: Cần thêm relationship giữa Teacher và Class
            # Tạm thời return True nếu là teacher
            return True
        return False
    
    if user_role == 'parent':
        user = current_user()
        if user and user.parent_profile:
            child_ids = [child.user_id for child in user.parent_profile.children]
            return student_id in child_ids
        return False
    
    if user_role == 'student':
        return user_id == student_id
    
    return False
