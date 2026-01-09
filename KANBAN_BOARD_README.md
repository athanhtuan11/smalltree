# Kanban Board Implementation Guide

## Overview
Đã implement Kanban Board tương tự Jira để quản lý công việc phát triển khóa học.

## Features Implemented

### 1. Project Management (Trang /tasks)
✅ **Project List View**
- Hiển thị danh sách projects dạng card grid
- Project avatar với màu sắc tùy chỉnh
- Hiển thị project key, name, description
- Task count và status badges
- Nút "Mở Board" để vào Kanban Board

✅ **Create Project Modal**
- Form tạo project mới với các fields:
  - Project Name (required)
  - Project Key (required, uppercase only)
  - Description
  - Color picker
- Validation: Project key chỉ chấp nhận chữ hoa

### 2. Kanban Board (Trang /tasks/<project_key>)
✅ **4 Column Layout**
- **To Do**: Công việc chưa bắt đầu
- **In Progress**: Đang thực hiện
- **Review**: Đang review
- **Done**: Hoàn thành

✅ **Drag & Drop Functionality**
- Sử dụng **Sortable.js** library
- Kéo thả tasks giữa các columns
- Visual feedback khi dragging (ghost effect)
- Auto-update task counts trong badges
- Console log để track status changes

✅ **Filter & Search**
- Search box tìm theo task title
- Filter theo assignee
- Filter theo priority
- Expandable filters button

✅ **Task Cards**
- Task key (VD: COURSE-12)
- Task title
- Type icons:
  - 📕 Story (green)
  - ☑️ Task (blue)
  - 🐛 Bug (red)
  - ⚡ Epic (yellow)
- Priority indicators:
  - ⏫ Urgent (red)
  - ⏫ High (yellow)
  - ⏬ Low (gray)
- Story points badge
- Assignee avatar
- Click to view detail

✅ **Create Task Modal**
- Form tạo task mới:
  - Title (required)
  - Description (textarea)
  - Type dropdown (Story/Task/Bug/Epic)
  - Priority dropdown (Low/Medium/High/Urgent)
  - Assignee dropdown
  - Story points (1-13)
- Split layout: Main info bên trái, metadata bên phải

### 3. Task Detail Page (Trang /tasks/<project_key>/<task_key>)
✅ **Main Content Area**
- Task header với type icon và title
- Task key badge
- Tabs navigation:
  - **Chi tiết**: Hiển thị description
  - **Comments**: Danh sách comments + form thêm comment
  - **Attachments**: Danh sách files + upload form
  - **Activity**: Timeline history log

✅ **Sidebar (Sticky)**
- Status dropdown (auto-save on change)
- Priority dropdown (auto-save on change)
- Assignee info with avatar
- Reporter info
- Story points badge
- Timestamps (Created, Updated)
- Delete task button (với confirm dialog)

✅ **Comments Tab**
- Danh sách comments với avatar, author, timestamp
- Form thêm comment mới
- Submit button

✅ **Attachments Tab**
- Danh sách files với icon, filename, filesize
- Download button cho mỗi file
- Upload form với file picker

✅ **Activity Timeline**
- Chronological history log
- Timeline design với markers và connecting lines
- Different marker colors cho different events
- Timestamps và action descriptions

## Technical Stack

### Frontend
- **Bootstrap 5**: UI framework
- **Bootstrap Icons**: Icon library
- **Sortable.js 1.15.0**: Drag & drop functionality
- **Custom CSS**: Kanban board styling, card hover effects
- **Vanilla JavaScript**: Event handlers, AJAX preparation

### Backend
- **Flask**: Web framework
- **Routes**: 
  - `GET /tasks` - Project list
  - `GET /tasks/project/create` - Create project form
  - `POST /tasks/project/create` - Handle project creation
  - `GET /tasks/<project_key>` - Kanban board
  - `GET /tasks/<project_key>/<task_key>` - Task detail

### Data (Currently Mock Data)
Mock data structure trong routes.py:
```python
# Projects
projects_list = [
    {'id': 1, 'key': 'COURSE', 'name': 'Course Development', ...}
]

# Tasks grouped by status
tasks_by_status = {
    'todo': [...],
    'in_progress': [...],
    'review': [...],
    'done': [...]
}

# Task detail
task = {
    'key': 'COURSE-8',
    'title': '...',
    'description': '...',
    'comments': [...],
    'attachments': [...]
}
```

## UI/UX Features

