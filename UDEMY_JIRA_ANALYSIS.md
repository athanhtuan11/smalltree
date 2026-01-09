# Phân tích Udemy & Jira - Xây dựng Courses and Apps

## 📚 UDEMY ANALYSIS - Course Platform

### 1. Course Structure (Cấu trúc khóa học)

```
Course
├── Landing Page (Trang giới thiệu)
│   ├── Title + Subtitle
│   ├── Thumbnail Image
│   ├── Preview Video
│   ├── Description
│   ├── What you'll learn (4+ bullets)
│   ├── Requirements
│   ├── Target audience
│   ├── Instructor info
│   └── Reviews & Ratings
│
├── Curriculum (Nội dung)
│   ├── Section 1
│   │   ├── Lecture 1 (Video)
│   │   ├── Lecture 2 (Text)
│   │   ├── Quiz 1
│   │   └── Assignment 1
│   ├── Section 2
│   └── Section N
│
└── Resources
    ├── Downloadable files
    ├── External links
    └── Source code
```

### 2. Instructor Dashboard (Giáo viên)

**Course Management:**
- Create new course wizard (Step-by-step)
- Curriculum builder (Drag & drop sections/lectures)
- Video uploader with processing status
- Bulk actions (publish, delete, reorder)
- Course settings (price, category, language)
- Q&A management
- Reviews moderation
- Performance analytics

**Curriculum Builder UI:**
```
┌─────────────────────────────────────────┐
│ + Add Section                           │
├─────────────────────────────────────────┤
│ ▼ Section 1: Introduction               │
│   ├─ 📹 Lecture 1: Welcome     [Edit]   │
│   ├─ 📹 Lecture 2: Overview    [Edit]   │
│   └─ + Add Lecture                      │
├─────────────────────────────────────────┤
│ ▼ Section 2: Getting Started            │
│   ├─ 📹 Lecture 3: Setup       [Edit]   │
│   ├─ 📄 Article 1: Resources   [Edit]   │
│   ├─ ❓ Quiz 1                 [Edit]   │
│   └─ + Add Lecture                      │
└─────────────────────────────────────────┘
```

### 3. Student Experience

**Course Player:**
```
┌──────────────────────────────────────────────┐
│           Video Player Area                  │
│     [Play/Pause] [Volume] [Speed] [CC]      │
│                                              │
│  ◄ Previous           Next ►                │
└──────────────────────────────────────────────┘
│ Sidebar (Curriculum)                        │
│ ✓ Lecture 1: Welcome (5:30)                │
│ ✓ Lecture 2: Overview (8:15)               │
│ ▶ Lecture 3: Setup (12:45) ← Current       │
│   Lecture 4: First Steps (10:20)           │
└──────────────────────────────────────────────┘
│ Tabs: Overview | Q&A | Notes | Reviews     │
└──────────────────────────────────────────────┘
```

**Key Features:**
- Auto-save progress (remember position)
- Take notes with timestamps
- Playback speed control (0.5x - 2x)
- Video quality selector
- Keyboard shortcuts
- Certificate after completion
- Download resources button

### 4. Database Structure (Udemy-inspired)

```sql
-- Courses
courses (id, title, slug, instructor_id, price, level, 
         thumbnail, preview_video, status, created_at)

-- Curriculum
sections (id, course_id, title, order_index)
lectures (id, section_id, title, type, video_url, 
         content, duration, order_index, is_preview)

-- Student Progress
enrollments (id, user_id, course_id, progress_percent, 
            enrolled_at, last_accessed, completed_at)
lecture_progress (id, enrollment_id, lecture_id, 
                 watched_seconds, is_completed)

-- Engagement
course_notes (id, enrollment_id, lecture_id, note_text, 
             timestamp_seconds)
course_reviews (id, course_id, user_id, rating, review_text)
course_qa (id, course_id, lecture_id, user_id, question, 
          answer, upvotes)
```

---

## 📋 JIRA ANALYSIS - Task Tracking

### 1. Project Structure

```
Project (Board)
├── Backlog (Chưa lên kế hoạch)
├── Sprint (Đang làm)
│   ├── To Do
│   ├── In Progress
│   ├── Code Review
│   ├── Testing
│   └── Done
└── Completed Sprints
```

