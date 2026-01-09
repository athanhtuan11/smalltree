# Courses and Apps - Hệ thống Quản lý Khóa học & Task Tracking

## Tổng quan

Hệ thống "Courses and Apps" bao gồm 3 module chính:
1. **Flashcard System** - Hệ thống học flashcard (đã có sẵn)
2. **Courses Module** - Quản lý khóa học (tương tự Udemy)
3. **Task Tracking Module** - Quản lý công việc (tương tự Jira)

---

## 🎓 Module 1: Courses (Khóa học)

### Tính năng chính:

#### Cho Giảng viên/Admin:
- **Tạo và quản lý khóa học**: Tạo khóa học mới với thông tin chi tiết
- **Quản lý nội dung**: Tổ chức khóa học thành các Section và Lesson
- **Upload video**: Hỗ trợ video từ YouTube, Vimeo hoặc upload local
- **Quản lý học viên**: Xem danh sách học viên đã đăng ký, theo dõi tiến độ
- **Thống kê**: Xem số lượng đăng ký, rating, completion rate

#### Cho Học sinh:
- **Duyệt khóa học**: Xem danh sách khóa học có sẵn
- **Đăng ký khóa học**: Enroll vào khóa học miễn phí hoặc trả phí
- **Học tập**: Xem video, đọc tài liệu, hoàn thành bài tập
- **Theo dõi tiến độ**: Xem % hoàn thành, lessons đã học
- **Đánh giá**: Rating và review khóa học

### Database Models:

```python
- Course: Thông tin khóa học
- CourseSection: Chương/phần trong khóa học
- Lesson: Bài học (video, text, quiz, assignment)
- Enrollment: Đăng ký khóa học của học sinh
- LessonProgress: Tiến độ học từng bài
- CourseReview: Đánh giá khóa học
```

### API Routes (dự kiến):

```
GET  /courses              # Danh sách khóa học
GET  /courses/<slug>       # Chi tiết khóa học
POST /courses              # Tạo khóa học mới (admin/teacher)
PUT  /courses/<id>         # Cập nhật khóa học
DEL  /courses/<id>         # Xóa khóa học

POST /courses/<id>/enroll  # Đăng ký khóa học
GET  /courses/<id>/learn   # Trang học (player)
POST /lessons/<id>/complete # Đánh dấu hoàn thành bài học
```

---

## 📋 Module 2: Task Tracking (Quản lý công việc)

### Tính năng chính:

#### Kanban Board:
- **Columns**: To Do, In Progress, Review, Done
- **Drag & Drop**: Kéo thả task giữa các cột
- **Filters**: Lọc theo assignee, priority, label
- **Quick create**: Tạo task nhanh ngay trên board

#### Task Management:
- **Task types**: Story, Task, Bug, Epic
- **Priority levels**: Low, Medium, High, Urgent
- **Assignment**: Gán task cho thành viên
- **Story points**: Ước tính độ phức tạp
- **Time tracking**: Log giờ làm việc
- **Attachments**: Đính kèm file, hình ảnh
- **Comments**: Thảo luận trên task
- **History**: Xem lịch sử thay đổi

#### Sprint Management (Scrum):
- **Sprint planning**: Lên kế hoạch sprint
- **Backlog**: Quản lý backlog
- **Sprint report**: Báo cáo sprint

### Database Models:

```python
- Project: Dự án/Board
- ProjectMember: Thành viên dự án
- Task: Task/Issue
- Sprint: Sprint (cho Scrum)
- TaskComment: Bình luận
- TaskAttachment: File đính kèm
- TaskHistory: Lịch sử thay đổi
- TaskLink: Liên kết giữa các task
```

### API Routes (dự kiến):

```
GET  /tasks                    # Danh sách projects
GET  /tasks/<project_key>      # Kanban board
GET  /tasks/<task_key>         # Chi tiết task
POST /tasks/<project_id>       # Tạo task mới
PUT  /tasks/<task_id>          # Cập nhật task
DEL  /tasks/<task_id>          # Xóa task

POST /tasks/<task_id>/comment  # Thêm comment
POST /tasks/<task_id>/attach   # Upload file
GET  /tasks/<task_id>/history  # Lịch sử task
```

---

## 🚀 Cài đặt & Khởi chạy

### 1. Import models vào database

Thêm vào `app/__init__.py`:

