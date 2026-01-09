"""
Example routes using new RBAC system
Ví dụ các routes đã được cập nhật với hệ thống phân quyền mới

Thay thế các route cũ bằng các route này
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth_helpers import (
    login_required, role_required, permission_required,
    admin_only, teacher_or_admin, current_user,
    can_access_course, can_manage_course
)
from app.models_users import User, StudentProfile, TeacherProfile
from app.models_courses import Course, Enrollment
from app.models import db

main = Blueprint('main', __name__)


# ==================== AUTHENTICATION ====================
@main.route('/login', methods=['GET', 'POST'])
def login():
    """Login với hệ thống mới"""
    if request.method == 'POST':
        email_or_username = request.form.get('username')
        password = request.form.get('password')
        
        # Tìm user bằng email hoặc username
        user = User.query.filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Tài khoản đã bị khóa!', 'danger')
                return redirect(url_for('main.login'))
            
            # Set session
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            session['full_name'] = user.full_name
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            flash(f'Xin chào {user.full_name}!', 'success')
            
            # Redirect theo role
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('main.teacher_dashboard'))
            elif user.role == 'parent':
                return redirect(url_for('main.parent_dashboard'))
            else:
                return redirect(url_for('main.courses'))
        else:
            flash('Email/Username hoặc mật khẩu không đúng!', 'danger')
    
    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký cho PUBLIC_STUDENT"""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Validate
        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng!', 'danger')
            return redirect(url_for('main.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username đã được sử dụng!', 'danger')
            return redirect(url_for('main.register'))
        
        # Create public_student
        from app.models_users import create_public_student
        user, profile = create_public_student(
            email=email,
            username=username,
            password=password,
            full_name=full_name
        )
        user.phone = phone
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        # TODO: Send verification email
        
        flash('Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')


# ==================== COURSES ====================
@main.route('/courses')
@login_required
def courses():
    """Danh sách khóa học - với phân quyền"""
    user = current_user()
    
    if user.role == 'admin':
        # Admin xem tất cả
        courses_list = Course.query.order_by(Course.created_at.desc()).all()
    
    elif user.role == 'teacher':
        # Teacher xem khóa học của mình
        if user.teacher_profile:
            courses_list = Course.query.filter_by(
                instructor_id=user.teacher_profile.id
            ).order_by(Course.created_at.desc()).all()
        else:
            courses_list = []
    
    elif user.role in ['student', 'public_student']:
        # Students xem khóa học published
        courses_list = Course.query.filter_by(status='published').order_by(Course.created_at.desc()).all()
    
    elif user.role == 'parent':
        # Parent xem khóa học của con đã đăng ký
        enrolled_course_ids = []
        if user.parent_profile:
            for child in user.parent_profile.children:
                enrollments = Enrollment.query.filter_by(student_id=child.user_id).all()
                enrolled_course_ids.extend([e.course_id for e in enrollments])
        
        courses_list = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()
    
    else:
        courses_list = []
    
    return render_template('courses/index.html', 
                         courses=courses_list,
                         user=user)


@main.route('/courses/create', methods=['GET', 'POST'])
@role_required('admin', 'teacher')
def course_create():
    """Tạo khóa học mới"""
    user = current_user()
    
    if request.method == 'POST':
        # Determine instructor
        if user.role == 'admin':
            # Admin có thể chọn instructor
            instructor_id = request.form.get('instructor_id')
            if not instructor_id:
                flash('Vui lòng chọn giảng viên!', 'danger')
                return redirect(url_for('main.course_create'))
        else:
            # Teacher tự động là instructor
            if not user.teacher_profile:
                flash('Không tìm thấy profile giảng viên!', 'danger')
                return redirect(url_for('main.courses'))
            instructor_id = user.teacher_profile.id
        
        # Create course
        from datetime import datetime
        title = request.form.get('title')
        slug = title.lower().replace(' ', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        course = Course(
            title=title,
            slug=slug,
            short_description=request.form.get('subtitle'),
            description=request.form.get('description'),
            instructor_id=instructor_id,
            category=request.form.get('category'),
            level=request.form.get('level'),
            price=float(request.form.get('price', 0)),
            status='draft',  # Mặc định là draft
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash(f'Khóa học "{title}" đã được tạo!', 'success')
        return redirect(url_for('main.course_detail', course_id=course.id))
    
    # GET: Show form
    teachers = None
    if user.role == 'admin':
        # Admin có thể chọn instructor
        teachers = User.query.filter_by(role='teacher').all()
    
    return render_template('courses/create.html', teachers=teachers, user=user)


@main.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    """Chi tiết khóa học"""
    course = Course.query.get_or_404(course_id)
    user = current_user()
    
    # Check xem user đã enroll chưa
    is_enrolled = False
    if user.role in ['student', 'public_student']:
        enrollment = Enrollment.query.filter_by(
            course_id=course_id,
            student_id=user.id,
            status='active'
        ).first()
        is_enrolled = enrollment is not None
    
    # Check xem có thể manage không
    can_manage = can_manage_course(course_id)
    
    # Get sections, reviews, instructor
    from app.models_courses import CourseSection, CourseReview
    sections = CourseSection.query.filter_by(course_id=course_id).order_by(CourseSection.order).all()
    reviews = CourseReview.query.filter_by(course_id=course_id).order_by(CourseReview.created_at.desc()).limit(10).all()
    
    instructor = None
    if course.instructor_id:
        teacher_profile = TeacherProfile.query.get(course.instructor_id)
        if teacher_profile:
            instructor = teacher_profile.user
    
    return render_template('courses/detail.html',
                         course=course,
                         sections=sections,
                         reviews=reviews,
                         instructor=instructor,
                         is_enrolled=is_enrolled,
                         can_manage=can_manage,
                         user=user)


@main.route('/courses/<int:course_id>/learn')
@login_required
def course_learn(course_id):
    """Video player - check quyền truy cập"""
    # Check quyền truy cập
    if not can_access_course(course_id):
        flash('Bạn chưa đăng ký khóa học này!', 'warning')
        return redirect(url_for('main.course_detail', course_id=course_id))
    
    course = Course.query.get_or_404(course_id)
    user = current_user()
    
    from app.models_courses import CourseSection, Lesson, Enrollment, LessonProgress
    sections = CourseSection.query.filter_by(course_id=course_id).order_by(CourseSection.order).all()
    
    # Get enrollment để track progress
    enrollment = None
    if user.role in ['student', 'public_student']:
        enrollment = Enrollment.query.filter_by(
            course_id=course_id,
            student_id=user.id
        ).first()
    
    # Find current lesson
    current_lesson = None
    if enrollment:
        for section in sections:
            for lesson in section.lessons:
                progress = LessonProgress.query.filter_by(
                    enrollment_id=enrollment.id,
                    lesson_id=lesson.id
                ).first()
                if not progress or not progress.is_completed:
                    current_lesson = lesson
                    break
            if current_lesson:
                break
    
    if not current_lesson and sections and sections[0].lessons:
        current_lesson = sections[0].lessons[0]
    
    return render_template('courses/learn.html',
                         course=course,
                         sections=sections,
                         current_lesson=current_lesson,
                         enrollment=enrollment,
                         user=user)


@main.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def course_enroll(course_id):
    """Đăng ký khóa học"""
    course = Course.query.get_or_404(course_id)
    user = current_user()
    
    # Check đã enroll chưa
    existing = Enrollment.query.filter_by(
        course_id=course_id,
        student_id=user.id
    ).first()
    
    if existing:
        flash('Bạn đã đăng ký khóa học này rồi!', 'info')
        return redirect(url_for('main.course_learn', course_id=course_id))
    
    # Logic đăng ký theo role
    if user.role == 'student':
        # Internal student
        if course.price == 0:
            # Miễn phí -> tự động enroll
            enrollment = Enrollment(
                course_id=course_id,
                student_id=user.id,
                status='active',
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
            
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('main.course_learn', course_id=course_id))
        else:
            # Trả phí -> cần phụ huynh thanh toán
            flash('Khóa học này cần thanh toán. Vui lòng liên hệ phụ huynh!', 'warning')
            return redirect(url_for('main.course_detail', course_id=course_id))
    
    elif user.role == 'public_student':
        # Public student phải thanh toán cho mọi khóa học
        if course.price > 0:
            # Redirect to payment
            return redirect(url_for('main.checkout', course_id=course_id))
        else:
            # Miễn phí nhưng vẫn cần enroll
            enrollment = Enrollment(
                course_id=course_id,
                student_id=user.id,
                status='active',
                enrolled_at=datetime.utcnow()
            )
            db.session.add(enrollment)
            db.session.commit()
            
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('main.course_learn', course_id=course_id))
    
    else:
        flash('Bạn không thể đăng ký khóa học!', 'danger')
        return redirect(url_for('main.courses'))


# ==================== STUDENTS MANAGEMENT ====================
@main.route('/students')
@role_required('admin', 'teacher', 'parent')
def students_list():
    """Danh sách học sinh - theo quyền"""
    user = current_user()
    
    if user.role == 'admin':
        # Admin xem tất cả
        students = StudentProfile.query.filter_by(student_type='internal').all()
    
    elif user.role == 'teacher':
        # Teacher xem học sinh trong lớp của mình
        # TODO: Cần implement Teacher-Class relationship
        # Tạm thời show tất cả
        students = StudentProfile.query.filter_by(student_type='internal').all()
    
    elif user.role == 'parent':
        # Parent xem con của mình
        students = user.parent_profile.children if user.parent_profile else []
    
    else:
        students = []
    
    return render_template('students/list.html', students=students, user=user)


@main.route('/students/<int:student_id>')
@login_required
def student_detail(student_id):
    """Chi tiết học sinh - check quyền"""
    from app.auth_helpers import can_view_student
    
    if not can_view_student(student_id):
        flash('Bạn không có quyền xem thông tin học sinh này!', 'danger')
        return redirect(url_for('main.students_list'))
    
    student = StudentProfile.query.filter_by(user_id=student_id).first_or_404()
    
    return render_template('students/detail.html', student=student)


# ==================== DASHBOARDS ====================
@main.route('/admin/dashboard')
@admin_only
def admin_dashboard():
    """Dashboard cho admin"""
    total_users = User.query.count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_students = StudentProfile.query.filter_by(student_type='internal').count()
    total_public = User.query.filter_by(role='public_student').count()
    total_courses = Course.query.count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_teachers=total_teachers,
                         total_students=total_students,
                         total_public=total_public,
                         total_courses=total_courses)


@main.route('/teacher/dashboard')
@role_required('teacher')
def teacher_dashboard():
    """Dashboard cho teacher"""
    user = current_user()
    
    my_courses = []
    my_students = []
    
    if user.teacher_profile:
        my_courses = Course.query.filter_by(instructor_id=user.teacher_profile.id).all()
        # TODO: Get students in teacher's classes
    
    return render_template('teacher/dashboard.html',
                         courses=my_courses,
                         students=my_students)


@main.route('/parent/dashboard')
@role_required('parent')
def parent_dashboard():
    """Dashboard cho parent"""
    user = current_user()
    
    children = []
    if user.parent_profile:
        children = user.parent_profile.children
    
    return render_template('parent/dashboard.html', children=children)
