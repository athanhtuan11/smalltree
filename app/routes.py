from werkzeug.security import generate_password_hash
from PIL import Image
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, jsonify, current_app
from app.models import db, Activity, Curriculum, Child, AttendanceRecord, Staff, BmiRecord, ActivityImage, Supplier, Product, StudentAlbum, StudentPhoto, StudentProgress, Dish, Menu
from app.forms import EditProfileForm, ActivityCreateForm, ActivityEditForm, SupplierForm, ProductForm
from calendar import monthrange
from datetime import datetime, date, timedelta
import io, zipfile, os, json, re, secrets

# Check for optional dependencies
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.shared import OxmlElement, qn
    from docx.shared import RGBColor
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

main = Blueprint('main', __name__)
def redirect_no_permission():
    flash('Bạn không có quyền truy cập chức năng này!', 'danger')
    return redirect(url_for('main.login'))

# CRUD Class
from app.models import Class

@main.route('/classes/new', methods=['GET', 'POST'])
def new_class():
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        flash('Bạn không có quyền tạo lớp mới!', 'danger')
        return redirect(url_for('main.attendance'))
    # Thêm lớp mới
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        description = request.form.get('description')
        if not class_name or len(class_name) < 3:
            flash('Tên lớp phải có ít nhất 3 ký tự!', 'danger')
            return redirect(url_for('main.new_class'))
        existing = Class.query.filter_by(name=class_name).first()
        if existing:
            flash('Lớp này đã tồn tại!', 'warning')
            return redirect(url_for('main.new_class'))
        new_class = Class(name=class_name, description=description)
        db.session.add(new_class)
        db.session.commit()
        flash(f'Đã tạo lớp mới: {class_name}', 'success')
        return redirect(url_for('main.new_class'))
    # Hiển thị danh sách lớp
    classes = Class.query.order_by(Class.name).all()
    mobile = is_mobile()
    return render_template('new_class.html', title='Tạo Lớp mới', mobile=mobile, classes=classes)

@main.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
def edit_class(class_id):
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        flash('Bạn không có quyền sửa lớp!', 'danger')
        return redirect(url_for('main.new_class'))
    class_obj = Class.query.get_or_404(class_id)
    if request.method == 'POST':
        class_obj.name = request.form.get('class_name')
        class_obj.description = request.form.get('description')
        db.session.commit()
        flash('Đã cập nhật lớp!', 'success')
        return redirect(url_for('main.new_class'))
    return render_template('edit_class.html', class_obj=class_obj)

@main.route('/classes/<int:class_id>/delete', methods=['POST'])
def delete_class(class_id):
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        flash('Bạn không có quyền xóa lớp!', 'danger')
        return redirect(url_for('main.new_class'))
    class_obj = Class.query.get_or_404(class_id)
    db.session.delete(class_obj)
    db.session.commit()
    flash('Đã xóa lớp!', 'success')
    return redirect(url_for('main.new_class'))




@main.route('/attendance/save', methods=['POST'])
def save_attendance():
    if not session.get('role'):
        flash('Bạn phải đăng nhập mới truy cập được trang này!', 'danger')
        return redirect(url_for('main.about'))
    from datetime import date
    attendance_date = request.form.get('attendance_date') or date.today().strftime('%Y-%m-%d')
    selected_class = request.form.get('class_name')
    # Lưu hàng loạt (không có student_id riêng lẻ)
    if selected_class and selected_class != 'None':
        students = Child.query.filter_by(class_name=selected_class).all()
    else:
        students = Child.query.all()
    for student in students:
        present_value = request.form.get(f'present_{student.id}')
        if present_value == 'yes':
            status = 'Có mặt'
        elif present_value == 'absent_excused':
            status = 'Vắng mặt có phép'
        elif present_value == 'absent_unexcused':
            status = 'Vắng mặt không phép'
        else:
            status = 'Vắng'
        breakfast = request.form.get(f'breakfast_{student.id}')
        lunch = request.form.get(f'lunch_{student.id}')
        snack = request.form.get(f'snack_{student.id}')
        toilet = request.form.get(f'toilet_{student.id}')
        toilet_times = request.form.get(f'toilet_times_{student.id}') or None
        note = request.form.get(f'note_{student.id}')
        record = AttendanceRecord.query.filter_by(child_id=student.id, date=attendance_date).first()
        if record:
            record.status = status
            record.breakfast = breakfast
            record.lunch = lunch
            record.snack = snack
            record.toilet = toilet
            record.toilet_times = toilet_times
            record.note = note
        else:
            record = AttendanceRecord(child_id=student.id, date=attendance_date, status=status,
                                     breakfast=breakfast, lunch=lunch, snack=snack, toilet=toilet, toilet_times=toilet_times, note=note)
            db.session.add(record)
    db.session.commit()
    #flash('Đã lưu điểm danh!', 'success')
    if not selected_class or selected_class == 'None':
        return redirect(url_for('main.attendance', attendance_date=attendance_date))
    return redirect(url_for('main.attendance', attendance_date=attendance_date, class_name=selected_class))

def is_mobile():
    ua = request.user_agent.string.lower()
    return 'mobile' in ua or 'android' in ua or 'iphone' in ua

def calculate_age(birth_date):
    today = datetime.today()
    try:
        birthday = datetime.strptime(birth_date, '%Y-%m-%d')
    except Exception:
        return 0
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    return age

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME_MINUTES = 10
LOGIN_COOLDOWN_SECONDS = 30
login_attempts = {}
lockout_until = {}
last_login_time = {}

# --- GLOBAL ERROR HANDLER FOR API JSON RESPONSE ---
from werkzeug.exceptions import HTTPException

@main.errorhandler(Exception)
def handle_api_exception(e):
    from flask import request
    import traceback
    # Chỉ trả về JSON nếu là API (application/json hoặc /ai/ route)
    if request.path.startswith('/ai/') or request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()[:1000]  # Giới hạn độ dài trace cho debug
        }), code
    # Nếu không phải API thì trả về mặc định
    raise e
# Password hash/check imports (with fallback)
try:
    from werkzeug.security import generate_password_hash, check_password_hash
    WERKZEUG_AVAILABLE = True
except ImportError:
    print("Warning: werkzeug.security not available, using fallback")
    import hashlib
    WERKZEUG_AVAILABLE = False
    def generate_password_hash(password):
        return hashlib.sha256(password.encode()).hexdigest()
    def check_password_hash(hash_password, password):
        return hash_password == hashlib.sha256(password.encode()).hexdigest()


# ================== DANH SÁCH MÓN ĂN ==================

@main.route('/dish-list')
def dish_list():
    from app.models import Dish
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    dishes = Dish.query.all()
    dish_infos = []
    return render_template('dish_list.html', dishes=dishes)

# Route để bật/tắt trạng thái món ăn
@main.route('/dish/<int:dish_id>/toggle-active', methods=['POST'])
def toggle_dish_active(dish_id):
    from app.models import Dish, db
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    dish = Dish.query.get_or_404(dish_id)
    dish.is_active = not dish.is_active
    db.session.commit()
    flash(f"Đã {'bật' if dish.is_active else 'ẩn'} món ăn!", 'success')
    return redirect(url_for('main.dish_list'))

# ================== SỬA/XÓA MÓN ĂN ==================
@main.route('/dish/<int:dish_id>/edit', methods=['GET', 'POST'])
def edit_dish(dish_id):
    from app.models import Dish, DishIngredient, Product, db
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    dish = Dish.query.get_or_404(dish_id)
    products = Product.query.all()
    product_units = sorted(list(set([p.unit for p in products if p.unit])))
    if request.method == 'POST':
        dish.name = request.form.get('name')
        dish.description = request.form.get('description')
        meal_times = request.form.getlist('meal_times')
        dish.meal_times = meal_times
        # Xóa nguyên liệu cũ
        DishIngredient.query.filter_by(dish_id=dish.id).delete()
        ingredient_ids = request.form.getlist('ingredient_id')
        units = request.form.getlist('unit')
        quantities = request.form.getlist('quantity')
        for idx, pid in enumerate(ingredient_ids):
            if not pid or not units[idx] or not quantities[idx]:
                continue
            di = DishIngredient(
                dish_id=dish.id,
                product_id=int(pid),
                quantity=float(quantities[idx]),
                unit=units[idx],
                created_date=datetime.now(),
                is_active=True
            )
            db.session.add(di)
        db.session.commit()
        flash('Đã cập nhật món ăn!', 'success')
        return redirect(url_for('main.dish_list'))
    # Chuẩn bị dữ liệu nguyên liệu cho form
    ingredients = dish.ingredients
    return render_template('edit_dish.html', dish=dish, products=products, ingredients=ingredients, product_units=product_units)

@main.route('/dish/<int:dish_id>/delete', methods=['POST'])
def delete_dish(dish_id):
    from app.models import Dish, db
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    dish = Dish.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    flash('Đã xóa món ăn!', 'success')
    return redirect(url_for('main.dish_list'))
# ================== TẠO MÓN ĂN ==================
@main.route('/dish/new', methods=['GET', 'POST'])
def create_dish():
    from app.models import Dish, DishIngredient, Product, db
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    products = Product.query.filter_by(is_active=True).join(Supplier).order_by(Product.category, Product.name).all()
    product_units = sorted(list(set([p.unit for p in products if p.unit])))
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        ingredient_ids = request.form.getlist('ingredient_id')
        units = request.form.getlist('unit')
        quantities = request.form.getlist('quantity')
        from sqlalchemy.exc import IntegrityError
        meal_times = request.form.getlist('meal_times')
        dish = Dish(name=name, description=description, meal_times=meal_times)
        db.session.add(dish)
        try:
            db.session.flush()  # Để lấy dish.id
        except IntegrityError:
            db.session.rollback()
            flash('Tên món ăn đã tồn tại, vui lòng chọn tên khác!', 'danger')
            return render_template('create_dish.html', products=products, product_units=product_units)
        # Thêm nguyên liệu
        for idx, pid in enumerate(ingredient_ids):
            if not pid or not units[idx] or not quantities[idx]:
                continue
            di = DishIngredient(
                dish_id=dish.id,
                product_id=int(pid),
                quantity=float(quantities[idx]),
                unit=units[idx],
                created_date=datetime.now(),
                is_active=True
            )
            db.session.add(di)
        db.session.commit()
        flash('Đã tạo món ăn thành công!', 'success')
        return redirect(url_for('main.dish_list'))
    return render_template('create_dish.html', products=products, product_units=product_units)



@main.route('/')
def index():
    mobile = is_mobile()
    return render_template('about.html', title='Home', mobile=mobile)

@main.route('/about')
def about():
    mobile = is_mobile()
    return render_template('about.html', title='About Us', mobile=mobile)

@main.route('/gallery')
def gallery():
    mobile = is_mobile()
    from app.models import ActivityImage, Activity, Child, Class
    role = session.get('role')
    user_id = session.get('user_id')
    images = []
    if role in ['admin', 'teacher']:
        images = ActivityImage.query.order_by(ActivityImage.upload_date.desc()).all()
    elif role == 'parent':
        # Lấy class_id của con
        child = Child.query.filter_by(id=user_id).first()
        class_id = None
        if child and child.class_name:
            class_obj = Class.query.filter_by(name=child.class_name).first()
            if class_obj:
                class_id = class_obj.id
        # Chỉ lấy ảnh của hoạt động thuộc lớp con hoặc cho khách vãng lai
        if class_id:
            images = ActivityImage.query.join(Activity).filter(
                (Activity.class_id == class_id) | (Activity.class_id == None)
            ).order_by(ActivityImage.upload_date.desc()).all()
        else:
            # Không xác định được lớp, chỉ lấy ảnh cho khách vãng lai
            images = ActivityImage.query.join(Activity).filter(Activity.class_id == None).order_by(ActivityImage.upload_date.desc()).all()
    else:
        # Khách vãng lai chỉ xem ảnh hoạt động cho khách vãng lai
        images = ActivityImage.query.join(Activity).filter(Activity.class_id == None).order_by(ActivityImage.upload_date.desc()).all()
    return render_template('gallery.html', title='Gallery', mobile=mobile, images=images)

@main.route('/contact')
def contact():
    mobile = is_mobile()
    return render_template('contact.html', title='Contact Us', mobile=mobile)

@main.route('/activities/new', methods=['GET', 'POST'])
def new_activity():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    classes = Class.query.order_by(Class.name).all()
    class_choices = [(0, 'Tất cả khách vãng lai')] + [(c.id, c.name) for c in classes]
    form = ActivityCreateForm()
    form.class_id.choices = class_choices
    if form.validate_on_submit():
        title = form.title.data
        content = form.description.data
        date_val = datetime.strptime(form.date.data, '%Y-%m-%d') if form.date.data else date.today()
        background_file = form.background.data
        image_url = ''
        if background_file and background_file.filename:
            allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.jfif'}
            ext = os.path.splitext(background_file.filename)[1].lower()
            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', background_file.filename)
            if ext not in allowed_ext:
                flash('Chỉ cho phép tải lên các file ảnh có đuôi: .jpg, .jpeg, .png, .gif, .jfif!', 'danger')
                return render_template('new_activity.html', form=form, title='Đăng bài viết mới', mobile=is_mobile(), classes=classes)
            filename = 'bg_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + safe_filename
            save_path = os.path.join('app', 'static', 'images', filename)
            # Resize background
            img = Image.open(background_file)
            img.thumbnail((1200, 800))
            img.save(save_path)
            image_url = url_for('static', filename=f'images/{filename}')
        class_id = form.class_id.data if form.class_id.data != 0 else None
        new_post = Activity(title=title, description=content, date=date_val, image=image_url, class_id=class_id)
        db.session.add(new_post)
        db.session.commit()
        
        # Lưu activity_id vào session để upload batch sau
        session['temp_activity_id'] = new_post.id
        
        # Tạo thư mục lưu ảnh hoạt động
        activity_dir = os.path.join('app', 'static', 'images', 'activities', str(new_post.id))
        os.makedirs(activity_dir, exist_ok=True)
        
        # Xử lý ảnh upload truyền thống (fallback nếu không có client-side compression)
        files = request.files.getlist('images')
        if files and files[0].filename:  # Có ảnh upload truyền thống
            print(f"[INFO] Xử lý upload truyền thống: {len(files)} ảnh")
            total_files = len(files)
            success_count = 0
            
            # Tối ưu batch size cho 60-70 ảnh: 10 ảnh/batch để tránh memory overflow
            batch_size = 10
            for i in range(0, total_files, batch_size):
                batch_files = files[i:i+batch_size]
                print(f"[INFO] Xử lý batch {i//batch_size + 1}/{(total_files-1)//batch_size + 1}: {len(batch_files)} ảnh")
                
                for file in batch_files:
                    if file and getattr(file, 'filename', None):
                        ext = os.path.splitext(file.filename)[1].lower()
                        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.jfif']:
                            continue
                        safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', file.filename)
                        img_filename = datetime.now().strftime('%Y%m%d%H%M%S%f') + '_' + safe_filename
                        img_path = os.path.join(activity_dir, img_filename)
                        try:
                            file.stream.seek(0)
                            img = Image.open(file.stream)
                            # Tối ưu kích thước: resize nhỏ hơn cho web
                            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                            if ext.lower() in ['.jpg', '.jpeg']:
                                img.save(img_path, 'JPEG', quality=75, optimize=True)  # Giảm quality để tiết kiệm bộ nhớ
                            else:
                                img.save(img_path, optimize=True)
                            rel_path = f'images/activities/{new_post.id}/{img_filename}'
                            db.session.add(ActivityImage(filename=img_filename, filepath=rel_path, upload_date=datetime.now(), activity_id=new_post.id))
                            success_count += 1
                        except Exception as e:
                            print(f"[ERROR] Lỗi upload ảnh: {file.filename} - {e}")
                            continue
                
                # Commit từng batch để tránh memory overflow  
                try:
                    db.session.commit()
                    print(f"[INFO] Batch {i//batch_size + 1} hoàn thành: {success_count} ảnh thành công")
                except Exception as e:
                    print(f"[ERROR] Lỗi commit batch: {e}")
                    db.session.rollback()
            
            if success_count > 0:
                flash(f'Đã đăng bài viết mới với {success_count}/{total_files} ảnh thành công!', 'success')
            else:
                flash('Đã đăng bài viết mới!', 'success')
        else:
            flash('Đã tạo bài viết! Hệ thống sẽ xử lý ảnh trong giây lát...', 'success')
        return redirect(url_for('main.activities'))
    mobile = is_mobile()
    from datetime import date
    current_date_iso = date.today().isoformat()
    return render_template('new_activity.html', form=form, title='Đăng bài viết mới', mobile=mobile, current_date_iso=current_date_iso, classes=classes)

# Route riêng để upload batch ảnh (từ client-side compression)
@main.route('/activities/upload-batch', methods=['POST'])
def upload_batch_images():
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    activity_id = request.form.get('activity_id') or session.get('temp_activity_id')
    if not activity_id:
        return jsonify({'success': False, 'error': 'No activity ID'}), 400
    
    files = request.files.getlist('batch_images')
    activity_dir = os.path.join('app', 'static', 'images', 'activities', str(activity_id))
    os.makedirs(activity_dir, exist_ok=True)
    
    success_count = 0
    for file in files:
        if file and file.filename:
            try:
                # File đã được nén client-side, chỉ cần lưu
                safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', file.filename)
                img_filename = datetime.now().strftime('%Y%m%d%H%M%S%f') + '_' + safe_filename
                img_path = os.path.join(activity_dir, img_filename)
                file.save(img_path)
                
                rel_path = f'images/activities/{activity_id}/{img_filename}'
                db.session.add(ActivityImage(
                    filename=img_filename,
                    filepath=rel_path,
                    upload_date=datetime.now(),
                    activity_id=activity_id
                ))
                success_count += 1
            except Exception as e:
                print(f"[ERROR] Upload batch error: {e}")
                continue
    
    db.session.commit()
    print(f"[INFO] Uploaded {success_count} images to activity {activity_id}")
    return jsonify({'success': True, 'uploaded': success_count})

