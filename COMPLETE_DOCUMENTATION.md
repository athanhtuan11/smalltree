# 📚 SMALLTREE ACADEMY - COMPLETE DOCUMENTATION

**Production Website**: [mamnoncaynho.com](http://mamnoncaynho.com)  
**Version**: 2.0.0  
**Last Updated**: January 9, 2026

A comprehensive nursery school management system with modern features: Student Management, RBAC Security, Learning Management (Courses), Flashcard System, Task Tracking (Kanban Board), and Cloudflare R2 Storage.

---

## 📋 MỤC LỤC

1. [Tổng quan Hệ thống](#1-tổng-quan-hệ-thống)
2. [RBAC - Hệ thống Phân quyền](#2-rbac---hệ-thống-phân-quyền)
3. [Courses Module - Quản lý Khóa học](#3-courses-module---quản-lý-khóa-học)
4. [Flashcard System - Học từ vựng](#4-flashcard-system---học-từ-vựng)
5. [Task Tracking - Kanban Board](#5-task-tracking---kanban-board)
6. [Cloudflare R2 Storage](#6-cloudflare-r2-storage)
7. [Deployment Guide](#7-deployment-guide)
8. [API Reference](#8-api-reference)

---

## 1. TỔNG QUAN HỆ THỐNG

### 🎯 Mục tiêu
SmallTree Academy là hệ thống quản lý mẫu giáo toàn diện, kết hợp:
- **Quản lý truyền thống**: Học sinh, điểm danh, hoạt động, thực đơn
- **LMS hiện đại**: Khóa học trực tuyến, flashcard, quiz
- **Công cụ quản lý**: Task tracking, analytics, báo cáo

### 🏗️ Kiến trúc Công nghệ

**Backend:**
- Framework: Flask 3.1.2 (Python 3.9+)
- Database: SQLite + SQLAlchemy ORM
- Authentication: Flask-Login + Bcrypt
- Migration: Flask-Migrate (Alembic)
- Forms: Flask-WTF + WTForms
- Security: CSRF Protection

**Frontend:**
- Template Engine: Jinja2
- UI Framework: Bootstrap 5.3
- Icons: Bootstrap Icons
- JavaScript Libraries:
  - Anime.js (animations)
  - Sortable.js (drag & drop)
  - Canvas Confetti (celebrations)
  - Chart.js (analytics)

**Storage:**
- Primary: Cloudflare R2 (object storage)
- Fallback: Local VPS storage
- CDN: Cloudflare global network

### 📁 Cấu trúc Thư mục

```
smalltree-website/
├── app/                              # Application core
│   ├── __init__.py                   # App factory
│   ├── models.py                     # Legacy models (Child, Staff, Activity)
│   ├── models_users.py               # RBAC user models (NEW)
│   ├── models_courses.py             # Course LMS models (NEW)
│   ├── models_tasks.py               # Kanban task models (NEW)
│   ├── routes.py                     # Main routes (7000+ lines)
│   ├── routes_rbac_management.py     # RBAC admin routes
│   ├── auth_helpers.py               # Authentication decorators
│   ├── forms.py                      # WTForms definitions
│   │
│   ├── templates/                    # Jinja2 templates
│   │   ├── base.html                 # Base layout
│   │   ├── index.html                # Homepage
│   │   ├── login.html                # Login page
│   │   ├── rbac/                     # RBAC management pages
│   │   ├── courses/                  # Course pages (4 pages)
│   │   │   ├── index.html            # Course list
│   │   │   ├── detail.html           # Course landing page
│   │   │   ├── curriculum.html       # Curriculum builder (NEW)
│   │   │   └── learn.html            # Video player
│   │   ├── flashcard/                # Flashcard pages
│   │   └── tasks/                    # Kanban board pages
│   │
│   ├── static/                       # Static files
│   │   ├── css/style.css             # Main stylesheet
│   │   ├── js/                       # JavaScript files
│   │   ├── images/                   # Static images
│   │   ├── flashcard/                # Flashcard assets
│   │   └── student_albums/           # Local photo storage
│   │
│   └── flashcard/                    # Flashcard module
│       ├── __init__.py
│       └── templates/flashcard/      # Flashcard templates
│
├── migrations/                       # Database migrations
│   ├── versions/                     # Migration files
│   └── alembic.ini                   # Alembic config
│
├── config.py                         # Main configuration
├── config_r2.py                      # R2 storage config
├── r2_storage.py                     # R2 SDK wrapper
├── run.py                            # Development server
├── requirements.txt                  # Python dependencies
├── seed_courses.py                   # Seed course data
├── seed_complete_course.py           # Seed complete curriculum (NEW)
└── migrate_users.py                  # Migrate old users to RBAC

```

### 🎨 Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| Student Management | ✅ Live | CRUD học sinh, upload avatar |
| Attendance Tracking | ✅ Live | Điểm danh hàng ngày, báo cáo |
| Activity Posts | ✅ Live | Đăng hoạt động, upload ảnh |
| Menu Planning | ✅ Live | Quản lý thực đơn, món ăn |
| BMI Tracking | ✅ Live | Theo dõi chiều cao, cân nặng |
| Student Albums | ✅ Live | Album ảnh cho từng học sinh |
| **RBAC System** | ✅ **NEW** | 5 roles, permission management |
| **Courses (LMS)** | ✅ **NEW** | Create, enroll, video player |
| **Curriculum Builder** | ✅ **NEW** | Sections, lectures, quiz, assignment |
| **Flashcard System** | ✅ Live | 3 modes, spaced repetition |
| **Task Tracking** | ✅ **NEW** | Kanban board, drag & drop |
| **R2 Storage** | ✅ Live | Cloudflare CDN, auto-upload |

---

## 2. RBAC - HỆ THỐNG PHÂN QUYỀN

### 🔐 Tổng quan

**Role-Based Access Control (RBAC)** thay thế hệ thống phân quyền cũ với:
- ✅ 5 user roles rõ ràng
- ✅ Permission-based authorization
- ✅ Decorator-based access control
- ✅ Web UI để quản lý quyền
- ✅ Bcrypt password hashing

### 📊 Database Schema

```
┌──────────────────────────────────────────────────────┐
│ users                                                 │
├──────────────────────────────────────────────────────┤
│ id (PK)                                              │
│ email (unique)                                       │
│ password_hash                                        │
│ full_name                                            │
│ role (admin/teacher/parent/student/public_student)  │
│ is_active                                            │
│ created_at, last_login                               │
└──────────────────────────────────────────────────────┘
         │
         ├─────► teacher_profiles (1:1)
         │       ├─ user_id (FK)
         │       ├─ employee_id
         │       ├─ subject_specialization
         │       └─ hire_date
         │
         ├─────► student_profiles (1:1)
         │       ├─ user_id (FK)
         │       ├─ student_id
         │       ├─ date_of_birth
         │       ├─ gender
         │       ├─ class_id
         │       └─ parent_id (FK → parent_profiles)
         │
         └─────► parent_profiles (1:1)
                 ├─ user_id (FK)
                 ├─ phone
                 ├─ address
                 └─ children → [student_profiles]
```

### 👥 5 User Roles

| Role | Mô tả | Permissions |
|------|-------|-------------|
| **admin** | Quản trị viên | FULL ACCESS - Tất cả quyền |
| **teacher** | Giáo viên | Quản lý học sinh, điểm danh, hoạt động, tạo khóa học |
| **parent** | Phụ huynh | Xem con, xem hoạt động, xem điểm danh, xem thực đơn |
| **student** | Học sinh (nội bộ) | Học khóa học, flashcard, xem hoạt động của mình |
| **public_student** | Học sinh ngoài | Chỉ học khóa học public, không access dữ liệu trường |

### 🔑 Permissions Matrix

| Permission | Admin | Teacher | Parent | Student | Public |
|-----------|-------|---------|--------|---------|--------|
| **Student Management** |
| view_students | ✅ | ✅ | ✅ (con) | ❌ | ❌ |
| manage_students | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Attendance** |
| view_attendance | ✅ | ✅ | ✅ (con) | ✅ (mình) | ❌ |
| manage_attendance | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Activities** |
| view_activities | ✅ | ✅ | ✅ | ✅ | ❌ |
| manage_activities | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Courses** |
| view_courses | ✅ | ✅ | ✅ | ✅ | ✅ |
| create_course | ✅ | ✅ | ❌ | ❌ | ❌ |
| manage_own_courses | ✅ | ✅ | ❌ | ❌ | ❌ |
| enroll_course | ✅ | ✅ | ✅ (con) | ✅ | ✅ |
| **System** |
| manage_users | ✅ | ❌ | ❌ | ❌ | ❌ |
| view_analytics | ✅ | ✅ | ❌ | ❌ | ❌ |
| manage_menu | ✅ | ✅ | ❌ | ❌ | ❌ |

### 🛠️ Authentication Decorators

```python
from app.auth_helpers import login_required, role_required, permission_required, admin_only

# Basic authentication
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Role-based access
@main.route('/admin/settings')
@role_required(['admin'])
def admin_settings():
    return render_template('settings.html')

# Multiple roles
@main.route('/courses/create')
@role_required(['admin', 'teacher'])
def create_course():
    return render_template('courses/create.html')

# Permission-based access
@main.route('/students')
@permission_required('view_students')
def student_list():
    return render_template('student_list.html')

# Admin only (shortcut)
@main.route('/users/manage')
@admin_only
def manage_users():
    return render_template('rbac/user_list.html')
```

### 🎛️ RBAC Management UI

**Access**: `/rbac/users` (Admin only)

**Features:**
1. **User List** (`/rbac/users`)
   - View all users with roles
   - Filter by role, status
   - Search by name/email
   - Quick role change
   - Toggle active/inactive

2. **Edit Permissions** (`/rbac/users/<id>/permissions`)
   - Change user role
   - View role permissions
   - Custom permission overrides (future)

3. **Role Management** (`/rbac/roles`)
   - View all roles
   - Permission matrix table
   - Edit role permissions

4. **Edit Role** (`/rbac/roles/<role>/edit`)
   - Checkbox interface
   - Preview permissions
   - Save changes (in-memory for now)

### 🔧 Setup & Installation

**1. Create RBAC tables:**
```bash
flask db stamp head
flask db revision --autogenerate -m "Add RBAC user system tables"
flask db upgrade
```

**2. Create test accounts:**
```python
from app.models_users import User, create_admin, create_teacher, create_student
from app import create_app, db

app = create_app()
with app.app_context():
    # Admin
    admin = create_admin(
        email='admin@smalltree.vn',
        password='admin123',
        full_name='Admin Trường'
    )
    
    # Teacher
    teacher = create_teacher(
        email='teacher@smalltree.vn',
        password='teacher123',
        full_name='Cô Hoa',
        employee_id='GV001'
    )
    
    # Student
    student = create_student(
        email='student@smalltree.vn',
        password='student123',
        full_name='Bé Minh',
        student_id='HS001',
        date_of_birth='2020-03-15'
    )
    
    db.session.commit()
```

**3. Test login:**
- Admin: `admin@smalltree.vn` / `admin123`
- Teacher: `teacher@smalltree.vn` / `teacher123`
- Student: `student@smalltree.vn` / `student123`

### 🔄 Migration from Old System

**Old system:**
- `Child` table (students)
- `Staff` table (teachers)
- Separate tables, no unified auth

**Migration script:** `migrate_users.py`

```bash
python migrate_users.py
```

**What it does:**
1. Copy all `Child` → `StudentProfile`
2. Copy all `Staff` → `TeacherProfile`
3. Generate secure passwords
4. Keep old tables intact (safe migration)

---

## 3. COURSES MODULE - QUẢN LÝ KHÓA HỌC

### 🎓 Overview

Learning Management System (LMS) tương tự **Udemy**, cho phép:
- Giáo viên tạo khóa học
- Học sinh đăng ký và học
- Video player với curriculum sidebar
- Progress tracking
- Quiz & assignments

### 📊 Database Models

```python
Course                      # Khóa học
├─ id, title, slug
├─ description, short_description
├─ instructor_id (FK → Staff)
├─ thumbnail, intro_video
├─ category, level, language
├─ price, status (draft/published)
├─ total_duration, total_lessons
├─ enrolled_count, rating_avg
└─ requirements (JSON), what_you_learn (JSON)

CourseSection               # Chương/Section
├─ id, course_id (FK)
├─ title, description
├─ order
└─ lectures → [Lesson]

Lesson                      # Bài học
├─ id, section_id (FK)
├─ title, description
├─ lesson_type (video/text/quiz/assignment)
├─ video_url, content
├─ duration (seconds)
├─ is_preview, order
└─ attachments (JSON)

Enrollment                  # Đăng ký khóa học
├─ id, course_id (FK)
├─ student_id (FK → User)
├─ enrolled_at, completed_at
├─ progress_percentage
└─ certificate_issued

LessonProgress             # Tiến độ từng bài
├─ id, lesson_id (FK)
├─ enrollment_id (FK)
├─ is_completed
├─ completed_at
└─ time_spent

CourseReview               # Đánh giá
├─ id, course_id (FK)
├─ user_id (FK)
├─ rating (1-5)
└─ comment
```

### 🎯 User Flows

#### For Instructors (Teachers/Admin):

**1. Create Course** (`/courses/create`)
- Fill basic info: title, description, category, level
- Upload thumbnail, intro video
- Set price, language
- Define requirements & learning outcomes

**2. Build Curriculum** (`/courses/<id>/curriculum`) ⭐ **NEW**
```
┌─────────────────────────────────────────────────────┐
│  [+ Add Section]                                    │
├─────────────────────────────────────────────────────┤
│  📁 Section 1: Introduction                         │
│     🎥 Lecture 1: Welcome (3 min) [Preview]        │
│     🎥 Lecture 2: Overview (5 min)                 │
│     📄 Lecture 3: Course FAQs                      │
│     [+ Add Lecture]                                 │
├─────────────────────────────────────────────────────┤
│  📁 Section 2: Python Setup                         │
│     🎥 Lecture 4: Install Python (8 min)           │
│     🎥 Lecture 5: IDE Setup (7 min)                │
│     ❓ Quiz: Setup Check                           │
│     [+ Add Lecture]                                 │
└─────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Add/edit/delete sections
- ✅ Add/edit/delete lectures
- ✅ 4 lecture types: Video, Article, Quiz, Assignment
- ✅ Drag & drop reordering (JavaScript)
- ✅ Preview toggle for free lectures
- ✅ Publish course button

**3. Manage Students**
- View enrolled students
- Track progress
- Answer Q&A
- Moderate reviews

#### For Students:

**1. Browse Courses** (`/courses`)
- Filter by category, level, price
- Search by keyword
- View ratings & enrollment count

**2. Course Detail** (`/courses/<slug>`)
- Watch intro video
- Read full description
- See curriculum outline
- View instructor profile
- Read reviews
- **Enroll** button

**3. Learn** (`/courses/<id>/learn`)
```
┌───────────────────────────────────────────────────┐
│          Video Player                             │
│  ▶️ [Progress bar] 🔊 ⚙️ ⛶                        │
│                                                   │
│  Lecture 3: Variables and Data Types             │
│  ◄ Previous                          Next ►      │
├───────────────────────────────────────────────────┤
│ 📑 Notes     💬 Q&A     📥 Resources             │
└───────────────────────────────────────────────────┘

Sidebar (Curriculum):
✅ Section 1: Intro (100%)
   ✅ Lecture 1: Welcome
   ✅ Lecture 2: Overview
▶️  Section 2: Basics (50%)
   ✅ Lecture 3: Variables ← Current
   ⭕ Lecture 4: Strings
   ⭕ Lecture 5: Lists
```

### 🔧 API Endpoints

#### Course Management
```
GET  /courses                          # List courses
GET  /courses/<slug>                   # Course detail page
POST /courses                          # Create course (teacher/admin)
GET  /courses/<id>/curriculum          # Curriculum builder page
POST /courses/<id>/enroll              # Enroll student
GET  /courses/<id>/learn               # Video player
```

#### Curriculum Builder (NEW)
```
POST   /api/courses/<id>/sections              # Create section
PUT    /api/courses/<id>/sections/<sid>        # Update section
DELETE /api/courses/<id>/sections/<sid>        # Delete section

POST   /api/sections/<sid>/lectures            # Create lecture
PUT    /api/sections/<sid>/lectures/<lid>      # Update lecture
DELETE /api/lectures/<lid>                     # Delete lecture

POST   /api/courses/<id>/publish               # Publish course
```

### 📦 Seed Data

**Quick start with sample course:**

```bash
# Tạo 1 khóa học Python hoàn chỉnh với 6 sections, 31 lectures
python seed_complete_course.py
```

**What it creates:**
- 1 Course: "Complete Python Bootcamp: Zero to Hero in Python"
- 6 Sections:
  1. Course Introduction (3 lectures)
  2. Python Setup (5 lectures)
  3. Python Basics (7 lectures)
  4. Control Flow (6 lectures)
  5. Functions (5 lectures)
  6. Object Oriented Programming (5 lectures)
- Mix of: Videos, Articles, Quizzes, Assignments
- Preview lectures enabled for Section 1

**Access:** `http://localhost:5000/courses/4/curriculum`

---

## 4. FLASHCARD SYSTEM - HỌC TỪ VỰNG

### 📚 Overview

Hệ thống flashcard cho trẻ mầm non với:
- ✅ 3 chế độ học tương tác
- ✅ Gamification (stars, streaks, stickers)
- ✅ Spaced repetition algorithm (Anki)
- ✅ Text-to-Speech tiếng Việt
- ✅ Giao diện thân thiện trẻ em

### 🎮 3 Learning Modes

**1. Flash Mode** (🎴)
- Xem hình + text
- Tap để lật thẻ
- TTS đọc tiếng Việt
- Đánh giá: Hard / Good / Easy

**2. Quiz Mode** (❓)
- Hiển thị hình
- 3 đáp án trắc nghiệm
- Pháo hoa khi đúng 🎉
- Animation anime.js

**3. Audio Mode** (🎧)
- Nghe âm thanh
- Chọn hình đúng
- Practice listening skills

### 📊 Database Models

```python
Deck                        # Bộ thẻ
├─ id, title, description
├─ cover_image (R2 URL)
├─ age_group (1-3, 3-5, 5-7)
├─ is_active
├─ card_count
└─ cards → [Card]

Card                        # Thẻ học
├─ id, deck_id (FK)
├─ front_text, back_text
├─ image_url (R2 URL)
├─ audio_url (R2 URL hoặc TTS)
├─ order
└─ created_at

Progress                    # Tiến độ học
├─ id, deck_id, card_id
├─ user_id (FK → Child)
├─ review_count
├─ ease_factor (độ khó)
├─ interval (khoảng cách ôn)
├─ due_date (ngày ôn tiếp)
└─ last_reviewed
```

### 🎯 Spaced Repetition Algorithm

**Based on Anki SM-2:**

```python
# Khi user đánh giá:
- Hard (1): interval = 1 day
- Good (3): interval = current * 1.5
- Easy (5): interval = current * 2.5

# Ease factor adjustment:
- Hard: ease_factor -= 0.15
- Easy: ease_factor += 0.15
```

**Due cards:**
- Cards with `due_date <= today` show first
- Sort by ease_factor (hard cards first)

### 🎨 UI Features

**Colors:**
- Mint (#b2f5ea)
- Pink (#ffc7e3)
- Yellow (#fdf39b)
- Blue (#cfe5ff)
- Purple (#e4d0ff)

**Animations:**
- Card flip (Anime.js)
- Confetti (Canvas Confetti)
- Star collection
- Progress bar

**Responsive:**
- Mobile-first design
- Touch-friendly buttons
- Large icons for kids

### 🔧 Teacher Dashboard

**Access:** `/flashcard/decks`

**Features:**
1. **Manage Decks**
   - Create deck với cover image
   - Set age group
   - Enable/disable

2. **Manage Cards**
   - Upload hình ảnh (auto R2)
   - Upload audio (custom voice)
   - Fallback TTS nếu không có audio
   - Preview card

3. **View Progress**
   - Số thẻ đã học
   - Streak count
   - Stars earned

### 📦 Storage

**Cloudflare R2 Paths:**
- Deck covers: `flashcard/covers/<filename>`
- Card images: `flashcard/cards/<filename>`
- Custom audio: `flashcard/audio/<filename>`

**Fallback:**
- Local: `static/flashcard/images/`
- TTS: Google TTS API (Vietnamese)

---

## 5. TASK TRACKING - KANBAN BOARD

### 📊 Overview

Jira-style Kanban board để quản lý công việc phát triển khóa học, features, bugs.

### 🎯 Features

**1. Project Management** (`/tasks`)
- Create projects với key (VD: COURSE, BUG)
- Color-coded avatars
- Task count badges
- Project description

**2. Kanban Board** (`/tasks/<project_key>`)

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   To Do     │ In Progress │   Review    │    Done     │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ 📕 COURSE-1 │ 📕 COURSE-3 │ ☑️ COURSE-5 │ 📕 COURSE-7 │
│ Video Player│ Quiz System │ Code Review │ Auth System │
│ @john  High │ @mary  Med  │ @bob  High  │ @john  Med  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ 🐛 BUG-12   │ ☑️ TASK-8   │             │ 🐛 BUG-9    │
│ Fix upload  │ Add tests   │             │ Login bug   │
│ @alice High │ @john Low   │             │ @mary High  │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**3. Drag & Drop**
- Sortable.js library
- Visual feedback
- Auto-save status
- Update task counts

**4. Filters**
- 🔍 Search by title
- 👤 Filter by assignee
- ⚡ Filter by priority
- 📋 Filter by type

**5. Task Detail** (`/tasks/<project_key>/<task_key>`)
- Full description
- Acceptance criteria
- Comments
- Attachments
- Activity history

### 📊 Database Models

```python
Project                     # Dự án
├─ id, key, name
├─ description
├─ color (#hex)
├─ created_at
└─ tasks → [Task]

Task                        # Task/Issue
├─ id, project_id (FK)
├─ key (AUTO: PROJECT-123)
├─ title, description
├─ type (story/task/bug)
├─ status (todo/in_progress/review/done)
├─ priority (low/medium/high)
├─ assignee_id (FK → User)
├─ reporter_id (FK → User)
├─ story_points
└─ sprint_id (FK)

Sprint                      # Sprint (Agile)
├─ id, project_id
├─ name, goal
├─ start_date, end_date
└─ status

TaskComment                 # Comments
TaskAttachment             # File attachments
TaskHistory                # Activity log
```

### 🔧 API Endpoints

```
GET  /tasks                             # Project list
POST /tasks/projects                    # Create project
GET  /tasks/<project_key>               # Kanban board
GET  /tasks/<project_key>/<task_key>    # Task detail

POST /api/tasks                         # Create task
PUT  /api/tasks/<id>                    # Update task
PUT  /api/tasks/<id>/status             # Move task
POST /api/tasks/<id>/comments           # Add comment
```

### 🎨 UI Components

**Task Types:**
- 📕 Story (green badge)
- ☑️ Task (blue badge)
- 🐛 Bug (red badge)

**Priority:**
- 🔴 High
- 🟡 Medium
- 🟢 Low

**Drag & Drop:**
- Ghost effect while dragging
- Smooth animations
- Column highlighting

---

## 6. CLOUDFLARE R2 STORAGE

### ☁️ Overview

Cloudflare R2 là object storage tương thích S3, **miễn phí bandwidth** (egress).

**Why R2?**
- ✅ No egress fees (download miễn phí)
- ✅ Global CDN
- ✅ S3-compatible API
- ✅ Cheap: $0.015/GB/month
- ✅ 100GB = ~36,000đ/tháng

### 📦 Storage Structure

```
smalltree-images/           # Bucket name
├── flashcard/
│   ├── covers/             # Deck covers
│   ├── cards/              # Card images
│   └── audio/              # Audio files
├── activities/             # Activity photos
├── student_albums/         # Student albums
├── students/
│   └── avatars/            # Student avatars
└── courses/
    ├── thumbnails/         # Course thumbnails
    └── videos/             # (Future) Course videos
```

### 🔧 Setup Guide

**1. Create Cloudflare Account**
- Visit: https://dash.cloudflare.com
- Sign up (free)

**2. Enable R2**
- Dashboard > R2
- Click "Purchase R2 Plan" (free tier)
- Add payment method (won't charge until usage)

**3. Create Bucket**
- Click "Create bucket"
- Name: `smalltree-images`
- Location: Auto
- Create

**4. Generate API Token**
- R2 Dashboard > "Manage R2 API Tokens"
- Create token:
  - Name: `smalltree-app`
  - Permissions: Read & Write
  - Bucket: `smalltree-images`
- **Save credentials:**
  - Access Key ID
  - Secret Access Key

**5. Configure App**

Create `config_r2.py`:
```python
# Cloudflare R2 Configuration
R2_ACCOUNT_ID = 'your-account-id'
R2_ACCESS_KEY_ID = 'your-access-key'
R2_SECRET_ACCESS_KEY = 'your-secret-key'
R2_BUCKET_NAME = 'smalltree-images'
R2_PUBLIC_URL = 'https://pub-xxxxx.r2.dev'
```

### 💻 Usage Examples

**Upload file:**
```python
from r2_storage import get_r2_storage

r2 = get_r2_storage()

# Upload from Flask file object
file = request.files['image']
r2_path = f"flashcard/cards/{filename}"
r2.upload_file(file, r2_path)

# Get public URL
url = f"{r2.public_url}/{r2_path}"
```

**Delete file:**
```python
r2.delete_file('flashcard/cards/old-image.jpg')
```

**List files:**
```python
files = r2.list_files('flashcard/cards/')
for file in files:
    print(file['Key'], file['Size'])
```

### 🔄 Migration from Local

**Script to migrate existing files:**

```bash
# Upload all flashcard images to R2
python migrate_flashcard_to_r2.py

# Upload student albums
python migrate_albums_to_r2.py
```

### 📊 Cost Estimate

| Usage | Storage | Cost/month |
|-------|---------|------------|
| 10GB | Images | ~3,600đ |
| 50GB | + Videos | ~18,000đ |
| 100GB | Full media | ~36,000đ |

**Note:** Download **MIỄN PHÍ** (unlimited egress)

---

## 7. DEPLOYMENT GUIDE

### 🚀 Production Deployment

**Server Requirements:**
- Ubuntu 20.04+ / Debian 10+
- Python 3.9+
- Nginx
- Supervisor (process manager)
- Domain name + SSL

### 📝 Step-by-Step Deployment

#### 1. Chuẩn bị Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git

# Create user
sudo useradd -m -s /bin/bash smalltree
sudo passwd smalltree
```

#### 2. Clone Repository

```bash
# Switch to smalltree user
su - smalltree

# Clone project
git clone https://github.com/athanhtuan11/smalltree.git /home/smalltree/smalltree
cd /home/smalltree/smalltree
```

#### 3. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Configure Application

**Create `.env` file:**
```bash
nano .env
```

```ini
# Flask Config
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this

# Database
DATABASE_URL=sqlite:///instance/smalltree.db

# R2 Storage
R2_ACCOUNT_ID=your-r2-account-id
R2_ACCESS_KEY_ID=your-r2-access-key
R2_SECRET_ACCESS_KEY=your-r2-secret-key
R2_BUCKET_NAME=smalltree-images
R2_PUBLIC_URL=https://pub-xxxxx.r2.dev

# Optional
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

#### 5. Initialize Database

```bash
# Run migrations
flask db upgrade

# Create admin account
python -c "
from app import create_app, db
from app.models_users import create_admin

app = create_app()
with app.app_context():
    admin = create_admin(
        email='admin@mamnoncaynho.com',
        password='CHANGE_THIS_PASSWORD',
        full_name='Admin Trường'
    )
    db.session.commit()
    print('✅ Admin created!')
"
```

#### 6. Setup Gunicorn (WSGI Server)

**Install:**
```bash
pip install gunicorn
```

**Create config:**
```bash
nano gunicorn_config.py
```

```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "/home/smalltree/logs/gunicorn_error.log"
accesslog = "/home/smalltree/logs/gunicorn_access.log"
loglevel = "info"
```

**Create log directory:**
```bash
mkdir -p /home/smalltree/logs
```

#### 7. Setup Supervisor (Process Manager)

**Create config:**
```bash
sudo nano /etc/supervisor/conf.d/smalltree.conf
```

```ini
[program:smalltree]
directory=/home/smalltree/smalltree
command=/home/smalltree/smalltree/venv/bin/gunicorn -c gunicorn_config.py run:app
user=smalltree
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/smalltree/logs/supervisor_error.log
stdout_logfile=/home/smalltree/logs/supervisor_output.log
```

**Start service:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smalltree
sudo supervisorctl status smalltree
```

#### 8. Setup Nginx (Web Server)

**Create config:**
```bash
sudo nano /etc/nginx/sites-available/smalltree
```

```nginx
server {
    listen 80;
    server_name mamnoncaynho.com www.mamnoncaynho.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mamnoncaynho.com www.mamnoncaynho.com;

    # SSL certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/mamnoncaynho.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mamnoncaynho.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Max upload size (for images/videos)
    client_max_body_size 100M;

    # Static files
    location /static {
        alias /home/smalltree/smalltree/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/smalltree /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 9. Setup SSL (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d mamnoncaynho.com -d www.mamnoncaynho.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### 10. Setup Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow 'OpenSSH'
sudo ufw enable
sudo ufw status
```

### 🔄 Update/Deployment Workflow

**Create deploy script:**
```bash
nano /home/smalltree/deploy.sh
```

```bash
#!/bin/bash
set -e

echo "🚀 Deploying SmallTree..."

# Navigate to project
cd /home/smalltree/smalltree

# Backup database
echo "📦 Backing up database..."
cp instance/smalltree.db instance/smalltree.db.backup-$(date +%Y%m%d-%H%M%S)

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin master

# Activate venv
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
flask db upgrade

# Restart app
echo "🔄 Restarting application..."
sudo supervisorctl restart smalltree

# Reload Nginx
sudo systemctl reload nginx

echo "✅ Deployment complete!"
```

**Make executable:**
```bash
chmod +x /home/smalltree/deploy.sh
```

**Run deployment:**
```bash
./deploy.sh
```

### 📊 Monitoring & Logs

**View logs:**
```bash
# Application logs
tail -f /home/smalltree/logs/gunicorn_error.log
tail -f /home/smalltree/logs/gunicorn_access.log

# Supervisor logs
tail -f /home/smalltree/logs/supervisor_error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Check status:**
```bash
# Application
sudo supervisorctl status smalltree

# Nginx
sudo systemctl status nginx

# Database size
du -h /home/smalltree/smalltree/instance/smalltree.db
```

### 🔧 Troubleshooting

**App not starting:**
```bash
# Check supervisor logs
sudo supervisorctl tail -f smalltree stderr

# Test Gunicorn manually
cd /home/smalltree/smalltree
source venv/bin/activate
gunicorn -c gunicorn_config.py run:app
```

**502 Bad Gateway:**
```bash
# Check if app is running
sudo supervisorctl status smalltree

# Check Gunicorn bind address matches Nginx proxy_pass
ps aux | grep gunicorn
```

**Database locked:**
```bash
# Stop app
sudo supervisorctl stop smalltree

# Check for locks
fuser /home/smalltree/smalltree/instance/smalltree.db

# Restart
sudo supervisorctl start smalltree
```

**Permission errors:**
```bash
# Fix ownership
sudo chown -R smalltree:smalltree /home/smalltree/smalltree

# Fix static files
sudo chmod -R 755 /home/smalltree/smalltree/app/static
```

---

## 8. API REFERENCE

### Authentication

All API endpoints require authentication via session cookie (Flask-Login).

**Login:**
```bash
POST /login
Content-Type: application/x-www-form-urlencoded

email=admin@smalltree.vn&password=admin123
```

**Logout:**
```bash
GET /logout
```

### Course APIs

**List courses:**
```bash
GET /courses?category=Programming&level=Beginner
```

**Course detail:**
```bash
GET /courses/complete-python-bootcamp
```

**Enroll course:**
```bash
POST /courses/4/enroll
```

**Create section:**
```bash
POST /api/courses/4/sections
Content-Type: multipart/form-data

title=Introduction
description=Welcome section
```

**Create lecture:**
```bash
POST /api/sections/1/lectures
Content-Type: multipart/form-data

title=Welcome Video
lesson_type=video
video_url=https://youtube.com/watch?v=xxx
duration=180
is_preview=on
```

**Delete lecture:**
```bash
DELETE /api/lectures/5
X-CSRFToken: <csrf_token>
```

**Publish course:**
```bash
POST /api/courses/4/publish
X-CSRFToken: <csrf_token>
```

### Flashcard APIs

**Get decks:**
```bash
GET /flashcard/api/decks
```

**Get due cards:**
```bash
GET /flashcard/api/decks/1/due_cards
```

**Submit review:**
```bash
POST /flashcard/api/cards/5/review
Content-Type: application/json

{
  "quality": 3,  // 1=Hard, 3=Good, 5=Easy
  "time_spent": 10
}
```

### Task APIs

**Create project:**
```bash
POST /tasks/projects
Content-Type: multipart/form-data

name=Course Platform
key=COURSE
description=Build online learning platform
color=#43a047
```

**Create task:**
```bash
POST /api/tasks
Content-Type: application/json

{
  "project_id": 1,
  "title": "Implement video player",
  "description": "Add HLS video player with subtitles",
  "type": "story",
  "priority": "high",
  "assignee_id": 2
}
```

**Update task status:**
```bash
PUT /api/tasks/5/status
Content-Type: application/json

{
  "status": "in_progress"
}
```

---

## 📞 SUPPORT & CONTACT

**Repository:** https://github.com/athanhtuan11/smalltree  
**Production:** https://mamnoncaynho.com  
**Email:** admin@mamnoncaynho.com

**Contributors:**
- Anh Tuan (athanhtuan11) - Lead Developer
- AI Assistant - Code Generation & Documentation

**Last Updated:** January 9, 2026  
**Version:** 2.0.0

---

## 📄 LICENSE

MIT License - Free to use and modify

---

**🎉 CONGRATULATIONS!**

You now have a complete SmallTree Academy documentation. Deploy with confidence! 🚀