### 2. Issue Types (Loại công việc)

| Type | Icon | Use Case | Fields |
|------|------|----------|--------|
| **Epic** | 🎯 | Tính năng lớn, nhiều tasks | Story points tổng |
| **Story** | 📖 | User story | Acceptance criteria |
| **Task** | ☑️ | Công việc kỹ thuật | Estimate, subtasks |
| **Bug** | 🐛 | Lỗi cần fix | Steps to reproduce |
| **Subtask** | 📌 | Task con | Parent task link |

### 3. Kanban Board UI

```
┌─────────────────────────────────────────────────────────┐
│ PROJECT-KEY  [Create] [Sprint] [Backlog] [Reports]     │
├─────────────────────────────────────────────────────────┤
│ Filter: All | My Issues | Recently Updated              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  TO DO (5)    │  IN PROGRESS (3)  │  REVIEW (2)  │ DONE │
│ ┌──────────┐  │ ┌──────────┐     │ ┌──────────┐│      │
│ │COURSE-12 │  │ │COURSE-8  │     │ │COURSE-5  ││      │
│ │Create... │  │ │Implement │     │ │Fix video ││      │
│ │         │  │ │player    │     │ │upload    ││      │
│ │📖 Story  │  │ │📖 Story  │     │ │🐛 Bug    ││      │
│ │⚡ High   │  │ │⚠️ Medium │     │ │⚠️ Medium ││      │
│ │👤 John   │  │ │👤 Jane   │     │ │👤 John   ││      │
│ └──────────┘  │ └──────────┘     │ └──────────┘│      │
│               │                   │              │      │
│ ┌──────────┐  │ ┌──────────┐     │              │      │
│ │COURSE-13 │  │ │COURSE-9  │     │              │      │
│ │...       │  │ │...       │     │              │      │
│ └──────────┘  │ └──────────┘     │              │      │
└─────────────────────────────────────────────────────────┘
```

### 4. Issue Detail (Chi tiết task)

```
┌─────────────────────────────────────────────────────┐
│ COURSE-12  [Edit] [Assign] [Comment] [More]       │
├─────────────────────────────────────────────────────┤
│ Create video upload feature                         │
│                                                     │
│ Type: 📖 Story            Priority: ⚡ High        │
│ Status: To Do            Assignee: 👤 John Doe     │
│ Reporter: Jane           Sprint: Sprint 5          │
│ Story Points: 8          Due Date: Jan 15, 2026    │
│                                                     │
│ ┌─ Description ────────────────────────────────┐  │
│ │ As an instructor, I want to upload videos    │  │
│ │ so that students can watch my lectures       │  │
│ │                                              │  │
│ │ Acceptance Criteria:                         │  │
│ │ - Support MP4, MOV formats                   │  │
│ │ - Max file size 2GB                          │  │
│ │ - Show upload progress                       │  │
│ └──────────────────────────────────────────────┘  │
│                                                     │
│ ┌─ Subtasks (2/5 done) ───────────────────────┐  │
│ │ ☑ Design upload UI                           │  │
│ │ ☑ Setup file storage                         │  │
│ │ ☐ Implement upload endpoint                  │  │
│ │ ☐ Add progress indicator                     │  │
│ │ ☐ Write tests                                │  │
│ └──────────────────────────────────────────────┘  │
│                                                     │
│ ┌─ Activity (Comments & History) ──────────────┐  │
│ │ Jane Smith • 2 hours ago                      │  │
│ │ "Started working on the upload endpoint"      │  │
│ │                                               │  │
│ │ System • 3 hours ago                          │  │
│ │ Status changed: Backlog → To Do               │  │
│ └──────────────────────────────────────────────┘  │
│                                                     │
│ ┌─ Attachments ─────────────────────────────────┐ │
│ │ 📎 wireframe.png (250 KB)                     │ │
│ │ 📎 requirements.pdf (1.2 MB)                  │ │
│ └──────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Links ──────────────────────────────────────┐ │
│ │ → Blocks: COURSE-15                           │ │
│ │ ← Related to: COURSE-10                       │ │
│ └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 5. Sprint Planning

**Sprint Board:**
- Drag tasks from Backlog → Sprint
- Set sprint dates (Start - End)
- Assign story points
- Velocity calculation
- Burndown chart

**Backlog Grooming:**
- Prioritize tasks
- Break down epics → stories → tasks
- Estimate story points (Fibonacci: 1,2,3,5,8,13)
- Assign to team members

### 6. Database Structure (Jira-inspired)

```sql
-- Projects
projects (id, key, name, type, owner_id, status)
project_members (id, project_id, user_id, role)

