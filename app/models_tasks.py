"""
Models cho hệ thống Task Tracking (tương tự Jira)
"""
from app.models import db
from datetime import datetime


class Project(db.Model):
    """Dự án - Project (tương tự Board trong Jira)"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    key = db.Column(db.String(10), unique=True, nullable=False)  # Ví dụ: COURSE, TASK
    description = db.Column(db.Text)
    
    # Owner và team
    owner_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    owner = db.relationship('Staff', backref=db.backref('owned_projects', lazy=True))
    
    # Settings
    project_type = db.Column(db.String(50), default='kanban')  # kanban, scrum
    status = db.Column(db.String(20), default='active')  # active, archived
    color = db.Column(db.String(7), default='#43a047')  # Màu sắc project
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Project {self.key}: {self.name}>'


class ProjectMember(db.Model):
    """Thành viên trong project"""
    __tablename__ = 'project_members'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    role = db.Column(db.String(50), default='member')  # admin, member, viewer
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('members', lazy=True))
    staff = db.relationship('Staff', backref=db.backref('project_memberships', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('project_id', 'staff_id', name='unique_project_member'),)
    
    def __repr__(self):
        return f'<ProjectMember project={self.project_id} staff={self.staff_id}>'


class Task(db.Model):
    """Task/Issue (tương tự Issue trong Jira)"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Thông tin cơ bản
    task_key = db.Column(db.String(50), unique=True, nullable=False)  # VD: COURSE-123
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    
    # Phân loại
    task_type = db.Column(db.String(50), default='task')  # story, task, bug, epic
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(50), default='todo')  # todo, in_progress, review, done
    
    # Gán người
    reporter_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)  # Người tạo
    assignee_id = db.Column(db.Integer, db.ForeignKey('staff.id'))  # Người được gán
    
    # Story points và estimate
    story_points = db.Column(db.Integer)  # Độ phức tạp (1, 2, 3, 5, 8, 13...)
    estimated_hours = db.Column(db.Float)  # Ước tính giờ
    logged_hours = db.Column(db.Float, default=0)  # Giờ đã log
    
    # Sprint/Epic
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    epic_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))  # Parent epic (self-reference)
    
    # Labels và tags
    labels = db.Column(db.Text)  # JSON array: ["frontend", "backend", "urgent"]
    
    # Dates
    due_date = db.Column(db.Date)
    start_date = db.Column(db.Date)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    
    # Order trong board
    board_order = db.Column(db.Integer, default=0)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))
    reporter = db.relationship('Staff', foreign_keys=[reporter_id], backref=db.backref('reported_tasks', lazy=True))
    assignee = db.relationship('Staff', foreign_keys=[assignee_id], backref=db.backref('assigned_tasks', lazy=True))
    sprint = db.relationship('Sprint', backref=db.backref('tasks', lazy=True))
    parent_epic = db.relationship('Task', remote_side=[id], backref=db.backref('sub_tasks', lazy=True))
    
    def __repr__(self):
        return f'<Task {self.task_key}: {self.title}>'


class Sprint(db.Model):
    """Sprint (cho Scrum)"""
    __tablename__ = 'sprints'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.Text)  # Sprint goal
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='planned')  # planned, active, completed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    project = db.relationship('Project', backref=db.backref('sprints', lazy=True))
    
    def __repr__(self):
        return f'<Sprint {self.name}>'


class TaskComment(db.Model):
    """Bình luận trên task"""
    __tablename__ = 'task_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)
    
    task = db.relationship('Task', backref=db.backref('comments', lazy=True, order_by='TaskComment.created_at'))
    author = db.relationship('Staff', backref=db.backref('task_comments', lazy=True))
    
    def __repr__(self):
        return f'<TaskComment task={self.task_id} author={self.author_id}>'


class TaskAttachment(db.Model):
    """File đính kèm task"""
    __tablename__ = 'task_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Đường dẫn file
    file_size = db.Column(db.Integer)  # Kích thước file (bytes)
    mime_type = db.Column(db.String(100))
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task = db.relationship('Task', backref=db.backref('attachments', lazy=True))
    uploader = db.relationship('Staff', backref=db.backref('task_attachments', lazy=True))
    
    def __repr__(self):
        return f'<TaskAttachment {self.filename}>'


class TaskHistory(db.Model):
    """Lịch sử thay đổi task (Activity log)"""
    __tablename__ = 'task_history'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    
    # Loại thay đổi
    action = db.Column(db.String(50), nullable=False)  # created, updated, status_changed, assigned, commented
    field_name = db.Column(db.String(100))  # Tên field thay đổi
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task = db.relationship('Task', backref=db.backref('history', lazy=True, order_by='TaskHistory.created_at.desc()'))
    user = db.relationship('Staff', backref=db.backref('task_history', lazy=True))
    
    def __repr__(self):
        return f'<TaskHistory task={self.task_id} action={self.action}>'


class TaskLink(db.Model):
    """Liên kết giữa các task (relates to, blocks, duplicates...)"""
    __tablename__ = 'task_links'
    
    id = db.Column(db.Integer, primary_key=True)
    source_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    target_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    link_type = db.Column(db.String(50), nullable=False)  # relates_to, blocks, duplicates, depends_on
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    
    source_task = db.relationship('Task', foreign_keys=[source_task_id], backref=db.backref('outgoing_links', lazy=True))
    target_task = db.relationship('Task', foreign_keys=[target_task_id], backref=db.backref('incoming_links', lazy=True))
    created_by = db.relationship('Staff', backref=db.backref('created_links', lazy=True))
    
    def __repr__(self):
        return f'<TaskLink {self.source_task_id} {self.link_type} {self.target_task_id}>'