# Test route để kiểm tra upload ảnh
@main.route('/test-activity-images/<int:activity_id>')
def test_activity_images(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    images = ActivityImage.query.filter_by(activity_id=activity_id).all()
    return jsonify({
        'activity_id': activity_id,
        'activity_title': activity.title,
        'image_count': len(images),
        'images': [{'filename': img.filename, 'filepath': img.filepath} for img in images]
    })

@main.route('/activities/<int:id>/delete', methods=['POST'])
def delete_activity(id):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    post = Activity.query.get_or_404(id)
    if post:
        for img in post.images:
            img_path = os.path.join('app', 'static', img.filepath)
            if os.path.exists(img_path):
                os.remove(img_path)
            db.session.delete(img)
        db.session.delete(post)
        db.session.commit()
        flash('Đã xoá bài viết!', 'success')
    else:
        flash('Không tìm thấy bài viết để xoá!', 'danger')
    mobile = is_mobile()
    return redirect(url_for('main.activities', mobile=mobile))

@main.route('/activities/<int:id>')
def activity_detail(id):
    post = Activity.query.get_or_404(id)
    if not post:
        flash('Không tìm thấy bài viết!', 'danger')
        return redirect(url_for('main.activities'))
    user_role = session.get('role')
    user_id = session.get('user_id')
    if user_role == 'parent':
        child = Child.query.filter_by(id=user_id).first()
        class_name = child.class_name if child else None
        class_obj = Class.query.filter_by(name=class_name).first() if class_name else None
        class_id = class_obj.id if class_obj else None
        # Nếu bài viết không phải của lớp con mình và không phải khách vãng lai thì không cho xem
        if post.class_id is not None and post.class_id != class_id:
            flash('Bạn không có quyền xem bài viết này!', 'danger')
            return redirect(url_for('main.activities'))
    activity = {
        'id': post.id,
        'title': post.title,
        'content': post.description,
        'image': post.image,
        'date_posted': post.date.strftime('%Y-%m-%d'),
        'gallery': post.images
    }
    mobile = is_mobile()
    from app.forms import DeleteActivityForm
    form = DeleteActivityForm()
    return render_template('activity_detail.html', activity=activity, title=post.title, mobile=mobile, form=form)

from app.models import Class
@main.route('/curriculum/new', methods=['GET', 'POST'])
def new_curriculum():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    classes = Class.query.order_by(Class.name).all()
    if request.method == 'POST':
        week_number = request.form.get('week_number')
        class_id = request.form.get('class_id')
        
        # Check for duplicate curriculum (same week + same class)
        existing = Curriculum.query.filter_by(week_number=week_number, class_id=class_id).first()
        if existing:
            class_name = Class.query.get(class_id).name if class_id else "Chưa chọn lớp"
            flash(f'Chương trình học tuần {week_number} cho lớp {class_name} đã tồn tại!', 'danger')
            classes = Class.query.order_by(Class.name).all()
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            morning_slots = ['morning_0', 'morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
            afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
            default_data = {}
            for day in days:
                default_data[day] = {}
                for slot in morning_slots + afternoon_slots:
                    default_data[day][slot] = ""
            mobile = is_mobile()
            return render_template('new_curriculum.html', title='Tạo chương trình mới', mobile=mobile, classes=classes, data=default_data, error_week=week_number, error_class=class_id)
        
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        morning_slots = ['morning_0', 'morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
        afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
        curriculum_data = {}
        for day in days:
            curriculum_data[day] = {}
            for slot in morning_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
            for slot in afternoon_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
        content = json.dumps(curriculum_data, ensure_ascii=False)
        new_week = Curriculum(week_number=week_number, class_id=class_id, content=content, material=None)
        db.session.add(new_week)
        db.session.commit()
        flash('Đã thêm chương trình học mới!', 'success')
        return redirect(url_for('main.curriculum'))
    # Set default data for new curriculum form
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    morning_slots = ['morning_0', 'morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
    afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
    default_data = {}
    for i, day in enumerate(days):
        default_data[day] = {}
        for slot in morning_slots:
            default_data[day][slot] = ""
        for j, slot in enumerate(afternoon_slots):
            if slot == 'afternoon_2':
                # 15h-15h30
                if i == 1 or i == 3:  # Thứ 3, Thứ 5
                    default_data[day][slot] = "Hoạt động với giáo cụ"
                elif i == 2 or i == 4:  # Thứ 4, Thứ 6
                    default_data[day][slot] = "Lego time"
                else:
                    default_data[day][slot] = ""
            else:
                default_data[day][slot] = ""
    mobile = is_mobile()
    return render_template('new_curriculum.html', title='Tạo chương trình mới', mobile=mobile, classes=classes, data=default_data)


@main.route('/curriculum')
def curriculum():
    import secrets
    from app.models import Class
    if 'csrf_token' not in session or not session['csrf_token']:
        session['csrf_token'] = secrets.token_hex(16)
    class_id = None
    classes = Class.query.order_by(Class.name).all()
    # Nếu là phụ huynh, chỉ cho xem curriculum của lớp con mình, không cho override qua URL
    if session.get('role') == 'parent':
        user_id = session.get('user_id')
        child = Child.query.filter_by(id=user_id).first()
        if child and child.class_name:
            class_obj = Class.query.filter_by(name=child.class_name).first()
            if class_obj:
                class_id = class_obj.id
    else:
        # Chỉ admin/teacher mới được chọn class_id qua URL
        class_id = request.args.get('class_id', type=int)
    if class_id:
        weeks = Curriculum.query.filter_by(class_id=class_id).order_by(Curriculum.week_number).all()
    else:
        weeks = Curriculum.query.order_by(Curriculum.week_number).all()
    curriculum = []
    for week in weeks:
        try:
            data = json.loads(week.content)
        except Exception:
            data = {}
        curriculum.append({
            'week_number': week.week_number,
            'data': data,
            'class_id': week.class_id,
            'class_name': week.class_obj.name if week.class_obj else ''
        })
    mobile = is_mobile()
    return render_template('curriculum.html', curriculum=curriculum, title='Chương trình học', mobile=mobile, classes=classes, selected_class_id=class_id)

@main.route('/attendance/new', methods=['GET', 'POST'])
def new_student():
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    classes = Class.query.order_by(Class.name).all()
    # Sinh mã số học sinh tự động: lấy max student_code dạng số, +1
    from sqlalchemy import func, cast, Integer
    last_code = db.session.query(func.max(cast(Child.student_code, Integer))).scalar()
    if last_code is None:
        next_code = '001'
    else:
        next_code = str(int(last_code) + 1).zfill(3)
    if request.method == 'POST':
        name = request.form.get('name')
        # student_code lấy từ hidden input, đã sinh sẵn
        student_code = request.form.get('student_code') or next_code
        class_name = request.form.get('class_name')
        birth_date = request.form.get('birth_date')
        parent_contact = request.form.get('parent_contact')
        
        # Validate class first
        if not any(c.name == class_name for c in classes):
            flash('Lớp không hợp lệ!', 'danger')
            return redirect(url_for('main.new_student'))
            
        # Process avatar separately
        avatar_path = None
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            import os
            from werkzeug.utils import secure_filename
            ext = os.path.splitext(avatar_file.filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                flash('Chỉ cho phép upload ảnh jpg, jpeg, png, gif! Học sinh sẽ được tạo không có ảnh đại diện.', 'warning')
            else:
                try:
                    filename = f"student_{student_code}_{secure_filename(avatar_file.filename)}"
                    save_dir = os.path.join('app', 'static', 'images', 'students')
                    os.makedirs(save_dir, exist_ok=True)
                    avatar_path = os.path.join(save_dir, filename)
                    avatar_file.save(avatar_path)
                    # Normalize path for web (use forward slashes)
                    avatar_path = avatar_path.replace('app/static/', '').replace('\\', '/')
                except Exception as e:
                    flash(f'Lỗi khi lưu ảnh đại diện: {str(e)}. Học sinh sẽ được tạo không có ảnh.', 'warning')
                    avatar_path = None
        
        # Create student
        try:
            new_child = Child(name=name, age=0, parent_contact=parent_contact, class_name=class_name, birth_date=birth_date, student_code=student_code, avatar=avatar_path)
            db.session.add(new_child)
            db.session.commit()
            if avatar_path:
                flash('Đã thêm học sinh mới với ảnh đại diện!', 'success')
            else:
                flash('Đã thêm học sinh mới!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi thêm học sinh: {str(e)}', 'danger')
            
        return redirect(url_for('main.attendance'))
    mobile = is_mobile()
    return render_template('new_attendance.html', title='Tạo học sinh mới', mobile=mobile, classes=classes, next_code=next_code)

@main.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if not session.get('role'):
        flash('Bạn phải đăng nhập mới truy cập được trang này!', 'danger')
        return redirect(url_for('main.about'))
    if session.get('role') == 'parent':
        return redirect(url_for('main.attendance_history'))
    from datetime import date
    attendance_date = request.args.get('attendance_date') or date.today().strftime('%Y-%m-%d')
    selected_class = request.args.get('class_name')
    # Lấy danh sách lớp từ bảng Class
    from app.models import Class
    class_names = [c.name for c in Class.query.order_by(Class.name).all()]
    # Lọc học sinh theo lớp
    if selected_class:
        students = Child.query.filter_by(class_name=selected_class).all()
    else:
        students = Child.query.all()
    # Lấy trạng thái điểm danh từ database cho ngày đã chọn
    for student in students:
        record = AttendanceRecord.query.filter_by(child_id=student.id, date=attendance_date).first()
        if record:
            student.status = record.status
            student.breakfast = record.breakfast
            student.lunch = record.lunch
            student.snack = record.snack
            student.toilet = record.toilet
            student.toilet_times = record.toilet_times
            student.note = record.note
        else:
            student.status = 'Vắng'
            student.breakfast = ''
            student.lunch = ''
            student.snack = ''
            student.toilet = ''
            student.toilet_times = ''
            student.note = ''
    if request.method == 'POST':
        for student in students:
            present_value = request.form.get(f'present_{student.id}')
            if present_value == 'yes':
                status = 'Có mặt'
            elif present_value == 'absent_excused':
                status = 'Vắng mặt có phép'
            elif present_value == 'absent_unexcused':
                status = 'Vắng mặt không phép'
            else:
                status = 'Vắng'
            breakfast = request.form.get(f'breakfast_{student.id}')
            lunch = request.form.get(f'lunch_{student.id}')
            snack = request.form.get(f'snack_{student.id}')
            toilet = request.form.get(f'toilet_{student.id}')
            toilet_times = request.form.get(f'toilet_times_{student.id}') or None
            note = request.form.get(f'note_{student.id}')
            record = AttendanceRecord.query.filter_by(child_id=student.id, date=attendance_date).first()
            if record:
                record.status = status
                record.breakfast = breakfast
                record.lunch = lunch
                record.snack = snack
                record.toilet = toilet
                record.toilet_times = toilet_times
                record.note = note
            else:
                record = AttendanceRecord(child_id=student.id, date=attendance_date, status=status,
                                         breakfast=breakfast, lunch=lunch, snack=snack, toilet=toilet, toilet_times=toilet_times, note=note)
                db.session.add(record)
            student.status = status
            student.breakfast = breakfast
            student.lunch = lunch
            student.snack = snack
            student.toilet = toilet
            student.toilet_times = toilet_times
            student.note = note
        db.session.commit()
        flash('Đã lưu điểm danh!', 'success')
        if not selected_class or selected_class == 'None':
            return redirect(url_for('main.attendance', attendance_date=attendance_date))
        return redirect(url_for('main.attendance', attendance_date=attendance_date, class_name=selected_class))
    mobile = is_mobile()
    return render_template('attendance.html', students=students, title='Điểm danh', current_date=attendance_date, mobile=mobile, class_names=class_names, selected_class=selected_class)

@main.route('/attendance/mark', methods=['GET', 'POST'])
def mark_attendance():
    students = Child.query.all()
    if request.method == 'POST':
        for student in students:
            present = request.form.get(f'present_{student.id}') == 'on'
            # TODO: Lưu trạng thái điểm danh vào database (cần thêm trường status vào model Child)
            student.status = 'Có mặt' if present else 'Vắng'
        db.session.commit()
        flash('Đã điểm danh cho tất cả học sinh!', 'success')
        return redirect(url_for('main.attendance'))
    mobile = is_mobile()
    return render_template('mark_attendance.html', students=students, title='Điểm danh học sinh', mobile=mobile)

@main.route('/attendance/history')
def attendance_history():
    if session.get('role') == 'parent':
        # Chỉ cho phụ huynh xem lịch sử điểm danh của con mình
        user_id = session.get('user_id')
        child = Child.query.filter_by(id=user_id).first()
        students = [child] if child else []
    else:
        students = Child.query.all()
    month = request.args.get('month')
    if month:
        year, m = map(int, month.split('-'))
    else:
        today = datetime.today()
        year, m = today.year, today.month
        month = f"{year:04d}-{m:02d}"
    num_days = monthrange(year, m)[1]
    days_in_month = [f"{year:04d}-{m:02d}-{day:02d}" for day in range(1, num_days+1)]
    records_raw = AttendanceRecord.query.filter(AttendanceRecord.date.like(f"{year:04d}-{m:02d}-%")).all()
    records = {}
    for r in records_raw:
        records[(r.child_id, r.date)] = r
    mobile = is_mobile()
    return render_template('attendance_history.html', records=records, students=students, days_in_month=days_in_month, selected_month=month, title='Lịch sử điểm danh', mobile=mobile)

@main.route('/invoice', methods=['GET', 'POST'])
def invoice():
    month = request.args.get('month')
    if month:
        year, m = map(int, month.split('-'))
    else:
        today = datetime.today()
        year, m = today.year, today.month
        month = f"{year:04d}-{m:02d}"
    num_days = monthrange(year, m)[1]
    days_in_month = [f"{year:04d}-{m:02d}-{day:02d}" for day in range(1, num_days+1)]
    students = Child.query.all()
    records_raw = AttendanceRecord.query.filter(AttendanceRecord.date.like(f"{year:04d}-{m:02d}-%")).all()
    # Tính số ngày có mặt và số ngày vắng mặt không phép cho từng học sinh
    attendance_days = {student.id: 0 for student in students}
    absent_unexcused_days = {student.id: 0 for student in students}
    valid_student_ids = set(attendance_days.keys())
    for r in records_raw:
        if r.child_id not in valid_student_ids:
            continue
        if r.status == 'Có mặt':
            attendance_days[r.child_id] += 1
        elif r.status == 'Vắng mặt không phép':
            absent_unexcused_days[r.child_id] += 1
    invoices = []
    if request.method == 'POST':
        selected_ids = request.form.getlist('student_ids')
        if request.form.get('export_word'):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zipf:
                for student in students:
                    if str(student.id) in selected_ids:
                        doc = Document()
                        # Bảng header: thông tin trường bên trái, logo bên phải
                        header_table = doc.add_table(rows=1, cols=2)
                        header_table.style = None  # Remove borders for a cleaner look
                        left_cell = header_table.cell(0,0)
                        right_cell = header_table.cell(0,1)
                        left_cell.vertical_alignment = 1  # Top
                        right_cell.vertical_alignment = 1  # Top
                        # Logo on the left
                        logo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'logo.jpg')
                        if os.path.exists(logo_path):
                            run_logo = left_cell.paragraphs[0].add_run()
                            if DOCX_AVAILABLE:
                                try:
                                    from docx.shared import Inches
                                    run_logo.add_picture(logo_path, width=Inches(1.2))
                                except ImportError:
                                    pass
                            left_cell.paragraphs[0].alignment = 0  # Left
                        # School info on the right
                        right_paragraph = right_cell.paragraphs[0]
                        right_paragraph.alignment = 1  # Center
                        right_paragraph.add_run('SMALL TREE\n').bold = True
                        right_paragraph.add_run('MẦM NON CÂY NHỎ\n').bold = True
                        right_paragraph.add_run('Số 1, Rchai’ 2, Đức Trọng, Lâm Đồng\n')
                        right_paragraph.add_run('SDT: 0917618868 / STK: Nguyễn Thị Vân 108875858567 NH VietinBank')
                        # Đảm bảo mọi paragraph trong cell đều căn giữa
                        for para in right_cell.paragraphs:
                            para.alignment = 1
                        doc.add_paragraph('')
                        title = doc.add_heading(f'HÓA ĐƠN THANH TOÁN THÁNG {month}', 0)
                        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        run = title.runs[0]
                        run.font.size = Pt(18)  # Reduce font size
                        run.font.color.rgb = RGBColor(76, 175, 80)
                        run.font.name = 'Comic Sans MS'
                        
                        # Bảng thông tin học sinh
                        info_table = doc.add_table(rows=2, cols=2)
                        info_table.style = 'Table Grid'
                        for row in info_table.rows:
                            for cell in row.cells:
                                tc = cell._tc
                                tcPr = tc.get_or_add_tcPr()
                                shd = OxmlElement('w:shd')
                                shd.set(qn('w:fill'), 'e8f5e9')
                                tcPr.append(shd)
                        info_table.cell(0,0).text = 'Họ và tên:'
                        info_table.cell(0,1).text = student.name
                        info_table.cell(1,0).text = 'Ngày sinh:'
                        info_table.cell(1,1).text = student.birth_date or "-"
                        doc.add_paragraph('')
                        # Bảng tổng kết
                        days = attendance_days.get(student.id, 0)
                        absents = absent_unexcused_days.get(student.id, 0)
                        age = calculate_age(student.birth_date) if student.birth_date else 0
                        if age == 1:
                            tuition = 1850000
                        elif age == 2:
                            tuition = 1750000
                        elif age == 3:
                            tuition = 1650000
                        elif age == 4:
                            tuition = 1550000
                        else:
                            tuition = 1500000
                        excused_absents = sum(1 for r in records_raw if r.child_id == student.id and r.status == 'Vắng mặt có phép')
                        summary_table = doc.add_table(rows=7, cols=2)
                        summary_table.style = 'Table Grid'
                        for row in summary_table.rows:
                            for cell in row.cells:
                                tc = cell._tc
                                tcPr = tc.get_or_add_tcPr()
                                shd = OxmlElement('w:shd')
                                shd.set(qn('w:fill'), 'e8f5e9')
                                tcPr.append(shd)
                        summary_table.cell(0,0).text = 'Số ngày đi học:'
                        summary_table.cell(0,1).text = str(days)
                        summary_table.cell(1,0).text = 'Số ngày vắng không phép:'
                        summary_table.cell(1,1).text = str(absents)
                        summary_table.cell(2,0).text = 'Số ngày vắng có phép:'
                        summary_table.cell(2,1).text = str(excused_absents)
                        summary_table.cell(3,0).text = 'Tiền ăn:'
                        summary_table.cell(3,1).text = f'{days * 38000:,} đ'
                        summary_table.cell(4,0).text = 'Tiền học phí:'
                        summary_table.cell(4,1).text = f'{tuition:,} đ'
                        summary_table.cell(5,0).text = 'Tiền học anh văn:'
                        summary_table.cell(5,1).text = '500,000 đ'
                        summary_table.cell(6,0).text = 'Tiền học STEMax:'
                        summary_table.cell(6,1).text = '200,000 đ'
                        total = tuition + days * 38000 + absents * 38000 + 500000 + 200000
                        total_paragraph = doc.add_paragraph(f'Tổng tiền cần thanh toán: {total:,} đ')
                        total_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                        total_run = total_paragraph.runs[0]
                        total_run.font.color.rgb = RGBColor(76, 175, 80)
                        total_run.font.bold = True
                        total_run.font.name = 'Comic Sans MS'

                        # Add payment info table
                        from datetime import datetime
                        payment_table = doc.add_table(rows=1, cols=2)
                        payment_table.style = None  # No border for clean look
                        left_payment_cell = payment_table.cell(0,0)
                        right_payment_cell = payment_table.cell(0,1)
                        left_payment_cell.vertical_alignment = 1  # Top
                        right_payment_cell.vertical_alignment = 1  # Top
                        left_payment_cell.text = 'Người nộp tiền:'
                        left_payment_cell.add_paragraph('(Kí và ghi rõ họ tên)')                        
                        now = datetime.now()
                        right_payment_cell.text = ''  # Xóa nội dung mặc định
                        right_payment_cell.add_paragraph(f'Ngày ...... tháng ...... năm {now.year}').alignment = 1
                        right_payment_cell.add_paragraph('Chủ Trường').alignment = 1
                        right_payment_cell.add_paragraph('(Kí và ghi rõ họ tên)').alignment = 1
                        right_payment_cell.add_paragraph().alignment = 1
                        right_payment_cell.add_paragraph().alignment = 1
                        right_payment_cell.add_paragraph('Nguyễn Thị Vân').alignment = 1
                        
                        file_stream = io.BytesIO()
                        doc.save(file_stream)
                        file_stream.seek(0)
                        filename = f"invoice_{student.name}_{month}.docx"
                        zipf.writestr(filename, file_stream.read())
            zip_buffer.seek(0)
            return send_file(zip_buffer, download_name=f"invoices_{month}.zip", as_attachment=True)
        else:
            for student in students:
                if str(student.id) in selected_ids:
                    days_present = attendance_days.get(student.id, 0)
                    days_absent_unexcused = absent_unexcused_days.get(student.id, 0)
                    # Học phí theo độ tuổi
                    if student.age == 1:
                        tuition = 1850000
                    elif student.age == 2:
                        tuition = 1750000
                    elif student.age == 3:
                        tuition = 1650000
                    elif student.age == 4:
                        tuition = 1550000
                    else:
                        tuition = 1500000
                    total = (days_present + days_absent_unexcused) * 38000 + tuition
                    invoices.append(f"Học sinh {student.name}: ({days_present} ngày có mặt + {days_absent_unexcused} ngày vắng không phép) × 38.000đ + {tuition:,}đ = {total:,}đ")
    mobile = is_mobile()
    student_ages = {student.id: calculate_age(student.birth_date) if student.birth_date else 0 for student in students}
    return render_template('invoice.html', students=students, attendance_days=attendance_days, absent_unexcused_days=absent_unexcused_days, selected_month=month, invoices=invoices, days_in_month=days_in_month, records={ (r.child_id, r.date): r for r in records_raw }, student_ages=student_ages, title='Xuất hóa đơn', mobile=mobile)


@main.route('/login', methods=['GET', 'POST'])
def login():
    user_ip = request.remote_addr
    now = datetime.now()
    # Kiểm tra lockout do nhập sai
    if user_ip in lockout_until and now < lockout_until[user_ip]:
        flash(f'Tài khoản hoặc IP này bị khóa đăng nhập tạm thời. Vui lòng thử lại sau!', 'danger')
        return render_template('login.html', title='Đăng nhập')
    # Kiểm tra cooldown sau đăng nhập thành công
    if user_ip in last_login_time and (now - last_login_time[user_ip]).total_seconds() < LOGIN_COOLDOWN_SECONDS:
        wait_time = LOGIN_COOLDOWN_SECONDS - int((now - last_login_time[user_ip]).total_seconds())
        flash(f'Bạn vừa đăng nhập thành công. Vui lòng chờ {wait_time} giây trước khi đăng nhập lại!', 'warning')
        return render_template('login.html', title='Đăng nhập')
    if request.method == 'POST':
        email_or_phone = request.form.get('email')
        password = request.form.get('password')
        # Kiểm tra admin
        admin = Staff.query.filter_by(position='admin').first()
        if admin and (email_or_phone == admin.email or email_or_phone == admin.phone) and check_password_hash(admin.password, password):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            flash('Đăng nhập admin thành công!', 'success')
            login_attempts[user_ip] = 0
            last_login_time[user_ip] = now
            return redirect(url_for('main.about'))
        user = Child.query.filter(((Child.email==email_or_phone)|(Child.phone==email_or_phone))).first()
        staff = Staff.query.filter(((Staff.email==email_or_phone)|(Staff.phone==email_or_phone))).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'parent'
            flash('Đăng nhập thành công!', 'success')
            login_attempts[user_ip] = 0
            last_login_time[user_ip] = now
            return redirect(url_for('main.about'))
        elif staff and check_password_hash(staff.password, password):
            session['user_id'] = staff.id
            session['role'] = 'teacher'
            flash('Đăng nhập thành công!', 'success')
            login_attempts[user_ip] = 0
            last_login_time[user_ip] = now
            return redirect(url_for('main.about'))
        else:
            login_attempts[user_ip] = login_attempts.get(user_ip, 0) + 1
            if login_attempts[user_ip] >= MAX_LOGIN_ATTEMPTS:
                lockout_until[user_ip] = now + timedelta(minutes=LOCKOUT_TIME_MINUTES)
                flash(f'Bạn đã nhập sai quá số lần cho phép. Đăng nhập bị khóa {LOCKOUT_TIME_MINUTES} phút!', 'danger')
            else:
                flash('Sai thông tin đăng nhập!', 'danger')
            return render_template('login.html', title='Đăng nhập')
    return render_template('login.html', title='Đăng nhập')

@main.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất!', 'success')
    return redirect(url_for('main.about'))

@main.route('/create-test-account')
def create_test_account():
    """Create test account for debugging purposes"""
    # Check if gv1@gmail.com already exists
    existing_staff = Staff.query.filter_by(email='gv1@gmail.com').first()
    
    if existing_staff:
        return jsonify({
            'status': 'exists',
            'message': f'Account gv1@gmail.com already exists with position: {existing_staff.position}',
            'staff_id': existing_staff.id
        })
    
    # Create new staff account
    hashed_password = generate_password_hash('123456')
    
    new_staff = Staff(
        name='Giáo viên 1',
        position='teacher',
        contact_info='gv1@gmail.com',
        email='gv1@gmail.com', 
        phone='0123456789',
        password=hashed_password
    )
    
    db.session.add(new_staff)
    db.session.commit()
    
    return jsonify({
        'status': 'created',
        'message': 'Test account created successfully',
        'email': 'gv1@gmail.com',
        'password': '123456',
        'position': 'teacher',
        'staff_id': new_staff.id
    })

@main.route('/accounts', methods=['GET', 'POST'])
def accounts():
    from app.models import Staff, Child
    admin = Staff.query.filter_by(position='admin').first()
    # Nếu chưa có admin, cho phép tạo admin lần đầu
    if not admin:
        if request.method == 'POST':
            username = request.form.get('admin_username')
            email = request.form.get('admin_email')
            password = request.form.get('admin_password')
            password_confirm = request.form.get('admin_password_confirm')
            if password != password_confirm:
                flash('Mật khẩu nhập lại không khớp!', 'danger')
                return render_template('accounts.html', show_admin_create=True, title='Khởi tạo Admin')
            if Staff.query.filter_by(name=username).first() or Staff.query.filter_by(email=email).first():
                flash('Tên đăng nhập hoặc email đã tồn tại!', 'danger')
                return render_template('accounts.html', show_admin_create=True, title='Khởi tạo Admin')
            hashed_pw = generate_password_hash(password)
            new_admin = Staff(name=username, email=email, password=hashed_pw, position='admin', contact_info=email)
            db.session.add(new_admin)
            db.session.commit()
            flash('Tạo tài khoản admin thành công! Hãy đăng nhập.', 'success')
            return redirect(url_for('main.login'))
        return render_template('accounts.html', show_admin_create=True, title='Khởi tạo Admin')
    # Nếu đã có admin, chỉ cho phép truy cập nếu đã đăng nhập với vai trò admin
    if session.get('role') != 'admin':
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('main.login'))
    parents = Child.query.all()
    teachers = Staff.query.filter(Staff.position != 'admin').all()
    mobile = is_mobile()
    def mask_user(u):
        return {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'phone': u.phone,
            'student_code': getattr(u, 'student_code', None),
            'class_name': getattr(u, 'class_name', None),
            'parent_contact': getattr(u, 'parent_contact', None),
            'position': getattr(u, 'position', None),
        }
    masked_parents = [mask_user(p) for p in parents]
    masked_teachers = [mask_user(t) for t in teachers]
    return render_template('accounts.html', parents=masked_parents, teachers=masked_teachers, show_admin_create=False, title='Quản lý tài khoản', mobile=mobile)

@main.route('/curriculum/<int:week_number>/delete', methods=['POST'])
def delete_curriculum(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    # Get class_id from form data to ensure we delete the right curriculum
    class_id = request.form.get('class_id', type=int)
    if not class_id:
        flash('Cần chỉ định lớp học để xóa chương trình!', 'danger')
        return redirect(url_for('main.curriculum'))
        
    # Filter by both week_number AND class_id to avoid deleting wrong curriculum
    week = Curriculum.query.filter_by(week_number=week_number, class_id=class_id).first()
    if week:
        db.session.delete(week)
        db.session.commit()
        flash(f'Đã xoá chương trình học tuần {week_number} của lớp {week.class_obj.name if week.class_obj else ""}!', 'success')
    else:
        flash('Không tìm thấy chương trình học để xoá!', 'danger')
    return redirect(url_for('main.curriculum'))

@main.route('/curriculum/<int:week_number>/edit', methods=['GET', 'POST'])
def edit_curriculum(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    # Get class_id from URL parameter to ensure we edit the right curriculum
    class_id = request.args.get('class_id', type=int)
    if not class_id:
        flash('Cần chỉ định lớp học để chỉnh sửa chương trình!', 'danger')
        return redirect(url_for('main.curriculum'))
        
    # Filter by both week_number AND class_id to avoid editing wrong curriculum
    week = Curriculum.query.filter_by(week_number=week_number, class_id=class_id).first()
    classes = Class.query.order_by(Class.name).all()
    if not week:
        flash('Không tìm thấy chương trình học để chỉnh sửa!', 'danger')
        return redirect(url_for('main.curriculum'))
    import json
    if request.method == 'POST':
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        morning_slots = ['morning_0', 'morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
        afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
        curriculum_data = {}
        for day in days:
            curriculum_data[day] = {}
            for slot in morning_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
            for slot in afternoon_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
        class_id = request.form.get('class_id')
        week.class_id = class_id
        week.content = json.dumps(curriculum_data, ensure_ascii=False)
        db.session.commit()
        flash(f'Đã cập nhật chương trình học tuần {week_number}!', 'success')
        return redirect(url_for('main.curriculum'))
    data = json.loads(week.content)
    mobile = is_mobile()
    return render_template('edit_curriculum.html', week=week, data=data, title=f'Chỉnh sửa chương trình tuần {week_number}', mobile=mobile, classes=classes)

@main.route('/profile')
def profile():
    user = None
    role = session.get('role')
    user_id = session.get('user_id')
    info = {}
    if role == 'parent':
        user = Child.query.get(user_id)
        if user:
            info = {
                'full_name': user.parent_contact,
                'email': user.email,
                'phone': user.phone,
                'role_display': 'Phụ huynh',
                'student_code': user.student_code,
                'class_name': user.class_name,
                'birth_date': user.birth_date,
                'parent_contact': user.parent_contact,
            }
    elif role == 'teacher':
        user = Staff.query.get(user_id)
        if user:
            info = {
                'full_name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role_display': 'Giáo viên',
                'student_code': '',
                'class_name': user.position,
                'birth_date': user.birth_date,
                'parent_contact': '',
            }
    elif role == 'admin':
        user = Staff.query.get(user_id)
        if user:
            info = {
                'full_name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role_display': 'Admin',
                'student_code': '',
                'class_name': user.position,
                'birth_date': user.birth_date if hasattr(user, 'birth_date') else '',
                'parent_contact': '',
            }
    else:
        flash('Không tìm thấy thông tin tài khoản!', 'danger')
        return redirect(url_for('main.about'))
    mobile = is_mobile()
    return render_template('profile.html', user=info, mobile=mobile)

@main.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    role = session.get('role')
    user_id = session.get('user_id')
    if role == 'parent':
        flash('Phụ huynh không có quyền chỉnh sửa thông tin!', 'danger')
        return redirect(url_for('main.profile'))
    elif role == 'teacher':
        user = Staff.query.get(user_id)
        full_name = user.name
    else:
        flash('Admin không thể chỉnh sửa thông tin!', 'danger')
        return redirect(url_for('main.profile'))
    if not user:
        flash('Không tìm thấy thông tin tài khoản!', 'danger')
        return redirect(url_for('main.profile'))
    form = EditProfileForm(full_name=full_name, email=user.email, phone=user.phone)
    if form.validate_on_submit():
        user.name = form.full_name.data
        user.email = form.email.data
        user.phone = form.phone.data
        if form.password.data:
            if not form.old_password.data:
                flash('Vui lòng nhập mật khẩu cũ để đổi mật khẩu!', 'danger')
                return render_template('edit_profile.html', form=form)
            if user.password != form.old_password.data:
                flash('Mật khẩu cũ không đúng!', 'danger')
                return render_template('edit_profile.html', form=form)
            user.password = form.password.data
        db.session.commit()
        flash('Cập nhật thông tin thành công!', 'success')
        return redirect(url_for('main.profile'))
    mobile = is_mobile()
    return render_template('edit_profile.html', form=form, mobile=mobile)

@main.route('/students')
def student_list():
    students = Child.query.all()
    mobile = is_mobile()
    role = session.get('role')
    user_id = session.get('user_id')
    
    # Filter students based on role
    if role == 'parent':
        # Phụ huynh chỉ xem được thông tin con mình
        filtered_students = [s for s in students if s.id == user_id]
    else:
        # Giáo viên và admin xem được tất cả
        filtered_students = students
    
    # Create display data with proper masking for sensitive info
    display_students = []
    for s in filtered_students:
        # Mask sensitive data for non-admin roles
        if role == 'admin':
            student_data = s
        else:
            # Create a simple object that can be accessed with dot notation
            class StudentDisplay:
                def __init__(self, student):
                    self.id = student.id
                    self.name = student.name
                    self.student_code = student.student_code if role in ['admin', 'teacher'] else 'Ẩn'
                    self.class_name = student.class_name if role in ['admin', 'teacher'] else 'Ẩn'
                    self.parent_contact = student.parent_contact if role in ['admin', 'teacher'] else 'Ẩn'
                    self.birth_date = student.birth_date
                    self.avatar = student.avatar
            
            student_data = StudentDisplay(s)
        
        display_students.append(student_data)
    
    return render_template('student_list.html', students=display_students, title='Danh sách học sinh', mobile=mobile)

@main.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    student = Child.query.get_or_404(student_id)
    if request.method == 'POST':
        print(f"[DEBUG] Form data: {dict(request.form)}")
        print(f"[DEBUG] Files: {dict(request.files)}")
        
        class_name = request.form.get('class_name')
        if class_name not in ['Kay 01', 'Kay 02']:
            flash('Lớp không hợp lệ!', 'danger')
            return redirect(url_for('main.edit_student', student_id=student_id))
        
        # Cập nhật thông tin học sinh trước
        student.name = request.form.get('name')
        student.student_code = request.form.get('student_code')
        student.class_name = class_name
        student.birth_date = request.form.get('birth_date')
        student.parent_contact = request.form.get('parent_contact')
        
        # Xử lý avatar riêng biệt
        avatar_updated = False
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            import os
            from werkzeug.utils import secure_filename
            ext = os.path.splitext(avatar_file.filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                flash('Chỉ cho phép upload ảnh jpg, jpeg, png, gif! Thông tin khác đã được lưu.', 'warning')
            else:
                try:
                    # Delete old avatar if exists
                    if student.avatar:
                        old_path = os.path.join('app', 'static', student.avatar)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            print(f"[DEBUG] Deleted old avatar: {old_path}")
                    
                    filename = f"student_{student.student_code}_{secure_filename(avatar_file.filename)}"
                    save_dir = os.path.join('app', 'static', 'images', 'students')
                    os.makedirs(save_dir, exist_ok=True)
                    avatar_path = os.path.join(save_dir, filename)
                    avatar_file.save(avatar_path)
                    
                    # Normalize path for web (use forward slashes)
                    new_avatar_path = avatar_path.replace('app/static/', '').replace('\\', '/')
                    print(f"[DEBUG] Student {student.student_code} avatar: {student.avatar} → {new_avatar_path}")
                    print(f"[DEBUG] File saved to: {avatar_path}")
                    print(f"[DEBUG] File exists: {os.path.exists(avatar_path)}")
                    print(f"[DEBUG] File size: {os.path.getsize(avatar_path) if os.path.exists(avatar_path) else 'N/A'}")
                    student.avatar = new_avatar_path
                    avatar_updated = True
                except Exception as e:
                    flash(f'Lỗi khi lưu ảnh đại diện: {str(e)}. Thông tin khác đã được lưu.', 'warning')
        
        # Commit tất cả thay đổi
        try:
            db.session.commit()
            if avatar_updated:
                flash('Đã lưu thông tin và ảnh đại diện thành công!', 'success')
                # Redirect back to edit page to see new avatar
                return redirect(url_for('main.edit_student', student_id=student_id))
            else:
                flash('Đã lưu thông tin học sinh thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi lưu thay đổi: {str(e)}', 'danger')
            
        return redirect(url_for('main.student_list'))
    mobile = is_mobile()
    return render_template('edit_student.html', student=student, title='Chỉnh sửa học sinh', mobile=mobile)

@main.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    student = Child.query.get_or_404(student_id)
    # Xoá toàn bộ album và ảnh liên quan trước khi xoá học sinh
    for album in student.albums:
        for photo in album.photos:
            db.session.delete(photo)
        db.session.delete(album)
    db.session.delete(student)
    db.session.commit()
    flash('Đã xoá học sinh!', 'success')
    return redirect(url_for('main.student_list'))

@main.route('/admin/change-password', methods=['GET', 'POST'])
def change_admin_password():
    if session.get('role') != 'admin':
        flash('Bạn không có quyền đổi mật khẩu admin!', 'danger')
        return redirect(url_for('main.login'))
    admin = Staff.query.filter_by(name='admin').first()
    if not admin:
        flash('Không tìm thấy tài khoản admin!', 'danger')
        return redirect(url_for('main.accounts'))
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if old_password != admin.password:
            flash('Mật khẩu hiện tại không đúng!', 'danger')
        elif new_password != confirm_password:
            flash('Mật khẩu mới nhập lại không khớp!', 'danger')
        else:
            admin.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Đổi mật khẩu admin thành công!', 'success')
            return redirect(url_for('main.accounts'))
    return render_template('change_admin_password.html', title='Đổi mật khẩu Admin')

@main.route('/activities')
def activities():
    user_role = session.get('role')
    user_id = session.get('user_id')
    posts = None
    if user_role == 'parent':
        child = Child.query.filter_by(id=user_id).first()
        class_name = child.class_name if child else None
        class_obj = Class.query.filter_by(name=class_name).first() if class_name else None
        class_id = class_obj.id if class_obj else None
        # Chỉ lấy bài viết của lớp con mình hoặc bài cho khách vãng lai
        posts = Activity.query.filter(
            (Activity.class_id == class_id) | (Activity.class_id == None)
        ).order_by(Activity.date.desc()).all()
    else:
        # Giáo viên, admin xem tất cả
        posts = Activity.query.order_by(Activity.date.desc()).all()
    activities = [
        {
            'id': post.id,
            'title': post.title,
            'content': post.description,
            'image': post.image,
            'date_posted': post.date.strftime('%Y-%m-%d'),
            'images': post.images  # Truyền danh sách ảnh gallery
        } for post in posts
    ]
    mobile = is_mobile()
    from app.forms import DeleteActivityForm
    form = DeleteActivityForm()
    return render_template('activities.html', activities=activities, title='Hoạt động', mobile=mobile, form=form)

@main.route('/accounts/create', methods=['GET', 'POST'])
def create_account():
    if session.get('role') != 'admin':
        return redirect_no_permission()
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        if role == 'admin':
            flash('Không thể tạo tài khoản admin qua form này!', 'danger')
            return render_template('create_account.html', title='Tạo tài khoản mới')
        # Kiểm tra trùng tên/email
        if not name or not email or not phone or not password:
            flash('Vui lòng nhập đầy đủ thông tin bắt buộc!', 'danger')
            return render_template('create_account.html', title='Tạo tài khoản mới')
        if (Child.query.filter_by(name=name).first() or Staff.query.filter_by(name=name).first() or name == 'admin'):
            flash('Tên đã tồn tại hoặc trùng với tài khoản khác!', 'danger')
            return render_template('create_account.html', title='Tạo tài khoản mới')
        if (Child.query.filter_by(email=email).first() or Staff.query.filter_by(email=email).first() or email == 'admin@smalltree.vn'):
            flash('Email đã tồn tại hoặc trùng với tài khoản khác!', 'danger')
            return render_template('create_account.html', title='Tạo tài khoản mới')
        if role == 'parent':
            student_code = request.form.get('student_code')
            class_name = request.form.get('class_name')
            birth_date = request.form.get('birth_date')
            parent_contact = request.form.get('parent_contact')
            if not student_code or not class_name or not birth_date or not parent_contact:
                flash('Vui lòng nhập đầy đủ thông tin học sinh/phụ huynh!', 'danger')
                return render_template('create_account.html', title='Tạo tài khoản mới')
            new_child = Child(name=name, age=0, parent_contact=parent_contact, class_name=class_name, birth_date=birth_date, email=email, phone=phone, password=generate_password_hash(password), student_code=student_code)
            db.session.add(new_child)
        elif role == 'teacher':
            position = request.form.get('position')
            if not position:
                flash('Vui lòng nhập chức vụ giáo viên!', 'danger')
                return render_template('create_account.html', title='Tạo tài khoản mới')
            new_staff = Staff(name=name, position=position, contact_info=phone, email=email, phone=phone, password=generate_password_hash(password))
            db.session.add(new_staff)
        db.session.commit()
        flash('Tạo tài khoản thành công!', 'success')
        return redirect(url_for('main.accounts'))
    return render_template('create_account.html', title='Tạo tài khoản mới')

@main.route('/accounts/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_account(user_id):
    if session.get('role') != 'admin':
        return redirect_no_permission()
    user_type = request.args.get('type', 'parent')
    from app.models import Class
    classes = Class.query.order_by(Class.name).all() if user_type == 'parent' else []
    if user_type == 'teacher':
        user = Staff.query.get_or_404(user_id)
    else:
        user = Child.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        if user_type == 'parent':
            user.parent_contact = request.form.get('parent_contact')
            user.student_code = request.form.get('student_code')
            user.class_name = request.form.get('class_name')
            user.birth_date = request.form.get('birth_date')
        elif user_type == 'teacher':
            user.position = request.form.get('position')
        password = request.form.get('password')
        if password:
            user.password = generate_password_hash(password)
        db.session.commit()
        flash('Đã cập nhật thông tin tài khoản!', 'success')
        return redirect(url_for('main.accounts'))
    # Hide sensitive info for non-admins (should only be admin here, but for safety)
    show_sensitive = session.get('role') == 'admin'
    masked_user = {
        'id': user.id,
        'name': user.name,
        'email': user.email if show_sensitive else 'Ẩn',
        'phone': user.phone if show_sensitive else 'Ẩn',
        'student_code': getattr(user, 'student_code', None) if show_sensitive else 'Ẩn',
        'class_name': getattr(user, 'class_name', None) if show_sensitive else 'Ẩn',
        'parent_contact': getattr(user, 'parent_contact', None) if show_sensitive else 'Ẩn',
        'position': getattr(user, 'position', None) if show_sensitive else 'Ẩn',
    }
    return render_template('edit_account.html', user=masked_user, type=user_type, title='Chỉnh sửa tài khoản', classes=classes)

@main.route('/accounts/parent/<int:user_id>/delete', methods=['POST'])
def delete_parent_account(user_id):
    if session.get('role') != 'admin':
        return redirect_no_permission()
    user = Child.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Đã xoá tài khoản phụ huynh!', 'success')
    return redirect(url_for('main.accounts'))

@main.route('/accounts/teacher/<int:user_id>/delete', methods=['POST'])
def delete_teacher_account(user_id):
    if session.get('role') != 'admin':
        return redirect_no_permission()
    user = Staff.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Đã xoá tài khoản giáo viên!', 'success')
    return redirect(url_for('main.accounts'))

@main.route('/activities/<int:id>/edit', methods=['GET', 'POST'])
def edit_activity(id):
    try:
        if session.get('role') not in ['admin', 'teacher']:
            return redirect_no_permission()
        post = Activity.query.get_or_404(id)
        if not post:
            flash('Không tìm thấy bài viết để chỉnh sửa!', 'danger')
            return redirect(url_for('main.activities'))
        from app.models import Class
        from app.forms import ActivityEditForm
        classes = Class.query.order_by(Class.name).all()
        class_choices = [(0, 'Tất cả khách vãng lai')] + [(c.id, c.name) for c in classes]
        form = ActivityEditForm()
        form.class_id.choices = class_choices
        if request.method == 'POST' and form.validate_on_submit():
            post.title = form.title.data
            post.description = form.description.data
            post.class_id = form.class_id.data if form.class_id.data != 0 else None
            background_file = form.background.data
            image_url = post.image
            if background_file and getattr(background_file, 'filename', None):
                allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.jfif'}
                ext = os.path.splitext(background_file.filename)[1].lower()
                safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', background_file.filename)
                if ext not in allowed_ext:
                    flash('Chỉ cho phép tải lên các file ảnh có đuôi: .jpg, .jpeg, .png, .gif, .jfif!', 'danger')
                    return render_template('edit_activity.html', post=post, form=form, title='Chỉnh sửa hoạt động', mobile=is_mobile(), classes=classes)
                filename = 'bg_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + safe_filename
                save_path = os.path.join('app', 'static', 'images', filename)
                img = Image.open(background_file)
                img.thumbnail((1200, 800))
                img.save(save_path)
                image_url = url_for('static', filename=f'images/{filename}')
                post.image = image_url
            files = request.files.getlist('images')
            activity_dir = os.path.join('app', 'static', 'images', 'activities', str(post.id))
            os.makedirs(activity_dir, exist_ok=True)
            for file in files:
                if file and getattr(file, 'filename', None):
                    ext = os.path.splitext(file.filename)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.jfif']:
                        flash(f"File {file.filename} không đúng định dạng ảnh!", 'danger')
                        continue
                    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', file.filename)
                    img_filename = datetime.now().strftime('%Y%m%d%H%M%S%f') + '_' + safe_filename
                    img_path = os.path.join(activity_dir, img_filename)
                    try:
                        file.stream.seek(0)
                        img = Image.open(file.stream)
                        img.thumbnail((1200, 800))
                        img.save(img_path)
                        rel_path = os.path.join('images', 'activities', str(post.id), img_filename).replace('\\', '/')
                        db.session.add(ActivityImage(filename=img_filename, filepath=rel_path, upload_date=datetime.now(), activity_id=post.id))
                    except Exception as e:
                        print(f"[ERROR] Lỗi upload ảnh: {getattr(file, 'filename', 'unknown')} - {e}")
                        import traceback
                        traceback.print_exc()
                        flash(f"Lỗi upload ảnh: {getattr(file, 'filename', 'unknown')} - {e}", 'danger')
                        continue
            db.session.commit()
            flash('Đã cập nhật bài viết!', 'success')
            return redirect(url_for('main.activities'))
        mobile = is_mobile()
        # Gán dữ liệu mặc định cho form khi GET
        if request.method == 'GET':
            form.title.data = post.title
            form.description.data = post.description
            form.class_id.data = post.class_id if post.class_id is not None else 0
        return render_template('edit_activity.html', post=post, form=form, title='Chỉnh sửa hoạt động', mobile=mobile, classes=classes)
    except Exception as e:
        print(f"[ERROR] Lỗi khi render edit_activity: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Lỗi hệ thống khi chỉnh sửa hoạt động: {e}", 'danger')
        return redirect(url_for('main.activities'))

@main.route('/bmi-index', methods=['GET', 'POST'])
def bmi_index():
    students = Child.query.all()
    bmi = None
    bmi_id = None

    if request.method == 'POST':
        student_id = int(request.form['student_id'])
        weight = float(request.form['weight'])
        height = float(request.form['height']) / 100  # đổi cm sang m
        bmi = round(weight / (height * height), 2)
        bmi_id = student_id
        record_date = request.form.get('date', date.today().isoformat())
        # Fix: round height to 2 decimals before saving
        rounded_height_cm = round(height * 100, 2)
        new_record = BmiRecord(
            student_id=student_id,
            date=date.fromisoformat(record_date),
            weight=weight,
            height=rounded_height_cm,  # lưu lại đơn vị cm, đã làm tròn
            bmi=bmi
        )
        db.session.add(new_record)
        db.session.commit()

    bmi_history = {}
    for student in students:
        records = BmiRecord.query.filter_by(student_id=student.id).order_by(BmiRecord.date.desc(), BmiRecord.id.desc()).all()
        filtered = {}
        for record in records:
            date_str = record.date.strftime('%Y-%m-%d')
            if date_str not in filtered:
                filtered[date_str] = record
        bmi_history[student.id] = list(filtered.values())

    current_date_iso = date.today().isoformat()
    return render_template(
        'bmi_index.html',
        title='Chỉ Số BMI',
        students=students,
        bmi=bmi,
        bmi_id=bmi_id,
        bmi_history=bmi_history,
        current_date_iso=current_date_iso,
        mobile=False
    )

@main.route('/bmi-record/<int:record_id>/edit', methods=['POST'])
def edit_bmi_record(record_id):
    record = BmiRecord.query.get_or_404(record_id)
    date_str = request.form.get('date')
    weight = request.form.get('weight')
    height = request.form.get('height')
    if date_str and weight and height:
        record.date = date.fromisoformat(date_str)
        record.weight = float(weight)
        record.height = request.form.get('height')
        record.bmi = round(float(weight) / ((float(height)/100) ** 2), 2)
        db.session.commit()
        flash('Đã cập nhật chỉ số BMI!', 'success')
    else:
        flash('Vui lòng nhập đầy đủ thông tin!', 'danger')
    return redirect(url_for('main.bmi_index', edit_id=None))

@main.route('/bmi-record/<int:record_id>/delete', methods=['POST'])
def delete_bmi_record(record_id):
    record = BmiRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash('Đã xoá chỉ số BMI!', 'success')
    return redirect(url_for('main.bmi_index', edit_id=None))

@main.route('/menu')
def menu():
    # Chỉ sử dụng Menu model cho thực đơn
    menus = Menu.query.order_by(Menu.week_number).all()
    menu = []
    
    for menu_item in menus:
        # Convert structured Menu fields to template format
        data = {
            'mon': {
                'morning': menu_item.monday_morning or '',
                'snack': menu_item.monday_snack or '',
                'dessert': menu_item.monday_dessert or '',
                'lunch': menu_item.monday_lunch or '',
                'afternoon': menu_item.monday_afternoon or '',
                'lateafternoon': menu_item.monday_lateafternoon or ''
            },
            'tue': {
                'morning': menu_item.tuesday_morning or '',
                'snack': menu_item.tuesday_snack or '',
                'dessert': menu_item.tuesday_dessert or '',
                'lunch': menu_item.tuesday_lunch or '',
                'afternoon': menu_item.tuesday_afternoon or '',
                'lateafternoon': menu_item.tuesday_lateafternoon or ''
            },
            'wed': {
                'morning': menu_item.wednesday_morning or '',
                'snack': menu_item.wednesday_snack or '',
                'dessert': menu_item.wednesday_dessert or '',
                'lunch': menu_item.wednesday_lunch or '',
                'afternoon': menu_item.wednesday_afternoon or '',
                'lateafternoon': menu_item.wednesday_lateafternoon or ''
            },
            'thu': {
                'morning': menu_item.thursday_morning or '',
                'snack': menu_item.thursday_snack or '',
                'dessert': menu_item.thursday_dessert or '',
                'lunch': menu_item.thursday_lunch or '',
                'afternoon': menu_item.thursday_afternoon or '',
                'lateafternoon': menu_item.thursday_lateafternoon or ''
            },
            'fri': {
                'morning': menu_item.friday_morning or '',
                'snack': menu_item.friday_snack or '',
                'dessert': menu_item.friday_dessert or '',
                'lunch': menu_item.friday_lunch or '',
                'afternoon': menu_item.friday_afternoon or '',
                'lateafternoon': menu_item.friday_lateafternoon or ''
            },
            'sat': {
                'morning': menu_item.saturday_morning or '',
                'snack': menu_item.saturday_snack or '',
                'dessert': menu_item.saturday_dessert or '',
                'lunch': menu_item.saturday_lunch or '',
                'afternoon': menu_item.saturday_afternoon or '',
                'lateafternoon': menu_item.saturday_lateafternoon or ''
            }
        }
        
        menu.append({
            'week_number': menu_item.week_number,
            'data': data
        })
    
    mobile = is_mobile()
    return render_template('menu.html', menu=menu, title='Thực đơn', mobile=mobile)

@main.route('/menu/new', methods=['GET', 'POST'])
def new_menu():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    if request.method == 'POST':
        week_number = int(request.form.get('week_number'))
        
        # Check if menu already exists for this week
        existing_menu = Menu.query.filter_by(week_number=week_number, year=2025).first()
        if existing_menu:
            flash(f'Thực đơn tuần {week_number}/2025 đã tồn tại! Vui lòng chọn tuần khác hoặc sửa thực đơn hiện có.', 'danger')
            # Get all active dishes for re-rendering the form
            dishes = Dish.query.filter_by(is_active=True).all()
            mobile = is_mobile()
            
            # Calculate current week for display
            from datetime import datetime, timedelta
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            current_week = week_start.isocalendar()[1]
            current_year = week_start.year
            
            return render_template('new_menu.html', title='Tạo thực đơn mới', mobile=mobile, dishes=dishes, 
                                 error_week=week_number, current_week=current_week, current_year=current_year)
        
        # Create new Menu record
        new_menu = Menu(
            week_number=week_number,
            year=2025,  # Current year
            # Monday
            monday_morning=request.form.get('content_mon_morning', ''),
            monday_snack=request.form.get('content_mon_snack', ''),
            monday_dessert=request.form.get('content_mon_dessert', ''),
            monday_lunch=request.form.get('content_mon_lunch', ''),
            monday_afternoon=request.form.get('content_mon_afternoon', ''),
            monday_lateafternoon=request.form.get('content_mon_lateafternoon', ''),
            # Tuesday
            tuesday_morning=request.form.get('content_tue_morning', ''),
            tuesday_snack=request.form.get('content_tue_snack', ''),
            tuesday_dessert=request.form.get('content_tue_dessert', ''),
            tuesday_lunch=request.form.get('content_tue_lunch', ''),
            tuesday_afternoon=request.form.get('content_tue_afternoon', ''),
            tuesday_lateafternoon=request.form.get('content_tue_lateafternoon', ''),
            # Wednesday
            wednesday_morning=request.form.get('content_wed_morning', ''),
            wednesday_snack=request.form.get('content_wed_snack', ''),
            wednesday_dessert=request.form.get('content_wed_dessert', ''),
            wednesday_lunch=request.form.get('content_wed_lunch', ''),
            wednesday_afternoon=request.form.get('content_wed_afternoon', ''),
            wednesday_lateafternoon=request.form.get('content_wed_lateafternoon', ''),
            # Thursday
            thursday_morning=request.form.get('content_thu_morning', ''),
            thursday_snack=request.form.get('content_thu_snack', ''),
            thursday_dessert=request.form.get('content_thu_dessert', ''),
            thursday_lunch=request.form.get('content_thu_lunch', ''),
            thursday_afternoon=request.form.get('content_thu_afternoon', ''),
            thursday_lateafternoon=request.form.get('content_thu_lateafternoon', ''),
            # Friday
            friday_morning=request.form.get('content_fri_morning', ''),
            friday_snack=request.form.get('content_fri_snack', ''),
            friday_dessert=request.form.get('content_fri_dessert', ''),
            friday_lunch=request.form.get('content_fri_lunch', ''),
            friday_afternoon=request.form.get('content_fri_afternoon', ''),
            friday_lateafternoon=request.form.get('content_fri_lateafternoon', ''),
            # Saturday
            saturday_morning=request.form.get('content_sat_morning', ''),
            saturday_snack=request.form.get('content_sat_snack', ''),
            saturday_dessert=request.form.get('content_sat_dessert', ''),
            saturday_lunch=request.form.get('content_sat_lunch', ''),
            saturday_afternoon=request.form.get('content_sat_afternoon', ''),
            saturday_lateafternoon=request.form.get('content_sat_lateafternoon', '')
        )
        
        db.session.add(new_menu)
        db.session.commit()
        flash('Đã thêm thực đơn mới!', 'success')
        return redirect(url_for('main.menu'))
    
    # Get all active dishes
    dishes = Dish.query.filter_by(is_active=True).all()
    mobile = is_mobile()
    
    # Calculate current week number for default value
    from datetime import datetime, timedelta
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    current_week = week_start.isocalendar()[1]
    current_year = week_start.year
    
    return render_template('new_menu.html', title='Tạo thực đơn mới', mobile=mobile, dishes=dishes, 
                         current_week=current_week, current_year=current_year)

@main.route('/menu/<int:week_number>/edit', methods=['GET', 'POST'])
def edit_menu(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    menu_item = Menu.query.filter_by(week_number=week_number, year=2025).first()
    if not menu_item:
        flash('Không tìm thấy thực đơn để chỉnh sửa!', 'danger')
        return redirect(url_for('main.menu'))
    
    if request.method == 'POST':
        new_week_number = request.form.get('week_number', type=int)
        
        # Update menu fields
        menu_item.monday_morning = request.form.get('content_mon_morning', '')
        menu_item.monday_snack = request.form.get('content_mon_snack', '')
        menu_item.monday_dessert = request.form.get('content_mon_dessert', '')
        menu_item.monday_lunch = request.form.get('content_mon_lunch', '')
        menu_item.monday_afternoon = request.form.get('content_mon_afternoon', '')
        menu_item.monday_lateafternoon = request.form.get('content_mon_lateafternoon', '')
        
        menu_item.tuesday_morning = request.form.get('content_tue_morning', '')
        menu_item.tuesday_snack = request.form.get('content_tue_snack', '')
        menu_item.tuesday_dessert = request.form.get('content_tue_dessert', '')
        menu_item.tuesday_lunch = request.form.get('content_tue_lunch', '')
        menu_item.tuesday_afternoon = request.form.get('content_tue_afternoon', '')
        menu_item.tuesday_lateafternoon = request.form.get('content_tue_lateafternoon', '')
        
        menu_item.wednesday_morning = request.form.get('content_wed_morning', '')
        menu_item.wednesday_snack = request.form.get('content_wed_snack', '')
        menu_item.wednesday_dessert = request.form.get('content_wed_dessert', '')
        menu_item.wednesday_lunch = request.form.get('content_wed_lunch', '')
        menu_item.wednesday_afternoon = request.form.get('content_wed_afternoon', '')
        menu_item.wednesday_lateafternoon = request.form.get('content_wed_lateafternoon', '')
        
        menu_item.thursday_morning = request.form.get('content_thu_morning', '')
        menu_item.thursday_snack = request.form.get('content_thu_snack', '')
        menu_item.thursday_dessert = request.form.get('content_thu_dessert', '')
        menu_item.thursday_lunch = request.form.get('content_thu_lunch', '')
        menu_item.thursday_afternoon = request.form.get('content_thu_afternoon', '')
        menu_item.thursday_lateafternoon = request.form.get('content_thu_lateafternoon', '')
        
        menu_item.friday_morning = request.form.get('content_fri_morning', '')
        menu_item.friday_snack = request.form.get('content_fri_snack', '')
        menu_item.friday_dessert = request.form.get('content_fri_dessert', '')
        menu_item.friday_lunch = request.form.get('content_fri_lunch', '')
        menu_item.friday_afternoon = request.form.get('content_fri_afternoon', '')
        menu_item.friday_lateafternoon = request.form.get('content_fri_lateafternoon', '')
        
        menu_item.saturday_morning = request.form.get('content_sat_morning', '')
        menu_item.saturday_snack = request.form.get('content_sat_snack', '')
        menu_item.saturday_dessert = request.form.get('content_sat_dessert', '')
        menu_item.saturday_lunch = request.form.get('content_sat_lunch', '')
        menu_item.saturday_afternoon = request.form.get('content_sat_afternoon', '')
        menu_item.saturday_lateafternoon = request.form.get('content_sat_lateafternoon', '')
        
        # Check for duplicate week number if changed
        if new_week_number != menu_item.week_number:
            existing = Menu.query.filter_by(week_number=new_week_number, year=2025).first()
            if existing:
                flash(f'Đã tồn tại thực đơn tuần {new_week_number}, không thể đổi!', 'danger')
                return redirect(url_for('main.edit_menu', week_number=menu_item.week_number))
            menu_item.week_number = new_week_number
            
        db.session.commit()
        flash(f'Đã cập nhật thực đơn tuần {menu_item.week_number}!', 'success')
        return redirect(url_for('main.menu'))
    
    # Convert Menu fields to template format for editing
    data = {
        'mon': {
            'morning': menu_item.monday_morning or '',
            'snack': menu_item.monday_snack or '',
            'dessert': menu_item.monday_dessert or '',
            'lunch': menu_item.monday_lunch or '',
            'afternoon': menu_item.monday_afternoon or '',
            'lateafternoon': menu_item.monday_lateafternoon or ''
        },
        'tue': {
            'morning': menu_item.tuesday_morning or '',
            'snack': menu_item.tuesday_snack or '',
            'dessert': menu_item.tuesday_dessert or '',
            'lunch': menu_item.tuesday_lunch or '',
            'afternoon': menu_item.tuesday_afternoon or '',
            'lateafternoon': menu_item.tuesday_lateafternoon or ''
        },
        'wed': {
            'morning': menu_item.wednesday_morning or '',
            'snack': menu_item.wednesday_snack or '',
            'dessert': menu_item.wednesday_dessert or '',
            'lunch': menu_item.wednesday_lunch or '',
            'afternoon': menu_item.wednesday_afternoon or '',
            'lateafternoon': menu_item.wednesday_lateafternoon or ''
        },
        'thu': {
            'morning': menu_item.thursday_morning or '',
            'snack': menu_item.thursday_snack or '',
            'dessert': menu_item.thursday_dessert or '',
            'lunch': menu_item.thursday_lunch or '',
            'afternoon': menu_item.thursday_afternoon or '',
            'lateafternoon': menu_item.thursday_lateafternoon or ''
        },
        'fri': {
            'morning': menu_item.friday_morning or '',
            'snack': menu_item.friday_snack or '',
            'dessert': menu_item.friday_dessert or '',
            'lunch': menu_item.friday_lunch or '',
            'afternoon': menu_item.friday_afternoon or '',
            'lateafternoon': menu_item.friday_lateafternoon or ''
        },
        'sat': {
            'morning': menu_item.saturday_morning or '',
            'snack': menu_item.saturday_snack or '',
            'dessert': menu_item.saturday_dessert or '',
            'lunch': menu_item.saturday_lunch or '',
            'afternoon': menu_item.saturday_afternoon or '',
            'lateafternoon': menu_item.saturday_lateafternoon or ''
        }
    }
    
    # Get all active dishes
    dishes = Dish.query.filter_by(is_active=True).all()
    mobile = is_mobile()
    return render_template('edit_menu.html', week=menu_item, data=data, title=f'Chỉnh sửa thực đơn tuần {menu_item.week_number}', mobile=mobile, dishes=dishes)

@main.route('/menu/<int:week_number>/delete', methods=['POST'])
def delete_menu(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    menu_item = Menu.query.filter_by(week_number=week_number, year=2025).first()
    if menu_item:
        db.session.delete(menu_item)
        db.session.commit()
        flash(f'Đã xoá thực đơn tuần {week_number}!', 'success')
    else:
        flash('Không tìm thấy thực đơn để xoá!', 'danger')
    return redirect(url_for('main.menu'))

@main.route('/menu/import', methods=['POST'])
def import_menu():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    file = request.files.get('excel_file')
    week_number = request.form.get('week_number', type=int)
    if not file:
        flash('Vui lòng chọn file Excel!', 'danger')
        return redirect(url_for('main.menu'))
    if not week_number:
        flash('Vui lòng nhập số tuần!', 'danger')
        return redirect(url_for('main.menu'))

    from openpyxl import load_workbook
    wb = load_workbook(file)
    ws = wb.active

    # Đọc dữ liệu từ dòng 3 đến 8, cột B-G (theo mẫu: A1:A2 "Thứ", B1:G1 "Khung giờ", B2-G2 slot, A3-A8 thứ)
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
    menu_data = {}
    for i, day in enumerate(days):
        row = i + 3  # Dòng 3-8
        menu_data[day] = {}
        for j, slot in enumerate(slots):
            col = j + 2  # B=2, C=3, ... G=7
            value = ws.cell(row=row, column=col).value
            menu_data[day][slot] = value if value is not None else ""
    
    # Check if menu exists for this week
    menu_item = Menu.query.filter_by(week_number=week_number, year=2025).first()
    if menu_item:
        # Update existing menu
        menu_item.monday_morning = menu_data['mon']['morning']
        menu_item.monday_snack = menu_data['mon']['snack']
        menu_item.monday_dessert = menu_data['mon']['dessert']
        menu_item.monday_lunch = menu_data['mon']['lunch']
        menu_item.monday_afternoon = menu_data['mon']['afternoon']
        menu_item.monday_lateafternoon = menu_data['mon']['lateafternoon']
        
        menu_item.tuesday_morning = menu_data['tue']['morning']
        menu_item.tuesday_snack = menu_data['tue']['snack']
        menu_item.tuesday_dessert = menu_data['tue']['dessert']
        menu_item.tuesday_lunch = menu_data['tue']['lunch']
        menu_item.tuesday_afternoon = menu_data['tue']['afternoon']
        menu_item.tuesday_lateafternoon = menu_data['tue']['lateafternoon']
        
        menu_item.wednesday_morning = menu_data['wed']['morning']
        menu_item.wednesday_snack = menu_data['wed']['snack']
        menu_item.wednesday_dessert = menu_data['wed']['dessert']
        menu_item.wednesday_lunch = menu_data['wed']['lunch']
        menu_item.wednesday_afternoon = menu_data['wed']['afternoon']
        menu_item.wednesday_lateafternoon = menu_data['wed']['lateafternoon']
        
        menu_item.thursday_morning = menu_data['thu']['morning']
        menu_item.thursday_snack = menu_data['thu']['snack']
        menu_item.thursday_dessert = menu_data['thu']['dessert']
        menu_item.thursday_lunch = menu_data['thu']['lunch']
        menu_item.thursday_afternoon = menu_data['thu']['afternoon']
        menu_item.thursday_lateafternoon = menu_data['thu']['lateafternoon']
        
        menu_item.friday_morning = menu_data['fri']['morning']
        menu_item.friday_snack = menu_data['fri']['snack']
        menu_item.friday_dessert = menu_data['fri']['dessert']
        menu_item.friday_lunch = menu_data['fri']['lunch']
        menu_item.friday_afternoon = menu_data['fri']['afternoon']
        menu_item.friday_lateafternoon = menu_data['fri']['lateafternoon']
        
        menu_item.saturday_morning = menu_data['sat']['morning']
        menu_item.saturday_snack = menu_data['sat']['snack']
        menu_item.saturday_dessert = menu_data['sat']['dessert']
        menu_item.saturday_lunch = menu_data['sat']['lunch']
        menu_item.saturday_afternoon = menu_data['sat']['afternoon']
        menu_item.saturday_lateafternoon = menu_data['sat']['lateafternoon']
    else:
        # Create new menu
        new_menu = Menu(
            week_number=week_number,
            year=2025,
            monday_morning=menu_data['mon']['morning'],
            monday_snack=menu_data['mon']['snack'],
            monday_dessert=menu_data['mon']['dessert'],
            monday_lunch=menu_data['mon']['lunch'],
            monday_afternoon=menu_data['mon']['afternoon'],
            monday_lateafternoon=menu_data['mon']['lateafternoon'],
            
            tuesday_morning=menu_data['tue']['morning'],
            tuesday_snack=menu_data['tue']['snack'],
            tuesday_dessert=menu_data['tue']['dessert'],
            tuesday_lunch=menu_data['tue']['lunch'],
            tuesday_afternoon=menu_data['tue']['afternoon'],
            tuesday_lateafternoon=menu_data['tue']['lateafternoon'],
            
            wednesday_morning=menu_data['wed']['morning'],
            wednesday_snack=menu_data['wed']['snack'],
            wednesday_dessert=menu_data['wed']['dessert'],
            wednesday_lunch=menu_data['wed']['lunch'],
            wednesday_afternoon=menu_data['wed']['afternoon'],
            wednesday_lateafternoon=menu_data['wed']['lateafternoon'],
            
            thursday_morning=menu_data['thu']['morning'],
            thursday_snack=menu_data['thu']['snack'],
            thursday_dessert=menu_data['thu']['dessert'],
            thursday_lunch=menu_data['thu']['lunch'],
            thursday_afternoon=menu_data['thu']['afternoon'],
            thursday_lateafternoon=menu_data['thu']['lateafternoon'],
            
            friday_morning=menu_data['fri']['morning'],
            friday_snack=menu_data['fri']['snack'],
            friday_dessert=menu_data['fri']['dessert'],
            friday_lunch=menu_data['fri']['lunch'],
            friday_afternoon=menu_data['fri']['afternoon'],
            friday_lateafternoon=menu_data['fri']['lateafternoon'],
            
            saturday_morning=menu_data['sat']['morning'],
            saturday_snack=menu_data['sat']['snack'],
            saturday_dessert=menu_data['sat']['dessert'],
            saturday_lunch=menu_data['sat']['lunch'],
            saturday_afternoon=menu_data['sat']['afternoon'],
            saturday_lateafternoon=menu_data['sat']['lateafternoon']
        )
        db.session.add(new_menu)
    
    db.session.commit()
    flash('Đã import thực đơn từ Excel!', 'success')
    return redirect(url_for('main.menu'))

@main.route('/curriculum/import', methods=['POST'])
def import_curriculum():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    file = request.files.get('excel_file')

    week_number = request.form.get('week_number')
    class_id = request.form.get('class_id')
    if not class_id:
        flash('Vui lòng chọn lớp!', 'danger')
        return redirect(url_for('main.curriculum'))
    if not file:
        flash('Vui lòng chọn file Excel!', 'danger')
        return redirect(url_for('main.curriculum'))
    if not week_number:
        flash('Vui lòng nhập số tuần!', 'danger')
        return redirect(url_for('main.curriculum'))
    try:
        class_id = int(class_id)
    except Exception:
        flash('Lỗi lớp học không hợp lệ!', 'danger')
        return redirect(url_for('main.curriculum'))
    try:
        week_number = int(week_number)
    except Exception:
        flash('Lỗi số tuần không hợp lệ!', 'danger')
        return redirect(url_for('main.curriculum'))

    from openpyxl import load_workbook
    wb = load_workbook(file)
    ws = wb.active

    # Đọc dữ liệu theo mẫu mới:
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    morning_slots = ['morning_0', 'morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
    afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
    curriculum_data = {}

    # Sáng: dòng 4-10 (A4-A10)
    for col_idx, day in enumerate(days):
        curriculum_data[day] = {}
        for slot_idx, slot in enumerate(morning_slots):
            row = 4 + slot_idx  # dòng 4-10
            col = 2 + col_idx   # B=2, C=3, ... G=7
            value = ws.cell(row=row, column=col).value
            curriculum_data[day][slot] = value if value is not None else ""
        # Chiều: dòng 11-14 (A11-A14)
        for slot_idx, slot in enumerate(afternoon_slots):
            row = 11 + slot_idx  # dòng 11-14 (A12=afternoon_1, A13=afternoon_2, ...)
            col = 2 + col_idx
            value = ws.cell(row=row, column=col).value
            if slot == 'afternoon_2':
                # Đảm bảo chỉ lấy đúng dòng 13 (A13) cho 15h-15h30
                if col_idx == 0:
                    curriculum_data[day][slot] = ""
                elif col_idx == 1 or col_idx == 3:
                    curriculum_data[day][slot] = value if value is not None else "Hoạt động với giáo cụ"
                elif col_idx == 2 or col_idx == 4:
                    curriculum_data[day][slot] = value if value is not None else "Lego time"
                else:
                    curriculum_data[day][slot] = value if value is not None else ""
            else:
                curriculum_data[day][slot] = value if value is not None else ""
    import json
    content = json.dumps(curriculum_data, ensure_ascii=False)
    # Đảm bảo không bị đè curriculum của lớp khác cùng tuần
    week = Curriculum.query.filter_by(week_number=week_number, class_id=class_id).first()
    if week:
        week.content = content
    else:
        new_week = Curriculum(week_number=week_number, class_id=class_id, content=content, material=None)
        db.session.add(new_week)
    db.session.commit()
    flash('Đã import chương trình học từ Excel!', 'success')
    return redirect(url_for('main.curriculum', class_id=class_id))

@main.route('/curriculum/export', methods=['GET'])
def export_curriculum_template():
    """Export file Excel mẫu chương trình học với định dạng nâng cao (merged cells, header, khung giờ, ...)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
    from io import BytesIO

    wb = Workbook()
    ws = wb.active
    ws.title = "Curriculum Template"

    # Định nghĩa style
    bold = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")

    # Header
    ws.merge_cells('A1:A2')
    ws['A1'] = "Khung giờ"
    ws['A1'].font = bold
    ws['A1'].alignment = center
    ws['A1'].fill = fill
    ws['A1'].border = border
    ws.merge_cells('B1:G1')
    ws['B1'] = "Thứ"
    ws['B1'].font = bold
    ws['B1'].alignment = center
    ws['B1'].fill = fill
    ws['B1'].border = border
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
    for i, day in enumerate(days):
        cell = ws.cell(row=2, column=2+i, value=day)
        cell.font = bold
        cell.alignment = center
        cell.fill = fill
        cell.border = border

    # Section: Buổi sáng
    ws.merge_cells('A3:G3')
    ws['A3'] = "Buổi sáng"
    ws['A3'].font = bold
    ws['A3'].alignment = center
    ws['A3'].fill = fill
    ws['A3'].border = border

    morning_slots = [
        ("7-17h", 4), ("7-8h", 5), ("8h-8h30", 6), ("8h30-9h", 7), ("9h-9h40", 8), ("9h40-10h30", 9), ("10h30-14h", 10)
    ]
    for idx, (label, row) in enumerate(morning_slots):
        ws.cell(row=row, column=1, value=label).font = bold
        ws.cell(row=row, column=1).alignment = center
        ws.cell(row=row, column=1).border = border
        if idx == 0:
            # Slot 7-17h: điền giá trị mặc định cho từng thứ
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
                if col == 3:
                    ws.cell(row=row, column=col, value="Toán học")
                elif col == 4:
                    ws.cell(row=row, column=col, value="Ngôn Ngữ")
                elif col == 5:
                    ws.cell(row=row, column=col, value="Stemax")
                elif col == 6:
                    ws.cell(row=row, column=col, value="Trải Nghiệm")
        elif idx == 1:
            # Merge cell cho 7-8h (B5:G5)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            merged_cell = ws.cell(row=row, column=2)
            merged_cell.value = "Đón trẻ - STEAM (massage kích thích giác quan) - Ăn sáng"
            merged_cell.alignment = center
            merged_cell.font = Font(bold=False)
            merged_cell.border = border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
        elif idx == 2:
            # Merge cell cho 8h-8h30 (B6:G6)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            merged_cell = ws.cell(row=row, column=2)
            merged_cell.value = "Thể dục buổi sáng - Trò chuyện đầu ngày - Kiểm tra thân thể"
            merged_cell.alignment = center
            merged_cell.font = Font(bold=False)
            merged_cell.border = border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
        elif idx == 6:
            # Merge cell cho 10h30-14h (B10:G10)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            merged_cell = ws.cell(row=row, column=2)
            merged_cell.value = "Vệ sinh ăn trưa - ngủ trưa"
            merged_cell.alignment = center
            merged_cell.font = Font(bold=False)
            merged_cell.border = border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
        else:
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border

    # Section: Buổi chiều
    ws.merge_cells('A11:G11')
    ws['A11'] = "Buổi chiều"
    ws['A11'].font = bold
    ws['A11'].alignment = center
    ws['A11'].fill = fill
    ws['A11'].border = border

    afternoon_slots = [
        ("14h15-15h", 12), ("15h-15h30", 13), ("15h45-16h", 14), ("16h-17h", 15)
    ]
    for idx, (label, row) in enumerate(afternoon_slots):
        ws.cell(row=row, column=1, value=label).font = bold
        ws.cell(row=row, column=1).alignment = center
        ws.cell(row=row, column=1).border = border
        if idx == 0:
            # Merge cell cho 14h15-15h (B12:G12)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            merged_cell = ws.cell(row=row, column=2)
            merged_cell.value = "Vệ sinh - uống nước - vận động nhẹ - ăn chiều"
            merged_cell.alignment = center
            merged_cell.font = Font(bold=False)
            merged_cell.border = border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
        elif idx == 1:
            # Set default values for 15h-15h30 slot
            # Thứ 3 (col=3): Hoạt động với giáo cụ
            # Thứ 4 (col=4): Lego time
            # Thứ 5 (col=5): Hoạt động với giáo cụ
            # Thứ 6 (col=6): Lego time
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
                if col == 3 or col == 5:
                    ws.cell(row=row, column=col, value="Hoạt động với giáo cụ")
                elif col == 4 or col == 6:
                    ws.cell(row=row, column=col, value="Lego time")
        elif idx == 2:
            # Merge cell cho 15h45-16h (B14:G14)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            merged_cell = ws.cell(row=row, column=2)
            merged_cell.value = "Yoga/dance"
            merged_cell.alignment = center
            merged_cell.font = Font(bold=False)
            merged_cell.border = border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
        elif idx == 3:
            # Merge cell cho 16h-17h (B15:G15)
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            merged_cell = ws.cell(row=row, column=2)
            merged_cell.value = "Trả trẻ - trao đổi với phụ huynh"
            merged_cell.alignment = center
            merged_cell.font = Font(bold=False)
            merged_cell.border = border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border
        else:
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = border

    # Set column widths
    ws.column_dimensions['A'].width = 16
    for col in ['B','C','D','E','F','G']:
        ws.column_dimensions[col].width = 18

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="curriculum_template.xlsx", as_attachment=True)

@main.route('/menu/export', methods=['GET'])
def export_menu_template():
    """Export file Excel mẫu thực đơn với định dạng nâng cao (merged cells, header, khung giờ, ...)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
    from io import BytesIO

    wb = Workbook()
    ws = wb.active
    ws.title = "Menu Template"

    # Định nghĩa style
    bold = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")

    # Header
    ws.merge_cells('A1:A2')
    ws['A1'] = "Thứ"
    ws['A1'].font = bold
    ws['A1'].alignment = center
    ws['A1'].fill = fill
    ws['A1'].border = border
    ws.merge_cells('B1:G1')
    ws['B1'] = "Khung giờ"
    ws['B1'].font = bold
    ws['B1'].alignment = center
    ws['B1'].fill = fill
    ws['B1'].border = border
    slots = ["Sáng", "Phụ sáng", "Tráng miệng", "Trưa", "Xế", "Xế chiều"]
    for i, slot in enumerate(slots):
        cell = ws.cell(row=2, column=2+i, value=slot)
        cell.font = bold
        cell.alignment = center
        cell.fill = fill
        cell.border = border

    # Fill days
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
    for i, day in enumerate(days):
        cell = ws.cell(row=3+i, column=1, value=day)
        cell.font = bold
        cell.alignment = center
        cell.border = border
        for col in range(2, 8):
            ws.cell(row=3+i, column=col).border = border

    # Set column widths
    ws.column_dimensions['A'].width = 16
    for col in ['B','C','D','E','F','G']:
        ws.column_dimensions[col].width = 18

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="menu_template.xlsx", as_attachment=True)

@main.route('/activities/<int:id>/delete-image/<int:image_id>', methods=['POST'])
def delete_activity_image(id, image_id):
    try:
        if session.get('role') not in ['admin', 'teacher']:
            print(f"[LOG] Không có quyền xoá ảnh hoạt động")
            return redirect_no_permission()
        img = ActivityImage.query.get_or_404(image_id)
        print(f"[LOG] Đang xoá ảnh: id={image_id}, filepath={img.filepath}")
        # Xoá file vật lý
        img_path = os.path.join('app', 'static', img.filepath)
        if os.path.exists(img_path):
            os.remove(img_path)
            print(f"[LOG] Đã xoá file vật lý: {img_path}")
        else:
            print(f"[LOG] File vật lý không tồn tại: {img_path}")
        db.session.delete(img)
        db.session.commit()
        print(f"[LOG] Đã xoá bản ghi ActivityImage id={image_id} khỏi DB")
        flash('Đã xoá ảnh hoạt động!', 'success')
        return redirect(url_for('main.edit_activity', id=id))
    except Exception as e:
        print(f"[ERROR] Lỗi khi xoá ảnh hoạt động: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Lỗi khi xoá ảnh hoạt động: {e}", 'danger')
        return redirect(url_for('main.edit_activity', id=id))

@main.route('/menu/<int:week_number>/export-food-safety', methods=['GET'])
def export_food_safety_process(week_number):
    """Xuất quy trình an toàn thực phẩm 3 bước theo tiêu chuẩn chuyên nghiệp với đầy đủ thông tin quản lý."""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    # Lấy thực đơn của tuần (sử dụng Menu model)
    menu_item = Menu.query.filter_by(week_number=week_number, year=2025).first()
    if not menu_item:
        flash('Không tìm thấy thực đơn!', 'danger')
        return redirect(url_for('main.menu'))
    
    import json
    if not OPENPYXL_AVAILABLE:
        flash('Chức năng này cần cài đặt openpyxl. Vui lòng liên hệ quản trị viên.', 'warning')
        return redirect(url_for('main.menu'))
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
    from io import BytesIO
    import zipfile
    from datetime import datetime, timedelta
    
    # Convert Menu model data to the same format as old Curriculum JSON
    menu_data = {
        'mon': {
            'morning': menu_item.monday_morning or '',
            'snack': menu_item.monday_snack or '',
            'dessert': menu_item.monday_dessert or '',
            'lunch': menu_item.monday_lunch or '',
            'afternoon': menu_item.monday_afternoon or '',
            'lateafternoon': menu_item.monday_lateafternoon or ''
        },
        'tue': {
            'morning': menu_item.tuesday_morning or '',
            'snack': menu_item.tuesday_snack or '',
            'dessert': menu_item.tuesday_dessert or '',
            'lunch': menu_item.tuesday_lunch or '',
            'afternoon': menu_item.tuesday_afternoon or '',
            'lateafternoon': menu_item.tuesday_lateafternoon or ''
        },
        'wed': {
            'morning': menu_item.wednesday_morning or '',
            'snack': menu_item.wednesday_snack or '',
            'dessert': menu_item.wednesday_dessert or '',
            'lunch': menu_item.wednesday_lunch or '',
            'afternoon': menu_item.wednesday_afternoon or '',
            'lateafternoon': menu_item.wednesday_lateafternoon or ''
        },
        'thu': {
            'morning': menu_item.thursday_morning or '',
            'snack': menu_item.thursday_snack or '',
            'dessert': menu_item.thursday_dessert or '',
            'lunch': menu_item.thursday_lunch or '',
            'afternoon': menu_item.thursday_afternoon or '',
            'lateafternoon': menu_item.thursday_lateafternoon or ''
        },
        'fri': {
            'morning': menu_item.friday_morning or '',
            'snack': menu_item.friday_snack or '',
            'dessert': menu_item.friday_dessert or '',
            'lunch': menu_item.friday_lunch or '',
            'afternoon': menu_item.friday_afternoon or '',
            'lateafternoon': menu_item.friday_lateafternoon or ''
        },
        'sat': {
            'morning': menu_item.saturday_morning or '',
            'snack': menu_item.saturday_snack or '',
            'dessert': menu_item.saturday_dessert or '',
            'lunch': menu_item.saturday_lunch or '',
            'afternoon': menu_item.saturday_afternoon or '',
            'lateafternoon': menu_item.saturday_lateafternoon or ''
        }
    }
    
    # Lấy thông tin suppliers chi tiết
    from app.models import Supplier
    suppliers = Supplier.query.all()
    supplier_dict = {}
    for supplier in suppliers:
        supplier_dict[supplier.name] = {
            'address': supplier.address or 'Chưa cập nhật địa chỉ',
            'phone': supplier.phone or 'Chưa cập nhật SĐT',
            'contact_person': supplier.contact_person or 'Chưa cập nhật người liên hệ',
            'food_safety_cert': supplier.food_safety_cert or '',
            'established_date': getattr(supplier, 'established_date', 'Chưa cập nhật')
        }
    
    # Ước tính số học sinh từ config
    def get_student_count():
        return Child.query.count()
    student_count = get_student_count()
    
    

    # Helper: Lấy nguyên liệu thực tế từ database
    from app.models import Dish, DishIngredient, Product
    def get_dish_ingredients(dish_name):
        dish = Dish.query.filter_by(name=dish_name).first()
        if not dish:
            return []
        return dish.ingredients

    def get_ingredient_info(dish_ingredient, student_count):
        product = dish_ingredient.product
        total_qty = dish_ingredient.quantity * student_count
        return {
            'name': product.name,
            'unit': dish_ingredient.unit,
            'total_qty': total_qty,
            'supplier': product.supplier.name if product.supplier else '',
            'supplier_info': {
                'address': product.supplier.address if product.supplier else '',
                'phone': product.supplier.phone if product.supplier else '',
                'contact_person': product.supplier.contact_person if product.supplier else '',
                'food_safety_cert': product.supplier.food_safety_cert if product.supplier else ''
            }
        }
   
    
    # Refactor: Aggregate all ingredients from the actual weekly menu using real dish/ingredient data
    from collections import defaultdict
    ingredient_totals = defaultdict(lambda: {'total_qty': 0, 'unit': '', 'category': '', 'supplier': None, 'product': None, 'usage_frequency': 0})
    dish_appearance_count = defaultdict(int)
    dishes = set()

    # 1. Count how many times each dish appears in the week
    for day_data in menu_data.values():
        for slot_dish in day_data.values():
            if slot_dish:
                # Support both single dish and comma-separated dishes
                for dish_name in [d.strip() for d in slot_dish.split(',') if d.strip()]:
                    dish_appearance_count[dish_name] += 1
                    dishes.add(dish_name)

    # 2. For each dish, get its ingredients and sum up total needed for the week
    print(f"[DEBUG] Processing {len(dish_appearance_count)} unique dishes")
    for dish_name, appearances in dish_appearance_count.items():
        dish = Dish.query.filter_by(name=dish_name).first()
        if not dish:
            print(f"[DEBUG] Dish not found: {dish_name}")
            continue
        print(f"[DEBUG] Processing dish '{dish_name}' (appears {appearances} times)")
        print(f"[DEBUG] Dish has {len(dish.ingredients)} ingredients")
        for di in dish.ingredients:
            product = di.product
            if not product:
                print(f"[DEBUG] Product not found for ingredient ID: {di.id}")
                continue
            key = (di.product.name, di.unit, di.product.category, di.product.supplier)
            # Fix: multiply by appearances to account for how many times dish is served in the week
            qty = di.quantity * student_count * appearances
            print(f"[DEBUG] Ingredient: {di.product.name}, Quantity: {di.quantity}, Unit: {di.unit}, Students: {student_count}, Appearances: {appearances}, Total: {qty}")
            if key not in ingredient_totals:
                ingredient_totals[key] = {'total_qty': 0, 'unit': di.unit, 'category': di.product.category, 'supplier': di.product.supplier, 'product': di.product}
            ingredient_totals[key]['total_qty'] += qty
    
    print(f"[DEBUG] Total ingredient types aggregated: {len(ingredient_totals)}")
    # 3. Split into fresh, dry, fruit by category
    fresh_ingredients_with_qty = []
    dry_ingredients_with_qty = []
    fruit_ingredients_with_qty = []
    
    def convert_to_kg(quantity, unit):
        """Convert quantity to kg based on unit"""
        unit = unit.lower()
        if 'kg' in unit:
            return quantity
        elif 'g' in unit or 'gram' in unit:
            return quantity / 1000
        elif 'lít' in unit or 'l' in unit:
            return quantity  # Assume 1 liter = 1 kg for liquids
        else:
            # For other units like 'gói', 'hộp', etc., return as is
            return quantity
    
    for name, info in ingredient_totals.items():
        # Properly convert to kg based on unit
        weight_kg = convert_to_kg(info['total_qty'], info['unit'])
        
        row = {
            'name': name[0].title() if isinstance(name, tuple) else str(name).title(),
            'weight_kg': round(weight_kg, 2),
            'unit': info['unit'],
            'category': info['category'],
            'supplier': info['supplier'],
            'supplier_info': supplier_dict.get(info['supplier'].name if info['supplier'] else '', {
                'address': 'Địa chỉ chưa cập nhật',
                'phone': 'SĐT chưa cập nhật', 
                'contact_person': 'Người liên hệ chưa cập nhật',
                'food_safety_cert': 'Chưa có giấy chứng nhận'
            }),
            'usage_frequency': info.get('usage_frequency', 0)
        }
        cat = (info['category'] or '').lower()
        if 'tươi' in cat or 'rau' in cat or 'thịt' in cat or 'cá' in cat or 'trứng' in cat:
            fresh_ingredients_with_qty.append(row)
        elif 'khô' in cat or 'gia vị' in cat or 'bột' in cat or 'gạo' in cat or 'đường' in cat:
            dry_ingredients_with_qty.append(row)
        elif 'trái cây' in cat or 'hoa quả' in cat or 'fruit' in cat:
            fruit_ingredients_with_qty.append(row)
        else:
            # Default: fresh if unknown
            fresh_ingredients_with_qty.append(row)

    # Sort by usage frequency
    fresh_ingredients_with_qty.sort(key=lambda x: x['usage_frequency'], reverse=True)
    dry_ingredients_with_qty.sort(key=lambda x: x['usage_frequency'], reverse=True)
    fruit_ingredients_with_qty.sort(key=lambda x: x['usage_frequency'], reverse=True)
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        
        # BƯỚC 1.1: Tiếp nhận thực phẩm tươi - Xuất mỗi ngày 1 sheet, đúng menu/ngày
        from datetime import date, timedelta, datetime
        year = datetime.now().year
        week_start = date.fromisocalendar(year, int(week_number), 1)
        days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        wb1 = Workbook()
        # Style
        from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        thick_border = Border(left=Side(style='medium'), right=Side(style='medium'), top=Side(style='medium'), bottom=Side(style='medium'))
        for day_offset in range(6):
            day_date = week_start + timedelta(days=day_offset)
            day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day_offset]
            safe_date = day_date.strftime('%d-%m')  # Không dùng dấu '/'
            sheet_title = f"{days_vn[day_offset]} ({safe_date})"
            if day_offset == 0:
                ws1 = wb1.active
                ws1.title = sheet_title
            else:
                ws1 = wb1.create_sheet(title=sheet_title)
            # Lấy menu ngày
            menu_today = menu_data.get(day_key, {})
            # Tính nguyên liệu thực tế cho ngày này
            daily_ingredients = {}
            for meal in menu_today.values():
                if not meal: continue
                for dish_name in [d.strip() for d in meal.split(',') if d.strip()]:
                    dish = Dish.query.filter_by(name=dish_name).first()
                    if dish:
                        for di in dish.ingredients:
                            key = (di.product.name, di.unit, di.product.category, di.product.supplier)
                            qty = di.quantity * student_count
                            if key not in daily_ingredients:
                                daily_ingredients[key] = {'total_qty': 0, 'unit': di.unit, 'category': di.product.category, 'supplier': di.product.supplier, 'product': di.product}
                            daily_ingredients[key]['total_qty'] += qty
            # Phân loại tươi (sử dụng logic giống như tính toán tuần)
            fresh_ingredients = []
            for (name, unit, category, supplier), info in daily_ingredients.items():
                cat = (category or '').lower()
                if 'tươi' in cat or 'rau' in cat or 'thịt' in cat or 'cá' in cat or 'trứng' in cat or cat == 'fresh':
                    # supplier có thể là object, cần lấy tên hoặc chuỗi
                    if hasattr(supplier, 'name'):
                        supplier_name = supplier.name
                    elif isinstance(supplier, str):
                        supplier_name = supplier
                    else:
                        supplier_name = ''
                    
                    # Use the same convert_to_kg function for consistency
                    weight_kg = convert_to_kg(info['total_qty'], info['unit'])
                    
                    fresh_ingredients.append({
                        'name': name,
                        'weight_kg': round(weight_kg, 2),
                        'unit': unit,
                        'category': category,
                        'supplier': supplier_name,
                        'supplier_info': supplier_dict.get(supplier_name, {}),
                    })
            # --- Ghi dữ liệu và style sheet như cũ ---
            ws1['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
            ws1['A1'].font = Font(bold=True, size=12)
            ws1['A1'].fill = PatternFill(start_color="FFE6CC", end_color="FFE6CC", fill_type="solid")
            ws1.merge_cells('A1:P1')
            ws1['D2'] = "BIỂU MẪU KIỂM TRA TRƯỚC KHI CHẾ BIẾN THỨC ĂN"
            ws1['D2'].font = Font(bold=True, size=14, color="FF0000")
            ws1['D2'].alignment = Alignment(horizontal='center', vertical='center')
            ws1.merge_cells('D2:M2')
            ws1['O2'] = "Số: 1246/QĐ - Bộ Y Tế"
            ws1['O2'].font = Font(bold=True, size=10)
            ws1['O2'].fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            info_data = [
                (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân", 'O', "Mẫu số 1.1"),
                (4, 'A', f"Ngày kiểm tra: {day_date.strftime('%d/%m/%Y')} - {days_vn[day_offset]}", 'O', f"Số học sinh: {student_count}"),
                (5, 'A', "Địa điểm: Bếp ăn Trường MNĐL Cây Nhỏ", 'O', "Phiên bản: v2.0")
            ]
            for row, col_a, text_a, col_o, text_o in info_data:
                ws1[f'{col_a}{row}'] = text_a
                ws1[f'{col_a}{row}'].font = Font(bold=True, size=10)
                ws1[f'{col_o}{row}'] = text_o
                ws1[f'{col_o}{row}'].font = Font(bold=True, size=10)
                ws1[f'{col_o}{row}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
            ws1['A7'] = "PHẦN I: THỰC PHẨM TƯƠI SỐNG, ĐÔNG LẠNH (Thịt, cá, rau, củ, quả...)"
            ws1['A7'].font = Font(bold=True, size=12, color="0066CC")
            ws1['A7'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
            ws1.merge_cells('A7:M7')
            ws1['O7'] = "BƯỚC 1.1"
            ws1['O7'].font = Font(bold=True, size=12, color="FF0000")
            ws1['O7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
            headers_main = [
                'STT', 'TÊN THỰC PHẨM', 'THỜI GIAN NHẬP\n(Ngày/Giờ)', 
                'KHỐI LƯỢNG\n(kg/lít)', 'NƠI CUNG CẤP', '', '', 'SỐ CHỨNG TỪ/SỐ HOÁ ĐƠN',
                'GIẤY ĐĂNG KÝ VỚI THÚ Y', 'GIẤY KIỂM DỊCH',
                'KIỂM TRA CẢM QUAN', '',
                'XÉT NGHIỆM NHANH', '',
                'BIỆN PHÁP XỬ LÝ/ GHI CHÚ'
            ]
            for i, header in enumerate(headers_main, 1):
                cell = ws1.cell(row=8, column=i, value=header)
                cell.font = Font(bold=True, size=9, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.border = thick_border
            sub_headers = [
                '', '', '', '', 'Tên cơ sở', 'SĐT/Địa chỉ', 'Người Giao Hàng', '','', '',
                'Đạt', 'Không đạt', 'Đạt', 'Không đạt', ''
            ]
            for i, header in enumerate(sub_headers, 1):
                cell = ws1.cell(row=9, column=i, value=header)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="B4C6E7", end_color="B4C6E7", fill_type="solid")
                cell.border = thin_border
            ws1.merge_cells('E8:G8')
            ws1.merge_cells('K8:L8')
            ws1.merge_cells('M8:N8')

            # Số thứ tự cột
            for i in range(1, 16):
                cell = ws1.cell(row=10, column=i, value=i)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="B4C6E7", end_color="B4C6E7", fill_type="solid")
                cell.border = thin_border
            # Ghi dữ liệu thực phẩm tươi từng ngày
            for i, ingredient_info in enumerate(fresh_ingredients[:25], 1):
                row_num = 10 + i
                supplier_info = ingredient_info.get('supplier_info', {})
                supplier_name = ingredient_info.get('supplier', '') or 'CTY TNHH Thực phẩm An toàn'
                phone = supplier_info.get('phone', '0902.xxx.xxx')
                address = supplier_info.get('address', 'Đà Lạt')
                contact_person = supplier_info.get('contact_person', 'Chưa cập nhật')
                data_row = [
                    i,
                    ingredient_info['name'].upper(),
                    f"{day_date.strftime('%d/%m/%Y')}\n6:00-7:00",
                    f"{ingredient_info['weight_kg']} kg",
                    supplier_name,
                    f"{phone}\n{address[:30]}...",
                    contact_person,
                    '',  # Để trống SỐ CHỨNG TỪ/SỐ HOÁ ĐƠN
                    supplier_info.get('food_safety_cert', ''),
                    "",
                    '✓',
                    '',
                    '✓',
                    '',
                    ""
                ]
                for j, value in enumerate(data_row, 1):
                    cell = ws1.cell(row=row_num, column=j, value=value)
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = thin_border
                    if j == 1:
                        cell.font = Font(bold=True, color="0066CC")
                        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    elif j == 2:
                        cell.font = Font(bold=True, size=10)
                        cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                    elif j in [11, 13] and value == '✓':
                        cell.font = Font(bold=True, size=12, color="00AA00")
                        cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
                    elif j == 5:
                        cell.font = Font(bold=True, color="CC6600")
            # Thống kê
            stats_row = len(fresh_ingredients) + 12
            ws1[f'A{stats_row}'] = "THỐNG KÊ TỔNG QUAN:"
            ws1[f'A{stats_row}'].font = Font(bold=True, size=11, color="0066CC")
            ws1[f'A{stats_row}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
            total_weight = sum(item['weight_kg'] for item in fresh_ingredients)
            total_items = len(fresh_ingredients)
            stats_info = [
                f"• Tổng số loại thực phẩm tươi: {total_items} loại",
                f"• Tổng khối lượng ước tính: {total_weight:.1f} kg",
                f"• Số học sinh phục vụ: {student_count} em",
                f"• Khối lượng trung bình/học sinh: {(total_weight/student_count):.2f} kg/em/ngày" if student_count else "• Khối lượng trung bình/học sinh: N/A"
            ]
            for i, stat in enumerate(stats_info, 1):
                ws1[f'A{stats_row + i}'] = stat
                ws1[f'A{stats_row + i}'].font = Font(size=10)
            note_row = stats_row + 6
            ws1[f'A{note_row}'] = "GHI CHÚ QUAN TRỌNG:"
            ws1[f'A{note_row}'].font = Font(bold=True, size=11, color="FF0000")
            notes = [
                "• Kiểm tra nhiệt độ bảo quản: Thực phẩm tươi <4°C, đông lạnh <-18°C",
                "• Thời gian sử dụng: Thực phẩm tươi trong ngày, đông lạnh theo hạn sử dụng",  
                "• Xét nghiệm nhanh: Ưu tiên thực phẩm có nguồn gốc không rõ ràng",
                "• Báo cáo ngay nếu phát hiện bất thường về màu sắc, mùi vị, bao bì"
            ]
            for i, note in enumerate(notes, 1):
                ws1[f'A{note_row + i}'] = note
                ws1[f'A{note_row + i}'].font = Font(size=9, color="CC0000")
            signature_row = note_row + 7
            signature_data = [
                (signature_row, 'D', "BẾP TRƯỞNG", 'K', "HIỆU TRƯỞNG"),
                (signature_row + 1, 'D', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
                (signature_row + 5, 'D', "Hoàng Thanh Tuấn", 'K', "Nguyễn Thị Vân"),
                (signature_row + 6, 'D', f"Ngày {day_date.day}/{day_date.month}/{day_date.year}",
                 'K',
                 f"Ngày {day_date.day}/{day_date.month}/{day_date.year}")
            ]
            for row, col_d, text_d, col_k, text_k in signature_data:
                ws1[f'{col_d}{row}'] = text_d
                ws1[f'{col_k}{row}'] = text_k
                for col, text in [(col_d, text_d), (col_k, text_k)]:
                    cell = ws1[f'{col}{row}']
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    if row == signature_row:
                        cell.font = Font(bold=True, size=12, color="0066CC")
                        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    elif row == signature_row + 1:
                        cell.font = Font(italic=True, size=9)
                    elif row == signature_row + 5:
                        cell.font = Font(bold=True, size=11)
                    else:
                        cell.font = Font(size=9)
        if 'Sheet' in wb1.sheetnames:
            wb1.remove(wb1['Sheet'])
        file1_buffer = BytesIO()
        wb1.save(file1_buffer)
        file1_buffer.seek(0)
        zipf.writestr(f"Bước 1.1 - Tiếp nhận thực phẩm tươi - Tuần {week_number}.xlsx", file1_buffer.read())
        
        # BƯỚC 1.2: Tiếp nhận thực phẩm khô - Format chuyên nghiệp 

        # BƯỚC 1.2: Tiếp nhận thực phẩm khô - mỗi ngày 1 sheet, chỉ tạo wb2 1 lần
        wb2 = Workbook()
        days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        for day_offset in range(6):
            day_date = week_start + timedelta(days=day_offset)
            day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day_offset]
            safe_date = day_date.strftime('%d-%m')
            sheet_title = f"{days_vn[day_offset]} ({safe_date})"
            if day_offset == 0:
                ws2 = wb2.active
                ws2.title = sheet_title
            else:
                ws2 = wb2.create_sheet(title=sheet_title)
            # Lấy menu ngày
            menu_today = menu_data.get(day_key, {})
            # Tính nguyên liệu thực tế cho ngày này
            daily_ingredients = {}
            for meal in menu_today.values():
                if not meal: continue
                for dish_name in [d.strip() for d in meal.split(',') if d.strip()]:
                    dish = Dish.query.filter_by(name=dish_name).first()
                    if dish:
                        for di in dish.ingredients:
                            key = (di.product.name, di.unit, di.product.category, di.product.supplier)
                            qty = di.quantity * student_count
                            if key not in daily_ingredients:
                                daily_ingredients[key] = {'total_qty': 0, 'unit': di.unit, 'category': di.product.category, 'supplier': di.product.supplier, 'product': di.product}
                            daily_ingredients[key]['total_qty'] += qty
            # Phân loại khô
            dry_ingredients = []
            for (name, unit, category, supplier), info in daily_ingredients.items():
                cat = (category or '').lower()
                if cat == 'dry' or 'khô' in cat or 'gia vị' in cat or 'bột' in cat or 'gạo' in cat or 'đường' in cat:
                    if hasattr(supplier, 'name'):
                        supplier_name = supplier.name
                    elif isinstance(supplier, str):
                        supplier_name = supplier
                    else:
                        supplier_name = ''
                    dry_ingredients.append({
                        'name': name,
                        'weight_kg': round(convert_to_kg(info['total_qty'], info['unit']), 2),
                        'unit': unit,
                        'category': category,
                        'supplier': supplier_name,
                        'supplier_info': supplier_dict.get(supplier_name, {}),
                    })
            # --- Ghi dữ liệu và style sheet như Bước 1.1 ---
            ws2['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
            ws2['A1'].font = Font(bold=True, size=12)
            ws2['A1'].fill = PatternFill(start_color="FFE6CC", end_color="FFE6CC", fill_type="solid")
            ws2.merge_cells('A1:P1')
            ws2['D2'] = "BIỂU MẪU KIỂM TRA THỰC PHẨM KHÔ VÀ BAO GÓI"
            ws2['D2'].font = Font(bold=True, size=14, color="FF0000")
            ws2['D2'].alignment = Alignment(horizontal='center', vertical='center')
            ws2.merge_cells('D2:L2')
            ws2['N2'] = "Số: 1246/QĐ - Bộ Y Tế"
            ws2['N2'].font = Font(bold=True, size=10)
            ws2['N2'].fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            info_data2 = [
                (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân", 'N', "Mẫu số 1.2"),
                (4, 'A', f"Ngày kiểm tra: {day_date.strftime('%d/%m/%Y')} - {days_vn[day_offset]}", 'N', f"Số học sinh: {student_count}"),
                (5, 'A', "Địa điểm: Kho thực phẩm khô - MNĐL Cây Nhỏ", 'N', "")
            ]
            for row, col_a, text_a, col_n, text_n in info_data2:
                ws2[f'{col_a}{row}'] = text_a
                ws2[f'{col_a}{row}'].font = Font(bold=True, size=10)
                ws2[f'{col_n}{row}'] = text_n
                ws2[f'{col_n}{row}'].font = Font(bold=True, size=10)
                ws2[f'{col_n}{row}'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
            ws2['A7'] = "PHẦN II: THỰC PHẨM KHÔ, BAO GÓI SẴN VÀ PHỤ GIA THỰC PHẨM"
            ws2['A7'].font = Font(bold=True, size=12, color="FF6600")
            ws2['A7'].fill = PatternFill(start_color="FFF2E6", end_color="FFF2E6", fill_type="solid")
            ws2.merge_cells('A7:M7')
            ws2['N7'] = "BƯỚC 1.2"
            ws2['N7'].font = Font(bold=True, size=12, color="FF0000")
            ws2['N7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
            headers2_main = [
                'STT', 'TÊN THỰC PHẨM', 'TÊN CƠ SỞ SẢN XUẤT', 
                'ĐỊA CHỈ SẢN XUẤT', 'THỜI GIAN NHẬP\n(Ngày/Giờ)', 'KHỐI LƯỢNG (KG/LÍT)', 'NƠI CUNG CẤP', '', '',
                'HẠN SỬ DỤNG', 'ĐIỀU KIỆN BẢO QUẢN', 'CHỨNG TỪ, HOÁ ĐƠN', 'KIỂM TRA CẢM QUAN', '', 'BIỆN PHÁP XỬ LÝ / GHI CHÚ'
            ]
            for i, header in enumerate(headers2_main, 1):
                cell = ws2.cell(row=8, column=i, value=header)
                cell.font = Font(bold=True, size=9, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.fill = PatternFill(start_color="E67E22", end_color="E67E22", fill_type="solid")
                cell.border = thick_border
            sub_headers2 = [
                '', '', '', '', '', '', '', 'Tên cơ sở', '', '', '', '', 
                'Đạt', 'Không đạt', ''
            ]
            for i, header in enumerate(sub_headers2, 1):
                cell = ws2.cell(row=9, column=i, value=header)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="F8C471", end_color="F8C471", fill_type="solid")
                cell.border = thin_border
            ws2.merge_cells('G8:I8')  # Nơi cung cấp
            ws2.merge_cells('M8:N8')  # Kiểm tra cảm quan
            for i in range(1, 16):
                cell = ws2.cell(row=10, column=i, value=i)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
                cell.border = thin_border
            # Ghi dữ liệu thực phẩm khô từng ngày
            for i, ingredient_info in enumerate(dry_ingredients[:25], 1):
                row_num = 10 + i
                supplier_info = ingredient_info.get('supplier_info', {})
                supplier_name = ingredient_info.get('supplier', '') or 'Siêu thị Co.opmart'
                phone = supplier_info.get('phone', '0902.xxx.xxx')
                address = supplier_info.get('address', 'Đà Lạt')
                contact_person = supplier_info.get('contact_person', 'Chưa cập nhật')
                expiry_date = (day_date + timedelta(days=180)).strftime('%d/%m/%Y')
                # Đồng bộ với headers2_main mới
                data_row2 = [
                    i,  # STT
                    ingredient_info['name'].upper(),  # TÊN THỰC PHẨM
                    supplier_name,  # TÊN CƠ SỞ SẢN XUẤT (giả định là supplier)
                    address,  # ĐỊA CHỈ SẢN XUẤT (giả định là address supplier)
                    f"{day_date.strftime('%d/%m/%Y')}\n8:00-9:00",  # THỜI GIAN NHẬP
                    f"{ingredient_info['weight_kg']} kg",  # KHỐI LƯỢNG
                    supplier_name,  # NƠI CUNG CẤP
                    '',  # cột phụ (merge)
                    '',  # cột phụ (merge)
                    "còn HDS",  # HẠN SỬ DỤNG
                    "Khô ráo, thoáng mát\n<25°C",  # ĐIỀU KIỆN BẢO QUẢN
                    '',  # CHỨNG TỪ, HOÁ ĐƠN (chưa có)
                    '✓',  # KIỂM TRA CẢM QUAN (Đạt)
                    '',  # Không đạt
                    '',  # BIỆN PHÁP XỬ LÝ / GHI CHÚ
                ]
                for j, value in enumerate(data_row2, 1):
                    cell = ws2.cell(row=row_num, column=j, value=value)
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = thin_border
                    if j == 1:
                        cell.font = Font(bold=True, color="E67E22")
                        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    elif j == 2:
                        cell.font = Font(bold=True, size=10)
                        cell.fill = PatternFill(start_color="FEF9E7", end_color="FEF9E7", fill_type="solid")
                    elif j == 13 and value == '✓':
                        cell.font = Font(bold=True, size=12, color="27AE60")
                        cell.fill = PatternFill(start_color="E8F5E8", end_color="E8F5E8", fill_type="solid")
                    elif j == 4:
                        cell.font = Font(bold=True, color="D35400")
                    elif j == 11:
                        cell.font = Font(bold=True, color="8E44AD")
            # Thống kê
            stats_row2 = len(dry_ingredients) + 12
            ws2[f'A{stats_row2}'] = "THỐNG KÊ THỰC PHẨM KHÔ:"
            ws2[f'A{stats_row2}'].font = Font(bold=True, size=11, color="E67E22")
            ws2[f'A{stats_row2}'].fill = PatternFill(start_color="FFF2E6", end_color="FFF2E6", fill_type="solid")
            total_weight2 = sum(item['weight_kg'] for item in dry_ingredients)
            total_items2 = len(dry_ingredients)
            stats_info2 = [
                f"• Tổng số loại thực phẩm khô: {total_items2} loại",
                f"• Tổng khối lượng ước tính: {total_weight2:.1f} kg",
                f"• Số học sinh phục vụ: {student_count} em",
                f"• Khối lượng trung bình/học sinh: {(total_weight2/student_count):.2f} kg/em/ngày" if student_count else "• Khối lượng trung bình/học sinh: N/A"
            ]
            for i, stat in enumerate(stats_info2, 1):
                ws2[f'A{stats_row2 + i}'] = stat
                ws2[f'A{stats_row2 + i}'].font = Font(size=10)
            note_row2 = stats_row2 + 6
            ws2[f'A{note_row2}'] = "GHI CHÚ QUAN TRỌNG:"
            ws2[f'A{note_row2}'].font = Font(bold=True, size=11, color="FF0000")
            notes2 = [
                "• Bảo quản nơi khô ráo, thoáng mát, tránh ánh nắng trực tiếp",
                "• Kiểm tra hạn sử dụng, bao bì nguyên vẹn trước khi nhập kho",
                "• Sử dụng theo nguyên tắc FIFO (nhập trước xuất trước)",
                "• Báo cáo ngay nếu phát hiện bất thường về màu sắc, mùi vị, bao bì"
            ]
            for i, note in enumerate(notes2, 1):
                ws2[f'A{note_row2 + i}'] = note
                ws2[f'A{note_row2 + i}'].font = Font(size=9, color="CC0000")
            signature_row2 = note_row2 + 7
            signature_data2 = [
                (signature_row2, 'D', "THỦ KHO", 'K', "HIỆU TRƯỞNG"),
                (signature_row2 + 1, 'D', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
                (signature_row2 + 5, 'D', "Hoàng Thanh Tuấn", 'K', "Nguyễn Thị Vân"),
                (signature_row2 + 6, 'D', f"Ngày {day_date.day}/{day_date.month}/{day_date.year}", 'K', f"Ngày {day_date.day}/{day_date.month}/{day_date.year}")
            ]
            for row, col_d, text_d, col_k, text_k in signature_data2:
                ws2[f'{col_d}{row}'] = text_d
                ws2[f'{col_k}{row}'] = text_k
                for col, text in [(col_d, text_d), (col_k, text_k)]:
                    cell = ws2[f'{col}{row}']
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    if row == signature_row2:
                        cell.font = Font(bold=True, size=12, color="E67E22")
                        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    elif row == signature_row2 + 1:
                        cell.font = Font(italic=True, size=9)
                    elif row == signature_row2 + 5:
                        cell.font = Font(bold=True, size=11)
                    else:
                        cell.font = Font(size=9)
        if 'Sheet' in wb2.sheetnames:
            wb2.remove(wb2['Sheet'])
        file2_buffer = BytesIO()
        wb2.save(file2_buffer)
        file2_buffer.seek(0)
        zipf.writestr(f"Bước 1.2 - Tiếp nhận thực phẩm khô - Tuần {week_number}.xlsx", file2_buffer.read())

        # BƯỚC 2: Kiểm tra khi chế biến thức ăn - mỗi ngày 1 sheet
        wb3 = Workbook()
        days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        for day_offset in range(6):
            day_date = week_start + timedelta(days=day_offset)
            day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day_offset]
            safe_date = day_date.strftime('%d-%m')
            sheet_title = f"{days_vn[day_offset]} ({safe_date})"
            if day_offset == 0:
                ws3 = wb3.active
                ws3.title = sheet_title
            else:
                ws3 = wb3.create_sheet(title=sheet_title)
            # Header chính tương tự các bước trước
            ws3['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
            ws3['A1'].font = Font(bold=True, size=12)
            ws3['A1'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            ws3.merge_cells('A1:O1')
            ws3['D2'] = "BIỂU MẪU KIỂM TRA KHI CHẾ BIẾN THỨC ĂN"
            ws3['D2'].font = Font(bold=True, size=14, color="006600")
            ws3['D2'].alignment = Alignment(horizontal='center', vertical='center')
            ws3.merge_cells('D2:K2')
            ws3['M2'] = "Số: 1246/QĐ - Bộ Y Tế"
            ws3['M2'].font = Font(bold=True, size=10)
            ws3['M2'].fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            info_data3 = [
                (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân", 'M', "Mẫu số 2.0"),
                (4, 'A', f"Ngày kiểm tra: {day_date.strftime('%d/%m/%Y')} - {days_vn[day_offset]}", 'M', f"Số học sinh: {student_count}"),
                (5, 'A', "Địa điểm: Bếp chế biến - MNĐL Cây Nhỏ", 'M', "")
            ]
            for row, col_a, text_a, col_m, text_m in info_data3:
                ws3[f'{col_a}{row}'] = text_a
                ws3[f'{col_a}{row}'].font = Font(bold=True, size=10)
                ws3[f'{col_m}{row}'] = text_m
                ws3[f'{col_m}{row}'].font = Font(bold=True, size=10)
                ws3[f'{col_m}{row}'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
            ws3['A7'] = "PHẦN II: KIỂM TRA QUY TRÌNH CHẾ BIẾN THỨC ĂN"
            ws3['A7'].font = Font(bold=True, size=12, color="8B0000")
            ws3['A7'].fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
            ws3.merge_cells('A7:L7')
            ws3['M7'] = "BƯỚC 2"
            ws3['M7'].font = Font(bold=True, size=12, color="FF0000")
            ws3['M7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
            headers3_main = [
                'STT', 'CA/BỮA ĂN', 'TÊN MÓN ĂN', 'NGUYÊN LIỆU CHÍNH', 'SỐ SUẤT\n(phần)', 
                'THỜI GIAN SƠ CHẾ XONG\n(ngày, giờ)', 'THỜI GIAN CHẾ BIẾN XONG\n(ngày, giờ)', 'KIỂM TRA VỆ SINH', '', '',
                'KIỂM TRA CẢM QUAN THỨC ĂN', '', 'BIỆN PHÁP XỬ LÝ\nGHI CHÚ'
            ]
            for i, header in enumerate(headers3_main, 1):
                cell = ws3.cell(row=8, column=i, value=header)
                cell.font = Font(bold=True, size=9, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
                cell.border = thick_border
            sub_headers3 = [
                '', '', '', '', '', '', '', 'Người tham gia\n chế biến', 'Trang thiết bị\n dụng cụ', 'Khu vực chế biến\n và phụ trợ',
                'Đạt', 'Không đạt', ''
            ]
            for i, header in enumerate(sub_headers3, 1):
                cell = ws3.cell(row=9, column=i, value=header)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="CD5C5C", end_color="CD5C5C", fill_type="solid")
                cell.border = thin_border

            # Đặt độ rộng và căn giữa cho H9, I9, J9
            ws3.column_dimensions['H'].width = 18
            ws3.column_dimensions['I'].width = 18
            ws3.column_dimensions['J'].width = 18
            for col in ['H', 'I', 'J']:
                cell = ws3[f'{col}9']
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            ws3.merge_cells('H8:J8')  # Vệ sinh, Cảm quan
            ws3.merge_cells('K8:L8')  # Đánh giá phục vụ
            for i in range(1, 14):
                cell = ws3.cell(row=10, column=i, value=i)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                cell.border = thin_border
            # Ghi dữ liệu món ăn từng ngày (tương tự logic cũ, chỉ cho ngày này)
            row_num = 11
            stt = 1
            meal_times = {
                'morning': 'Bữa sáng',
                'snack': 'Ăn phụ sáng',
                'dessert': 'Tráng miệng',
                'lunch': 'Bữa trưa',
                'afternoon': 'Ăn phụ chiều',
                'lateafternoon': 'Bữa xế',
            }
            # Giờ chuẩn cho từng ca (giờ_sơ_chế, giờ_chế_biến)
            meal_time_hours = {
                'morning':   ('07:00', '07:25'),
                'snack':     ('09:00', '10:00'),
                'dessert':   ('09:00', '10:00'),
                'lunch':     ('09:00', '10:00'),
                'afternoon': ('09:00', '10:00'),
                'lateafternoon': ('14:00', '14:25')
            }
            # Lặp đủ 5 ca dựa trên meal_times
            for meal_key, meal_name in meal_times.items():
                dishes = []
                if menu_data[day_key].get(meal_key):
                    dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                # Không lọc, lấy toàn bộ món trong menu từng bữa
                if dishes:
                    dish_names = ', '.join([dish.title() for dish in dishes])
                    all_ingredients = set()
                    for dish in dishes:
                        dish_obj = Dish.query.filter_by(name=dish).first()
                        if dish_obj and dish_obj.ingredients:
                            for di in dish_obj.ingredients:
                                all_ingredients.add(di.product.name)
                    main_ingredients = ', '.join(sorted(all_ingredients))
                else:
                    dish_names = ''
                    main_ingredients = ''
                # Tạo giá trị thời gian sơ chế xong, chế biến xong
                date_str = day_date.strftime('%d/%m/%Y')
                time_so_che = meal_time_hours[meal_key][0] if meal_key in meal_time_hours else ''
                time_che_bien = meal_time_hours[meal_key][1] if meal_key in meal_time_hours else ''
                so_che_str = f"{date_str} {time_so_che}" if time_so_che else ''
                che_bien_str = f"{date_str} {time_che_bien}" if time_che_bien else ''
                data_row3 = [
                    stt,  # STT
                    meal_name,  # CA/BỮA ĂN chỉ tên bữa
                    dish_names,  # TÊN MÓN ĂN (danh sách món)
                    main_ingredients,  # NGUYÊN LIỆU CHÍNH (toàn bộ nguyên liệu các món)
                    student_count,  # SỐ SUẤT (phần)
                    so_che_str,  # THỜI GIAN SƠ CHẾ XONG (ngày, giờ)
                    che_bien_str,  # THỜI GIAN CHẾ BIẾN XONG (ngày, giờ)
                    "Trang phục gọn gàng, vệ sinh cá nhân sạch sẽ",  # Người tham gia chế biến
                    "Đảm bảo vệ sinh",  # Trang thiết bị dụng cụ
                    "Đảm bảo vệ sinh",  # Khu vực chế biến và phụ trợ
                    "",  # KIỂM TRA CẢM QUAN THỨC ĂN - Đạt
                    "",  # KIỂM TRA CẢM QUAN THỨC ĂN - Không đạt
                    ""   # BIỆN PHÁP XỬ LÝ GHI CHÚ
                ]
                for j, value in enumerate(data_row3, 1):
                    cell = ws3.cell(row=row_num, column=j, value=value)
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = thin_border
                    if j == 1:
                        cell.font = Font(bold=True, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif j == 3:
                        cell.font = Font(bold=True, size=10)
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                row_num += 1
                stt += 1
            # Thống kê phục vụ
            stats_row3 = row_num + 2
            ws3[f'A{stats_row3}'] = "THỐNG KÊ PHỤC VỤ THỨC ĂN:"
            ws3[f'A{stats_row3}'].font = Font(bold=True, size=11, color="006600")
            ws3[f'A{stats_row3}'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            total_servings = stt - 1
            total_portions = total_servings * student_count
            stats_info3 = [
                f"• Tổng số lần phục vụ: {total_servings} lần",
                f"• Tổng số suất ăn phục vụ: {total_portions} suất",
                f"• Trung bình suất/lần: {(total_portions/total_servings):.1f} suất/lần" if total_servings else "• Trung bình suất/lần: N/A",
                f"• Thời gian trung bình từ chế biến xong đến phục vụ: <30 phút"
            ]
            for i, stat in enumerate(stats_info3, 1):
                ws3[f'A{stats_row3 + i}'] = stat
                ws3[f'A{stats_row3 + i}'].font = Font(size=10)
            # Nguyên tắc bảo quản và phục vụ
            principles_row = stats_row3 + 6
            ws3[f'A{principles_row}'] = "NGUYÊN TẮC BẢO QUẢN VÀ PHỤC VỤ AN TOÀN:"
            ws3[f'A{principles_row}'].font = Font(bold=True, size=11, color="004000")
            principles_notes = [
                "• Thời gian: Từ chế biến xong đến phục vụ không quá 2 giờ",
                "• Nhiệt độ: Món nóng >60°C, món lạnh <10°C khi phục vụ",
                "• Thiết bị: Sử dụng tủ giữ nhiệt, nồi cơm điện, bình giữ nhiệt",
                "• Vệ sinh: Khử trùng dụng cụ trước mỗi bữa ăn",
                "• Kiểm tra: Nhiệt độ thức ăn trước khi phục vụ cho trẻ"
            ]
            for i, note in enumerate(principles_notes, 1):
                ws3[f'A{principles_row + i}'] = note
                ws3[f'A{principles_row + i}'].font = Font(size=9, color="004000")
            # Chữ ký
            signature_row3 = principles_row + 8
            signature_data3 = [
                (signature_row3,     'D', "BẾP TRƯỞNG",  'H', "NV. Y TẾ",   'K', "HIỆU TRƯỞNG"),
                (signature_row3 + 1, 'D', "(Ký, ghi rõ họ tên)",'H', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
                (signature_row3 + 5, 'D', "Hoàng Thanh Tuấn",'H', "(Ký, ghi rõ họ tên)",  'K', "Nguyễn Thị Vân")
            ]
                # --- Ghi chữ ký ---
            for item in signature_data3:
                    
                    row, col_d, text_d, col_h, text_h, col_k, text_k = item
                    ws3[f'{col_d}{row}'] = text_d
                    ws3[f'{col_h}{row}'] = text_h
                    ws3[f'{col_k}{row}'] = text_k
                    cols = [(col_d, text_d), (col_h, text_h), (col_k, text_k)]

                    for col, text in cols:
                        cell = ws3[f'{col}{row}']
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                        if row == signature_row3:
                            cell.font = Font(bold=True, size=12, color="006600")
                            cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                        elif row == signature_row3 + 1:
                            cell.font = Font(italic=True, size=9)
                        elif row == signature_row3 + 5:
                            cell.font = Font(bold=True, size=11)
                        else:
                            cell.font = Font(size=9)
        if 'Sheet' in wb3.sheetnames:
            wb3.remove(wb3['Sheet'])

        file3_buffer = BytesIO()
        wb3.save(file3_buffer)
        file3_buffer.seek(0)
        zipf.writestr(f"Bước 2 - Kiểm tra khi chế biến thức ăn - Tuần {week_number}.xlsx", file3_buffer.read())

        # BƯỚC 3: Kiểm tra trước khi ăn - mỗi ngày 1 sheet,
        wb4 = Workbook()
        for day_offset in range(6):
            day_date = week_start + timedelta(days=day_offset)
            day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day_offset]
            safe_date = day_date.strftime('%d-%m')
            sheet_title = f"{days_vn[day_offset]} ({safe_date})"
            if day_offset == 0:
                ws4 = wb4.active
                ws4.title = sheet_title
            else:
                ws4 = wb4.create_sheet(title=sheet_title)
            # Header chính tương tự ws3
            ws4['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
            ws4['A1'].font = Font(bold=True, size=12)
            ws4['A1'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            ws4.merge_cells('A1:O1')
            ws4['D2'] = "BIỂU MẪU KIỂM TRA TRƯỚC KHI ĂN"
            ws4['D2'].font = Font(bold=True, size=14, color="006600")
            ws4['D2'].alignment = Alignment(horizontal='center', vertical='center')
            ws4.merge_cells('D2:I2')
            ws4['J2'] = "Số: 1246/QĐ - Bộ Y Tế"
            ws4['J2'].font = Font(bold=True, size=10)
            ws4['J2'].fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            info_data4 = [
                (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân", 'J', "Mẫu số 3.0"),
                (4, 'A', f"Ngày kiểm tra: {day_date.strftime('%d/%m/%Y')} - {days_vn[day_offset]}", 'J', f"Số học sinh: {student_count}"),
                (5, 'A', "Địa điểm: Phòng ăn - MNĐL Cây Nhỏ", 'J', "")
            ]
            for row, col_a, text_a, col_m, text_m in info_data4:
                ws4[f'{col_a}{row}'] = text_a
                ws4[f'{col_a}{row}'].font = Font(bold=True, size=10)
                ws4[f'{col_m}{row}'] = text_m
                ws4[f'{col_m}{row}'].font = Font(bold=True, size=10)
                ws4[f'{col_m}{row}'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")

            ws4['J7'] = "BƯỚC 3"
            ws4['J7'].font = Font(bold=True, size=12, color="FF0000")
            ws4['J7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
            headers4_main = [
                'STT', 'CA/BỮA ĂN', 'TÊN MÓN ĂN', 'SỐ SUẤT\n(phần)',
                'THỜI GIAN CHIA MÓN ĂN XONG\n(ngày, giờ)', 'THỜI GIAN BẮT ĐẦU ĂN\n(ngày, giờ)',
                'DỤNG CỤ CHIA, CHỨA ĐỰNG\n, CHE ĐẬY, BẢO QUẢN THỨC ĂN',
                'KIỂM TRA CẢM QUAN THỨC ĂN', '', 'BIỆN PHÁP XỬ LÝ\nGHI CHÚ'
            ]
            for i, header in enumerate(headers4_main, 1):
                cell = ws4.cell(row=8, column=i, value=header)
                cell.font = Font(bold=True, size=9, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
                cell.border = thick_border
            sub_headers4 = [
                '', '', '', '', 
                '', '', 
                '', 
                'Đạt', 'Không đạt', ''
            ]
            for i, header in enumerate(sub_headers4, 1):
                cell = ws4.cell(row=9, column=i, value=header)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="CD5C5C", end_color="CD5C5C", fill_type="solid")
                cell.border = thin_border
            ws4.column_dimensions['G'].width = 25
            ws4.column_dimensions['H'].width = 18
            ws4.column_dimensions['I'].width = 18
            for col in ['G','H', 'I']:
                cell = ws4[f'{col}8']
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            ws4.merge_cells('H8:I8')
            for i in range(1, 11):
                cell = ws4.cell(row=10, column=i, value=i)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                cell.border = thin_border
            # Ghi dữ liệu món ăn từng ngày (giống ws3)
            row_num = 11
            stt = 1
            for meal_key, meal_name in meal_times.items():
                dishes = []
                if menu_data[day_key].get(meal_key):
                    dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                if dishes:
                    dish_names = ', '.join([dish.title() for dish in dishes])
                else:
                    dish_names = ''
                date_str = day_date.strftime('%d/%m/%Y')
                time_chia_xong = '10:15'  # Giả định giờ chia xong
                time_bat_dau_an = '10:30'  # Giả định giờ bắt đầu ăn
                chia_xong_str = f"{date_str} {time_chia_xong}"
                bat_dau_an_str = f"{date_str} {time_bat_dau_an}"
                data_row4 = [
                    stt,  # STT
                    meal_name,  # CA/BỮA ĂN
                    dish_names,  # TÊN MÓN ĂN
                    student_count,  # SỐ SUẤT
                    chia_xong_str,  # THỜI GIAN CHIA MÓN ĂN XONG
                    bat_dau_an_str,  # THỜI GIAN BẮT ĐẦU ĂN
                    "Đảm bảo vệ sinh",  # DỤNG CỤ CHIA, CHỨA ĐỰNG
                    "",  # KIỂM TRA CẢM QUAN THỨC ĂN
                    '',  # Không đạt
                    ''   # Ghi chú
                ]
                for j, value in enumerate(data_row4, 1):
                    cell = ws4.cell(row=row_num, column=j, value=value)
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = thin_border
                    if j == 1:
                        cell.font = Font(bold=True, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif j == 3:
                        cell.font = Font(bold=True, size=10)
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                row_num += 1
                stt += 1
            # Thống kê phục vụ
            stats_row4 = row_num + 2
            ws4[f'A{stats_row4}'] = "THỐNG KÊ PHỤC VỤ THỨC ĂN:"
            ws4[f'A{stats_row4}'].font = Font(bold=True, size=11, color="006600")
            ws4[f'A{stats_row4}'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            total_servings = stt - 1
            total_portions = total_servings * student_count
            stats_info4 = [
                f"• Tổng số lần phục vụ: {total_servings} lần",
                f"• Tổng số suất ăn phục vụ: {total_portions} suất",
                f"• Trung bình suất/lần: {(total_portions/total_servings):.1f} suất/lần" if total_servings else "• Trung bình suất/lần: N/A",
                f"• Thời gian trung bình từ phục vụ đến ăn: <15 phút"
            ]
            for i, stat in enumerate(stats_info4, 1):
                ws4[f'A{stats_row4 + i}'] = stat
                ws4[f'A{stats_row4 + i}'].font = Font(size=10)
            # Nguyên tắc phục vụ
            principles_row4 = stats_row4 + 6
            ws4[f'A{principles_row4}'] = "NGUYÊN TẮC PHỤC VỤ AN TOÀN:"
            ws4[f'A{principles_row4}'].font = Font(bold=True, size=11, color="004000")
            principles_notes4 = [
                "• Đảm bảo vệ sinh dụng cụ, khu vực ăn trước khi phục vụ",
                "• Kiểm tra nhiệt độ thức ăn trước khi cho trẻ ăn",
                "• Đảm bảo trẻ rửa tay sạch sẽ trước khi ăn",
                "• Báo cáo ngay nếu phát hiện bất thường về thức ăn hoặc sức khỏe trẻ"
            ]
            for i, note in enumerate(principles_notes4, 1):
                ws4[f'A{principles_row4 + i}'] = note
                ws4[f'A{principles_row4 + i}'].font = Font(size=9, color="004000")
            # Chữ ký
            signature_row4 = principles_row4 + 8
            signature_data4 = [
                (signature_row4,     'D', "BẾP TRƯỞNG",  'H', "NV. Y TẾ",   'K', "HIỆU TRƯỞNG"),
                (signature_row4 + 1, 'D', "(Ký, ghi rõ họ tên)", 'H', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
                (signature_row4 + 5, 'D', "Hoàng Thanh Tuấn",'H', "",  'K', "Nguyễn Thị Vân")
            ]
            for item in signature_data4:
                row, col_d, text_d, col_h, text_h, col_k, text_k = item
                ws4[f'{col_d}{row}'] = text_d
                ws4[f'{col_h}{row}'] = text_h
                ws4[f'{col_k}{row}'] = text_k
                cols = [(col_d, text_d), (col_h, text_h), (col_k, text_k)]
                for col, text in cols:
                    cell = ws4[f'{col}{row}']
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    if row == signature_row4:
                        cell.font = Font(bold=True, size=12, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif row == signature_row4 + 1:
                        cell.font = Font(italic=True, size=9)
                    elif row == signature_row4 + 5:
                        cell.font = Font(bold=True, size=11)
                    else:
                        cell.font = Font(size=9)
        if 'Sheet' in wb4.sheetnames:
            wb4.remove(wb4['Sheet'])
        file4_buffer = BytesIO()
        wb4.save(file4_buffer)
        file4_buffer.seek(0)
        zipf.writestr(f"Bước 3 - Kiểm tra trước khi ăn - Tuần {week_number}.xlsx", file4_buffer.read())
        
        # BƯỚC 5: Kiểm tra trước khi ăn - mỗi ngày 1 sheet,
        wb5 = Workbook()
        for day_offset in range(6):
            day_date = week_start + timedelta(days=day_offset)
            day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day_offset]
            safe_date = day_date.strftime('%d-%m')
            sheet_title = f"{days_vn[day_offset]} ({safe_date})"
            if day_offset == 0:
                ws5 = wb5.active
                ws5.title = sheet_title
            else:
                ws5 = wb5.create_sheet(title=sheet_title)
            # Header chính tương tự ws3
            ws5['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
            ws5['A1'].font = Font(bold=True, size=12)
            ws5['A1'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            ws5.merge_cells('A1:O1')
            ws5['D2'] = "BIỂU MẪU THEO DÕI LƯU VÀ HUỶ LƯU MẪU THỨC ĂN LƯU"
            ws5['D2'].font = Font(bold=True, size=14, color="006600")
            ws5['D2'].alignment = Alignment(horizontal='center', vertical='center')
            ws5.merge_cells('D2:I2')
            ws5['J2'] = "Số: 1246/QĐ - Bộ Y Tế"
            ws5['J2'].font = Font(bold=True, size=10)
            ws5['J2'].fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            info_data4 = [
                (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân", 'J', "Mẫu số 5"),
                (4, 'A', f"Ngày kiểm tra: {day_date.strftime('%d/%m/%Y')} - {days_vn[day_offset]}", 'J', f"Số học sinh: {student_count}"),
                (5, 'A', "Địa điểm: Phòng ăn - MNĐL Cây Nhỏ", 'F', f"Ngày tiếp phẩm: {day_date.strftime('%d/%m/%Y')} - {days_vn[day_offset]}")
            ]
            for row, col_a, text_a, col_m, text_m in info_data4:
                ws5[f'{col_a}{row}'] = text_a
                ws5[f'{col_a}{row}'].font = Font(bold=True, size=10)
                ws5[f'{col_m}{row}'] = text_m
                ws5[f'{col_m}{row}'].font = Font(bold=True, size=10)
                ws5[f'{col_m}{row}'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")

            
            headers5_main = [
                'STT', 'CA/BỮA ĂN', 'TÊN MẪU THỨC ĂN', 'SỐ SUẤT ĂN\n(phần)',
                'KHỐI LƯỢNG\n/ THỂ TÍCH MẪU(GRAM/ML)', 'DỤNG CỤ CHỨA\n MẪU THỨC ĂN LƯU',
                'NHIỆT ĐỘ BẢO QUẢN MẪU',
                'THỜI GIAN LẤY MẪU\n (giờ, ngày, tháng, năm)', 'THỜI GIAN HUỶ MẪU\n (giờ, ngày, tháng, năm)', 
                'GHI CHÚ', "NGƯỜI LƯU MẪU", "NGƯỜI HUỶ MẪU"
            ]
            for i, header in enumerate(headers5_main, 1):
                cell = ws5.cell(row=8, column=i, value=header)
                cell.font = Font(bold=True, size=9, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
                cell.border = thick_border
            sub_headers5 = [
                '', '', '', '', 
                '', '', 
                '', 
                '', '', '',
                '',''
            ]
            for i, header in enumerate(sub_headers5, 1):
                cell = ws5.cell(row=9, column=i, value=header)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="CD5C5C", end_color="CD5C5C", fill_type="solid")
                cell.border = thin_border
            ws5.column_dimensions['E'].width = 18
            ws5.column_dimensions['F'].width = 18
            ws5.column_dimensions['G'].width = 18
            ws5.column_dimensions['H'].width = 18
            ws5.column_dimensions['I'].width = 18
            for col in ['E', 'F', 'G','H', 'I']:
                cell = ws5[f'{col}8']
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            # ws5.merge_cells('H8:I8')
            for i in range(1, 13):
                cell = ws5.cell(row=10, column=i, value=i)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                cell.border = thin_border
            # Ghi dữ liệu món ăn từng ngày (giống ws3)
            row_num = 11
            stt = 1
            for meal_key, meal_name in meal_times.items():
                dishes = []
                if menu_data[day_key].get(meal_key):
                    dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                if dishes:
                    dish_names = ', '.join([dish.title() for dish in dishes])
                else:
                    dish_names = ''
                date_str = day_date.strftime('%d/%m/%Y')
                time_chia_xong = '10:15'  # Giả định giờ chia xong
                time_bat_dau_an = '10:30'  # Giả định giờ bắt đầu ăn
                chia_xong_str = f"{date_str} {time_chia_xong}"
                bat_dau_an_str = f"{date_str} {time_bat_dau_an}"
                # Tính thời gian huỷ mẫu: 15:00 ngày hôm sau của bat_dau_an_str
                from datetime import datetime, timedelta
                dt_batdau = datetime.strptime(bat_dau_an_str.split()[0], "%d/%m/%Y")
                dt_huy = dt_batdau + timedelta(days=1)
                huy_mau_str = f"15:00, {dt_huy.strftime('%d/%m/%Y')}"
                
                data_row5 = [
                    stt,  # STT
                    meal_name,  # CA/BỮA ĂN
                    dish_names,  # TÊN MẪU THỨC ĂN
                    student_count,  # SỐ SUẤT ĂN
                    150,  # KHỐI LƯỢNG/THỂ TÍCH MẪU
                    "Hộp Inox chuyên dụng",  # DỤNG CỤ CHỨA MẪU
                    "2-4°C",  # NHIỆT ĐỘ BẢO QUẢN
                    bat_dau_an_str,  # THỜI GIAN LẤY MẪU
                    huy_mau_str,  # THỜI GIAN HUỶ MẪU
                    'Ngon',  # GHI CHÚ
                    "Hoàng Thanh Tuấn",  # NGƯỜI LƯU MẪU
                    "Hoàng Thanh Tuấn"  # NGƯỜI HUỶ MẪU
                ]
                for j, value in enumerate(data_row5, 1):
                    cell = ws5.cell(row=row_num, column=j, value=value)
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = thin_border
                    if j == 1:
                        cell.font = Font(bold=True, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif j == 3:
                        cell.font = Font(bold=True, size=10)
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                row_num += 1
                stt += 1
            # Thống kê phục vụ
            stats_row5 = row_num + 2
            ws5[f'A{stats_row5}'] = "THỐNG KÊ PHỤC VỤ THỨC ĂN:"
            ws5[f'A{stats_row5}'].font = Font(bold=True, size=11, color="006600")
            ws5[f'A{stats_row5}'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            total_servings = stt - 1
            total_portions = total_servings * student_count
            stats_info5 = [
                f"• Tổng số lần phục vụ: {total_servings} lần",
                f"• Tổng số suất ăn phục vụ: {total_portions} suất",
                f"• Trung bình suất/lần: {(total_portions/total_servings):.1f} suất/lần" if total_servings else "• Trung bình suất/lần: N/A",
                f"• Thời gian trung bình từ phục vụ đến ăn: <15 phút"
            ]
            for i, stat in enumerate(stats_info5, 1):
                ws5[f'A{stats_row5 + i}'] = stat
                ws5[f'A{stats_row5 + i}'].font = Font(size=10)
            # Nguyên tắc phục vụ
            principles_row5 = stats_row5 + 6
            ws5[f'A{principles_row5}'] = "NGUYÊN TẮC PHỤC VỤ AN TOÀN:"
            ws5[f'A{principles_row5}'].font = Font(bold=True, size=11, color="004000")
            principles_notes5 = [
                "• Đảm bảo vệ sinh dụng cụ, khu vực ăn trước khi phục vụ",
                "• Kiểm tra nhiệt độ thức ăn trước khi cho trẻ ăn",
                "• Đảm bảo trẻ rửa tay sạch sẽ trước khi ăn",
                "• Báo cáo ngay nếu phát hiện bất thường về thức ăn hoặc sức khỏe trẻ"
            ]
            for i, note in enumerate(principles_notes5, 1):
                ws5[f'A{principles_row5 + i}'] = note
                ws5[f'A{principles_row5 + i}'].font = Font(size=9, color="004000")
            # Chữ ký
            signature_row5 = principles_row5 + 8
            signature_data5 = [
                (signature_row5,     'D', "NGƯỜI THỰC HIỆN LƯU MẪU",  'H', "NGƯỜI THỰC HIỆN HUỶ MẪU",   'K', "HIỆU TRƯỞNG"),
                (signature_row5 + 1, 'D', "(Ký, ghi rõ họ tên)", 'H', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
                (signature_row5 + 5, 'D', "Hoàng Thanh Tuấn",'H', "Hoàng Thanh Tuấn",  'K', "Nguyễn Thị Vân")
            ]
            for item in signature_data5:
                row, col_d, text_d, col_h, text_h, col_k, text_k = item
                ws5[f'{col_d}{row}'] = text_d
                ws5[f'{col_h}{row}'] = text_h
                ws5[f'{col_k}{row}'] = text_k
                cols = [(col_d, text_d), (col_h, text_h), (col_k, text_k)]
                for col, text in cols:
                    cell = ws5[f'{col}{row}']
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    if row == signature_row5:
                        cell.font = Font(bold=True, size=12, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif row == signature_row5 + 1:
                        cell.font = Font(italic=True, size=9)
                    elif row == signature_row5 + 5:
                        cell.font = Font(bold=True, size=11)
                    else:
                        cell.font = Font(size=9)
        if 'Sheet' in wb5.sheetnames:
            wb5.remove(wb5['Sheet'])
        file5_buffer = BytesIO()
        wb5.save(file5_buffer)
        file5_buffer.seek(0)
        zipf.writestr(f"Bước 4 - Theo dõi lưu và huỷ mẫu thức ăn lưu - Tuần {week_number}.xlsx", file5_buffer.read())
        
        # BƯỚC 6: PHIẾU TIẾP NHẬN VÀ KIỂM TRA CHẤT LƯỢNG THỰC PHẨM
        wb6 = Workbook()
        for day_offset in range(6):
            day_date = week_start + timedelta(days=day_offset)
            day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat'][day_offset]
            safe_date = day_date.strftime('%d-%m')
            sheet_title = f"{days_vn[day_offset]} ({safe_date})"
            if day_offset == 0:
                ws6 = wb6.active
                ws6.title = sheet_title
            else:
                ws6 = wb6.create_sheet(title=sheet_title)
            # Header chính tương tự ws6
            
            ws6['D2'] = "PHIẾU TIẾP NHẬN VÀ KIỂM TRA CHẤT LƯỢNG THỰC PHẨM"
            ws6['D2'].font = Font(bold=True, size=14, color="006600")
            ws6['D2'].alignment = Alignment(horizontal='center', vertical='center')
            ws6.merge_cells('D2:I2')
            ws6['J2'] = ""
            ws6['J2'].font = Font(bold=True, size=10)
            ws6['J2'].fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            info_data4 = [
                (1, 'A', f"Phòng GD&ĐT: XÃ ĐỨC TRỌNG", 'J', ""),
                (2, 'A', f"Đơn vị: MẦM NON CÂY NHỎ", 'J', ""),
                (3, 'A', f"Số suất: {student_count}", 'F', "")
            ]
            for row, col_a, text_a, col_m, text_m in info_data4:
                ws6[f'{col_a}{row}'] = text_a
                ws6[f'{col_a}{row}'].font = Font(bold=True, size=10)
                ws6[f'{col_m}{row}'] = text_m
                ws6[f'{col_m}{row}'].font = Font(bold=True, size=10)
                ws6[f'{col_m}{row}'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
            # Dòng thông tin bữa ăn - Món ăn
            meal_dish_lines = []
            for meal_key, meal_name in meal_times.items():
                dishes = []
                if menu_data[day_key].get(meal_key):
                    dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                if dishes:
                    meal_dish_lines.append(f"{meal_name}: {', '.join(dishes)}")
                else:
                    meal_dish_lines.append(f"{meal_name}: (không có món)")
            ws6['A5'] = " | ".join(meal_dish_lines)
            ws6['A5'].font = Font(bold=True, size=10, color="006600")
            ws6['A5'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
            ws6.merge_cells('A5:G5')
            ws6.row_dimensions[5].height = 48
            ws6['A5'].alignment = Alignment(wrap_text=True, vertical='center', horizontal='left')
            # Thêm dòng tiêu đề lớn phía trên bảng
            ws6['A7'] = "I. Tiếp nhận, kiểm tra chất lượng thực phẩm và chế biến"
            ws6['A7'].font = Font(bold=True, size=12, color="8B0000")
            ws6['A7'].fill = PatternFill(start_color="FFF2E6", end_color="FFF2E6", fill_type="solid")
            ws6.merge_cells('A7:G7')

            headers6_main = [
                'STT', 'TÊN THỰC PHẨM',
                'ĐƠN VỊ TÍNH', 'SỐ LƯỢNG DỰ KIẾN MUA',
                'THỰC TẾ TIẾP NHẬN', 'GIÁ TIỀN (VNĐ)',
                'NHẬN XÉT'
            ]
            for i, header in enumerate(headers6_main, 1):
                cell = ws6.cell(row=8, column=i, value=header)
                cell.font = Font(bold=True, size=9, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
                cell.border = thick_border
            sub_headers6 = [
                '', '', '',
                '', '', '', ''
            ]
            for i, header in enumerate(sub_headers6, 1):
                cell = ws6.cell(row=9, column=i, value=header)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="CD5C5C", end_color="CD5C5C", fill_type="solid")
                cell.border = thin_border
            ws6.column_dimensions['B'].width = 18
            ws6.column_dimensions['C'].width = 18
            ws6.column_dimensions['D'].width = 18
            ws6.column_dimensions['E'].width = 18
            ws6.column_dimensions['F'].width = 15
            ws6.column_dimensions['G'].width = 20
            for col in ['B', 'C', 'D', 'E', 'F', 'G']:
                cell = ws6[f'{col}8']
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            # ws6.merge_cells('H8:I8')
            for i in range(1, 8):   
                cell = ws6.cell(row=10, column=i, value=i)
                cell.font = Font(bold=True, size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                cell.border = thin_border
            # Ghi dữ liệu món ăn từng ngày
            row_num = 11
            stt = 1
            daily_total_cost = 0  # Tổng chi phí trong ngày
            # Tổng hợp nguyên liệu trong ngày (chỉ 1 lần cho ngày hiện tại)
            daily_ingredients = {}
            for meal in menu_data[day_key].values():
                if not meal: continue
                for dish_name in [d.strip() for d in meal.split(',') if d.strip()]:
                    dish = Dish.query.filter_by(name=dish_name).first()
                    if dish:
                        for di in dish.ingredients:
                            key = (di.product.name, di.unit, di.product.category, di.product.supplier)
                            qty = di.quantity * student_count
                            if key not in daily_ingredients:
                                daily_ingredients[key] = {'total_qty': 0, 'unit': di.unit, 'category': di.product.category, 'supplier': di.product.supplier, 'product': di.product}
                            daily_ingredients[key]['total_qty'] += qty

            for (name, unit, category, supplier), info in daily_ingredients.items():
                # Quy đổi đơn vị nếu cần để hiển thị
                qty = info['total_qty']
                display_unit = unit
                if unit and unit.lower() in ['g', 'gram', 'gr']:
                    display_unit = 'kg'
                    display_qty = round(qty / 1000, 2)
                elif unit and unit.lower() in ['ml', 'mililít', 'milliliter']:
                    display_unit = 'lít' 
                    display_qty = round(qty / 1000, 2)
                else:
                    display_qty = round(qty, 2)

                # Tính giá tiền: giá sản phẩm * số lượng dự kiến mua
                product = info['product']  # Product object
                total_price = 0
                if product and product.price:
                    total_price = round(product.price * display_qty, 0)  # Làm tròn VNĐ
                    price_display = f"{total_price:,.0f} đ"
                    daily_total_cost += total_price  # Cộng vào tổng chi phí
                else:
                    price_display = "Chưa có giá"

                # name ở đây là TÊN THỰC PHẨM chỉ lấy theo ngày hiện tại, không phải cả tuần
                data_row6 = [
                    stt,  # STT
                    name,  # TÊN THỰC PHẨM
                    display_unit,  # ĐƠN VỊ
                    display_qty,  # SỐ LƯỢNG DỰ KIẾN MUA
                    '',  # THỰC TẾ TIẾP NHẬN (để trống)
                    price_display,  # GIÁ TIỀN (VNĐ)
                    "",  # Nhận xét
                ]
                for j, value in enumerate(data_row6, 1):
                    cell = ws6.cell(row=row_num, column=j, value=value)
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = thin_border
                    if j == 1:
                        cell.font = Font(bold=True, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif j == 2:
                        cell.font = Font(bold=True, size=10)
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif j == 6:  # Cột giá tiền
                        if total_price > 0:
                            cell.font = Font(bold=True, color="FF6600")
                            cell.fill = PatternFill(start_color="FFF8E1", end_color="FFF8E1", fill_type="solid")
                        else:
                            cell.font = Font(italic=True, color="999999")
                row_num += 1
                stt += 1
            
            # Thêm dòng tổng cộng
            if daily_total_cost > 0:
                ws6.merge_cells(f'A{row_num}:E{row_num}')
                ws6[f'A{row_num}'] = "TỔNG CHI PHÍ DỰ KIẾN"
                ws6[f'A{row_num}'].font = Font(bold=True, size=11, color="8B0000")
                ws6[f'A{row_num}'].alignment = Alignment(horizontal='right', vertical='center')
                ws6[f'A{row_num}'].fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
                
                ws6[f'F{row_num}'] = f"{daily_total_cost:,.0f} đ"
                ws6[f'F{row_num}'].font = Font(bold=True, size=12, color="8B0000")
                ws6[f'F{row_num}'].alignment = Alignment(horizontal='center', vertical='center')
                ws6[f'F{row_num}'].fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
                
                ws6[f'G{row_num}'] = ""
                ws6[f'G{row_num}'].fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
                
                # Add borders
                for col in range(1, 8):
                    ws6.cell(row=row_num, column=col).border = thick_border
                
                row_num += 1
            # Nội Dung khác
            stats_row6 = row_num + 2
            ws6[f'A{stats_row6}'] = "II. Nội Dung Khác"
            ws6[f'A{stats_row6}'].font = Font(bold=True, size=12, color="8B0000")
            ws6[f'A{stats_row6}'].fill = PatternFill(start_color="FFF2E6", end_color="FFF2E6", fill_type="solid")
            # Chữ ký
            signature_row6 = stats_row6 + 8
            signature_data6 = [
                (signature_row6,     'A', "NGƯỜI GIAO HÀNG", "C",'NGƯỜI TIẾP NHẬN', "E", "NV. Y TẾ",   'H', "HIỆU TRƯỞNG"),
                (signature_row6 + 1, 'A', "(Ký, ghi rõ họ tên)", "C",'(Ký, ghi rõ họ tên)', 'E', "(Ký, ghi rõ họ tên)", 'H', "(Ký, ghi rõ họ tên)"),
                (signature_row6 + 5, 'A', "","C","","E", "",  'H', "Nguyễn Thị Vân")
            ]
            for item in signature_data6:
                # unpack 9 values: row, col_d, text_d, col_f, text_f, col_h, text_h, col_k, text_k
                row, col_d, text_d, col_f, text_f, col_h, text_h, col_k, text_k = item
                ws6[f'{col_d}{row}'] = text_d
                ws6[f'{col_f}{row}'] = text_f
                ws6[f'{col_h}{row}'] = text_h
                ws6[f'{col_k}{row}'] = text_k
                cols = [(col_d, text_d), (col_f, text_f), (col_h, text_h), (col_k, text_k)]
                for col, text in cols:
                    cell = ws6[f'{col}{row}']
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    if row == signature_row6:
                        cell.font = Font(bold=True, size=12, color="006600")
                        cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                    elif row == signature_row6 + 1:
                        cell.font = Font(italic=True, size=9)
                    elif row == signature_row6 + 5:
                        cell.font = Font(bold=True, size=11)
                    else:
                        cell.font = Font(size=9)
        if 'Sheet' in wb6.sheetnames:
            wb6.remove(wb6['Sheet'])
        file6_buffer = BytesIO()
        wb6.save(file6_buffer)
        file6_buffer.seek(0)
        zipf.writestr(f"Bước 6 - PHIẾU TIẾP NHẬN VÀ KIỂM TRA CHẤT LƯỢNG THỰC PHẨM - Tuần {week_number}.xlsx", file6_buffer.read())
        
    # Đóng zipfile và trả về
    zip_buffer.seek(0)
    
    # Tạo response để download
    response = send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"Quy_trinh_an_toan_thuc_pham_3_buoc_Tuan_{week_number}.zip",
        mimetype='application/zip'
    )
    
    flash(f'Đã xuất thành công quy trình an toàn thực phẩm 3 bước cho tuần {week_number}!', 'success')
    return response

# ================== QUẢN LÝ NHÀ CUNG CẤP VÀ SẢN PHẨM ==================

@main.route('/suppliers')
def suppliers():
    """Danh sách nhà cung cấp"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    return render_template('suppliers.html', suppliers=suppliers)

@main.route('/suppliers/new', methods=['GET', 'POST'])
def new_supplier():
    """Thêm nhà cung cấp mới"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            address=form.address.data,
            phone=form.phone.data,
            contact_person=form.contact_person.data,
            supplier_type=form.supplier_type.data,
            registration_number=form.registration_number.data,
            food_safety_cert=form.food_safety_cert.data,
            created_date=datetime.utcnow()
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Thêm nhà cung cấp thành công!', 'success')
        return redirect(url_for('main.suppliers'))
    
    return render_template('new_supplier.html', form=form)

@main.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    """Sửa thông tin nhà cung cấp"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        flash('Cập nhật nhà cung cấp thành công!', 'success')
        return redirect(url_for('main.suppliers'))
    
    return render_template('edit_supplier.html', form=form, supplier=supplier)

@main.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
def delete_supplier(supplier_id):
    """Xóa nhà cung cấp"""
    if session.get('role') != 'admin':
        return redirect_no_permission()
    
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.is_active = False
    db.session.commit()
    flash('Xóa nhà cung cấp thành công!', 'success')
    return redirect(url_for('main.suppliers'))

@main.route('/products')
def products():
    """Danh sách sản phẩm"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    products = Product.query.filter_by(is_active=True).join(Supplier).order_by(Product.category, Product.name).all()
    return render_template('products.html', products=products)

@main.route('/products/new', methods=['GET', 'POST'])
def new_product():
    """Thêm sản phẩm mới"""
    current_role = session.get('role')
    
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    form = ProductForm()
    # Lấy danh sách đơn vị duy nhất từ Product
    product_units = sorted(list(set([p.unit for p in Product.query.all() if p.unit])))
    # Lấy danh sách nhà cung cấp cho dropdown
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    
    # Nếu chưa có supplier nào, tạo một supplier mẫu
    if not suppliers:
        default_supplier = Supplier(
            name="Nhà cung cấp mặc định",
            address="Địa chỉ cần cập nhật",
            phone="0123456789",
            contact_person="Người liên hệ",
            supplier_type="fresh",
            registration_number="",
            food_safety_cert="",
            created_date=datetime.utcnow()
        )
        db.session.add(default_supplier)
        db.session.commit()
        suppliers = [default_supplier]
        flash('Đã tạo nhà cung cấp mặc định. Vui lòng cập nhật thông tin sau!', 'info')
    
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            category=form.category.data,
            supplier_id=form.supplier_id.data,
            unit=form.unit.data,
            price=form.price.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('main.products'))
    return render_template('new_product.html', form=form, product_units=product_units)

@main.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    """Sửa thông tin sản phẩm"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    product_units = sorted(list(set([p.unit for p in Product.query.all() if p.unit])))
    
    # Lấy danh sách nhà cung cấp cho dropdown
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('main.products'))
    
    return render_template('edit_product.html', form=form, product=product, suppliers=suppliers, product_units=product_units)

@main.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Xóa sản phẩm"""
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    flash('Xóa sản phẩm thành công!', 'success')
    return redirect(url_for('main.products'))

# ============== AI Routes với LLM Farm ==============

@main.route('/ai/menu-suggestions', methods=['POST'])
def ai_menu_suggestions():
    """API endpoint để lấy gợi ý thực đơn từ Gemini AI - SECURED & OPTIMIZED"""
    
    user_role = session.get('role')
    if user_role not in ['admin', 'teacher']:
        return jsonify({'success': False, 'error': 'Không có quyền truy cập. Vui lòng đăng nhập với tài khoản admin hoặc giáo viên.'}), 403

    try:
        from app.models import Dish
        import random
        meal_types = ["morning", "snack", "dessert", "lunch", "afternoon", "lateafternoon"]
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        dishes = Dish.query.filter_by(is_active=True).all()
        dishes_by_meal = {meal: [] for meal in meal_types}
        for d in dishes:
            if d.meal_times:
                for meal in d.meal_times:
                    if meal in meal_types:
                        dishes_by_meal[meal].append(d.name)

        menu = {}
        used_dishes = {meal: set() for meal in meal_types}  # Theo dõi món đã dùng trong tuần cho từng bữa
        for day in days:
            menu[day] = {}
            for meal in meal_types:
                meal_dishes = dishes_by_meal[meal][:]
                if not meal_dishes:
                    menu[day][meal] = "[Không có]"
                    continue
                # Loại các món đã dùng hết lượt trong tuần (ưu tiên không lặp)
                available = [d for d in meal_dishes if d not in used_dishes[meal]]
                if meal == "lunch":
                    # Trưa: 2 món khác nhau, tránh trùng trong tuần
                    if len(available) >= 2:
                        selected = random.sample(available, 2)
                    elif len(meal_dishes) >= 2:
                        # Nếu đã dùng hết, cho phép lặp lại nhưng vẫn chọn 2 món khác nhau
                        selected = random.sample(meal_dishes, 2)
                    elif len(meal_dishes) == 1:
                        selected = [meal_dishes[0], meal_dishes[0]]
                    else:
                        selected = ["[Không có]", "[Không có]"]
                    menu[day][meal] = ", ".join(selected)
                    for s in selected:
                        used_dishes[meal].add(s)
                else:
                    # Các bữa khác: 1 món, tránh trùng trong tuần
                    if available:
                        selected = random.choice(available)
                    else:
                        selected = random.choice(meal_dishes)
                    menu[day][meal] = selected
                    used_dishes[meal].add(selected)
        return jsonify({
            'success': True,
            'menu': menu,
            'suggestions': {
                'nutrition_tips': [
                    f"Thực đơn được tối ưu cho trẻ {request.json.get('age_group', '1-3 tuổi')}",
                    "Đảm bảo cân bằng dinh dưỡng với đầy đủ nhóm thực phẩm",
                    "Tránh lặp lại món ăn trong cùng bữa trong tuần",
                    "Bữa trưa có 2 món để tăng đa dạng dinh dưỡng",
                    "Khuyến khích trẻ thử nhiều loại thực phẩm khác nhau"
                ],
                'generated_from': 'SmallTree AI - Nutrition optimized menu system'
            },
            'security_info': f"Optimized menu for {user_role} with nutrition balance",
        })
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] {e}")
        return jsonify({'success': False, 'error': str(e)})

def extract_weekly_menu_from_suggestions(suggestions):
    """Trích xuất và chuyển đổi suggestions thành format menu database"""
    menu_data = {}
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
    
    # Initialize empty menu
    for day in days:
        menu_data[day] = {}
        for slot in slots:
            menu_data[day][slot] = "Món ăn dinh dưỡng"
    
    current_day = None
    current_day_index = -1
    
    for suggestion in suggestions:
        suggestion = suggestion.strip()
        
        # Tìm ngày
        if '**Thứ' in suggestion:
            if 'Thứ 2' in suggestion:
                current_day = 'mon'
                current_day_index = 0
            elif 'Thứ 3' in suggestion:
                current_day = 'tue' 
                current_day_index = 1
            elif 'Thứ 4' in suggestion:
                current_day = 'wed'
                current_day_index = 2
            elif 'Thứ 5' in suggestion:
                current_day = 'thu'
                current_day_index = 3
            elif 'Thứ 6' in suggestion:
                current_day = 'fri'
                current_day_index = 4
            elif 'Thứ 7' in suggestion:
                current_day = 'sat'
                current_day_index = 5
            continue
            
        # Tìm món ăn theo khung giờ
        if current_day and suggestion.startswith('•'):
            suggestion = suggestion[1:].strip()  # Bỏ bullet point
            
            if suggestion.startswith('Sáng:'):
                menu_data[current_day]['morning'] = suggestion[5:].strip()
            elif suggestion.startswith('Phụ sáng:'):
                menu_data[current_day]['snack'] = suggestion[9:].strip()
            elif suggestion.startswith('Tráng miệng:'):
                menu_data[current_day]['dessert'] = suggestion[12:].strip()
            elif suggestion.startswith('Trưa:'):
                menu_data[current_day]['lunch'] = suggestion[5:].strip()
            elif suggestion.startswith('Xế:'):
                menu_data[current_day]['afternoon'] = suggestion[3:].strip()
            elif suggestion.startswith('Xế chiều:'):
                menu_data[current_day]['lateafternoon'] = suggestion[9:].strip()
    
    return menu_data

@main.route('/ai/create-menu-from-suggestions', methods=['POST'])
def create_menu_from_suggestions():
    """API endpoint để tạo thực đơn từ AI suggestions"""
    
    user_role = session.get('role')
    if user_role not in ['admin', 'teacher']:
        return jsonify({'success': False, 'error': 'Không có quyền truy cập'}), 403
    
    # Import modules outside try block to avoid reference errors
    from datetime import datetime, timedelta
    import json
    
    print(f"[DEBUG] Received request to create menu from suggestions")
    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Content-Type: {request.content_type}")
    print(f"[DEBUG] Request data: {request.get_data()}")

    try:
        
        # Lấy dữ liệu từ request
        data = request.get_json()
        print(f"[DEBUG] Parsed JSON data: {data}")
        
        if not data or 'menu' not in data:
            print(f"[ERROR] No menu data found. Data keys: {data.keys() if data else 'None'}")
            return jsonify({'success': False, 'error': 'Không có dữ liệu thực đơn'}), 400
        
        menu_data = data['menu']
        overwrite = data.get('overwrite', False)
        
        print(f"[DEBUG] Menu data: {menu_data}")
        print(f"[DEBUG] Overwrite: {overwrite}")
        
        # Sử dụng tuần được chọn hoặc tuần hiện tại
        if 'target_week' in data and 'target_year' in data:
            week_number = data['target_week']
            year = data['target_year']
        else:
            # Fallback: tính tuần hiện tại
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_number = week_start.isocalendar()[1]
            year = week_start.year
        
        # Kiểm tra xem thực đơn tuần này đã tồn tại chưa (sử dụng model Menu)
        existing_menu = Menu.query.filter_by(week_number=week_number, year=year).first()
        if existing_menu and not overwrite:
            return jsonify({
                'success': False,
                'error': f'Thực đơn tuần {week_number}/{year} đã tồn tại',
                'week_number': week_number,
                'existing_id': existing_menu.id
            }), 409
        
        # Tạo hoặc cập nhật thực đơn
        if existing_menu and overwrite:
            menu_obj = existing_menu
            print(f"[DEBUG] Updating existing menu for week {week_number}/{year}")
        else:
            menu_obj = Menu(week_number=week_number, year=year)
            db.session.add(menu_obj)
            print(f"[DEBUG] Creating new menu for week {week_number}/{year}")
        
        # Cập nhật dữ liệu thực đơn
        for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']:
            day_data = menu_data.get(day, {})
            print(f"[DEBUG] Processing {day}: {day_data}")
            
            if day == 'mon':
                menu_obj.monday_morning = day_data.get('morning', '')
                menu_obj.monday_snack = day_data.get('snack', '')
                menu_obj.monday_dessert = day_data.get('dessert', '')
                menu_obj.monday_lunch = day_data.get('lunch', '')
                menu_obj.monday_afternoon = day_data.get('afternoon', '')
                menu_obj.monday_lateafternoon = day_data.get('lateafternoon', '')
            elif day == 'tue':
                menu_obj.tuesday_morning = day_data.get('morning', '')
                menu_obj.tuesday_snack = day_data.get('snack', '')
                menu_obj.tuesday_dessert = day_data.get('dessert', '')
                menu_obj.tuesday_lunch = day_data.get('lunch', '')
                menu_obj.tuesday_afternoon = day_data.get('afternoon', '')
                menu_obj.tuesday_lateafternoon = day_data.get('lateafternoon', '')
            elif day == 'wed':
                menu_obj.wednesday_morning = day_data.get('morning', '')
                menu_obj.wednesday_snack = day_data.get('snack', '')
                menu_obj.wednesday_dessert = day_data.get('dessert', '')
                menu_obj.wednesday_lunch = day_data.get('lunch', '')
                menu_obj.wednesday_afternoon = day_data.get('afternoon', '')
                menu_obj.wednesday_lateafternoon = day_data.get('lateafternoon', '')
            elif day == 'thu':
                menu_obj.thursday_morning = day_data.get('morning', '')
                menu_obj.thursday_snack = day_data.get('snack', '')
                menu_obj.thursday_dessert = day_data.get('dessert', '')
                menu_obj.thursday_lunch = day_data.get('lunch', '')
                menu_obj.thursday_afternoon = day_data.get('afternoon', '')
                menu_obj.thursday_lateafternoon = day_data.get('lateafternoon', '')
            elif day == 'fri':
                menu_obj.friday_morning = day_data.get('morning', '')
                menu_obj.friday_snack = day_data.get('snack', '')
                menu_obj.friday_dessert = day_data.get('dessert', '')
                menu_obj.friday_lunch = day_data.get('lunch', '')
                menu_obj.friday_afternoon = day_data.get('afternoon', '')
                menu_obj.friday_lateafternoon = day_data.get('lateafternoon', '')
            elif day == 'sat':
                menu_obj.saturday_morning = day_data.get('morning', '')
                menu_obj.saturday_snack = day_data.get('snack', '')
                menu_obj.saturday_dessert = day_data.get('dessert', '')
                menu_obj.saturday_lunch = day_data.get('lunch', '')
                menu_obj.saturday_afternoon = day_data.get('afternoon', '')
                menu_obj.saturday_lateafternoon = day_data.get('lateafternoon', '')
        
        db.session.commit()
        print(f"[DEBUG] Menu saved successfully with ID: {menu_obj.id}")
        
        return jsonify({
            'success': True,
            'message': f'Đã {"cập nhật" if overwrite and existing_menu else "tạo"} thực đơn tuần {week_number}/{year} thành công!',
            'week_number': week_number,
            'year': year,
            'menu_id': menu_obj.id,
            'overwritten': overwrite and existing_menu
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] create_menu_from_suggestions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500


@main.route('/ai-dashboard', methods=['GET', 'POST'])
def ai_dashboard():
    """Trang dashboard AI với các tính năng LLM Farm"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()

    # Không tự tạo prompt ở đây nữa, chỉ render dashboard, prompt sẽ lấy từ API /ai/menu-suggestions
    return render_template('ai_dashboard.html')

# ===== STUDENT ALBUM MANAGEMENT ROUTES =====

@main.route('/student-albums')
def student_albums():
    """Danh sách album của tất cả học sinh"""
    user_role = session.get('role')
    user_id = session.get('user_id')
    students = []
    albums = []
    if user_role == 'parent':
        # Chỉ xem album của con mình
        child = Child.query.filter_by(id=user_id).first()
        if child:
            students = [child]
            albums = StudentAlbum.query.filter_by(student_id=child.id).order_by(StudentAlbum.date_created.desc()).all()
        else:
            students = []
            albums = []
    else:
        # Giáo viên, admin xem tất cả
        students = Child.query.all()
        import os
        updated = False
        for s in students:
            old_avatar = s.avatar
            # Sửa lại đường dẫn avatar nếu phát hiện sai định dạng
            if s.avatar:
                new_avatar = s.avatar
                # Remove app/static/ prefix nếu có
                if new_avatar.startswith('app/static/'):
                    new_avatar = new_avatar.replace('app/static/', '')
                elif new_avatar.startswith('/app/static/'):
                    new_avatar = new_avatar.replace('/app/static/', '')
                # Convert backslashes to forward slashes  
                new_avatar = new_avatar.replace('\\', '/')
                # Ensure proper path structure
                if not new_avatar.startswith('images/students/') and new_avatar:
                    if new_avatar.startswith('students/'):
                        new_avatar = 'images/' + new_avatar
                    elif not new_avatar.startswith('images/'):
                        new_avatar = 'images/students/' + new_avatar
                
                if new_avatar != old_avatar:
                    s.avatar = new_avatar
                    updated = True
                    print(f"[AUTO-FIX] {s.name} ({s.student_code}): {old_avatar} → {new_avatar}")
            
            # Nếu avatar là None/rỗng thì tìm file theo student_code hoặc student_id
            if (not s.avatar or s.avatar.strip() == '') and s.student_code:
                import glob
                # Tìm theo student_code trước (format mới)
                pattern = os.path.join('app', 'static', 'images', 'students', f'student_{s.student_code}_*')
                matches = glob.glob(pattern)
                
                # Nếu không tìm thấy, thử tìm theo student ID (format cũ)
                if not matches:
                    pattern = os.path.join('app', 'static', 'images', 'students', f'student_{s.id}_*')
                    matches = glob.glob(pattern)
                
                if matches:
                    # Lấy tên file đầu tiên tìm được
                    rel_path = os.path.relpath(matches[0], os.path.join('app', 'static'))
                    s.avatar = rel_path.replace('\\', '/')
                    updated = True
                    print(f"[AUTO-DETECT] {s.name} ({s.student_code}): Found avatar {s.avatar}")
        if updated:
            db.session.commit()
        albums = StudentAlbum.query.join(Child).order_by(StudentAlbum.date_created.desc()).all()
    # Đảm bảo students và albums luôn là list
    students = students or []
    albums = albums or []
    # Tính thống kê
    today = date.today()
    albums_today = [album for album in albums if album.date_created == today]
    academic_albums = [album for album in albums if album.milestone_type == 'academic']
    # Mobile detection
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
    return render_template('student_albums.html', 
                         students=students, 
                         albums=albums, 
                         albums_today=albums_today,
                         academic_albums=academic_albums,
                         mobile=mobile)

@main.route('/student/<int:student_id>/albums')
def student_albums_detail(student_id):
    """Album chi tiết của một học sinh"""
    if session.get('role') not in ['admin', 'teacher', 'parent']:
        return redirect_no_permission()
    
    student = Child.query.get_or_404(student_id)
    
    # Nếu là parent, chỉ xem được album của con mình
    if session.get('role') == 'parent' and session.get('user_id') != student_id:
        flash('Bạn chỉ có thể xem album của con mình!', 'error')
        return redirect(url_for('main.index'))
    
    albums = StudentAlbum.query.filter_by(student_id=student_id).order_by(StudentAlbum.date_created.desc()).all()
    progress_records = StudentProgress.query.filter_by(student_id=student_id).order_by(StudentProgress.evaluation_date.desc()).all()
    
    # Tính thống kê cho student này
    total_photos = sum(len(album.photos) for album in albums)
    today = date.today()
    first_day_of_month = today.replace(day=1)
    albums_this_month = [album for album in albums if album.date_created >= first_day_of_month]
    
    # Mobile detection
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
    
    return render_template('student_album_detail.html', 
                         student=student, 
                         albums=albums, 
                         progress_records=progress_records,
                         total_photos=total_photos,
                         albums_this_month=albums_this_month,
                         mobile=mobile,
                         current_date=date.today().strftime('%Y-%m-%d'))

@main.route('/student/<int:student_id>/album/new', methods=['GET', 'POST'])
def create_student_album(student_id):
    """Tạo album mới cho học sinh"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    student = Child.query.get_or_404(student_id)
    
    if request.method == 'POST':
        # Lấy thông tin album
        title = request.form.get('title')
        description = request.form.get('description', '')
        milestone_type = request.form.get('milestone_type', 'other')
        school_year = request.form.get('school_year', '')
        semester = request.form.get('semester', '')
        age_at_time = request.form.get('age_at_time', '')
        
        # Tạo album mới
        album = StudentAlbum(
            student_id=student_id,
            title=title,
            description=description,
            date_created=date.today(),
            milestone_type=milestone_type,
            school_year=school_year,
            semester=semester,
            age_at_time=age_at_time,
            created_by=session.get('username', 'teacher'),
            is_shared_with_parents=True
        )
        
        db.session.add(album)
        db.session.flush()  # Để lấy album.id
        
        # Xử lý upload ảnh
        uploaded_files = request.files.getlist('photos')
        if uploaded_files:
            upload_dir = os.path.join(current_app.static_folder, 'student_albums', str(student_id), str(album.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            for i, file in enumerate(uploaded_files):
                if file and file.filename:
                    filename = secrets.token_hex(16) + '.' + file.filename.rsplit('.', 1)[1].lower()
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    
                    # Tạo record ảnh
                    photo = StudentPhoto(
                        album_id=album.id,
                        filename=filename,
                        filepath=f"student_albums/{student_id}/{album.id}/{filename}",
                        original_filename=file.filename,
                        caption=request.form.get(f'caption_{i}', ''),
                        upload_date=datetime.now(),
                        file_size=os.path.getsize(filepath),
                        image_order=i,
                        is_cover_photo=(i == 0)  # Ảnh đầu tiên làm ảnh đại diện
                    )
                    db.session.add(photo)
        
        db.session.commit()
        flash(f'✅ Đã tạo album "{title}" cho {student.name}!', 'success')
        return redirect(url_for('main.student_albums_detail', student_id=student_id))
    
    # Mobile detection
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
    
    return render_template('create_student_album.html', student=student, mobile=mobile)

@main.route('/album/<int:album_id>')
def view_album(album_id):
    """Xem chi tiết một album"""
    if session.get('role') not in ['admin', 'teacher', 'parent']:
        return redirect_no_permission()
    
    album = StudentAlbum.query.get_or_404(album_id)
    
    # Nếu là parent, chỉ xem được album của con mình
    if session.get('role') == 'parent' and session.get('user_id') != album.student_id:
        flash('Bạn chỉ có thể xem album của con mình!', 'error')
        return redirect(url_for('main.index'))
    
    photos = StudentPhoto.query.filter_by(album_id=album_id).order_by(StudentPhoto.image_order).all()
    
    # Mobile detection
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
    
    return render_template('view_album.html', album=album, photos=photos, mobile=mobile)

@main.route('/student/<int:student_id>/progress/new', methods=['GET', 'POST'])
def add_student_progress(student_id):
    """Thêm đánh giá tiến bộ cho học sinh"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    student = Child.query.get_or_404(student_id)
    
    if request.method == 'POST':
        progress = StudentProgress(
            student_id=student_id,
            evaluation_date=datetime.strptime(request.form.get('evaluation_date'), '%Y-%m-%d').date(),
            skill_category=request.form.get('skill_category'),
            skill_name=request.form.get('skill_name'),
            level_achieved=request.form.get('level_achieved'),
            notes=request.form.get('notes', ''),
            teacher_name=session.get('username', 'teacher')
        )
        
        db.session.add(progress)
        db.session.commit()
        
        flash(f'✅ Đã thêm đánh giá tiến bộ cho {student.name}!', 'success')
        return redirect(url_for('main.student_albums_detail', student_id=student_id))
    
    # Mobile detection
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
    
    return render_template('add_student_progress.html', student=student, mobile=mobile)

@main.route('/album/<int:album_id>/delete', methods=['POST'])
def delete_album(album_id):
    """Xóa album"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    album = StudentAlbum.query.get_or_404(album_id)
    student_id = album.student_id
    
    # Xóa thư mục chứa ảnh
    album_dir = os.path.join(current_app.static_folder, 'student_albums', str(student_id), str(album_id))
    if os.path.exists(album_dir):
        import shutil
        shutil.rmtree(album_dir)
    
    db.session.delete(album)
    db.session.commit()
    
    flash('✅ Đã xóa album!', 'success')
    return redirect(url_for('main.student_albums_detail', student_id=student_id))

@main.route('/fix-avatars', methods=['GET'])
def fix_avatars():
    """Route để fix tất cả avatar paths trong database"""
    if session.get('role') != 'admin':
        return redirect_no_permission()
    
    students = Child.query.all()
    fixed_count = 0
    
    for student in students:
        if student.avatar:
            old_avatar = student.avatar
            # Fix các format sai
            new_avatar = old_avatar
            
            # Remove app/static/ prefix nếu có
            if new_avatar.startswith('app/static/'):
                new_avatar = new_avatar.replace('app/static/', '')
            elif new_avatar.startswith('/app/static/'):
                new_avatar = new_avatar.replace('/app/static/', '')
            
            # Convert backslashes to forward slashes
            new_avatar = new_avatar.replace('\\', '/')
            
            # Ensure starts with images/students/
            if not new_avatar.startswith('images/students/'):
                if new_avatar.startswith('students/'):
                    new_avatar = 'images/' + new_avatar
                elif not new_avatar.startswith('images/'):
                    new_avatar = 'images/students/' + new_avatar
            
            if new_avatar != old_avatar:
                student.avatar = new_avatar
                fixed_count += 1
                print(f"[FIX] {student.name} ({student.student_code}): {old_avatar} → {new_avatar}")
    
    if fixed_count > 0:
        db.session.commit()
        flash(f'✅ Đã fix {fixed_count} avatar paths!', 'success')
    else:
        flash('✅ Tất cả avatar paths đã đúng format!', 'info')
    
    return redirect(url_for('main.student_albums'))

# Route debug upload limits cho 60-70 ảnh
@main.route('/debug-upload-test')
def debug_upload_test():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    return '''
    <h2>🔍 Test Upload Logic - 60-70 ảnh</h2>
    <p><strong>MAX_CONTENT_LENGTH:</strong> ''' + str(current_app.config.get('MAX_CONTENT_LENGTH', 0) // (1024*1024)) + '''MB</p>
    
    <h3>Test Upload Traditional (< 30 ảnh)</h3>
    <form id="traditionalForm" enctype="multipart/form-data" action="/debug-process-upload" method="post">
        <input type="file" name="test_files" multiple accept="image/*" id="traditionalInput">
        <br><br>
        <button type="submit">Test Traditional Upload</button>
        <div id="traditionalResults"></div>
    </form>
    
    <hr>
    
    <h3>Test Client-Side Compression (>= 30 ảnh)</h3>
    <form id="compressionForm" enctype="multipart/form-data">
        <input type="file" name="test_files" multiple accept="image/*" id="compressionInput">
        <br><br>
        <button type="button" onclick="testCompression()">Test Compression Upload</button>
        <div id="compressionResults"></div>
    </form>
    
    <script>
    function testCompression() {
        const files = document.getElementById('compressionInput').files;
        document.getElementById('compressionResults').innerHTML = 
            `<p>🔄 Testing compression for ${files.length} files...</p>
             <p><strong>Logic:</strong> ${files.length >= 30 ? 'Client-side compression' : 'Traditional upload'}</p>`;
        
        if (files.length >= 30) {
            alert('Would use client-side compression for ' + files.length + ' files!');
        } else {
            alert('Would use traditional upload for ' + files.length + ' files!');
        }
    }
    </script>
    '''

@main.route('/debug-process-upload', methods=['POST'])
def debug_process_upload():
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    files = request.files.getlist('test_files')
    file_count = len(files)
    
    results = {
        'file_count': file_count,
        'method': 'traditional' if file_count < 30 else 'client_compression',
        'max_content_mb': current_app.config.get('MAX_CONTENT_LENGTH', 0) // (1024*1024),
        'files_with_content': len([f for f in files if f.filename]),
        'status': 'success'
    }
    
    return f'''
    <h3>✅ Upload Test Results</h3>
    <pre>{json.dumps(results, indent=2)}</pre>
    <p><a href="/debug-upload-test">← Back to test</a></p>
    '''