-- Issues
tasks (id, project_id, task_key, title, description,
      type, priority, status, reporter_id, assignee_id,
      story_points, due_date, board_order)

-- Sprints
sprints (id, project_id, name, goal, start_date, 
        end_date, status)
sprint_tasks (id, sprint_id, task_id, order_index)

-- Workflow
task_status_transitions (id, from_status, to_status, task_id)
task_history (id, task_id, user_id, action, field, 
             old_value, new_value, created_at)

-- Collaboration
task_comments (id, task_id, user_id, content, created_at)
task_attachments (id, task_id, filename, file_path, size)
task_watchers (id, task_id, user_id)
task_links (id, source_task_id, target_task_id, link_type)
```

---

## 🎯 IMPLEMENTATION PLAN

### Phase 1: Courses (Udemy-style) - 2 weeks

**Week 1: Core Features**
- [ ] Course CRUD (Create, Read, Update, Delete)
- [ ] Curriculum builder (Sections + Lectures)
- [ ] Video upload & storage (R2 hoặc local)
- [ ] Basic course player
- [ ] Enrollment system

**Week 2: Advanced Features**
- [ ] Video.js player với progress tracking
- [ ] Student notes với timestamps
- [ ] Q&A system
- [ ] Course reviews & ratings
- [ ] Certificate generation

### Phase 2: Task Tracking (Jira-style) - 2 weeks

**Week 1: Kanban Board**
- [ ] Project management (Create, list)
- [ ] Issue types (Epic, Story, Task, Bug)
- [ ] Drag & drop Kanban board (Sortable.js)
- [ ] Issue detail modal
- [ ] Comments & attachments

**Week 2: Sprint & Reporting**
- [ ] Backlog management
- [ ] Sprint planning
- [ ] Sprint board
- [ ] Burndown chart
- [ ] Velocity tracking

---

## 🛠️ TECH STACK

### Frontend
- **UI Framework**: Bootstrap 5
- **Drag & Drop**: Sortable.js
- **Video Player**: Video.js
- **Charts**: Chart.js
- **Rich Text Editor**: Quill.js (for descriptions)

### Backend
- **Framework**: Flask
- **ORM**: SQLAlchemy
- **File Storage**: Cloudflare R2 / Local
- **Video Processing**: FFmpeg (optional)

### Database
- **Development**: SQLite
- **Production**: PostgreSQL

---

## 📊 KEY FEATURES COMPARISON

| Feature | Udemy | Our Implementation |
|---------|-------|-------------------|
| Course Builder | ✅ Drag-drop | ✅ Sections + Lectures |
| Video Player | ✅ Custom player | ✅ Video.js |
| Progress Tracking | ✅ Auto-save | ✅ Real-time |
| Certificates | ✅ PDF | ✅ PDF/Image |
| Q&A | ✅ Forum-style | ⏳ Phase 2 |
| Reviews | ✅ 5-star | ✅ 5-star |

| Feature | Jira | Our Implementation |
|---------|------|-------------------|
| Kanban Board | ✅ Drag-drop | ✅ Sortable.js |
| Issue Types | ✅ Multiple | ✅ Epic/Story/Task/Bug |
| Sprints | ✅ Full scrum | ✅ Sprint planning |
| Subtasks | ✅ Nested | ✅ Parent-child |
| Workflow | ✅ Customizable | ✅ Predefined |
| Reports | ✅ Advanced | ✅ Basic charts |

---

## 🚀 NEXT STEPS

1. **Implement Course Builder** (Priority #1)
   - Create form với sections/lectures
   - Upload video functionality
   - Preview mode

2. **Implement Kanban Board** (Priority #2)
   - Drag-drop between columns
   - Quick create task modal
   - Filter & search

3. **Polish UI/UX**
   - Mobile responsive
   - Loading states
   - Error handling
   - Success notifications

Bạn muốn tôi bắt đầu với feature nào trước? Course Builder hay Kanban Board?
