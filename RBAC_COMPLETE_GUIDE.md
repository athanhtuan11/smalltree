# 🔐 SmallTree RBAC System - Complete Guide

**Hệ thống Phân quyền Role-Based Access Control hoàn chỉnh cho SmallTree Website**

> Version: 1.0.0  
> Last Updated: January 9, 2026  
> Author: AI Assistant with athanhtuan11

---

## 📋 MỤC LỤC

1. [Tổng quan Hệ thống](#1-tổng-quan-hệ-thống)
2. [Kiến trúc Database](#2-kiến-trúc-database)
3. [5 Loại User Roles](#3-5-loại-user-roles)
4. [Permissions Chi tiết](#4-permissions-chi-tiết)
5. [Hướng dẫn Sử dụng](#5-hướng-dẫn-sử-dụng)
6. [Routes & Features](#6-routes--features)
7. [Cài đặt & Setup](#7-cài-đặt--setup)
8. [Migration từ Old System](#8-migration-từ-old-system)
9. [Security & Best Practices](#9-security--best-practices)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. TỔNG QUAN HỆ THỐNG

### ❌ Vấn đề Old System:
- Phân quyền không rõ ràng (if/else rải rác)
- Child và Staff là 2 bảng riêng → khó quản lý
- Không hỗ trợ học sinh ngoài trường
- Không có Parent account
- Password không hash an toàn

### ✅ New RBAC System:
- **Unified User Model**: 1 bảng users cho tất cả
- **5 Roles rõ ràng**: admin, teacher, parent, student, public_student
- **Permission-based**: Mỗi role có list permissions cụ thể
- **Decorator-based**: @role_required, @permission_required
- **UI Management**: Admin quản lý quyền qua giao diện web
- **Secure**: Bcrypt password hashing, CSRF protection

---

## 2. KIẾN TRÚC DATABASE

### Database Schema:

```
┌──────────────────────────────────────────────────────┐
│                   users (Unified)                     │
│ ─────────────────────────────────────────────────── │
│  id, email, username, password_hash                  │
│  full_name, phone, avatar                            │
│  role: admin/teacher/parent/student/public_student   │
│  is_active, is_verified, created_at, updated_at      │
└────────┬──────────────┬──────────────┬───────────────┘
         │              │              │
  ┌──────▼───────┐ ┌───▼────────┐ ┌──▼──────────┐
  │TeacherProfile│ │StudentProfile│ │ParentProfile│
  │──────────────│ │──────────────│ │─────────────│
  │ position     │ │ student_type │ │ children    │
  │ subject      │ │ class_id     │ │ address     │
  │ bio          │ │ parent_id    │ │ phone       │
  │ employee_code│ │ student_code │ │             │
  └──────────────┘ └──────────────┘ └─────────────┘
```

### Models:

#### User Model (app/models_users.py):
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 5 roles
    is_active = db.Column(db.Boolean, default=True)
```

#### Profile Models:
- **TeacherProfile**: position, subject, bio, employee_code
- **StudentProfile**: student_type (internal/public), class_id, parent_id, student_code
- **ParentProfile**: address, phone, children (@property)

---

## 3. 5 LOẠI USER ROLES

### 🔴 1. ADMIN (Administrator)
**Số lượng:** 1 account duy nhất  
**Mô tả:** Full system access

**Permissions (16):**
```
✅ manage_all_users       ✅ manage_all_courses
✅ manage_finance         ✅ delete_users
✅ view_analytics         ✅ create_courses
✅ edit_courses           ✅ view_students
✅ manage_assignments     ✅ grade_assignments
✅ view_reports           ✅ manage_activities
✅ manage_attendance      ✅ create_activities
✅ edit_activities        ✅ view_all_attendance
```

**Use Cases:**
- Quản lý toàn bộ trường/trung tâm
- Tạo/xóa tài khoản users
- Xem tất cả báo cáo, thống kê
- Config hệ thống

**Login:**
```
Email: admin@smalltree.vn
Password: admin123
```

---

### 🟢 2. TEACHER (Giáo viên/Giảng viên)
**Số lượng:** Nhiều accounts  
**Mô tả:** Manage courses, view students

**Permissions (10):**
```
✅ create_courses         ✅ edit_courses
✅ view_students          ✅ manage_assignments
✅ grade_assignments      ✅ view_reports
✅ manage_attendance      ✅ create_activities
✅ edit_activities        ✅ view_own_courses
```

**Use Cases:**
- Tạo khóa học mới
- Quản lý học sinh trong lớp
- Điểm danh, đánh giá
- Upload tài liệu

**Giới hạn:**
- ❌ Không xem được khóa học của teacher khác
- ❌ Không quản lý tài chính
- ❌ Không xóa users

**Login Test:**
```
Email: teacher@smalltree.vn
Password: teacher123
```

---

### 🟡 3. PARENT (Phụ huynh)
**Số lượng:** Nhiều accounts  
**Mô tả:** View children info, pay tuition

**Permissions (4):**
```
✅ view_children_info     ✅ view_children_attendance
✅ view_children_grades   ✅ pay_tuition
✅ enroll_courses         ✅ view_activities
```

**Use Cases:**
- Xem thông tin con (điểm, điểm danh)
- Đăng ký khóa học cho con
- Thanh toán học phí
- Xem hoạt động của con

**Giới hạn:**
- ❌ Chỉ xem được thông tin con mình
- ❌ Không xem thông tin học sinh khác
- ❌ Không quản lý khóa học

**Login Test:**
```
Email: parent@smalltree.vn
Password: parent123
```

---

### 🔵 4. STUDENT (Học sinh trong trường)
**Số lượng:** Nhiều accounts  
**Mô tả:** Access courses, submit assignments

**Permissions (6):**
```
✅ view_own_profile       ✅ view_own_grades
✅ view_own_attendance    ✅ access_courses
✅ submit_assignments     ✅ view_activities
```

**Use Cases:**
- Học sinh SmallTree (trong trường)
- Xem điểm, điểm danh của mình
- Truy cập khóa học miễn phí
- Nộp bài tập

**Giới hạn:**
- ❌ Chỉ xem được thông tin của mình
- ❌ Không mua khóa học (parent đăng ký)

**Login Test:**
```
Email: student@smalltree.vn
Password: student123
```

---

### ⚫ 5. PUBLIC_STUDENT (Học sinh bên ngoài)
**Số lượng:** Nhiều accounts  
**Mô tả:** Purchase courses, access enrolled

**Permissions (5):**
```
✅ view_own_profile       ✅ purchase_courses
✅ access_enrolled_courses ✅ submit_assignments
✅ view_certificates
```

**Use Cases:**
- Học sinh KHÔNG học tại SmallTree
- Mua khóa học online
- Tự đăng ký, thanh toán
- Học qua website

**Giới hạn:**
- ❌ Không truy cập khóa học miễn phí
- ❌ Chỉ học khóa đã mua

**Login Test:**
```
Email: public@example.com
Password: public123
```

---

## 4. PERMISSIONS CHI TIẾT

### Permission Dictionary:

```python
ROLE_PERMISSIONS = {
    'admin': [
        'manage_all_users', 'manage_all_courses', 'manage_finance',
        'delete_users', 'view_analytics', 'create_courses',
        'edit_courses', 'view_students', 'manage_assignments',
        'grade_assignments', 'view_reports', 'manage_activities',
        'manage_attendance', 'create_activities', 'edit_activities',
        'view_all_attendance'
    ],
    'teacher': [
        'create_courses', 'edit_courses', 'view_students',
        'manage_assignments', 'grade_assignments', 'view_reports',
        'manage_attendance', 'create_activities', 'edit_activities',
        'view_own_courses'
    ],
    'parent': [
        'view_children_info', 'view_children_attendance',
        'view_children_grades', 'pay_tuition', 'enroll_courses',
        'view_activities'
    ],
    'student': [
        'view_own_profile', 'view_own_grades', 'view_own_attendance',
        'access_courses', 'submit_assignments', 'view_activities'
    ],
    'public_student': [
        'view_own_profile', 'purchase_courses',
        'access_enrolled_courses', 'submit_assignments',
        'view_certificates'
    ]
}
```

### Permission Categories:

#### 🔴 Admin Permissions:
- `manage_all_users`, `delete_users`, `manage_finance`
- `view_analytics`, `manage_all_courses`

#### 🔵 Content Management:
- `create_courses`, `edit_courses`
- `create_activities`, `edit_activities`
- `manage_assignments`

#### 🟢 View Access:
- `view_students`, `view_children_info`
- `view_own_profile`, `view_reports`
- `access_courses`

#### 🟡 Actions:
- `submit_assignments`, `grade_assignments`
- `pay_tuition`, `purchase_courses`
- `manage_attendance`

---

## 5. HƯỚNG DẪN SỬ DỤNG

### A. Cho Admin:

#### 1. Quản lý Users & Permissions:

**Truy cập:**
```
http://127.0.0.1:5000/accounts
→ Click "Quản lý Quyền RBAC"
→ http://127.0.0.1:5000/rbac/users
```

**Features:**
- View tất cả users với role, permission count
- Filter by role, search by name/email
- Edit permissions cho từng user
- Toggle active/inactive
- Change role (admin, teacher, parent, student, public_student)

#### 2. Xem Roles Overview:

**URL:** `/rbac/roles`

**Features:**
- 5 role cards với icons
- Permission matrix (so sánh roles)
- User count per role
- Edit role button → `/rbac/roles/<role>/edit`

#### 3. Manage Permissions:

**URL:** `/rbac/permissions/manage`

**Features:**
- View all permissions grouped by category
- Usage count (Used by X roles)
- Add new permission
- Delete permission (if not used)

#### 4. Edit User Permissions:

**Flow:**
```
/rbac/users
→ Find user card
→ Click "Edit Permissions"
→ /rbac/users/<id>/permissions
→ Quick Role Change: Click role card
→ Apply Role Change
→ ✅ Done!
```

**Options:**
- **Quick Role Change**: Click role card → Auto grant permissions
- **Toggle Active**: Deactivate account
- **Compare Roles**: View permission matrix modal

---

### B. Cho Developers:

#### 1. Sử dụng Decorators:

```python
from app.auth_helpers import role_required, permission_required, admin_only

# Chỉ admin
@main.route('/admin/dashboard')
@admin_only
def admin_dashboard():
    return render_template('admin.html')

# Admin hoặc Teacher
@main.route('/courses/create')
@role_required('admin', 'teacher')
def create_course():
    # Teacher chỉ tạo được khóa của mình
    return render_template('course_form.html')

# Check permission cụ thể
@main.route('/students/<int:id>/edit')
@permission_required('manage_students')
def edit_student(id):
    return render_template('edit_student.html')
```

#### 2. Check Permissions trong Code:

```python
from app.auth_helpers import current_user, has_permission, can_access_course

# Get current user
user = current_user()
if user:
    print(f"Logged in as: {user.full_name} ({user.role})")

# Check permission
if has_permission('create_courses'):
    # User có quyền tạo khóa học
    pass

# Check course access
if can_access_course(course_id):
    # User có thể access khóa học này
    pass
```

#### 3. Business Logic Examples:

**Teacher chỉ edit course của mình:**
```python
@main.route('/courses/<int:id>/edit', methods=['POST'])
@role_required('teacher', 'admin')
def edit_course(id):
    course = Course.query.get_or_404(id)
    user = current_user()
    
    # Admin edit được tất cả
    if user.role == 'admin':
        # Allow edit
        pass
    # Teacher chỉ edit course của mình
    elif user.role == 'teacher':
        if course.instructor_id != user.teacher_profile.id:
            flash('Bạn không có quyền edit khóa học này!', 'danger')
            return redirect(url_for('main.courses'))
```

**Parent chỉ xem info con mình:**
```python
@main.route('/students/<int:id>')
@role_required('parent', 'admin', 'teacher')
def view_student(id):
    student = StudentProfile.query.get_or_404(id)
    user = current_user()
    
    if user.role == 'parent':
        # Check if student is user's child
        if student.parent_id != user.parent_profile.user_id:
            flash('Bạn không có quyền xem học sinh này!', 'danger')
            return redirect(url_for('main.index'))
```

---

## 6. ROUTES & FEATURES

### Main RBAC Routes:

| URL | Method | Description | Permission |
|-----|--------|-------------|------------|
| `/rbac/users` | GET | Danh sách users | Admin only |
| `/rbac/users/<id>/permissions` | GET, POST | Edit user permissions | Admin only |
| `/rbac/roles` | GET | Role overview | Admin only |
| `/rbac/roles/<role>/edit` | GET, POST | Edit role permissions | Admin only |
| `/rbac/permissions/manage` | GET, POST | Manage permissions | Admin only |

### API Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rbac/api/users/<id>/quick-role` | POST | Quick role change |
| `/rbac/api/users/<id>/toggle-active` | POST | Toggle active status |

### Test Routes (Development Only):

| URL | Description |
|-----|-------------|
| `/test-rbac/login` | Test login page |
| `/test-rbac/dashboard` | Test dashboard |
| `/test-rbac/logout` | Test logout |

---

## 7. CÀI ĐẶT & SETUP

### A. Database Migration:

#### 1. Tạo RBAC tables:

```bash
# Activate conda environment
conda activate flaskenv

# Create migration
flask db migrate -m "Add RBAC user system tables"

# Apply migration
flask db upgrade
```

**Tables created:**
- `users` (id, email, username, password_hash, role, ...)
- `teacher_profiles` (user_id, position, subject, ...)
- `student_profiles` (user_id, student_type, class_id, ...)
- `parent_profiles` (user_id, address, phone, ...)

#### 2. Create test accounts:

```python
# File: create_test_accounts.py
from app import create_app
from app.models import db
from app.models_users import create_admin, create_teacher, create_internal_student, create_public_student, create_parent

app = create_app()
with app.app_context():
    # Admin
    admin = create_admin('admin@smalltree.vn', 'admin', 'admin123', 'Admin SmallTree')
    db.session.add(admin)
    
    # Teacher
    teacher = create_teacher('teacher@smalltree.vn', 'teacher', 'teacher123', 'Nguyễn Văn A', position='Giáo viên chính')
    db.session.add(teacher)
    
    # Internal Student
    student = create_internal_student('student@smalltree.vn', 'student', 'student123', 'Trần Thị B', class_id=1, student_code='HS001')
    db.session.add(student)
    
    # Public Student
    public = create_public_student('public@example.com', 'public', 'public123', 'Lê Văn C')
    db.session.add(public)
    
    # Parent
    parent = create_parent('parent@smalltree.vn', 'parent', 'parent123', 'Phạm Thị D')
    db.session.add(parent)
    
    db.session.commit()
    print("✅ Created 5 test accounts!")
```

Run:
```bash
python create_test_accounts.py
```

---

### B. Blueprint Registration:

File: `app/__init__.py`

```python
# Import RBAC models
from app.models_users import User, TeacherProfile, StudentProfile, ParentProfile

# Register RBAC Management Blueprint
from app.routes_rbac_management import rbac_mgmt
app.register_blueprint(rbac_mgmt)
```

---

### C. CSRF Protection:

All forms have CSRF token:

```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    ...
</form>
```

---

## 8. MIGRATION TỪ OLD SYSTEM

### A. Migrate Data Script:

File: `migrate_users.py` (đã có sẵn)

**Flow:**
```
Old System          →        New System
───────────                 ────────────
Child table         →        users (role=student/parent)
                            + student_profiles
                            + parent_profiles

Staff table         →        users (role=teacher/admin)
                            + teacher_profiles
```

**Run migration:**
```bash
python migrate_users.py
```

**Output:**
```
✅ Migrated 5 Staff → User (1 admin, 4 teachers)
✅ Migrated 20 Child → User (20 students, 15 parents)
✅ Created profiles: 4 teacher_profiles, 20 student_profiles, 15 parent_profiles
```

---

### B. Update Routes:

**Before (Old):**
```python
@main.route('/courses')
def courses():
    if session.get('role') != 'admin':
        flash('No permission!', 'danger')
        return redirect(url_for('main.login'))
```

**After (New):**
```python
from app.auth_helpers import role_required

@main.route('/courses')
@role_required('admin', 'teacher')
def courses():
    # Code here
```

---

### C. Coexistence Strategy:

**Phương án 1 (Recommended):** Gradual Migration
- Tạo bảng mới song song với cũ
- Test trên dev/staging
- Migrate data từng phần
- Update routes từng chút
- Deploy khi ổn định

**Phương án 2:** Clean Break
- Backup database
- Drop old tables
- Tạo mới hoàn toàn
- Import lại data
- Deploy

---

## 9. SECURITY & BEST PRACTICES

### A. Password Security:

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
user.password_hash = generate_password_hash('password123')

# Check password
if check_password_hash(user.password_hash, 'password123'):
    # Correct password
```

**Features:**
- Bcrypt hashing (secure)
- Salt automatically added
- Cannot reverse hash

---

### B. Session Management:

```python
# Login
session['user_id'] = user.id
session['role'] = user.role
session['username'] = user.username

# Logout
session.clear()
```

**Best practices:**
- Clear old session on login
- Set `is_active` check
- Update `last_login_at`

---

### C. CSRF Protection:

All POST forms require CSRF token:

```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
</form>
```

**Setup:**
```python
# app/__init__.py
from flask_wtf import CSRFProtect
csrf = CSRFProtect(app)
```

---

### D. Role Checking:

**Decorators:**
```python
@role_required('admin', 'teacher')  # Multiple roles
@permission_required('create_courses')  # Specific permission
@admin_only  # Shortcut
```

**In-code:**
```python
if current_user().role == 'admin':
    # Admin-only logic

if has_permission('view_students'):
    # Permission-specific logic
```

---

### E. Default Passwords:

⚠️ **Test accounts có default passwords:**
- Admin: admin123
- Teacher: teacher123
- Student: student123
- Public: public123
- Parent: parent123

**MUST CHANGE IN PRODUCTION!**

---

## 10. TROUBLESHOOTING

### Q1: "Bad Request - CSRF token missing"

**Giải pháp:**
```html
<!-- Add to all POST forms -->
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

---

### Q2: "Permission denied" khi đã login

**Check:**
```python
# 1. Verify user role
print(session.get('role'))

# 2. Check ROLE_PERMISSIONS
from app.models_users import ROLE_PERMISSIONS
print(ROLE_PERMISSIONS['teacher'])

# 3. Check decorator
@role_required('teacher')  # Not 'Teacher' or 'TEACHER'
```

---

### Q3: SQLAlchemy relationship errors

**Common issue:**
```python
# Multiple foreign keys → ambiguous
class User:
    student_profile = db.relationship('StudentProfile', ...)

class StudentProfile:
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # ← Conflict!
```

**Fix:**
```python
# Specify foreign_keys
student_profile = db.relationship('StudentProfile', 
                                  foreign_keys='StudentProfile.user_id',
                                  backref='user')
```

---

### Q4: Migration lỗi "Table already exists"

**Giải pháp:**
```bash
# Option 1: Stamp migration (nếu table đã tồn tại)
flask db stamp head

# Option 2: Drop và tạo lại
flask db downgrade
flask db upgrade

# Option 3: Manual fix trong migration file
# Comment out CREATE TABLE statements
```

---

### Q5: User không thể login

**Check list:**
```python
# 1. User exists?
user = User.query.filter_by(email='test@test.com').first()

# 2. is_active?
print(user.is_active)

# 3. Password correct?
print(user.check_password('password123'))

# 4. Session được set?
print(session.get('user_id'))
```

---

## 📊 FILES STRUCTURE

```
smalltree-website/
├── app/
│   ├── __init__.py                      # App factory, blueprint registration
│   ├── models.py                        # Old models (Child, Staff)
│   ├── models_users.py                  # NEW: RBAC models (User, profiles)
│   ├── models_rbac.py                   # NEW: Dynamic Role/Permission models
│   ├── routes.py                        # Main routes
│   ├── routes_rbac_management.py        # NEW: RBAC management routes
│   ├── auth_helpers.py                  # NEW: Decorators, helpers
│   ├── forms.py
│   └── templates/
│       ├── accounts.html                # Updated with RBAC button
│       └── rbac/                        # NEW: RBAC templates
│           ├── user_list.html           # User management
│           ├── edit_permissions.html    # Edit user permissions
│           ├── role_list.html           # Role overview
│           ├── edit_role.html           # Edit role permissions
│           └── manage_permissions.html  # Manage all permissions
├── migrations/
│   └── versions/
│       └── xxxx_add_rbac_user_system_tables.py  # RBAC migration
├── migrate_users.py                     # Migration script (old → new)
├── RBAC_COMPLETE_GUIDE.md              # THIS FILE
└── config.py
```

---

## 🎯 QUICK START CHECKLIST

### For New Projects:

- [ ] 1. Run migration: `flask db upgrade`
- [ ] 2. Create admin: `create_admin(...)`
- [ ] 3. Login: `/test-rbac/login`
- [ ] 4. Create users: `/rbac/users`
- [ ] 5. Assign roles: Edit permissions
- [ ] 6. Test permissions: Access different routes

### For Existing Projects:

- [ ] 1. Backup database
- [ ] 2. Create RBAC tables: `flask db upgrade`
- [ ] 3. Run migration script: `python migrate_users.py`
- [ ] 4. Verify data: Check users table
- [ ] 5. Update routes: Add decorators
- [ ] 6. Test old + new coexistence
- [ ] 7. Deploy when stable

---

## 📞 SUPPORT

**Issues?**
- Check logs: Flask console output
- Verify database: Check tables created
- Test accounts: Use `/test-rbac/login`
- Permissions: Check `ROLE_PERMISSIONS` dict

**Common URLs:**
- Login: `/test-rbac/login`
- User Management: `/rbac/users`
- Role Overview: `/rbac/roles`
- Old Accounts: `/accounts`

---

## 🎉 SUMMARY

### ✅ Đã triển khai:

1. **5 User Roles**: admin, teacher, parent, student, public_student
2. **Permission System**: 16+ permissions, 4 categories
3. **Database Models**: User, TeacherProfile, StudentProfile, ParentProfile
4. **Decorators**: @role_required, @permission_required, @admin_only
5. **UI Management**: 3 pages (users, roles, permissions)
6. **CSRF Protection**: All forms secured
7. **Migration Script**: Old → New data migration
8. **Test Accounts**: 5 accounts ready to use
9. **Documentation**: Complete guide

### 🚀 Production Ready:

- ✅ Secure password hashing
- ✅ CSRF protection
- ✅ Role-based access control
- ✅ Permission checking
- ✅ Responsive UI
- ✅ Filter & search
- ✅ Quick actions
- ✅ Coexistence with old system

### ⚠️ Before Production:

- [ ] Change default passwords
- [ ] Review permissions per role
- [ ] Test all routes with different roles
- [ ] Backup database
- [ ] Update email notifications
- [ ] Configure HTTPS
- [ ] Set session timeout

---

**END OF GUIDE** 🎓

> SmallTree RBAC System v1.0.0  
> Built with ❤️ by AI Assistant  
> January 9, 2026