### Visual Design
- **Project Cards**: Hover lift effect, shadow on hover
- **Project Avatar**: Colored square badge với first 2 chars của key
- **Task Cards**: Smooth hover animation, cursor grab/grabbing
- **Ghost Effect**: Semi-transparent khi dragging
- **Badges**: Bootstrap badges cho counts, status, story points
- **Sticky Sidebar**: Task detail sidebar stays visible when scrolling

### Responsive Design
- Grid layout auto-adjusts:
  - Desktop: 4 columns
  - Tablet: 2 columns  
  - Mobile: 1 column
- Horizontal scroll cho Kanban board trên mobile
- Flexible filters bar

### Color Coding
- **Project Colors**: Customizable via color picker
- **Type Icons**: Story=green, Task=blue, Bug=red, Epic=yellow
- **Priority**: Urgent=red, High=yellow, Medium=default, Low=gray
- **Status Badges**: Different colors cho each status

## Next Steps (TODO)

### Phase 1: Database Integration
- [ ] Migrate models_tasks.py to database
- [ ] Run Flask-Migrate để tạo tables
- [ ] Replace mock data với database queries
- [ ] Implement CRUD operations:
  - Create project
  - Create task
  - Update task status (drag & drop)
  - Update task fields (detail page)
  - Add comments
  - Upload attachments
  - Delete tasks

### Phase 2: Advanced Features
- [ ] **Backlog View**: Separate view cho tasks chưa sprint
- [ ] **Sprint Planning**: 
  - Create/close sprints
  - Drag tasks vào sprint
  - Sprint burndown chart
- [ ] **Real-time Updates**: 
  - WebSockets cho multi-user collaboration
  - Live badge updates
- [ ] **Advanced Filters**:
  - Filter by labels/tags
  - Filter by sprint
  - Custom filter combinations
  - Save filter presets
- [ ] **Bulk Operations**:
  - Multi-select tasks
  - Bulk assign
  - Bulk update status
  - Bulk delete

### Phase 3: Analytics & Reports
- [ ] **Dashboard**:
  - Tasks by status chart
  - Tasks by assignee chart
  - Tasks by priority chart
  - Velocity chart (story points per sprint)
- [ ] **Reports**:
  - Sprint report
  - Burndown chart
  - Cumulative flow diagram
  - Time tracking report

### Phase 4: Integration
- [ ] **Course Module Integration**:
  - Link tasks to courses
  - Auto-create tasks khi create course
  - Task completion tracking in course dashboard
- [ ] **Notification System**:
  - Email notifications cho assignments
  - In-app notifications cho comments
  - Due date reminders
- [ ] **Export/Import**:
  - Export to CSV/Excel
  - Import tasks from CSV
  - Jira import compatibility

## File Structure
```
app/
├── models_tasks.py          # Database models
├── routes.py                # Route handlers (updated)
└── templates/
    └── tasks/
        ├── index.html       # Project list ✅
        ├── create_project.html  # (handled by modal in index)
        ├── board.html       # Kanban board ✅
        └── detail.html      # Task detail ✅
```

## Testing Checklist

### Manual Testing
- [x] Access /tasks without login → redirect to login
- [x] Login as teacher/admin → can access /tasks
- [x] See project list with mock data
- [x] Click "Mở Board" → navigate to board
- [x] See 4 columns với tasks
- [x] Drag task từ To Do → In Progress → works
- [x] Badge counts update after drag
- [x] Click task card → navigate to detail page
- [x] Task detail shows all tabs
- [x] Breadcrumb navigation works
- [ ] Create project modal works (needs backend)
- [ ] Create task modal works (needs backend)
- [ ] Change status in detail page (needs backend)
- [ ] Add comment (needs backend)

## Known Issues & Limitations

### Current Limitations
1. **Mock Data Only**: All data is hardcoded in routes.py
2. **No Persistence**: Changes don't save to database
3. **No Authentication Check**: Assignee dropdown hardcoded
4. **No File Upload**: Attachment upload not implemented
5. **No AJAX**: Status updates log to console only

### Browser Compatibility
- Tested on: Chrome, Edge (modern browsers)
- Requires: JavaScript enabled
- Sortable.js: Works on all modern browsers
- Grid layout: CSS Grid support required

## Screenshots Location
(Add screenshots after testing)
- Project list view
- Kanban board with drag & drop
- Task detail page with tabs
- Create modals

## Deployment Notes
- Sortable.js loaded from CDN
- Bootstrap 5 Icons required
- No additional npm packages needed
- Works with existing Flask app structure

---
**Status**: ✅ Phase 1 Complete (UI/UX) - Ready for database integration
**Next Priority**: Database models → CRUD operations → Real data