```python
# Import models mới
from app.models_courses import (
    Course, CourseSection, Lesson, 
    Enrollment, LessonProgress, CourseReview
)
from app.models_tasks import (
    Project, ProjectMember, Task, Sprint,
    TaskComment, TaskAttachment, TaskHistory, TaskLink
)
```

### 2. Tạo migration

```bash
cd d:\04_SmallTree\02_copilot_smalltree\smalltree-website
python -m flask db migrate -m "Add courses and tasks modules"
python -m flask db upgrade
```

### 3. Test routes

Sau khi tạo routes và templates, test qua menu:
- **App → Apps**: Flashcard (cũ)
- **App → Khóa học**: Courses module (mới)
- **App → Task Tracking**: Tasks module (mới)

---

## 📝 Use Cases

### Use Case 1: Tạo khóa học mới
1. Admin/Teacher đăng nhập
2. Vào menu "App → Khóa học"
3. Click "Tạo khóa học mới"
4. Điền thông tin: Tiêu đề, mô tả, category, level
5. Upload thumbnail
6. Tạo sections và lessons
7. Upload video hoặc viết nội dung text
8. Publish khóa học

### Use Case 2: Học sinh học khóa học
1. Học sinh đăng nhập
2. Duyệt danh sách khóa học
3. Click vào khóa học để xem chi tiết
4. Click "Đăng ký khóa học"
5. Bắt đầu học: xem video, đọc tài liệu
6. Hệ thống tự động lưu tiến độ
7. Hoàn thành khóa học → nhận certificate

### Use Case 3: Quản lý task soạn khóa học
1. Teacher tạo Project "Course Development"
2. Tạo Epic "Khóa học Toán lớp 1"
3. Breakdown thành các tasks:
   - "Viết outline khóa học"
   - "Quay video bài 1: Số tự nhiên"
   - "Tạo bài tập thực hành"
   - "Review nội dung"
4. Gán task cho các giáo viên
5. Di chuyển task qua các trạng thái trên Kanban board
6. Comment, đính kèm file, log giờ
7. Hoàn thành tất cả tasks → khóa học sẵn sàng publish

---

## 🎨 UI/UX Design

### Courses Module:
- **Course List**: Card grid với thumbnail, title, rating, price
- **Course Detail**: Hero section, curriculum sidebar, description tabs
- **Course Player**: Video player, lesson list sidebar, notes, attachments
- **Dashboard**: Enrolled courses, progress bars, continue learning

### Task Tracking Module:
- **Kanban Board**: Columns với cards, drag-drop
- **Task Detail**: Modal hoặc side panel với đầy đủ thông tin
- **Backlog**: List view với filters
- **Sprint Board**: Burn-down chart, sprint stats

---

## 🔐 Phân quyền

### Courses:
- **Admin**: Full access
- **Teacher**: Tạo và quản lý khóa học của mình
- **Student**: Xem, đăng ký, học khóa học

### Task Tracking:
- **Project Admin**: Quản lý project, thêm/xóa thành viên
- **Project Member**: Tạo/edit/comment tasks
- **Viewer**: Chỉ xem

---

## 📚 Tài liệu tham khảo

- **Udemy**: https://www.udemy.com (Course UI/UX)
- **Jira**: https://www.atlassian.com/software/jira (Task Tracking)
- **Trello**: https://trello.com (Kanban Board)
- **Teachable**: https://teachable.com (Course platform)

---

## 🛠️ Công nghệ sử dụng

- **Backend**: Flask, SQLAlchemy
- **Frontend**: Bootstrap 5, jQuery, Bootstrap Icons
- **Database**: SQLite (dev), PostgreSQL (production)
- **Video**: HTML5 Video Player hoặc Video.js
- **Drag & Drop**: Sortable.js hoặc jQuery UI

---

## 📅 Roadmap

### Phase 1: MVP (Minimum Viable Product)
- ✅ Database models
- ⏳ Basic routes và templates
- ⏳ Course CRUD operations
- ⏳ Simple Kanban board

### Phase 2: Core Features
- Video player với progress tracking
- Enrollment và payment (nếu cần)
- Task comments và attachments
- Sprint management

### Phase 3: Advanced Features
- Quiz và assignments
- Certificates
- Advanced reporting
- Notifications
- Mobile responsive

---

## 👥 Team

- **Product Owner**: [Tên bạn]
- **Developers**: [Team members]
- **Content Creators**: Giáo viên

---

## 📞 Support

Nếu có câu hỏi hoặc cần hỗ trợ, vui lòng liên hệ qua:
- Email: [email]
- GitHub Issues: [repo URL]
