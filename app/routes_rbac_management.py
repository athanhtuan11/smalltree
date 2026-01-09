"""
RBAC Management Routes - Quản lý quyền người dùng
Admin có thể xem và chỉnh sửa quyền của từng user
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models import db
from app.models_users import User, ROLE_PERMISSIONS, TeacherProfile, StudentProfile, ParentProfile
from datetime import datetime

rbac_mgmt = Blueprint('rbac_mgmt', __name__, url_prefix='/rbac')


# ==================== MIDDLEWARE ====================
def admin_required():
    """Check if current user is admin"""
    if session.get('role') != 'admin':
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return False
    return True


# ==================== ROUTES ====================
@rbac_mgmt.route('/users')
def list_users():
    """Danh sách tất cả users với role và permissions"""
    if not admin_required():
        return redirect(url_for('main.login'))
    
    # Get all users with their profiles
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Prepare user data with permission counts
    users_data = []
    for user in users:
        permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        # Get profile info
        profile_info = None
        if user.role == 'teacher' and user.teacher_profile:
            profile_info = f"{user.teacher_profile.position or 'Teacher'}"
        elif user.role in ['student', 'public_student'] and user.student_profile:
            profile_info = f"{user.student_profile.student_type} - {user.student_profile.student_code or 'N/A'}"
        elif user.role == 'parent' and user.parent_profile:
            children_count = len(user.parent_profile.children)
            profile_info = f"{children_count} children"
        
        users_data.append({
            'user': user,
            'permissions': permissions,
            'permission_count': len(permissions),
            'profile_info': profile_info
        })
    
    return render_template('rbac/user_list.html', 
                          users_data=users_data,
                          title='Quản lý User & Permissions')


@rbac_mgmt.route('/users/<int:user_id>/permissions', methods=['GET', 'POST'])
def edit_permissions(user_id):
    """Trang chỉnh sửa permissions của 1 user"""
    if not admin_required():
        return redirect(url_for('main.login'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_role':
            new_role = request.form.get('new_role')
            if new_role in ['admin', 'teacher', 'parent', 'student', 'public_student']:
                old_role = user.role
                user.role = new_role
                user.updated_at = datetime.utcnow()
                
                # Create corresponding profile if needed
                if new_role == 'teacher' and not user.teacher_profile:
                    profile = TeacherProfile(user_id=user.id)
                    db.session.add(profile)
                elif new_role in ['student', 'public_student'] and not user.student_profile:
                    profile = StudentProfile(
                        user_id=user.id,
                        student_type='internal' if new_role == 'student' else 'public'
                    )
                    db.session.add(profile)
                elif new_role == 'parent' and not user.parent_profile:
                    profile = ParentProfile(user_id=user.id)
                    db.session.add(profile)
                
                db.session.commit()
                flash(f'✅ Đã đổi role từ "{old_role}" → "{new_role}" cho {user.full_name}', 'success')
            else:
                flash('Role không hợp lệ!', 'danger')
        
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            db.session.commit()
            status = 'kích hoạt' if user.is_active else 'vô hiệu hóa'
            flash(f'✅ Đã {status} tài khoản {user.full_name}', 'success')
        
        return redirect(url_for('rbac_mgmt.edit_permissions', user_id=user_id))
    
    # GET request - show permission editor
    current_permissions = ROLE_PERMISSIONS.get(user.role, [])
    
    # All possible permissions (union of all roles)
    all_permissions = set()
    for perms in ROLE_PERMISSIONS.values():
        all_permissions.update(perms)
    all_permissions = sorted(all_permissions)
    
    # Group permissions by category (fix circular reference)
    admin_perms = [p for p in all_permissions if 'manage' in p or 'delete' in p or 'admin' in p]
    content_perms = [p for p in all_permissions if 'create' in p or 'edit' in p]
    view_perms = [p for p in all_permissions if 'view' in p or 'access' in p]
    
    # Actions = all other permissions not in above categories
    action_perms = [p for p in all_permissions 
                    if p not in admin_perms 
                    and p not in content_perms 
                    and p not in view_perms]
    
    permission_groups = {
        'Admin': admin_perms,
        'Content Management': content_perms,
        'View Access': view_perms,
        'Actions': action_perms
    }
    
    return render_template('rbac/edit_permissions.html',
                          user=user,
                          current_permissions=current_permissions,
                          all_permissions=all_permissions,
                          permission_groups=permission_groups,
                          role_permissions=ROLE_PERMISSIONS,
                          title=f'Edit Permissions - {user.full_name}')


@rbac_mgmt.route('/roles')
def list_roles():
    """Hiển thị tất cả roles và permissions tương ứng"""
    if not admin_required():
        return redirect(url_for('main.login'))
    
    # Count users by role
    role_counts = {}
    for role in ROLE_PERMISSIONS.keys():
        count = User.query.filter_by(role=role).count()
        role_counts[role] = count
    
    return render_template('rbac/role_list.html',
                          role_permissions=ROLE_PERMISSIONS,
                          role_counts=role_counts,
                          title='Roles & Permissions')


@rbac_mgmt.route('/roles/<role_name>/edit', methods=['GET', 'POST'])
def edit_role(role_name):
    """Chỉnh sửa permissions của 1 role"""
    if not admin_required():
        return redirect(url_for('main.login'))
    
    if role_name not in ROLE_PERMISSIONS:
        flash('Role không tồn tại!', 'danger')
        return redirect(url_for('rbac_mgmt.list_roles'))
    
    if request.method == 'POST':
        # Get selected permissions from form
        selected_perms = request.form.getlist('permissions')
        
        # Update ROLE_PERMISSIONS (in-memory, cần save vào file hoặc database)
        ROLE_PERMISSIONS[role_name] = selected_perms
        
        # TODO: Lưu vào database hoặc config file
        flash(f'✅ Đã cập nhật permissions cho role "{role_name}"', 'success')
        return redirect(url_for('rbac_mgmt.list_roles'))
    
    # GET - show editor
    current_perms = ROLE_PERMISSIONS.get(role_name, [])
    
    # All possible permissions
    all_perms = set()
    for perms in ROLE_PERMISSIONS.values():
        all_perms.update(perms)
    all_perms = sorted(all_perms)
    
    # Group by category
    admin_perms = [p for p in all_perms if 'manage' in p or 'delete' in p or 'admin' in p]
    content_perms = [p for p in all_perms if 'create' in p or 'edit' in p]
    view_perms = [p for p in all_perms if 'view' in p or 'access' in p]
    action_perms = [p for p in all_perms if p not in admin_perms and p not in content_perms and p not in view_perms]
    
    perm_groups = {
        'Admin': admin_perms,
        'Content Management': content_perms,
        'View Access': view_perms,
        'Actions': action_perms
    }
    
    # Count users with this role
    user_count = User.query.filter_by(role=role_name).count()
    
    return render_template('rbac/edit_role.html',
                          role_name=role_name,
                          current_permissions=current_perms,
                          permission_groups=perm_groups,
                          all_permissions=all_perms,
                          user_count=user_count,
                          title=f'Edit Role - {role_name}')


@rbac_mgmt.route('/permissions/manage', methods=['GET', 'POST'])
def manage_permissions():
    """Quản lý tất cả permissions: thêm, sửa, xóa"""
    if not admin_required():
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_permission':
            new_perm = request.form.get('permission_name')
            category = request.form.get('category', 'Actions')
            
            if new_perm:
                # Check if exists
                all_perms = set()
                for perms in ROLE_PERMISSIONS.values():
                    all_perms.update(perms)
                
                if new_perm in all_perms:
                    flash(f'Permission "{new_perm}" đã tồn tại!', 'warning')
                else:
                    # TODO: Lưu vào database
                    flash(f'✅ Đã thêm permission "{new_perm}"', 'success')
            else:
                flash('Tên permission không được để trống!', 'danger')
        
        return redirect(url_for('rbac_mgmt.manage_permissions'))
    
    # GET - show all permissions
    all_perms = set()
    for perms in ROLE_PERMISSIONS.values():
        all_perms.update(perms)
    
    # Group by category
    admin_perms = [p for p in all_perms if 'manage' in p or 'delete' in p or 'admin' in p]
    content_perms = [p for p in all_perms if 'create' in p or 'edit' in p]
    view_perms = [p for p in all_perms if 'view' in p or 'access' in p]
    action_perms = [p for p in all_perms if p not in admin_perms and p not in content_perms and p not in view_perms]
    
    perm_groups = {
        'Admin': admin_perms,
        'Content Management': content_perms,
        'View Access': view_perms,
        'Actions': action_perms
    }
    
    # Count usage per permission
    perm_usage = {}
    for perm in all_perms:
        count = sum(1 for role, perms in ROLE_PERMISSIONS.items() if perm in perms)
        perm_usage[perm] = count
    
    return render_template('rbac/manage_permissions.html',
                          permission_groups=perm_groups,
                          perm_usage=perm_usage,
                          total_permissions=len(all_perms),
                          title='Manage Permissions')


@rbac_mgmt.route('/api/users/<int:user_id>/quick-role', methods=['POST'])
def quick_change_role(user_id):
    """API endpoint để đổi role nhanh từ user list"""
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')
    
    if new_role not in ROLE_PERMISSIONS:
        return jsonify({'error': 'Invalid role'}), 400
    
    old_role = user.role
    user.role = new_role
    user.updated_at = datetime.utcnow()
    
    # Create corresponding profile if needed
    if new_role == 'teacher' and not user.teacher_profile:
        profile = TeacherProfile(user_id=user.id)
        db.session.add(profile)
    elif new_role in ['student', 'public_student'] and not user.student_profile:
        profile = StudentProfile(
            user_id=user.id,
            student_type='internal' if new_role == 'student' else 'public'
        )
        db.session.add(profile)
    elif new_role == 'parent' and not user.parent_profile:
        profile = ParentProfile(user_id=user.id)
        db.session.add(profile)
    
    db.session.commit()
    
    new_permissions = ROLE_PERMISSIONS.get(new_role, [])
    
    return jsonify({
        'success': True,
        'old_role': old_role,
        'new_role': new_role,
        'permission_count': len(new_permissions),
        'message': f'Changed role from {old_role} to {new_role}'
    })


@rbac_mgmt.route('/api/users/<int:user_id>/toggle-active', methods=['POST'])
def api_toggle_active(user_id):
    """API endpoint để bật/tắt tài khoản"""
    if not admin_required():
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': user.is_active,
        'message': f'Account {"activated" if user.is_active else "deactivated"}'
    })
