"""
Dynamic Role & Permission Models
Cho phép admin tạo và quản lý roles & permissions động
"""
from app.models import db
from datetime import datetime


class Role(db.Model):
    """
    Bảng Role - Lưu các vai trò trong hệ thống
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Metadata
    is_system_role = db.Column(db.Boolean, default=False)  # Role hệ thống không thể xóa
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    permissions = db.relationship('Permission', 
                                 secondary='role_permissions',
                                 back_populates='roles',
                                 lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def get_permissions(self):
        """Lấy list tên permissions"""
        return [p.name for p in self.permissions]
    
    def has_permission(self, permission_name):
        """Check role có permission không"""
        return self.permissions.filter_by(name=permission_name).first() is not None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'permission_count': self.permissions.count(),
            'permissions': self.get_permissions()
        }


class Permission(db.Model):
    """
    Bảng Permission - Lưu các quyền trong hệ thống
    """
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Admin, Content Management, View Access, Actions
    
    # Metadata
    is_system_permission = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('Role',
                           secondary='role_permissions',
                           back_populates='permissions',
                           lazy='dynamic')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'is_system_permission': self.is_system_permission
        }


# Association table for many-to-many relationship
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
    db.Column('granted_at', db.DateTime, default=datetime.utcnow),
    db.Column('granted_by', db.Integer, db.ForeignKey('users.id'))
)


# ==================== HELPER FUNCTIONS ====================

def init_system_roles():
    """
    Khởi tạo 5 roles hệ thống mặc định
    Chỉ chạy 1 lần khi setup database
    """
    from app.models_users import ROLE_PERMISSIONS
    
    # Tạo tất cả permissions trước
    all_perms = set()
    for perms in ROLE_PERMISSIONS.values():
        all_perms.update(perms)
    
    permission_objs = {}
    for perm_name in all_perms:
        # Categorize permission
        if 'manage' in perm_name or 'delete' in perm_name or 'admin' in perm_name:
            category = 'Admin'
        elif 'create' in perm_name or 'edit' in perm_name:
            category = 'Content Management'
        elif 'view' in perm_name or 'access' in perm_name:
            category = 'View Access'
        else:
            category = 'Actions'
        
        perm = Permission.query.filter_by(name=perm_name).first()
        if not perm:
            perm = Permission(
                name=perm_name,
                display_name=perm_name.replace('_', ' ').title(),
                category=category,
                is_system_permission=True
            )
            db.session.add(perm)
        permission_objs[perm_name] = perm
    
    db.session.flush()  # Flush để có IDs
    
    # Tạo 5 roles hệ thống
    role_configs = [
        ('admin', 'Administrator', 'Full system access and management'),
        ('teacher', 'Teacher', 'Manage courses, view students, create content'),
        ('parent', 'Parent', 'View children info, pay tuition, enroll courses'),
        ('student', 'Student', 'Access courses, submit assignments, view grades'),
        ('public_student', 'Public Student', 'Purchase and access enrolled courses')
    ]
    
    for role_name, display_name, description in role_configs:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(
                name=role_name,
                display_name=display_name,
                description=description,
                is_system_role=True
            )
            db.session.add(role)
            db.session.flush()
        
        # Assign permissions
        perm_names = ROLE_PERMISSIONS.get(role_name, [])
        for perm_name in perm_names:
            perm = permission_objs.get(perm_name)
            if perm and not role.has_permission(perm_name):
                role.permissions.append(perm)
    
    db.session.commit()
    print(f"✅ Initialized {len(role_configs)} system roles and {len(permission_objs)} permissions")


def get_role_permissions_dict():
    """
    Lấy ROLE_PERMISSIONS từ database thay vì hard-coded
    Fallback về hard-coded nếu database chưa có data
    """
    try:
        roles = Role.query.filter_by(is_active=True).all()
        if not roles:
            # Fallback to hard-coded
            from app.models_users import ROLE_PERMISSIONS
            return ROLE_PERMISSIONS
        
        result = {}
        for role in roles:
            result[role.name] = role.get_permissions()
        return result
    except Exception as e:
        print(f"⚠️ Error loading roles from DB: {e}")
        from app.models_users import ROLE_PERMISSIONS
        return ROLE_PERMISSIONS
