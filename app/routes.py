

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, jsonify, current_app
from app.models import db, Activity, Curriculum, Child, AttendanceRecord, Staff, BmiRecord, ActivityImage, Supplier, Product, StudentAlbum, StudentPhoto, StudentProgress
from app.forms import EditProfileForm, ActivityCreateForm, ActivityEditForm, SupplierForm, ProductForm
from calendar import monthrange
from datetime import datetime, date, timedelta
import io, zipfile, os, json, re, secrets


# Import optional dependencies with error handling
try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except ImportError:
    print("Warning: python-docx not available")
    DOCX_AVAILABLE = False
    Document = None
    Pt = None


# Import AI menu suggestion (single entry point)
try:
    from app.menu_ai import get_ai_menu_suggestions
except ImportError:
    print("Warning: menu_ai not available")
    def get_ai_menu_suggestions(*args, **kwargs):
        return "AI service not available"

# Enhanced Security imports
from .security_utils import (
    sanitize_input, validate_age_group, validate_menu_count, 
    validate_ip_address, is_sql_injection_attempt, 
    log_security_event, check_rate_limit, clean_rate_limit_storage
)

# Rate limiting cho AI endpoints - Security enhancement
ai_request_timestamps = {}
AI_RATE_LIMIT_SECONDS = 10  # Chỉ cho phép 1 request AI mỗi 10 giây/user

# More optional imports with error handling
try:
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import RGBColor
except ImportError:
    WD_ALIGN_PARAGRAPH = None
    OxmlElement = None
    qn = None
    RGBColor = None

try:
    from openpyxl import load_workbook, Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    print("Warning: openpyxl not available")
    OPENPYXL_AVAILABLE = False
    load_workbook = None
    Workbook = None
    PatternFill = None
    Font = None
    Alignment = None
    Border = None
    Side = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    print("Warning: PIL (Pillow) not available")
    PIL_AVAILABLE = False
    Image = None

main = Blueprint('main', __name__)



# DEBUG: Test Curriculum AI import ngay khi khởi động
try:
    print("🔍 [STARTUP DEBUG] Testing curriculum AI import...")
    from app.curriculum_ai import curriculum_ai_service
    print("✅ [STARTUP SUCCESS] Curriculum AI imported successfully!")
    print(f"📋 [STARTUP INFO] Service type: {type(curriculum_ai_service)}")
except Exception as e:
    print(f"❌ [STARTUP ERROR] Failed to import curriculum AI: {e}")
    import traceback
    print(f"📋 [STARTUP TRACEBACK] {traceback.format_exc()}")

def redirect_no_permission():
    flash('Bạn không có quyền truy cập chức năng này!', 'danger')
    return redirect(request.referrer or url_for('main.index'))

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
    from app.models import ActivityImage
    images = ActivityImage.query.order_by(ActivityImage.upload_date.desc()).all()
    return render_template('gallery.html', title='Gallery', mobile=mobile, images=images)

@main.route('/contact')
def contact():
    mobile = is_mobile()
    return render_template('contact.html', title='Contact Us', mobile=mobile)

@main.route('/activities/new', methods=['GET', 'POST'])
def new_activity():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    form = ActivityCreateForm()
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
                return render_template('new_activity.html', form=form, title='Đăng bài viết mới', mobile=is_mobile())
            filename = 'bg_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + safe_filename
            save_path = os.path.join('app', 'static', 'images', filename)
            # Resize background
            img = Image.open(background_file)
            img.thumbnail((1200, 800))
            img.save(save_path)
            image_url = url_for('static', filename=f'images/{filename}')
        new_post = Activity(title=title, description=content, date=date_val, image=image_url)
        db.session.add(new_post)
        db.session.commit()
        # Tạo thư mục lưu ảnh hoạt động
        activity_dir = os.path.join('app', 'static', 'images', 'activities', str(new_post.id))
        os.makedirs(activity_dir, exist_ok=True)
        # Lưu nhiều ảnh hoạt động
        files = request.files.getlist('images')
        for file in files:
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
                    img.thumbnail((1200, 800))
                    img.save(img_path)
                    rel_path = f'images/activities/{new_post.id}/{img_filename}'
                    db.session.add(ActivityImage(filename=img_filename, filepath=rel_path, upload_date=datetime.now(), activity_id=new_post.id))
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Lỗi upload ảnh: {file.filename} - {e}")
                    traceback.print_exc()
                    flash(f"Lỗi upload ảnh: {file.filename} - {e}", 'danger')
                    continue
        db.session.commit()
        flash('Đã đăng bài viết mới!', 'success')
        return redirect(url_for('main.activities'))
    mobile = is_mobile()
    from datetime import date
    current_date_iso = date.today().isoformat()
    return render_template('new_activity.html', form=form, title='Đăng bài viết mới', mobile=mobile, current_date_iso=current_date_iso)

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

@main.route('/curriculum/new', methods=['GET', 'POST'])
def new_curriculum():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    if request.method == 'POST':
        week_number = request.form.get('week_number')
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        morning_slots = ['morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6', 'morning_7']
        afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
        curriculum_data = {}
        for day in days:
            curriculum_data[day] = {}
            for slot in morning_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
            for slot in afternoon_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
        content = json.dumps(curriculum_data, ensure_ascii=False)
        new_week = Curriculum(week_number=week_number, content=content, material=None)
        db.session.add(new_week)
        db.session.commit()
        flash('Đã thêm chương trình học mới!', 'success')
        return redirect(url_for('main.curriculum'))
    mobile = is_mobile()
    return render_template('new_curriculum.html', title='Tạo chương trình mới', mobile=mobile)

@main.route('/curriculum')
def curriculum():
    import secrets
    if 'csrf_token' not in session or not session['csrf_token']:
        session['csrf_token'] = secrets.token_hex(16)
    weeks = Curriculum.query.order_by(Curriculum.week_number).all()
    curriculum = []
    for week in weeks:
        try:
            data = json.loads(week.content)
        except Exception:
            data = {}
        curriculum.append({
            'week_number': week.week_number,
            'data': data
        })
    mobile = is_mobile()
    return render_template('curriculum.html', curriculum=curriculum, title='Chương trình học', mobile=mobile)

@main.route('/attendance/new', methods=['GET', 'POST'])
def new_student():
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    if request.method == 'POST':
        name = request.form.get('name')
        student_code = request.form.get('student_code')
        class_name = request.form.get('class_name')
        birth_date = request.form.get('birth_date')
        parent_contact = request.form.get('parent_contact')
        if class_name not in ['Kay 01', 'Kay 02']:
            flash('Lớp không hợp lệ!', 'danger')
            return redirect(url_for('main.new_student'))
        new_child = Child(name=name, age=0, parent_contact=parent_contact, class_name=class_name, birth_date=birth_date, student_code=student_code)
        db.session.add(new_child)
        db.session.commit()
        flash('Đã thêm học sinh mới!', 'success')
        return redirect(url_for('main.attendance'))
    mobile = is_mobile()
    return render_template('new_attendance.html', title='Tạo học sinh mới', mobile=mobile)

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
    # Lấy danh sách lớp cố định
    class_names = ['Kay 01', 'Kay 02']
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
        else:
            student.status = 'Vắng'
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
            record = AttendanceRecord.query.filter_by(child_id=student.id, date=attendance_date).first()
            if record:
                record.status = status
            else:
                record = AttendanceRecord(child_id=student.id, date=attendance_date, status=status)
                db.session.add(record)
            student.status = status
        db.session.commit()
        flash('Đã lưu điểm danh!', 'success')
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

@main.route('/register', methods=['GET'])
def register():
    return render_template('register.html', title='Đăng ký tài khoản')

@main.route('/register/parent', methods=['POST'])
def register_parent():
    name = request.form.get('parent_name')
    email = request.form.get('parent_email')
    phone = request.form.get('parent_phone')
    child_name = request.form.get('child_name')
    child_age = request.form.get('child_age')
    password = request.form.get('parent_password')
    password_confirm = request.form.get('parent_password_confirm')
    if password != password_confirm:
        flash('Mật khẩu nhập lại không khớp!', 'danger')
        return render_template('register.html', title='Đăng ký tài khoản')
    # Kiểm tra trùng tên hoặc email với Child, Staff, admin
    if (Child.query.filter_by(name=child_name).first() or
        Staff.query.filter_by(name=child_name).first() or
        child_name == 'admin'):
        flash('Tên học sinh đã tồn tại hoặc trùng với tài khoản khác!', 'danger')
        return render_template('register.html', title='Đăng ký tài khoản')
    if (Child.query.filter_by(email=email).first() or
        Staff.query.filter_by(email=email).first() or
        email == 'admin@smalltree.vn'):
        flash('Email đã tồn tại hoặc trùng với tài khoản khác!', 'danger')
        return render_template('register.html', title='Đăng ký tài khoản')
    student_code = request.form.get('student_code')
    hashed_pw = generate_password_hash(password)
    new_child = Child(name=child_name, age=child_age, parent_contact=name, email=email, phone=phone, password=hashed_pw, student_code=student_code)
    db.session.add(new_child)
    db.session.commit()
    flash('Đăng ký phụ huynh thành công!', 'success')
    return redirect(url_for('main.about'))

@main.route('/register/teacher', methods=['POST'])
def register_teacher():
    name = request.form.get('teacher_name')
    email = request.form.get('teacher_email')
    phone = request.form.get('teacher_phone')
    position = request.form.get('teacher_position')
    password = request.form.get('teacher_password')
    password_confirm = request.form.get('teacher_password_confirm')
    if password != password_confirm:
        flash('Mật khẩu nhập lại không khớp!', 'danger')
        return render_template('register.html', title='Đăng ký tài khoản')
    # Kiểm tra trùng tên hoặc email với Child, Staff, admin
    if (Staff.query.filter_by(name=name).first() or
        Child.query.filter_by(name=name).first() or
        name == 'admin'):
        flash('Tên giáo viên đã tồn tại hoặc trùng với tài khoản khác!', 'danger')
        return render_template('register.html', title='Đăng ký tài khoản')
    if (Staff.query.filter_by(email=email).first() or
        Child.query.filter_by(email=email).first() or
        email == 'admin@smalltree.vn'):
        flash('Email đã tồn tại hoặc trùng với tài khoản khác!', 'danger')
        return render_template('register.html', title='Đăng ký tài khoản')
    hashed_pw = generate_password_hash(password)
    new_staff = Staff(name=name, position=position, contact_info=phone, email=email, phone=phone, password=hashed_pw)
    db.session.add(new_staff)
    db.session.commit()
    flash('Đăng ký giáo viên thành công!', 'success')
    return redirect(url_for('main.about'))

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
    # Chỉ cho phép đăng nhập bằng tài khoản administrator duy nhất
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    if session.get('role') != 'admin':
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['user_id'] = 'admin'
                session['role'] = 'admin'
                flash('Đăng nhập administrator thành công!', 'success')
                parents = Child.query.all()
                teachers = Staff.query.all()
                mobile = is_mobile()
                return render_template('accounts.html', parents=parents, teachers=teachers, show_modal=False, title='Quản lý tài khoản', mobile=mobile)
            else:
                flash('Sai tài khoản hoặc mật khẩu administrator!', 'danger')
                return render_template('accounts.html', show_modal=True, title='Quản lý tài khoản')
        return render_template('accounts.html', show_modal=True, title='Quản lý tài khoản')
    parents = Child.query.all()
    teachers = Staff.query.all()
    mobile = is_mobile()
    # Hide sensitive info for non-admins
    show_sensitive = session.get('role') == 'admin'
    def mask_user(u):
        return {
            'id': u.id,
            'name': u.name,
            'email': u.email if show_sensitive else 'Ẩn',
            'phone': u.phone if show_sensitive else 'Ẩn',
            'student_code': getattr(u, 'student_code', None) if show_sensitive else 'Ẩn',
            'class_name': getattr(u, 'class_name', None) if show_sensitive else 'Ẩn',
            'parent_contact': getattr(u, 'parent_contact', None) if show_sensitive else 'Ẩn',
            'position': getattr(u, 'position', None) if show_sensitive else 'Ẩn',
        }
    masked_parents = [mask_user(p) for p in parents]
    masked_teachers = [mask_user(t) for t in teachers]
    return render_template('accounts.html', parents=masked_parents, teachers=masked_teachers, show_modal=False, title='Quản lý tài khoản', mobile=mobile)

@main.route('/curriculum/<int:week_number>/delete', methods=['POST'])
def delete_curriculum(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if week:
        db.session.delete(week)
        db.session.commit()
        flash(f'Đã xoá chương trình học tuần {week_number}!', 'success')
    else:
        flash('Không tìm thấy chương trình học để xoá!', 'danger')
    return redirect(url_for('main.curriculum'))

@main.route('/curriculum/<int:week_number>/edit', methods=['GET', 'POST'])
def edit_curriculum(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if not week:
        flash('Không tìm thấy chương trình học để chỉnh sửa!', 'danger')
        return redirect(url_for('main.curriculum'))
    import json
    if request.method == 'POST':
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        morning_slots = ['morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6', 'morning_7']
        afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
        curriculum_data = {}
        for day in days:
            curriculum_data[day] = {}
            for slot in morning_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
            for slot in afternoon_slots:
                curriculum_data[day][slot] = request.form.get(f'{day}_{slot}')
        week.content = json.dumps(curriculum_data, ensure_ascii=False)
        db.session.commit()
        flash(f'Đã cập nhật chương trình học tuần {week_number}!', 'success')
        return redirect(url_for('main.curriculum'))
    data = json.loads(week.content)
    mobile = is_mobile()
    return render_template('edit_curriculum.html', week=week, data=data, title=f'Chỉnh sửa chương trình tuần {week_number}', mobile=mobile)

@main.route('/profile')
def profile():
    user = None
    role = session.get('role')
    user_id = session.get('user_id')
    if role == 'parent':
        user = Child.query.get(user_id)
        role_display = 'Phụ huynh'
        full_name = user.parent_contact if user else ''
        info = {
            'full_name': full_name,
            'email': user.email if user else '',
            'phone': user.phone if user else '',
            'role_display': role_display,
            'student_code': user.student_code if user else '',
            'class_name': user.class_name if user else '',
            'birth_date': user.birth_date if user else '',
            'parent_contact': user.parent_contact if user else '',
        }
    elif role == 'teacher' or role == 'admin':
        # Giáo viên và admin xem được tất cả thông tin của bản thân
        user = Staff.query.get(user_id) if role == 'teacher' else None
        role_display = 'Giáo viên' if role == 'teacher' else 'Admin'
        full_name = user.name if user else 'Admin'
        info = {
            'full_name': full_name,
            'email': user.email if user else '',
            'phone': user.phone if user else '',
            'role_display': role_display,
            'student_code': '',
            'class_name': getattr(user, 'position', '') if user else '',
            'birth_date': '',
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
    def mask_student(s):
        if role == 'parent':
            # Phụ huynh chỉ xem được thông tin con mình
            if s.id != user_id:
                return None
            return {
                'id': s.id,
                'name': s.name,
                'email': s.email,
                'phone': s.phone,
                'student_code': s.student_code,
                'class_name': s.class_name,
                'parent_contact': s.parent_contact,
            }
        # Giáo viên và admin xem được tất cả thông tin
        return {
            'id': s.id,
            'name': s.name,
            'email': s.email,
            'phone': s.phone,
            'student_code': s.student_code,
            'class_name': s.class_name,
            'parent_contact': s.parent_contact,
        }
    masked_students = [m for m in (mask_student(s) for s in students) if m]
    return render_template('student_list.html', students=masked_students, title='Danh sách học sinh', mobile=mobile)

@main.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    student = Child.query.get_or_404(student_id)
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        if class_name not in ['Kay 01', 'Kay 02']:
            flash('Lớp không hợp lệ!', 'danger')
            return redirect(url_for('main.edit_student', student_id=student_id))
        student.name = request.form.get('name')
        student.student_code = request.form.get('student_code')
        student.class_name = class_name
        student.birth_date = request.form.get('birth_date')
        student.parent_contact = request.form.get('parent_contact')
        db.session.commit()
        flash('Đã lưu thay đổi!', 'success')
        return redirect(url_for('main.student_list'))
    mobile = is_mobile()
    return render_template('edit_student.html', student=student, title='Chỉnh sửa học sinh', mobile=mobile)

@main.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    if session.get('role') != 'admin' and session.get('role') != 'teacher':
        return redirect_no_permission()
    student = Child.query.get_or_404(student_id)
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
    return render_template('edit_account.html', user=masked_user, type=user_type, title='Chỉnh sửa tài khoản')

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
        from app.forms import ActivityEditForm
        form = ActivityEditForm()
        if request.method == 'POST':
            print('---[DEBUG] POST DATA---')
            print('form.title:', form.title.data)
            print('form.description:', form.description.data)
            print('form.background:', form.background.data)
            print('request.files:', request.files)
            print('request.files.getlist("images"):', request.files.getlist('images'))
            print('form.validate_on_submit:', form.validate_on_submit())
        if request.method == 'POST' and form.validate_on_submit():
            post.title = form.title.data
            post.description = form.description.data
            background_file = form.background.data
            image_url = post.image
            if background_file and getattr(background_file, 'filename', None):
                allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.jfif'}
                ext = os.path.splitext(background_file.filename)[1].lower()
                safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', background_file.filename)
                if ext not in allowed_ext:
                    flash('Chỉ cho phép tải lên các file ảnh có đuôi: .jpg, .jpeg, .png, .gif, .jfif!', 'danger')
                    return render_template('edit_activity.html', post=post, form=form, title='Chỉnh sửa hoạt động', mobile=is_mobile())
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
        return render_template('edit_activity.html', post=post, form=form, title='Chỉnh sửa hoạt động', mobile=mobile)
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
    weeks = Curriculum.query.order_by(Curriculum.week_number).all()
    menu = []
    for week in weeks:
        try:
            data = json.loads(week.content) if week.content else {}
            # Ensure all days and slots exist
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
            for day in days:
                if day not in data:
                    data[day] = {}
                for slot in slots:
                    if slot not in data[day]:
                        data[day][slot] = ''
        except Exception as e:
            print(f"Error parsing JSON for week {week.week_number}: {e}")
            data = {}
            # Initialize empty structure
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
            slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
            for day in days:
                data[day] = {}
                for slot in slots:
                    data[day][slot] = ''
        menu.append({
            'week_number': week.week_number,
            'data': data
        })
    mobile = is_mobile()
    return render_template('menu.html', menu=menu, title='Thực đơn', mobile=mobile)

@main.route('/menu/new', methods=['GET', 'POST'])
def new_menu():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    if request.method == 'POST':
        week_number = request.form.get('week_number')
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
        menu_data = {}
        for day in days:
            menu_data[day] = {}
            for slot in slots:
                menu_data[day][slot] = request.form.get(f'content_{day}_{slot}')
        content = json.dumps(menu_data, ensure_ascii=False)
        new_week = Curriculum(week_number=week_number, content=content, material=None)
        db.session.add(new_week)
        db.session.commit()
        flash('Đã thêm thực đơn mới!', 'success')
        return redirect(url_for('main.menu'))
    mobile = is_mobile()
    return render_template('new_menu.html', title='Tạo thực đơn mới', mobile=mobile)

@main.route('/menu/<int:week_number>/edit', methods=['GET', 'POST'])
def edit_menu(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if not week:
        flash('Không tìm thấy thực đơn để chỉnh sửa!', 'danger')
        return redirect(url_for('main.menu'))
    import json
    if request.method == 'POST':
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        slots = ['morning', 'snack', 'dessert', 'lunch', 'afternoon', 'lateafternoon']
        menu_data = {}
        for day in days:
            menu_data[day] = {}
            for slot in slots:
                menu_data[day][slot] = request.form.get(f'content_{day}_{slot}')
        week.content = json.dumps(menu_data, ensure_ascii=False)
        db.session.commit()
        flash(f'Đã cập nhật thực đơn tuần {week_number}!', 'success')
        return redirect(url_for('main.menu'))
    data = json.loads(week.content)
    mobile = is_mobile()
    return render_template('edit_menu.html', week=week, data=data, title=f'Chỉnh sửa thực đơn tuần {week_number}', mobile=mobile)

@main.route('/menu/<int:week_number>/delete', methods=['POST'])
def delete_menu(week_number):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if week:
        db.session.delete(week)
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
    week_number = request.form.get('week_number')
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
    import json
    content = json.dumps(menu_data, ensure_ascii=False)
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if week:
        week.content = content
    else:
        new_week = Curriculum(week_number=week_number, content=content, material=None)
        db.session.add(new_week)
    db.session.commit()
    flash('Đã import thực đơn từ Excel!', 'success')
    return redirect(url_for('main.menu'))

@main.route('/curriculum/import', methods=['POST'])
def import_curriculum():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    file = request.files.get('excel_file')
    week_number = request.form.get('week_number')
    if not file:
        flash('Vui lòng chọn file Excel!', 'danger')
        return redirect(url_for('main.curriculum'))
    if not week_number:
        flash('Vui lòng nhập số tuần!', 'danger')
        return redirect(url_for('main.curriculum'))

    from openpyxl import load_workbook
    wb = load_workbook(file)
    ws = wb.active

    # Đọc dữ liệu theo mẫu mới:
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    morning_slots = ['morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
    afternoon_slots = ['afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']
    curriculum_data = {}

    # Sáng: dòng 4-9 (A4-A9)
    for col_idx, day in enumerate(days):
        curriculum_data[day] = {}
        for slot_idx, slot in enumerate(morning_slots):
            row = 4 + slot_idx  # dòng 4-9
            col = 2 + col_idx   # B=2, C=3, ... G=7
            value = ws.cell(row=row, column=col).value
            curriculum_data[day][slot] = value if value is not None else ""
        # Chiều: dòng 11-14 (A11-A14)
        for slot_idx, slot in enumerate(afternoon_slots):
            row = 11 + slot_idx  # dòng 11-14
            col = 2 + col_idx
            value = ws.cell(row=row, column=col).value
            curriculum_data[day][slot] = value if value is not None else ""
    import json
    content = json.dumps(curriculum_data, ensure_ascii=False)
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if week:
        week.content = content
    else:
        new_week = Curriculum(week_number=week_number, content=content, material=None)
        db.session.add(new_week)
    db.session.commit()
    flash('Đã import chương trình học từ Excel!', 'success')
    return redirect(url_for('main.curriculum'))

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
        ("7-8h", 4), ("8h-8h30", 5), ("8h30-9h", 6), ("9h-9h40", 7), ("9h40-10h30", 8), ("10h30-14h", 9)
    ]
    for label, row in morning_slots:
        ws.cell(row=row, column=1, value=label).font = bold
        ws.cell(row=row, column=1).alignment = center
        ws.cell(row=row, column=1).border = border
        for col in range(2, 8):
            ws.cell(row=row, column=col).border = border

    # Section: Buổi chiều
    ws.merge_cells('A10:G10')
    ws['A10'] = "Buổi chiều"
    ws['A10'].font = bold
    ws['A10'].alignment = center
    ws['A10'].fill = fill
    ws['A10'].border = border

    afternoon_slots = [
        ("14h15-15h", 11), ("15h-15h30", 12), ("15h45-16h", 13), ("16h-17h", 14)
    ]
    for label, row in afternoon_slots:
        ws.cell(row=row, column=1, value=label).font = bold
        ws.cell(row=row, column=1).alignment = center
        ws.cell(row=row, column=1).border = border
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
    
    # Lấy thực đơn của tuần
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if not week:
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
    
    menu_data = json.loads(week.content)
    
    # Lấy thông tin suppliers chi tiết
    from app.models import Supplier
    suppliers = Supplier.query.all()
    supplier_dict = {}
    for supplier in suppliers:
        supplier_dict[supplier.name] = {
            'address': supplier.address or 'Chưa cập nhật địa chỉ',
            'phone': supplier.phone or 'Chưa cập nhật SĐT',
            'contact_person': supplier.contact_person or 'Chưa cập nhật người liên hệ',
            'food_safety_cert': supplier.food_safety_cert or 'Chưa có giấy chứng nhận',
            'established_date': getattr(supplier, 'established_date', 'Chưa cập nhật')
        }
    
    # Ước tính số học sinh từ config
    def get_student_count():
        import os
        import json
        config_file = 'student_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('student_count', 25)
            except:
                pass
        return 25  # Mặc định
    
    student_count = get_student_count()
    
    # Hàm lấy thông tin dinh dưỡng cơ bản
    def get_nutritional_info(ingredient):
        """Trả về thông tin dinh dưỡng cơ bản của nguyên liệu"""
        nutrition_map = {
            # Protein
            'thịt heo': 'Protein: 26g, Chất béo: 20g',
            'thịt bò': 'Protein: 30g, Iron: 2.6mg',  
            'thịt gà': 'Protein: 31g, Vitamin B6: 0.9mg',
            'cá basa': 'Protein: 13g, Omega-3: 0.3g',
            'tôm': 'Protein: 24g, Selenium: 48mcg',
            'trứng gà': 'Protein: 13g, Choline: 294mg',
            
            # Rau củ
            'cải xanh': 'Vitamin C: 75mg, Folate: 80mcg',
            'cà chua': 'Lycopene: 3mg, Vitamin C: 28mg',
            'khoai tây': 'Potassium: 425mg, Vitamin C: 20mg',
            'củ cải': 'Fiber: 2g, Vitamin C: 27mg',
            
            # Tinh bột
            'gạo tẻ': 'Carbs: 28g, Protein: 2.7g',
            'bánh mì': 'Carbs: 49g, Fiber: 2.6g',
            
            # Khác
            'sữa tươi': 'Calcium: 276mg, Protein: 8g',
            'dầu ăn': 'Vitamin E: 14mg, Healthy fats'
        }
        return nutrition_map.get(ingredient, 'Thông tin dinh dưỡng chưa cập nhật')
    
    def get_smart_ingredients(dish_name):
        """Tạo danh sách nguyên liệu thông minh dựa trên tên món"""
        dish_lower = dish_name.lower()
        ingredients = []
        
        # Protein
        if any(meat in dish_lower for meat in ['thịt', 'heo', 'bò', 'gà']):
            ingredients.append('Thịt tươi')
        if any(fish in dish_lower for fish in ['cá', 'tôm', 'cua']):
            ingredients.append('Hải sản tươi')
        if 'trứng' in dish_lower:
            ingredients.append('Trứng gà')
        
        # Rau củ
        if any(veg in dish_lower for veg in ['canh', 'rau', 'củ', 'cải']):
            ingredients.append('Rau củ tươi')
        if any(seasoning in dish_lower for seasoning in ['xào', 'rim', 'kho']):
            ingredients.append('Gia vị, dầu ăn')
        
        # Tinh bột
        if any(starch in dish_lower for starch in ['cơm', 'gạo', 'bún', 'mì']):
            ingredients.append('Tinh bột')
        
        return ', '.join(ingredients) if ingredients else 'Nguyên liệu tự nhiên'
    
    def get_serving_temperature(dish_name):
        """Xác định nhiệt độ phục vụ phù hợp"""
        dish_lower = dish_name.lower()
        
        if any(hot in dish_lower for hot in ['canh', 'cháo', 'súp']):
            return '60-65°C'
        elif any(warm in dish_lower for warm in ['cơm', 'xào', 'rim', 'kho']):
            return '55-60°C'
        elif any(cool in dish_lower for cool in ['trái cây', 'sữa chua', 'chè']):
            return '15-20°C'
        else:
            return '45-50°C'
    
    def get_dish_nutrition(dish_name):
        """Trả về thông tin dinh dưỡng của món ăn"""
        dish_lower = dish_name.lower()
        
        if any(protein in dish_lower for protein in ['thịt', 'cá', 'tôm', 'trứng']):
            return 'Giàu protein, hỗ trợ phát triển'
        elif any(veg in dish_lower for veg in ['rau', 'củ', 'canh']):
            return 'Giàu vitamin, khoáng chất'
        elif any(fruit in dish_lower for fruit in ['trái cây', 'cam', 'chuối']):
            return 'Vitamin C, chất xơ'
        elif 'cơm' in dish_lower:
            return 'Năng lượng, carbohydrate'
        else:
            return 'Cân bằng dinh dưỡng'
    
    def get_sample_note(dish_name):
        """Trả về ghi chú đặc biệt cho lưu mẫu"""
        dish_lower = dish_name.lower()
        
        if any(liquid in dish_lower for liquid in ['canh', 'súp', 'chào']):
            return 'Để nguội trước\nkhi lưu mẫu'
        elif any(fried in dish_lower for fried in ['chiên', 'rán']):
            return 'Tách riêng\ndầu mỡ'
        elif any(raw in dish_lower for raw in ['sống', 'tái']):
            return 'Không lưu mẫu\nthực phẩm sống'
        elif any(dairy in dish_lower for dairy in ['sữa', 'yaourt']):
            return 'Bảo quản lạnh\nriêng biệt'
        else:
            return 'Bảo quản\ntheo quy chuẩn'
    
    def get_heating_equipment(dish_name):
        """Trả về thiết bị giữ nhiệt phù hợp"""
        dish_lower = dish_name.lower()
        
        if 'cơm' in dish_lower:
            return 'Nồi cơm điện\ngiữ nhiệt'
        elif any(soup in dish_lower for soup in ['canh', 'súp']):
            return 'Nồi inox\nđậy nắp'
        elif any(fried in dish_lower for fried in ['chiên', 'rán', 'nướng']):
            return 'Khay inox\nđèn hâm nóng'
        elif any(drink in dish_lower for drink in ['nước', 'sữa', 'trà']):
            return 'Bình giữ nhiệt\n2 lớp'
        else:
            return 'Tủ giữ nhiệt\nchuyên dụng'
    
    def get_actual_portions(dish_name, base_count):
        """Tính số suất thực tế dựa trên món ăn"""
        if not dish_name:  # Default case
            return base_count
            
        dish_lower = dish_name.lower()
        
        # Món ăn chính: đủ số suất
        if any(main in dish_lower for main in ['cơm', 'thịt', 'cá', 'canh']):
            return base_count
        # Món phụ: ít hơn 10%
        elif any(side in dish_lower for side in ['rau', 'salad']):
            return int(base_count * 0.9)
        # Đồ uống: nhiều hơn 5% (dự phòng)
        elif any(drink in dish_lower for drink in ['nước', 'sữa']):
            return int(base_count * 1.05)
        # Tráng miệng: ít hơn 15%
        elif any(dessert in dish_lower for dessert in ['trái cây', 'chè', 'yaourt']):
            return int(base_count * 0.85)
        else:
            return base_count
    
    def get_serving_note(dish_name):
        """Trả về ghi chú đặc biệt khi phục vụ"""
        dish_lower = dish_name.lower()
        
        if any(hot in dish_lower for hot in ['canh', 'súp', 'cháo']):
            return 'Kiểm tra nhiệt độ\ntrước khi phục vụ'
        elif any(cold in dish_lower for cold in ['trái cây', 'yaourt']):
            return 'Giữ lạnh\nđến khi phục vụ'
        elif any(careful in dish_lower for careful in ['xương', 'gai']):
            return 'Kiểm tra xương/gai\ntrước phục vụ'
        elif any(portion in dish_lower for portion in ['thịt', 'cá']):
            return 'Cắt nhỏ phù hợp\nđộ tuổi trẻ'
        else:
            return 'Phục vụ ngay\nsau chế biến'
    
    # Bảng tính toán khối lượng chi tiết theo khoa học dinh dưỡng (gram/học sinh/bữa)
    ingredient_portions = {
        # === NHÓM PROTEIN ===
        'thịt heo': 45, 'thịt bò': 50, 'thịt gà': 55, 'thịt vịt': 50,
        'cá basa': 60, 'cá hồi': 65, 'cá thu': 60, 'cá rô': 55,
        'tôm': 40, 'cua': 45, 'mực': 50, 'nghêu': 45,
        'trứng gà': 50, 'trứng vịt': 45, 'trứng cút': 30,
        'đậu hũ': 70, 'đậu phụ': 65, 'tàu hũ ky': 40,
        
        # === NHÓM RAU CỦ TƯƠI ===
        'cải xanh': 80, 'rau muống': 85, 'cải ngọt': 75, 'cải thìa': 80,
        'súp lơ': 90, 'bông cải': 85, 'cà rót': 70, 'đậu cove': 60,
        'cà chua': 45, 'dưa leo': 35, 'ớt chuông': 30,
        'khoai tây': 120, 'khoai lang': 110, 'củ sen': 90, 'củ cải': 100,
        'nấm': 60, 'giá đỗ': 50, 'hành tây': 25, 'tỏi': 8,
        
        # === NHÓM TINH BỘT ===
        'gạo tẻ': 80, 'gạo nàng hương': 85, 'gạo st25': 90,
        'bún tươi': 70, 'bánh phở': 65, 'mì sợi': 60,
        'bánh mì': 100, 'bánh bao': 120, 'bánh cuốn': 80,
        
        # === NHÓM THỰC PHẨM KHÔ ===
        'đường trắng': 15, 'đường phèn': 12, 'muối': 3, 'nước mắm': 8,
        'dầu ăn': 10, 'dầu oliu': 8, 'bơ': 15, 'mỡ': 5,
        'bột ngọt': 2, 'hạt nêm': 3, 'tương ớt': 5, 'sốt cà': 10,
        'sữa tươi': 200, 'sữa chua': 150, 'yaourt': 120,
        
        # === NHÓM TRÁI CÂY ===
        'chuối': 120, 'táo': 100, 'cam': 150, 'xoài': 130,
        'đu đủ': 140, 'dưa hấu': 180, 'dâu tây': 80, 'nho': 90
    }
    
    # Tạo danh sách món ăn và phân tích nguyên liệu thông minh
    dishes = []
    fresh_ingredients_with_qty = []
    dry_ingredients_with_qty = []
    fruit_ingredients_with_qty = []
    
    ingredient_count = {}
    dish_details = {}  # Lưu thông tin chi tiết từng món
    
    # Phân tích thực đơn chi tiết
    for day_key, day_data in menu_data.items():
        for meal_type, meal in day_data.items():
            if meal:
                dish_list = [dish.strip() for dish in meal.split(',') if dish.strip()]
                dishes.extend(dish_list)
                
                # Phân tích nguyên liệu thông minh dựa trên tên món
                for dish in dish_list:
                    dish_lower = dish.lower()
                    dish_ingredients = []
                    
                    # Tìm nguyên liệu trong tên món
                    for ingredient_key, portion in ingredient_portions.items():
                        if ingredient_key in dish_lower or any(word in dish_lower for word in ingredient_key.split()):
                            if ingredient_key not in ingredient_count:
                                ingredient_count[ingredient_key] = 0
                            ingredient_count[ingredient_key] += 1
                            dish_ingredients.append(ingredient_key)
                    
                    # Lưu thông tin món ăn
                    dish_details[dish] = {
                        'ingredients': dish_ingredients,
                        'meal_type': meal_type,
                        'day': day_key
                    }
    
    # Tính toán khối lượng thực tế và phân loại thông minh
    for ingredient_key, count in ingredient_count.items():
        # Tính khối lượng: số lần xuất hiện × khẩu phần × số học sinh × hệ số điều chỉnh
        adjustment_factor = 1.2 if count > 5 else 1.1  # Tăng 20% nếu dùng nhiều, 10% nếu ít
        total_weight = count * ingredient_portions[ingredient_key] * student_count * adjustment_factor
        weight_kg = round(total_weight / 1000, 2)
        
        # Chọn supplier phù hợp thông minh
        suitable_supplier = None
        supplier_info = {}
        
        # Logic chọn supplier dựa trên loại nguyên liệu
        if any(protein in ingredient_key for protein in ['thịt', 'cá', 'tôm', 'cua', 'trứng']):
            # Tìm supplier thực phẩm tươi sống
            for supplier_name in supplier_dict.keys():
                if any(keyword in supplier_name.lower() for keyword in ['tươi sống', 'hải sản', 'thịt', 'protein']):
                    suitable_supplier = supplier_name
                    break
        elif any(veg in ingredient_key for veg in ['rau', 'cải', 'củ', 'nấm']):
            # Tìm supplier rau củ
            for supplier_name in supplier_dict.keys():
                if any(keyword in supplier_name.lower() for keyword in ['rau củ', 'nông sản', 'organic']):
                    suitable_supplier = supplier_name
                    break
        elif any(fruit in ingredient_key for fruit in ['chuối', 'táo', 'cam', 'xoài', 'đu đủ', 'dâu']):
            # Tìm supplier trái cây
            for supplier_name in supplier_dict.keys():
                if any(keyword in supplier_name.lower() for keyword in ['trái cây', 'hoa quả', 'fruit']):
                    suitable_supplier = supplier_name
                    break
        
        # Nếu không tìm được supplier chuyên biệt, dùng supplier đầu tiên
        if not suitable_supplier and supplier_dict:
            suitable_supplier = list(supplier_dict.keys())[0]
        
        supplier_info = supplier_dict.get(suitable_supplier, {
            'address': 'Địa chỉ chưa cập nhật',
            'phone': 'SĐT chưa cập nhật',
            'contact_person': 'Người liên hệ chưa cập nhật',
            'food_safety_cert': 'Chưa có giấy chứng nhận'
        })
        
        ingredient_info = {
            'name': ingredient_key.title(),
            'weight_kg': weight_kg,
            'supplier': suitable_supplier or 'Nhà cung cấp chưa xác định',
            'supplier_info': supplier_info,
            'usage_frequency': count,
            'nutritional_value': get_nutritional_info(ingredient_key)
        }
        
        # Phân loại thông minh dựa trên đặc tính nguyên liệu
        if any(fresh in ingredient_key for fresh in ['thịt', 'cá', 'tôm', 'cua', 'trứng', 'rau', 'cải', 'củ', 'nấm', 'cà chua']):
            fresh_ingredients_with_qty.append(ingredient_info)
        elif any(fruit in ingredient_key for fruit in ['chuối', 'táo', 'cam', 'xoài', 'đu đủ', 'dâu']):
            fruit_ingredients_with_qty.append(ingredient_info)
        else:
            dry_ingredients_with_qty.append(ingredient_info)
    
    # Sắp xếp theo độ ưu tiên dinh dưỡng
    fresh_ingredients_with_qty.sort(key=lambda x: x['usage_frequency'], reverse=True)
    dry_ingredients_with_qty.sort(key=lambda x: x['usage_frequency'], reverse=True)
    fruit_ingredients_with_qty.sort(key=lambda x: x['usage_frequency'], reverse=True)
    
    # Loại bỏ trùng lặp món ăn và phân loại
    dishes = list(set(dishes))
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        
        # BƯỚC 1.1: Tiếp nhận thực phẩm tươi - Theo tiêu chuẩn chuyên nghiệp
        wb1 = Workbook()
        ws1 = wb1.active
        ws1.title = "Kiểm tra thực phẩm tươi"
        
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Định dạng border và style chuyên nghiệp
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        thick_border = Border(
            left=Side(style='thick'),
            right=Side(style='thick'),
            top=Side(style='thick'),
            bottom=Side(style='thick')
        )
        
        # Header chính - Dòng 1-5
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
        
        # Thông tin kiểm tra
        info_data = [
            (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân - Bếp trưởng", 'O', "Mẫu số 1.1"),
            (4, 'A', f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')} - Tuần {week_number}", 'O', f"Số học sinh: {student_count}"),
            (5, 'A', "Địa điểm: Bếp ăn Trường MNĐL Cây Nhỏ", 'O', "Phiên bản: v2.0")
        ]
        
        for row, col_a, text_a, col_o, text_o in info_data:
            ws1[f'{col_a}{row}'] = text_a
            ws1[f'{col_a}{row}'].font = Font(bold=True, size=10)
            ws1[f'{col_o}{row}'] = text_o
            ws1[f'{col_o}{row}'].font = Font(bold=True, size=10)
            ws1[f'{col_o}{row}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        
        # Tiêu đề phần I
        ws1['A7'] = "PHẦN I: THỰC PHẨM TƯƠI SỐNG, ĐÔNG LẠNH (Thịt, cá, rau, củ, quả...)"
        ws1['A7'].font = Font(bold=True, size=12, color="0066CC")
        ws1['A7'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        ws1.merge_cells('A7:M7')
        ws1['P7'] = "BƯỚC 1.1"
        ws1['P7'].font = Font(bold=True, size=12, color="FF0000")
        ws1['P7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
        
        # Header bảng chính - dòng 8-10
        headers_main = [
            'STT', 'TÊN THỰC PHẨM', 'XUẤT XỨ', 'THỜI GIAN NHẬP\n(Ngày/Giờ)', 
            'KHỐI LƯỢNG\n(kg/lít)', 'NHÀ CUNG CẤP', 'LIÊN HỆ', 'SỐ CHỨNG TỪ',
            'GIẤY PHÉP\nATTP', 'CHỨNG NHẬN\nVỆ SINH', 'KIỂM TRA CẢM QUAN',
            '', 'XÉT NGHIỆM NHANH', '', 'BIỆN PHÁP XỬ LÝ', 'GHI CHÚ DINH DƯỠNG'
        ]
        
        for i, header in enumerate(headers_main, 1):
            cell = ws1.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.border = thick_border
        
        # Sub-headers chi tiết - dòng 9
        sub_headers = [
            '', '', '', '', '', 'Tên cơ sở', 'SĐT/Địa chỉ', '', '', '', 
            'Đạt', 'Không đạt', 'Đạt', 'Không đạt', '', ''
        ]
        
        for i, header in enumerate(sub_headers, 1):
            cell = ws1.cell(row=9, column=i, value=header)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="B4C6E7", end_color="B4C6E7", fill_type="solid")
            cell.border = thin_border
        
        # Merge cells cho headers
        merge_ranges = ['K8:L8', 'M8:N8']  # Kiểm tra cảm quan, Xét nghiệm nhanh
        for merge_range in merge_ranges:
            ws1.merge_cells(merge_range)
        
        # Số thứ tự cột - dòng 10
        for i in range(1, 17):
            cell = ws1.cell(row=10, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu thực phẩm tươi với thông tin chi tiết
        for i, ingredient_info in enumerate(fresh_ingredients_with_qty[:25], 1):
            row_num = 10 + i
            supplier_info = ingredient_info.get('supplier_info', {})
            
            # Tạo thông tin xuất xứ thông minh
            origin = "Việt Nam"
            if any(keyword in ingredient_info['name'].lower() for keyword in ['hồi', 'cá hồi']):
                origin = "Na Uy/Chile"
            elif any(keyword in ingredient_info['name'].lower() for keyword in ['bò', 'thịt bò']):
                origin = "Úc/Việt Nam"
            
            data_row = [
                i,  # STT
                ingredient_info['name'].upper(),  # Tên thực phẩm
                origin,  # Xuất xứ
                f"{week_start.strftime('%d/%m/%Y')}\n6:00-7:00",  # Thời gian nhập
                f"{ingredient_info['weight_kg']} kg",  # Khối lượng
                ingredient_info.get('supplier', 'CTY TNHH Thực phẩm An toàn'),  # Nhà cung cấp
                f"{supplier_info.get('phone', '0902.xxx.xxx')}\n{supplier_info.get('address', 'Đà Lạt')[:30]}...",  # Liên hệ
                f"HD{1000+i:04d}",  # Số chứng từ tự động
                supplier_info.get('food_safety_cert', 'ATTP-001/2024'),  # Giấy phép
                "Đạt chuẩn VN",  # Chứng nhận vệ sinh
                '✓',  # Đạt cảm quan
                '',  # Không đạt cảm quan
                '✓' if ingredient_info['usage_frequency'] > 3 else '',  # Xét nghiệm (với thực phẩm dùng nhiều)
                '',  # Không đạt xét nghiệm
                "Bảo quản lạnh\nSử dụng ngay",  # Biện pháp xử lý
                ingredient_info.get('nutritional_value', 'N/A')[:25] + "..."  # Ghi chú dinh dưỡng
            ]
            
            for j, value in enumerate(data_row, 1):
                cell = ws1.cell(row=row_num, column=j, value=value)
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = thin_border
                
                # Styling đặc biệt
                if j == 1:  # STT
                    cell.font = Font(bold=True, color="0066CC")
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                elif j == 2:  # Tên thực phẩm  
                    cell.font = Font(bold=True, size=10)
                    cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                elif j in [11, 13] and value == '✓':  # Đánh dấu đạt
                    cell.font = Font(bold=True, size=12, color="00AA00")
                    cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
                elif j == 5:  # Khối lượng
                    cell.font = Font(bold=True, color="CC6600")
        
        # Thêm thông tin thống kê
        stats_row = len(fresh_ingredients_with_qty) + 12
        
        # Thống kê tổng quan
        ws1[f'A{stats_row}'] = "THỐNG KÊ TỔNG QUAN:"
        ws1[f'A{stats_row}'].font = Font(bold=True, size=11, color="0066CC")
        ws1[f'A{stats_row}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        
        total_weight = sum(item['weight_kg'] for item in fresh_ingredients_with_qty)
        total_items = len(fresh_ingredients_with_qty)
        
        stats_info = [
            f"• Tổng số loại thực phẩm tươi: {total_items} loại",
            f"• Tổng khối lượng ước tính: {total_weight:.1f} kg",
            f"• Số học sinh phục vụ: {student_count} em",
            f"• Khối lượng trung bình/học sinh: {total_weight/student_count:.2f} kg/em/tuần"
        ]
        
        for i, stat in enumerate(stats_info, 1):
            ws1[f'A{stats_row + i}'] = stat
            ws1[f'A{stats_row + i}'].font = Font(size=10)
        
        # Thêm ghi chú quan trọng
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
        
        # Chữ ký chuyên nghiệp
        signature_row = note_row + 7
        
        # Thêm khung chữ ký
        signature_data = [
            (signature_row, 'D', "BẾP TRƯỞNG", 'K', "HIỆU TRƯỞNG"),
            (signature_row + 1, 'D', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
            (signature_row + 5, 'D', "Nguyễn Thị Vân", 'K', "Nguyễn Thị Vân"),
            (signature_row + 6, 'D', f"Ngày {today.day}/{today.month}/{today.year}", 'K', f"Ngày {today.day}/{today.month}/{today.year}")
        ]
        
        for row, col_d, text_d, col_k, text_k in signature_data:
            ws1[f'{col_d}{row}'] = text_d
            ws1[f'{col_k}{row}'] = text_k
            
            # Định dạng chữ ký
            for col, text in [(col_d, text_d), (col_k, text_k)]:
                cell = ws1[f'{col}{row}']
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if row == signature_row:  # Chức danh
                    cell.font = Font(bold=True, size=12, color="0066CC")
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                elif row == signature_row + 1:  # Hướng dẫn
                    cell.font = Font(italic=True, size=9)
                elif row == signature_row + 5:  # Tên
                    cell.font = Font(bold=True, size=11)
                else:  # Ngày
                    cell.font = Font(size=9)
        
        file1_buffer = BytesIO()
        wb1.save(file1_buffer)
        file1_buffer.seek(0)
        zipf.writestr(f"Bước 1.1 - Tiếp nhận thực phẩm tươi - Tuần {week_number}.xlsx", file1_buffer.read())
        
        
        # BƯỚC 1.2: Tiếp nhận thực phẩm khô - Format chuyên nghiệp 
        wb2 = Workbook()
        ws2 = wb2.active
        ws2.title = "Kiểm tra thực phẩm khô"
        
        # Header chính giống Bước 1.1
        ws2['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
        ws2['A1'].font = Font(bold=True, size=12)
        ws2['A1'].fill = PatternFill(start_color="FFE6CC", end_color="FFE6CC", fill_type="solid")
        ws2.merge_cells('A1:P1')
        
        ws2['D2'] = "BIỂU MẪU KIỂM TRA THỰC PHẨM KHÔ VÀ BAO GÓI"
        ws2['D2'].font = Font(bold=True, size=14, color="FF0000")
        ws2['D2'].alignment = Alignment(horizontal='center', vertical='center')
        ws2.merge_cells('D2:M2')
        
        ws2['O2'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws2['O2'].font = Font(bold=True, size=10)
        ws2['O2'].fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        
        # Thông tin kiểm tra
        info_data2 = [
            (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân - Bếp trưởng", 'O', "Mẫu số 1.2"),
            (4, 'A', f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')} - Tuần {week_number}", 'O', f"Số học sinh: {student_count}"),
            (5, 'A', "Địa điểm: Kho thực phẩm khô - MNĐL Cây Nhỏ", 'O', "Phiên bản: v2.0")
        ]
        
        for row, col_a, text_a, col_o, text_o in info_data2:
            ws2[f'{col_a}{row}'] = text_a
            ws2[f'{col_a}{row}'].font = Font(bold=True, size=10)
            ws2[f'{col_o}{row}'] = text_o
            ws2[f'{col_o}{row}'].font = Font(bold=True, size=10)
            ws2[f'{col_o}{row}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        
        # Tiêu đề phần II
        ws2['A7'] = "PHẦN II: THỰC PHẨM KHÔ, BAO GÓI SẴN VÀ PHỤ GIA THỰC PHẨM"
        ws2['A7'].font = Font(bold=True, size=12, color="FF6600")
        ws2['A7'].fill = PatternFill(start_color="FFF2E6", end_color="FFF2E6", fill_type="solid")
        ws2.merge_cells('A7:M7')
        ws2['P7'] = "BƯỚC 1.2"
        ws2['P7'].font = Font(bold=True, size=12, color="FF0000")
        ws2['P7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
        
        # Header bảng chính - dòng 8-10  
        headers2_main = [
            'STT', 'TÊN THỰC PHẨM', 'NHÃN HIỆU', 'NHÀ SẢN XUẤT', 'ĐỊA CHỈ SẢN XUẤT',
            'THỜI GIAN NHẬP', 'KHỐI LƯỢNG\n(kg/lít)', 'NHÀ CUNG CẤP', 'LIÊN HỆ', 'HẠN SỬ DỤNG',
            'BẢO QUẢN', 'SỐ LÔ/MÃ', 'KIỂM TRA CẢM QUAN', '', 'BIỆN PHÁP', 'DINH DƯỠNG'
        ]
        
        for i, header in enumerate(headers2_main, 1):
            cell = ws2.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="E67E22", end_color="E67E22", fill_type="solid")
            cell.border = thick_border
        
        # Sub-headers chi tiết
        sub_headers2 = [
            '', '', '', '', '', '', '', 'Tên cơ sở', 'SĐT/Địa chỉ', '', '', '', 
            'Đạt', 'Không đạt', '', ''
        ]
        
        for i, header in enumerate(sub_headers2, 1):
            cell = ws2.cell(row=9, column=i, value=header)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="F8C471", end_color="F8C471", fill_type="solid")
            cell.border = thin_border
        
        # Merge cells cho headers
        ws2.merge_cells('M8:N8')  # Kiểm tra cảm quan
        
        # Số thứ tự cột
        for i in range(1, 17):
            cell = ws2.cell(row=10, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu thực phẩm khô chi tiết
        for i, ingredient_info in enumerate(dry_ingredients_with_qty[:25], 1):
            row_num = 10 + i
            supplier_info = ingredient_info.get('supplier_info', {})
            
            # Tạo thông tin hạn sử dụng thông minh
            expiry_date = (today + timedelta(days=365)).strftime('%d/%m/%Y') if 'gạo' in ingredient_info['name'].lower() else (today + timedelta(days=180)).strftime('%d/%m/%Y')
            
            # Nhãn hiệu thông minh
            brand = "Chưa xác định"
            if 'gạo' in ingredient_info['name'].lower():
                brand = "ST25/Jasmine"
            elif 'sữa' in ingredient_info['name'].lower():
                brand = "Vinamilk/TH"
            elif 'dầu' in ingredient_info['name'].lower():
                brand = "Tường An/Neptune"
            
            data_row2 = [
                i,  # STT
                ingredient_info['name'].upper(),  # Tên thực phẩm
                brand,  # Nhãn hiệu
                "Công ty TNHH Thực phẩm Việt",  # Nhà sản xuất
                "KCN Đồng An, Thuận An, Bình Dương",  # Địa chỉ sản xuất
                f"{week_start.strftime('%d/%m/%Y')}\n8:00-9:00",  # Thời gian nhập
                f"{ingredient_info['weight_kg']} kg",  # Khối lượng
                ingredient_info.get('supplier', 'Siêu thị Co.opmart'),  # Nhà cung cấp
                f"{supplier_info.get('phone', '0902.xxx.xxx')}\n{supplier_info.get('address', 'Đà Lạt')[:25]}...",  # Liên hệ
                expiry_date,  # Hạn sử dụng
                "Khô ráo, thoáng mát\n<25°C",  # Bảo quản
                f"LOT{2024000+i:06d}",  # Số lô
                '✓',  # Đạt cảm quan
                '',  # Không đạt
                "Sử dụng theo FIFO\nKiểm tra định kỳ",  # Biện pháp
                ingredient_info.get('nutritional_value', 'N/A')[:20] + "..."  # Dinh dưỡng
            ]
            
            for j, value in enumerate(data_row2, 1):
                cell = ws2.cell(row=row_num, column=j, value=value)
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = thin_border
                
                # Styling đặc biệt
                if j == 1:  # STT
                    cell.font = Font(bold=True, color="E67E22")
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                elif j == 2:  # Tên thực phẩm
                    cell.font = Font(bold=True, size=10)
                    cell.fill = PatternFill(start_color="FEF9E7", end_color="FEF9E7", fill_type="solid")
                elif j == 13 and value == '✓':  # Đánh dấu đạt
                    cell.font = Font(bold=True, size=12, color="27AE60")
                    cell.fill = PatternFill(start_color="E8F5E8", end_color="E8F5E8", fill_type="solid")
                elif j == 7:  # Khối lượng
                    cell.font = Font(bold=True, color="D35400")
                elif j == 10:  # Hạn sử dụng
                    cell.font = Font(bold=True, color="8E44AD")
        
        # Thống kê cho thực phẩm khô
        stats_row2 = len(dry_ingredients_with_qty) + 12
        ws2[f'A{stats_row2}'] = "THỐNG KÊ THỰC PHẨM KHÔ:"
        ws2[f'A{stats_row2}'].font = Font(bold=True, size=11, color="E67E22")
        ws2[f'A{stats_row2}'].fill = PatternFill(start_color="FFF2E6", end_color="FFF2E6", fill_type="solid")
        
        total_weight2 = sum(item['weight_kg'] for item in dry_ingredients_with_qty)
        total_items2 = len(dry_ingredients_with_qty)
        
        stats_info2 = [
            f"• Tổng số loại thực phẩm khô: {total_items2} loại",
            f"• Tổng khối lượng ước tính: {total_weight2:.1f} kg", 
            f"• Tỷ lệ thực phẩm khô/tổng: {total_weight2/(total_weight+total_weight2)*100:.1f}%",
            f"• Chu kỳ nhập hàng khuyến nghị: 2 tuần/lần"
        ]
        
        for i, stat in enumerate(stats_info2, 1):
            ws2[f'A{stats_row2 + i}'] = stat
            ws2[f'A{stats_row2 + i}'].font = Font(size=10)
        
        # Ghi chú đặc biệt cho thực phẩm khô
        note_row2 = stats_row2 + 6
        ws2[f'A{note_row2}'] = "NGUYÊN TẮC BẢO QUẢN THỰC PHẨM KHÔ:"
        ws2[f'A{note_row2}'].font = Font(bold=True, size=11, color="D35400")
        
        notes2 = [
            "• Nhiệt độ: <25°C, độ ẩm: <60%, tránh ánh sáng trực tiếp",
            "• Nguyên tắc FIFO: First In - First Out (hàng nhập trước - xuất trước)",
            "• Kiểm tra hạn sử dụng hàng tuần, báo cáo hàng cận date",
            "• Bảo quản riêng biệt: gia vị, ngũ cốc, đồ khô"
        ]
        
        for i, note in enumerate(notes2, 1):
            ws2[f'A{note_row2 + i}'] = note
            ws2[f'A{note_row2 + i}'].font = Font(size=9, color="A0522D")
        
        # Chữ ký tương tự Bước 1.1
        signature_row2 = note_row2 + 7
        signature_data2 = [
            (signature_row2, 'D', "BẾP TRƯỞNG", 'K', "HIỆU TRƯỞNG"),
            (signature_row2 + 1, 'D', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
            (signature_row2 + 5, 'D', "Nguyễn Thị Vân", 'K', "Nguyễn Thị Vân"),
            (signature_row2 + 6, 'D', f"Ngày {today.day}/{today.month}/{today.year}", 'K', f"Ngày {today.day}/{today.month}/{today.year}")
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
        
        file2_buffer = BytesIO()
        wb2.save(file2_buffer)
        file2_buffer.seek(0)
        zipf.writestr(f"Bước 1.2 - Tiếp nhận thực phẩm khô - Tuần {week_number}.xlsx", file2_buffer.read())
        
        # BƯỚC 2: Kiểm tra khi chế biến thức ăn - Format chuyên nghiệp
        wb3 = Workbook()
        ws3 = wb3.active
        ws3.title = "Kiểm tra chế biến"
        
        # Header chính tương tự các bước trước
        ws3['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
        ws3['A1'].font = Font(bold=True, size=12)
        ws3['A1'].fill = PatternFill(start_color="FFE6CC", end_color="FFE6CC", fill_type="solid")
        ws3.merge_cells('A1:O1')
        
        ws3['D2'] = "BIỂU MẪU KIỂM TRA KHI CHẾ BIẾN THỨC ĂN"
        ws3['D2'].font = Font(bold=True, size=14, color="FF0000")
        ws3['D2'].alignment = Alignment(horizontal='center', vertical='center')
        ws3.merge_cells('D2:K2')
        
        ws3['M2'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws3['M2'].font = Font(bold=True, size=10)
        ws3['M2'].fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        
        # Thông tin kiểm tra
        info_data3 = [
            (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân - Bếp trưởng", 'M', "Mẫu số 2.0"),
            (4, 'A', f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')} - Tuần {week_number}", 'M', f"Số học sinh: {student_count}"),
            (5, 'A', "Địa điểm: Bếp chế biến - MNĐL Cây Nhỏ", 'M', "Phiên bản: v2.0")
        ]
        
        for row, col_a, text_a, col_m, text_m in info_data3:
            ws3[f'{col_a}{row}'] = text_a
            ws3[f'{col_a}{row}'].font = Font(bold=True, size=10)
            ws3[f'{col_m}{row}'] = text_m
            ws3[f'{col_m}{row}'].font = Font(bold=True, size=10)
            ws3[f'{col_m}{row}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        
        # Tiêu đề phần II
        ws3['A7'] = "PHẦN II: KIỂM TRA QUY TRÌNH CHẾ BIẾN THỨC ĂN"
        ws3['A7'].font = Font(bold=True, size=12, color="8B0000")
        ws3['A7'].fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
        ws3.merge_cells('A7:L7')
        ws3['O7'] = "BƯỚC 2"
        ws3['O7'].font = Font(bold=True, size=12, color="FF0000")
        ws3['O7'].fill = PatternFill(start_color="FFEEEE", end_color="FFEEEE", fill_type="solid")
        
        # Header bảng chính - dòng 8
        headers3_main = [
            'STT', 'CA/BỮA ĂN', 'TÊN MÓN ĂN', 'NGUYÊN LIỆU CHÍNH', 'SỐ SUẤT\n(phần)', 
            'SƠ CHẾ XONG\n(giờ)', 'CHẾ BIẾN XONG\n(giờ)', 'KIỂM TRA VỆ SINH', '', '',
            'CẢM QUAN THỨC ĂN', '', 'BIỆN PHÁP\nXỬ LÝ', 'GHI CHÚ\nDINH DƯỠNG', 'NHIỆT ĐỘ\nMÓN ĂN'
        ]
        
        for i, header in enumerate(headers3_main, 1):
            cell = ws3.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
            cell.border = thick_border
        
        # Sub-headers chi tiết - dòng 9
        sub_headers3 = [
            '', '', '', '', '', '', '', 'Nhân viên', 'Dụng cụ', 'Khu vực',
            'Đạt', 'Không đạt', '', '', ''
        ]
        
        for i, header in enumerate(sub_headers3, 1):
            cell = ws3.cell(row=9, column=i, value=header)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="CD5C5C", end_color="CD5C5C", fill_type="solid")
            cell.border = thin_border
        
        # Merge cells cho headers
        merge_ranges3 = ['H8:J8', 'K8:L8']  # Vệ sinh, Cảm quan
        for merge_range in merge_ranges3:
            ws3.merge_cells(merge_range)
        
        # Số thứ tự cột
        for i in range(1, 16):
            cell = ws3.cell(row=10, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu món ăn theo ca với thông tin chi tiết
        row_num = 11
        meal_times = {
            'morning': ('Bữa sáng\n6:30-7:00', '6:00', '6:25'),
            'snack': ('Ăn phụ sáng\n9:00-9:30', '8:30', '8:55'), 
            'lunch': ('Bữa trưa\n11:00-12:00', '10:00', '10:50'),
            'afternoon': ('Ăn phụ chiều\n14:30-15:00', '14:00', '14:25'),
            'lateafternoon': ('Bữa xế\n16:00-16:30', '15:30', '15:55'),
            'dessert': ('Tráng miệng\n12:15-12:30', '11:50', '12:10')
        }
        
        stt = 1
        days_vn = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        
        for day_idx, day_key in enumerate(days):
            if day_key in menu_data:
                for meal_key, (ca_name, start_time, end_time) in meal_times.items():
                    if menu_data[day_key].get(meal_key):
                        dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                        for dish in dishes:
                            # Tạo nguyên liệu thông minh dựa trên tên món
                            ingredients = get_smart_ingredients(dish)
                            temperature = get_serving_temperature(dish)
                            
                            data_row3 = [
                                stt,  # STT
                                f"{days_vn[day_idx]}\n{ca_name}",  # Ca/bữa ăn với ngày
                                dish.title(),  # Tên món ăn
                                ingredients,  # Nguyên liệu chính
                                f"{student_count} phần",  # Số suất
                                start_time,  # Sơ chế xong
                                end_time,  # Chế biến xong
                                "Đạt chuẩn\nVS-ATTP",  # Nhân viên
                                "Sạch sẽ\nKhử trùng",  # Dụng cụ
                                "Đảm bảo\n5S",  # Khu vực
                                '✓',  # Đạt cảm quan
                                '',  # Không đạt
                                "Giữ nhiệt độ\nPhục vụ ngay",  # Biện pháp
                                get_dish_nutrition(dish),  # Ghi chú dinh dưỡng
                                temperature  # Nhiệt độ
                            ]
                            
                            for j, value in enumerate(data_row3, 1):
                                cell = ws3.cell(row=row_num, column=j, value=value)
                                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                                cell.border = thin_border
                                
                                # Styling đặc biệt
                                if j == 1:  # STT
                                    cell.font = Font(bold=True, color="8B0000")
                                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                                elif j == 3:  # Tên món ăn
                                    cell.font = Font(bold=True, size=10)
                                    cell.fill = PatternFill(start_color="FFF0F5", end_color="FFF0F5", fill_type="solid")
                                elif j == 11 and value == '✓':  # Đạt
                                    cell.font = Font(bold=True, size=12, color="228B22")
                                    cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                                elif j == 15:  # Nhiệt độ
                                    cell.font = Font(bold=True, color="FF4500")
                            
                            row_num += 1
                            stt += 1
                            
                            if row_num > 40:  # Giới hạn số dòng
                                break
                    if row_num > 40:
                        break
                if row_num > 40:
                    break
        
        # Thống kê quy trình chế biến
        stats_row3 = row_num + 2
        ws3[f'A{stats_row3}'] = "THỐNG KÊ QUY TRÌNH CHẾ BIẾN:"
        ws3[f'A{stats_row3}'].font = Font(bold=True, size=11, color="8B0000")
        ws3[f'A{stats_row3}'].fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
        
        total_dishes = stt - 1
        total_meals = len([meal for day_data in menu_data.values() for meal in day_data.values() if meal])
        
        stats_info3 = [
            f"• Tổng số món ăn trong tuần: {total_dishes} món",
            f"• Tổng số bữa ăn: {total_meals} bữa",
            f"• Trung bình món/bữa: {total_dishes/total_meals:.1f} món/bữa",
            f"• Thời gian chế biến trung bình: 25-30 phút/món"
        ]
        
        for i, stat in enumerate(stats_info3, 1):
            ws3[f'A{stats_row3 + i}'] = stat
            ws3[f'A{stats_row3 + i}'].font = Font(size=10)
        
        # Quy trình an toàn thực phẩm
        safety_row = stats_row3 + 6
        ws3[f'A{safety_row}'] = "QUY TRÌNH AN TOÀN THỰC PHẨM KHI CHẾ BIẾN:"
        ws3[f'A{safety_row}'].font = Font(bold=True, size=11, color="DC143C")
        
        safety_notes = [
            "• Nhiệt độ chế biến: >75°C (kiểm tra bằng nhiệt kế thực phẩm)",
            "• Thời gian từ chế biến xong đến phục vụ: <2 giờ",
            "• Nguyên tắc: Nấu chín, ăn nóng, bảo quản lạnh", 
            "• Kiểm tra cảm quan: màu sắc, mùi vị, độ chín, độ mềm phù hợp trẻ em"
        ]
        
        for i, note in enumerate(safety_notes, 1):
            ws3[f'A{safety_row + i}'] = note
            ws3[f'A{safety_row + i}'].font = Font(size=9, color="B22222")
        
        # Chữ ký chuyên nghiệp
        signature_row3 = safety_row + 7
        signature_data3 = [
            (signature_row3, 'C', "BẾP TRƯỞNG", 'I', "HIỆU TRƯỞNG"),
            (signature_row3 + 1, 'C', "(Ký, ghi rõ họ tên)", 'I', "(Ký, ghi rõ họ tên)"),
            (signature_row3 + 5, 'C', "Nguyễn Thị Vân", 'I', "Nguyễn Thị Vân"),
            (signature_row3 + 6, 'C', f"Ngày {today.day}/{today.month}/{today.year}", 'I', f"Ngày {today.day}/{today.month}/{today.year}")
        ]
        
        for row, col_c, text_c, col_i, text_i in signature_data3:
            ws3[f'{col_c}{row}'] = text_c
            ws3[f'{col_i}{row}'] = text_i
            
            for col, text in [(col_c, text_c), (col_i, text_i)]:
                cell = ws3[f'{col}{row}']
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if row == signature_row3:
                    cell.font = Font(bold=True, size=12, color="8B0000")
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                elif row == signature_row3 + 1:
                    cell.font = Font(italic=True, size=9)
                elif row == signature_row3 + 5:
                    cell.font = Font(bold=True, size=11)
                else:
                    cell.font = Font(size=9)
        
        file3_buffer = BytesIO()
        wb3.save(file3_buffer)
        file3_buffer.seek(0)
        zipf.writestr(f"Bước 2 - Kiểm tra chế biến thức ăn - Tuần {week_number}.xlsx", file3_buffer.read())
        
        # BƯỚC 2.1: Kiểm tra mẫu thức ăn lưu mẫu - Format chuyên nghiệp
        wb21 = Workbook()
        ws21 = wb21.active
        ws21.title = "Lưu mẫu thức ăn"
        
        # Header chính
        ws21['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
        ws21['A1'].font = Font(bold=True, size=12)
        ws21['A1'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        ws21.merge_cells('A1:P1')
        
        ws21['D2'] = "BIỂU MẪU KIỂM TRA MẪU THỨC ĂN LƯU MẪU"
        ws21['D2'].font = Font(bold=True, size=14, color="0066CC")
        ws21['D2'].alignment = Alignment(horizontal='center', vertical='center')
        ws21.merge_cells('D2:L2')
        
        ws21['N2'] = "Số: 1247/QĐ - Bộ Y Tế"
        ws21['N2'].font = Font(bold=True, size=10)
        ws21['N2'].fill = PatternFill(start_color="CCE6FF", end_color="CCE6FF", fill_type="solid")
        
        # Thông tin kiểm tra
        info_data21 = [
            (3, 'A', f"Người lưu mẫu: Nguyễn Thị Vân - Bếp trưởng", 'N', "Mẫu số 2.1"),
            (4, 'A', f"Tuần kiểm tra: Tuần {week_number} ({week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')})", 'N', f"Số suất: {student_count}"),
            (5, 'A', "Địa điểm lưu mẫu: Tủ lạnh chuyên dụng - Bếp ăn", 'N', "Nhiệt độ: 2-8°C")
        ]
        
        for row, col_a, text_a, col_n, text_n in info_data21:
            ws21[f'{col_a}{row}'] = text_a
            ws21[f'{col_a}{row}'].font = Font(bold=True, size=10)
            ws21[f'{col_n}{row}'] = text_n
            ws21[f'{col_n}{row}'].font = Font(bold=True, size=10)
            ws21[f'{col_n}{row}'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
        
        # Tiêu đề phần chính
        ws21['A7'] = "PHẦN III: KIỂM TRA MẪU THỨC ĂN LƯU MẪU"
        ws21['A7'].font = Font(bold=True, size=12, color="0066CC")
        ws21['A7'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        ws21.merge_cells('A7:M7')
        ws21['P7'] = "BƯỚC 2.1"
        ws21['P7'].font = Font(bold=True, size=12, color="0066CC")
        ws21['P7'].fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
        
        # Header bảng chính
        headers21 = [
            'STT', 'NGÀY/BUỔI', 'TÊN MÓN ĂN', 'THỜI GIAN\nLƯU MẪU', 'SỐ LƯỢNG\nMẪU (g)', 
            'NHIỆT ĐỘ\nLƯU MẪU', 'THỜI GIAN\nBẢO QUẢN', 'ĐÁNH GIÁ CẢM QUAN', '', '',
            'TÌNH TRẠNG\nMẪU', 'SỐ LÔ\nMẪU', 'GHI CHÚ\nĐẶC BIỆT', 'NGƯỜI\nLƯU MẪU', 'KIỂM TRA\nCUỐI NGÀY'
        ]
        
        for i, header in enumerate(headers21, 1):
            cell = ws21.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
            cell.border = thick_border
        
        # Sub-headers cho cảm quan
        sub_headers21 = [
            '', '', '', '', '', '', '', 'Màu sắc', 'Mùi vị', 'Kết cấu',
            '', '', '', '', ''
        ]
        
        for i, header in enumerate(sub_headers21, 1):
            cell = ws21.cell(row=9, column=i, value=header)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="4D94FF", end_color="4D94FF", fill_type="solid")
            cell.border = thin_border
        
        # Merge cells cho headers
        ws21.merge_cells('H8:J8')  # Đánh giá cảm quan
        
        # Số thứ tự cột
        for i in range(1, 16):
            cell = ws21.cell(row=10, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu lưu mẫu
        row_num = 11
        stt = 1
        
        for day_idx, day_key in enumerate(days):
            if day_key in menu_data:
                current_date = week_start + timedelta(days=day_idx)
                
                # Chỉ lưu mẫu bữa trưa và bữa phụ chính
                key_meals = {
                    'lunch': 'Bữa trưa\n11:00-12:00',
                    'snack': 'Ăn phụ sáng\n9:00-9:30',
                    'afternoon': 'Ăn phụ chiều\n14:30-15:00'
                }
                
                for meal_key, meal_name in key_meals.items():
                    if menu_data[day_key].get(meal_key):
                        dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                        for dish in dishes:
                            # Chỉ lưu mẫu món chính, không lưu nước uống
                            if any(keyword in dish.lower() for keyword in ['nước', 'sữa', 'trà', 'chanh']):
                                continue
                                
                            sample_time = '11:45' if meal_key == 'lunch' else ('9:15' if meal_key == 'snack' else '14:45')
                            lot_number = f"LM{current_date.strftime('%d%m')}{stt:02d}"
                            
                            data_row21 = [
                                stt,  # STT
                                f"{days_vn[day_idx]}\n{current_date.strftime('%d/%m')}\n{meal_name}",  # Ngày/buổi
                                dish.title(),  # Tên món ăn
                                sample_time,  # Thời gian lưu mẫu
                                "100g",  # Số lượng mẫu
                                "2-4°C",  # Nhiệt độ lưu mẫu
                                "48 giờ",  # Thời gian bảo quản
                                "Bình thường",  # Màu sắc
                                "Tự nhiên",  # Mùi vị
                                "Phù hợp",  # Kết cấu
                                "Đạt chuẩn\nATTP",  # Tình trạng mẫu
                                lot_number,  # Số lô mẫu
                                get_sample_note(dish),  # Ghi chú đặc biệt
                                "N.T.Vân",  # Người lưu mẫu
                                "✓"  # Kiểm tra cuối ngày
                            ]
                            
                            for j, value in enumerate(data_row21, 1):
                                cell = ws21.cell(row=row_num, column=j, value=value)
                                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                                cell.border = thin_border
                                
                                # Styling đặc biệt
                                if j == 1:  # STT
                                    cell.font = Font(bold=True, color="0066CC")
                                    cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                                elif j == 3:  # Tên món ăn
                                    cell.font = Font(bold=True, size=10)
                                    cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                                elif j == 15 and value == '✓':  # Kiểm tra
                                    cell.font = Font(bold=True, size=12, color="228B22")
                                    cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                                elif j == 12:  # Số lô
                                    cell.font = Font(bold=True, color="FF6600")
                            
                            row_num += 1
                            stt += 1
                            
                            if row_num > 35:  # Giới hạn
                                break
                    if row_num > 35:
                        break
                if row_num > 35:
                    break
        
        # Thống kê lưu mẫu
        stats_row21 = row_num + 2
        ws21[f'A{stats_row21}'] = "THỐNG KÊ LƯU MẪU THỨC ĂN:"
        ws21[f'A{stats_row21}'].font = Font(bold=True, size=11, color="0066CC")
        ws21[f'A{stats_row21}'].fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        
        total_samples = stt - 1
        stats_info21 = [
            f"• Tổng số mẫu lưu trong tuần: {total_samples} mẫu",
            f"• Thời gian bảo quản: 48 giờ (2 ngày)",
            f"• Nhiệt độ lưu mẫu: 2-4°C (tủ lạnh chuyên dụng)",
            f"• Tần suất kiểm tra: 2 lần/ngày (sáng và chiều)"
        ]
        
        for i, stat in enumerate(stats_info21, 1):
            ws21[f'A{stats_row21 + i}'] = stat
            ws21[f'A{stats_row21 + i}'].font = Font(size=10)
        
        # Quy trình lưu mẫu
        procedure_row = stats_row21 + 6
        ws21[f'A{procedure_row}'] = "QUY TRÌNH LƯU MẪU THỨC ĂN:"
        ws21[f'A{procedure_row}'].font = Font(bold=True, size=11, color="004080")
        
        procedure_notes = [
            "• Lấy mẫu: Ngay sau khi chế biến xong, trước khi phục vụ",
            "• Dụng cụ: Thìa/muỗng vô trùng, hộp nhựa có nắp đậy kín",
            "• Ghi nhãn: Tên món, ngày giờ, số lô, người lấy mẫu",
            "• Bảo quản: Tủ lạnh riêng, không để chung với thực phẩm khác",
            "• Hủy mẫu: Sau 48 giờ nếu không có sự cố thực phẩm"
        ]
        
        for i, note in enumerate(procedure_notes, 1):
            ws21[f'A{procedure_row + i}'] = note
            ws21[f'A{procedure_row + i}'].font = Font(size=9, color="004080")
        
        # Chữ ký
        signature_row21 = procedure_row + 8
        signature_data21 = [
            (signature_row21, 'D', "NGƯỜI LƯU MẪU", 'L', "HIỆU TRƯỞNG"),
            (signature_row21 + 1, 'D', "(Ký, ghi rõ họ tên)", 'L', "(Ký, ghi rõ họ tên)"),
            (signature_row21 + 5, 'D', "Nguyễn Thị Vân", 'L', "Nguyễn Thị Vân"),
            (signature_row21 + 6, 'D', f"Ngày {today.day}/{today.month}/{today.year}", 'L', f"Ngày {today.day}/{today.month}/{today.year}")
        ]
        
        for row, col_d, text_d, col_l, text_l in signature_data21:
            ws21[f'{col_d}{row}'] = text_d
            ws21[f'{col_l}{row}'] = text_l
            
            for col, text in [(col_d, text_d), (col_l, text_l)]:
                cell = ws21[f'{col}{row}']
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if row == signature_row21:
                    cell.font = Font(bold=True, size=12, color="0066CC")
                    cell.fill = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid")
                elif row == signature_row21 + 1:
                    cell.font = Font(italic=True, size=9)
                elif row == signature_row21 + 5:
                    cell.font = Font(bold=True, size=11)
                else:
                    cell.font = Font(size=9)
        
        file21_buffer = BytesIO()
        wb21.save(file21_buffer)
        file21_buffer.seek(0)
        zipf.writestr(f"Bước 2.1 - Lưu mẫu thức ăn - Tuần {week_number}.xlsx", file21_buffer.read())
        
        # BƯỚC 3: Kiểm tra bảo quản và phục vụ thức ăn - Format chuyên nghiệp  
        wb4 = Workbook()
        ws4 = wb4.active
        ws4.title = "Bảo quản và phục vụ"
        
        # Header chính
        ws4['A1'] = "TÊN CƠ SỞ: MNĐL Cây Nhỏ"
        ws4['A1'].font = Font(bold=True, size=12)
        ws4['A1'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
        ws4.merge_cells('A1:O1')
        
        ws4['D2'] = "BIỂU MẪU KIỂM TRA BẢO QUẢN VÀ PHỤC VỤ THỨC ĂN"
        ws4['D2'].font = Font(bold=True, size=14, color="006600")
        ws4['D2'].alignment = Alignment(horizontal='center', vertical='center')
        ws4.merge_cells('D2:K2')
        
        ws4['M2'] = "Số: 1248/QĐ - Bộ Y Tế"
        ws4['M2'].font = Font(bold=True, size=10)
        ws4['M2'].fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        
        # Thông tin kiểm tra
        info_data4 = [
            (3, 'A', f"Người kiểm tra: Nguyễn Thị Vân - Bếp trưởng", 'M', "Mẫu số 3.0"),
            (4, 'A', f"Tuần kiểm tra: Tuần {week_number} ({week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')})", 'M', f"Số học sinh: {student_count}"),
            (5, 'A', "Khu vực: Bếp ăn + Khu phục vụ - MNĐL Cây Nhỏ", 'M', "Chuẩn: ATTP 2021")
        ]
        
        for row, col_a, text_a, col_m, text_m in info_data4:
            ws4[f'{col_a}{row}'] = text_a
            ws4[f'{col_a}{row}'].font = Font(bold=True, size=10)
            ws4[f'{col_m}{row}'] = text_m
            ws4[f'{col_m}{row}'].font = Font(bold=True, size=10)
            ws4[f'{col_m}{row}'].fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
        
        # Tiêu đề phần chính
        ws4['A7'] = "PHẦN IV: KIỂM TRA BẢO QUẢN VÀ PHỤC VỤ THỨC ĂN"
        ws4['A7'].font = Font(bold=True, size=12, color="006600")
        ws4['A7'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
        ws4.merge_cells('A7:L7')
        ws4['O7'] = "BƯỚC 3"
        ws4['O7'].font = Font(bold=True, size=12, color="006600")
        ws4['O7'].fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
        
        # Header bảng chính
        headers4 = [
            'STT', 'NGÀY/CA\nPHỤC VỤ', 'TÊN MÓN ĂN', 'THỜI GIAN\nHOÀN THÀNH', 'THỜI GIAN\nPHỤC VỤ',
            'NHIỆT ĐỘ\nKHI PHỤC VỤ', 'THIẾT BỊ\nGIỮ NHIỆT', 'VỆ SINH DỤNG CỤ', '', 
            'ĐÁNH GIÁ\nPHỤC VỤ', '', 'BIỆN PHÁP\nXỬ LÝ', 'SỐ SUẤT\nTHỰC TẾ', 'GHI CHÚ\nĐẶC BIỆT'
        ]
        
        for i, header in enumerate(headers4, 1):
            cell = ws4.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9, color="FFFFFF")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="006600", end_color="006600", fill_type="solid")
            cell.border = thick_border
        
        # Sub-headers chi tiết
        sub_headers4 = [
            '', '', '', '', '', '', '', 'Chén/bát', 'Thìa/đũa',
            'Đạt', 'Không đạt', '', '', ''
        ]
        
        for i, header in enumerate(sub_headers4, 1):
            cell = ws4.cell(row=9, column=i, value=header)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="4D9900", end_color="4D9900", fill_type="solid")
            cell.border = thin_border
        
        # Merge cells cho headers
        merge_ranges4 = ['H8:I8', 'J8:K8']  # Vệ sinh dụng cụ, Đánh giá phục vụ
        for merge_range in merge_ranges4:
            ws4.merge_cells(merge_range)
        
        # Số thứ tự cột
        for i in range(1, 15):
            cell = ws4.cell(row=10, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu phục vụ thức ăn
        row_num = 11
        stt = 1
        
        for day_idx, day_key in enumerate(days):
            if day_key in menu_data:
                current_date = week_start + timedelta(days=day_idx)
                
                for meal_key, (ca_name, start_time, end_time) in meal_times.items():
                    if menu_data[day_key].get(meal_key):
                        dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                        for dish in dishes:
                            # Thời gian phục vụ
                            serve_times = {
                                'morning': '6:30',
                                'snack': '9:00', 
                                'lunch': '11:00',
                                'afternoon': '14:30',
                                'lateafternoon': '16:00',
                                'dessert': '12:15'
                            }
                            serve_time = serve_times.get(meal_key, '12:00')
                            
                            # Thiết bị giữ nhiệt
                            equipment = get_heating_equipment(dish)
                            serving_temp = get_serving_temperature(dish)
                            actual_portions = get_actual_portions(dish, student_count)
                            
                            data_row4 = [
                                stt,  # STT
                                f"{days_vn[day_idx]}\n{current_date.strftime('%d/%m')}\n{ca_name}",  # Ngày/ca
                                dish.title(),  # Tên món ăn
                                end_time,  # Thời gian hoàn thành
                                serve_time,  # Thời gian phục vụ
                                serving_temp,  # Nhiệt độ khi phục vụ
                                equipment,  # Thiết bị giữ nhiệt
                                "Sạch sẽ\nKhử trùng",  # Chén/bát
                                "Sạch sẽ\nKhử trùng",  # Thìa/đũa
                                '✓',  # Đạt
                                '',  # Không đạt
                                "Phục vụ\nđúng giờ",  # Biện pháp xử lý
                                f"{actual_portions} phần",  # Số suất thực tế
                                get_serving_note(dish)  # Ghi chú đặc biệt
                            ]
                            
                            for j, value in enumerate(data_row4, 1):
                                cell = ws4.cell(row=row_num, column=j, value=value)
                                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                                cell.border = thin_border
                                
                                # Styling đặc biệt
                                if j == 1:  # STT
                                    cell.font = Font(bold=True, color="006600")
                                    cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                                elif j == 3:  # Tên món ăn
                                    cell.font = Font(bold=True, size=10)
                                    cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                                elif j == 10 and value == '✓':  # Đạt
                                    cell.font = Font(bold=True, size=12, color="228B22")
                                    cell.fill = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")
                                elif j == 6:  # Nhiệt độ
                                    cell.font = Font(bold=True, color="FF4500")
                                elif j == 13:  # Số suất thực tế
                                    cell.font = Font(bold=True, color="0066CC")
                            
                            row_num += 1
                            stt += 1
                            
                            if row_num > 40:  # Giới hạn
                                break
                    if row_num > 40:
                        break
                if row_num > 40:
                    break
        
        # Thống kê phục vụ
        stats_row4 = row_num + 2
        ws4[f'A{stats_row4}'] = "THỐNG KÊ PHỤC VỤ THỨC ĂN:"
        ws4[f'A{stats_row4}'].font = Font(bold=True, size=11, color="006600")
        ws4[f'A{stats_row4}'].fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")
        
        total_servings = stt - 1
        total_portions = sum(get_actual_portions('', student_count) for _ in range(total_servings))
        
        stats_info4 = [
            f"• Tổng số lần phục vụ: {total_servings} lần",
            f"• Tổng số suất ăn phục vụ: {total_portions} suất",
            f"• Trung bình suất/lần: {total_portions/total_servings:.1f} suất/lần",
            f"• Thời gian trung bình từ chế biến xong đến phục vụ: <30 phút"
        ]
        
        for i, stat in enumerate(stats_info4, 1):
            ws4[f'A{stats_row4 + i}'] = stat
            ws4[f'A{stats_row4 + i}'].font = Font(size=10)
        
        # Nguyên tắc bảo quản và phục vụ
        principles_row = stats_row4 + 6
        ws4[f'A{principles_row}'] = "NGUYÊN TẮC BẢO QUẢN VÀ PHỤC VỤ AN TOÀN:"
        ws4[f'A{principles_row}'].font = Font(bold=True, size=11, color="004000")
        
        principles_notes = [
            "• Thời gian: Từ chế biến xong đến phục vụ không quá 2 giờ",
            "• Nhiệt độ: Món nóng >60°C, món lạnh <10°C khi phục vụ",
            "• Thiết bị: Sử dụng tủ giữ nhiệt, nồi cơm điện, bình giữ nhiệt",
            "• Vệ sinh: Khử trùng dụng cụ trước mỗi bữa ăn",
            "• Kiểm tra: Nhiệt độ thức ăn trước khi phục vụ cho trẻ"
        ]
        
        for i, note in enumerate(principles_notes, 1):
            ws4[f'A{principles_row + i}'] = note
            ws4[f'A{principles_row + i}'].font = Font(size=9, color="004000")
        
        # Chữ ký
        signature_row4 = principles_row + 8
        signature_data4 = [
            (signature_row4, 'D', "NHÂN VIÊN PHỤC VỤ", 'K', "HIỆU TRƯỞNG"),
            (signature_row4 + 1, 'D', "(Ký, ghi rõ họ tên)", 'K', "(Ký, ghi rõ họ tên)"),
            (signature_row4 + 5, 'D', "Nguyễn Thị Vân", 'K', "Nguyễn Thị Vân"),
            (signature_row4 + 6, 'D', f"Ngày {today.day}/{today.month}/{today.year}", 'K', f"Ngày {today.day}/{today.month}/{today.year}")
        ]
        
        for row, col_d, text_d, col_k, text_k in signature_data4:
            ws4[f'{col_d}{row}'] = text_d
            ws4[f'{col_k}{row}'] = text_k
            
            for col, text in [(col_d, text_d), (col_k, text_k)]:
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
        
        file4_buffer = BytesIO()
        wb4.save(file4_buffer)
        file4_buffer.seek(0)
        zipf.writestr(f"Bước 3 - Bảo quản và phục vụ thức ăn - Tuần {week_number}.xlsx", file4_buffer.read())
    
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
            unit=form.unit.data
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
    if session.get('role') not in ['admin', 'teacher']:
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
    
    # Khôi phục role check với caching để tăng tốc
    user_role = session.get('role')
    if user_role not in ['admin', 'teacher']:
        return jsonify({
            'success': False,
            'error': 'Không có quyền truy cập. Vui lòng đăng nhập với tài khoản admin hoặc giáo viên.'
        }), 403
    
    # Enhanced Rate Limiting với security utils
    user_ip = validate_ip_address(request.remote_addr)
    rate_allowed, wait_seconds = check_rate_limit(f"ai_menu_{user_ip}", AI_RATE_LIMIT_SECONDS)
    
    if not rate_allowed:
        log_security_event('RATE_LIMIT_EXCEEDED', f'User: {user_role}, Wait: {wait_seconds}s', user_ip)
        return jsonify({
            'success': False,
            'error': f'Vui lòng chờ {wait_seconds} giây trước khi tạo thực đơn tiếp theo.'
        }), 429
    
    # Clean up old rate limit entries periodically
    clean_rate_limit_storage()
    
    print(f"� [SECURITY] Menu suggestions API called by {user_role} from {user_ip}")
    
    try:
        # Input validation và sanitization  
        if not request.json:
            return jsonify({
                'success': False,
                'error': 'Dữ liệu request không hợp lệ'
            }), 400
            
        # Sanitize và validate inputs
        age_group = str(request.json.get('age_group', '2-3 tuổi')).strip()
        available_ingredients = str(request.json.get('available_ingredients', '')).strip()
        dietary_requirements = str(request.json.get('dietary_requirements', '')).strip()
        
        # Length limits để tránh abuse
        if len(available_ingredients) > 1000:
            return jsonify({
                'success': False,
                'error': 'Danh sách nguyên liệu quá dài (tối đa 1000 ký tự)'
            }), 400
            
        if len(dietary_requirements) > 500:
            return jsonify({
                'success': False,
                'error': 'Yêu cầu đặc biệt quá dài (tối đa 500 ký tự)'
            }), 400
        
        # Validate age group
        valid_age_groups = ['6-12 tháng', '1-2 tuổi', '2-3 tuổi', '3-4 tuổi', '4-5 tuổi', '1-5 tuổi']
        if age_group not in valid_age_groups:
            age_group = '2-3 tuổi'  # Default fallback
        
        count = 5  # Fixed count for consistency

        # Lấy danh sách món ăn hiện tại (chỉ active)
        from app.models import Dish
        dishes = Dish.query.filter_by(is_active=True).all()
        dish_names = [d.name for d in dishes]
        # Prompt AI CHUẨN: chỉ dùng đúng danh sách món, không tự tạo thêm ngoài
        prompt = (
            "# YÊU CẦU TẠO THỰC ĐƠN TUẦN\n"
            f"DANH SÁCH MÓN ĂN: {', '.join(dish_names)}\n"
            "- Chỉ sử dụng đúng các món trong danh sách trên để tạo thực đơn 1 tuần (36 bữa, 6 ngày, mỗi ngày 6 bữa).\n"
            "- TUYỆT ĐỐI KHÔNG được tự ý thêm, sáng tạo, hoặc đề xuất bất kỳ món ăn nào ngoài danh sách này.\n"
            "- Nếu không đủ món để xoay vòng, hãy lặp lại các món trong danh sách, nhưng không được thêm món mới.\n"
            "- Nếu có yêu cầu đặc biệt, tôi sẽ ghi rõ ở phần bên dưới.\n"
            "- Bữa Phụ sáng (snack) chiều thường sử dụng các món ăn nhẹ như sữa, sữa hạt ....\n"
            "- Bữa Tráng miệng (dessert) thường sử dụng các món ăn nhẹ như sữa, sữa hạt ....\n"
            "- Bữa Xế chiều (lateafternoon) thường sử dụng các món ăn nhẹ như sữa, sữa hạt ....\n"
            "- TUYỆT ĐỐI KHÔNG sử dụng món mặn, món chính cho bữa phụ sáng, tráng miệng, xế chiều \n"
            "\nYêu cầu đặc biệt: [Điền các món bạn muốn thêm hoặc lưu ý khác tại đây]\n"
            "\nTRẢ VỀ DUY NHẤT DỮ LIỆU JSON THEO ĐÚNG ĐỊNH DẠNG SAU (KHÔNG GIẢI THÍCH, KHÔNG THÊM TEXT NGOÀI JSON):\n"
            '{\n'
            '  "mon": {"morning": "...", "snack": "...", "dessert": "...", "lunch": "...", "afternoon": "...", "lateafternoon": "..."},\n'
            '  "tue": {...},\n'
            '  "wed": {...},\n'
            '  "thu": {...},\n'
            '  "fri": {...},\n'
            '  "sat": {...}\n'
            '}\n'
            "\nChỉ trả về JSON đúng format trên, không thêm bất kỳ text nào khác."
        )

        # 🚀 ALWAYS use single entry point for AI menu suggestion
        try:
            print(f"🚀 [MENU AI] Always using prompt CHUẨN truyền vào cho mọi provider!")
            print(f"[DEBUG] Prompt truyền vào Menu-AI:\n{prompt}")
            suggestions = get_ai_menu_suggestions(
                age_group=age_group,
                dietary_requirements=dietary_requirements,
                count=count,
                available_ingredients=available_ingredients,
                menu_prompt=prompt
            )
            print(f"[DEBUG] Raw AI suggestions: {repr(suggestions)}")
            # Nếu suggestions là string và có JSON object bên trong, cố gắng extract JSON
            if isinstance(suggestions, str):
                import re
                import json
                # Tìm JSON object đầu tiên trong string
                match = re.search(r'\{[\s\S]*\}', suggestions)
                if match:
                    json_str = match.group(0)
                    try:
                        suggestions_obj = json.loads(json_str)
                        print("[DEBUG] Extracted JSON object from AI string response.")
                        suggestions = suggestions_obj
                    except Exception as json_err:
                        print(f"[ERROR] Failed to parse extracted JSON: {json_err}")
            # Nếu suggestions là list, kiểm tra từng phần tử xem có JSON object không
            if isinstance(suggestions, list):
                import re
                import json
                for idx, s in enumerate(suggestions):
                    if isinstance(s, str):
                        match = re.search(r'\{[\s\S]*\}', s)
                        if match:
                            json_str = match.group(0)
                            try:
                                suggestions_obj = json.loads(json_str)
                                print(f"[DEBUG] Extracted JSON object from AI list response at index {idx}.")
                                suggestions = suggestions_obj
                                break
                            except Exception as json_err:
                                print(f"[ERROR] Failed to parse extracted JSON in list: {json_err}")
            # Nếu suggestions là list và có dòng provider, log provider
            if isinstance(suggestions, list):
                for s in suggestions:
                    if "Generated by:" in s:
                        print(f"[DEBUG] Provider trả về: {s}")
            print(f"✅ [MENU AI SUCCESS] Menu AI completed for {user_role}")
        except Exception as menu_ai_error:
            print(f"⚠️ [MENU AI ERROR] Menu AI failed: {menu_ai_error}")
            suggestions = [
                "❌ Không thể tạo menu từ AI",
                "🔄 Vui lòng kiểm tra kết nối mạng và thử lại",
                f"📝 Error: {str(menu_ai_error)[:100]}"
            ]
        # Log successful operation
        print(f"✅ [SUCCESS] Menu generated for {user_role} - Age: {age_group}, Ingredients: {len(available_ingredients)} chars")

        # Nếu AI trả về dict đúng format menu thì trả về luôn
        if isinstance(suggestions, dict) and all(day in suggestions for day in ['mon','tue','wed','thu','fri','sat']):
            return jsonify({
                'success': True,
                'menu': suggestions,
                'age_group': age_group,
                'security_info': f"Generated securely for {user_role}",
                'prompt': prompt,
                'dish_names': dish_names
            })
        # Nếu không phải dict, cố gắng convert về menu chuẩn
        # Nếu là list (suggestions text), dùng extract_weekly_menu_from_suggestions
        if isinstance(suggestions, list):
            menu_data = extract_weekly_menu_from_suggestions(suggestions)
            return jsonify({
                'success': True,
                'menu': menu_data,
                'age_group': age_group,
                'security_info': f"Generated securely for {user_role} (fallback from suggestions)",
                'prompt': prompt,
                'dish_names': dish_names
            })
        # Nếu là string, cũng convert sang list trước khi extract
        if isinstance(suggestions, str):
            menu_data = extract_weekly_menu_from_suggestions([suggestions])
            return jsonify({
                'success': True,
                'menu': menu_data,
                'age_group': age_group,
                'security_info': f"Generated securely for {user_role} (fallback from string)",
                'prompt': prompt,
                'dish_names': dish_names
            })
        # Nếu không convert được, trả về menu rỗng
        menu_data = extract_weekly_menu_from_suggestions([])
        return jsonify({
            'success': True,
            'menu': menu_data,
            'age_group': age_group,
            'security_info': f"Generated securely for {user_role} (empty fallback)",
            'prompt': prompt,
            'dish_names': dish_names
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Create Menu Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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


# ============== CURRICULUM AI Routes ==============

def convert_structured_to_frontend_format(ai_result, age_group, week_number, themes, special_focus):
    """
    Convert new structured curriculum format to frontend-compatible format
    Tạo output tương tự menu AI - list của strings dễ đọc
    """
    try:
        print(f"🔍 [DEBUG] Starting frontend format conversion")
        print(f"🔍 [DEBUG] AI result keys: {list(ai_result.keys()) if isinstance(ai_result, dict) else 'Not a dict'}")
        
        structured_data = ai_result.get('data', {})
        provider = ai_result.get('provider', 'unknown')
        
        print(f"🔍 [DEBUG] Structured data keys: {list(structured_data.keys()) if isinstance(structured_data, dict) else 'Not a dict'}")
        print(f"🔍 [DEBUG] Provider: {provider}")
        
        # Tạo list activities tương tự menu AI format
        curriculum_items = []
        
        # Header thông tin
        curriculum_items.extend([
            f"📚 **CHƯƠNG TRÌNH HỌC TUẦN {week_number}**",
            f"👶 **Độ tuổi:** {age_group}",
            f"🎯 **Chủ đề:** {themes if themes else 'Chủ đề phát triển toàn diện'}",
            f"⭐ **Trọng tâm:** {special_focus if special_focus else 'Phát triển đa dạng kỹ năng'}",
            ""
        ])
        
        # Day mapping
        day_names = {
            'mon': 'Thứ 2', 'tue': 'Thứ 3', 'wed': 'Thứ 4',
            'thu': 'Thứ 5', 'fri': 'Thứ 6'
        }
        
        # Time slot mapping với emoji
        time_slots = {
            'morning_1': '🌅 7h-8h: Đón trẻ & Ăn sáng',
            'morning_2': '🏃 8h-8h30: Thể dục & Trò chuyện',
            'morning_3': '🌳 8h30-9h: Hoạt động ngoài trời',
            'morning_4': '🇬🇧 9h-9h30: English & Bữa phụ',
            'morning_5': '📚 9h30-10h: Học tập chính',
            'morning_6': '🍚 10h30-14h: Ăn trưa & Nghỉ trưa',
            'afternoon_1': '🧩 14h15-15h: Lego/Giáo cụ',
            'afternoon_2': '🥤 15h-15h30: Uống nước & Ăn xế',
            'afternoon_3': '🧘 15h45-16h: Yoga/Hoạt động sáng tạo',
            'afternoon_4': '👋 16h-17h: Tự do & Đón trẻ'
        }
        
        # Process each day
        daily_activities = []  # Format for JavaScript compatibility
        
        for day_code in ['mon', 'tue', 'wed', 'thu', 'fri']:
            if day_code not in structured_data:
                continue
                
            day_name = day_names[day_code]
            day_data = structured_data[day_code]
            
            # Create activities array for this day
            activities = []
            
            # Add activities for each time slot
            for slot_code in ['morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6',
                             'afternoon_1', 'afternoon_2', 'afternoon_3', 'afternoon_4']:
                
                if slot_code in day_data and day_data[slot_code]:
                    activity_content = day_data[slot_code]
                    time_label = time_slots.get(slot_code, f'{slot_code}:').replace('🌅 ', '').replace('🏃 ', '').replace('🌳 ', '').replace('🇬🇧 ', '').replace('📚 ', '').replace('🍚 ', '').replace('🧩 ', '').replace('🥤 ', '').replace('🧘 ', '').replace('👋 ', '')
                    
                    activities.append({
                        'time': time_label,
                        'activity': activity_content[:50] + ('...' if len(activity_content) > 50 else ''),
                        'description': activity_content
                    })
            
            # Special formatting for Wednesday (Thứ 4 vui vẻ)
            if day_code == 'wed':
                day_display_name = f"{day_name} - THỨ 4 VUI VẺ"
            else:
                day_display_name = day_name
                
            daily_activities.append({
                'day': day_display_name,
                'activities': activities
            })
        
        # Return format compatible with frontend JavaScript
        return {
            'week_number': week_number,
            'age_group': age_group,
            'themes': themes or 'Chủ đề phát triển toàn diện',
            'special_focus': special_focus or 'Phát triển đa dạng kỹ năng',
            'daily_activities': daily_activities,  # JavaScript-compatible format
            'materials': [
                'Đồ chơi giáo dục phù hợp độ tuổi',
                'Sách tranh và flashcard chủ đề',
                'Vật liệu tô vẽ và sáng tạo',
                'Đồ chơi Lego và giáo cụ',
                'Thảm yoga và nhạc cụ'
            ],
            'provider': provider,
            'structured_data': structured_data,  # Keep for create curriculum endpoint
            'curriculum': structured_data  # For database storage
        }
        
    except Exception as e:
        print(f"❌ [DEBUG] Error converting structured format: {e}")
        print(f"❌ [DEBUG] Error type: {type(e)}")
        print(f"❌ [DEBUG] AI result received: {ai_result}")
        return {
            'week_number': week_number,
            'age_group': age_group,
            'themes': themes or 'Lỗi xử lý dữ liệu',
            'special_focus': special_focus or 'Lỗi xử lý dữ liệu',
            'daily_activities': [],
            'materials': [],
            'provider': 'error',
            'error': str(e)
        }







@main.route('/debug-curriculum')
def debug_curriculum():
    """Debug curriculum AI import"""
    try:
        # Step 1: Test import
        print("🔍 [DEBUG] Step 1: Testing import...")
        from app.curriculum_ai import curriculum_ai_service
        print("✅ [DEBUG] Import successful")
        
        # Step 2: Test service object
        print("🔍 [DEBUG] Step 2: Testing service object...")
        service_type = type(curriculum_ai_service).__name__
        print(f"✅ [DEBUG] Service type: {service_type}")
        
        return f"""
        <h2>🔍 Curriculum AI Debug</h2>
        <p>✅ Import thành công</p>
        <p>✅ Service type: {service_type}</p>
        <p><a href='/test-curriculum-ai'>Test chức năng AI</a></p>
        <p><a href='/login'>Đăng nhập để test full</a></p>
        """
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ [DEBUG ERROR] {str(e)}")
        print(f"📋 [TRACEBACK] {error_detail}")
        
        return f"""
        <h2>❌ Curriculum AI Debug Error</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Type:</strong> {type(e).__name__}</p>
        <pre>{error_detail}</pre>
        """

@main.route('/test-curriculum-ai')
def test_curriculum_ai():
    """Test curriculum AI service trực tiếp"""
    try:
        # Import curriculum AI service
        from app.curriculum_ai import curriculum_ai_service
        
        print("🧪 [TEST] Testing curriculum AI service...")
        
        # Test với parameters đơn giản
        result = curriculum_ai_service.generate_weekly_curriculum(
            age_group="2-3 tuổi",
            week_number=1,
            themes="Động vật",
            special_focus="Phát triển ngôn ngữ"
        )
        
        return jsonify({
            'success': True,
            'message': 'Curriculum AI service hoạt động bình thường',
            'result_keys': list(result.keys()) if result else None
        })
        
    except Exception as e:
        print(f"❌ [TEST ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@main.route('/create-test-teacher')
def create_test_teacher():
    """Tạo tài khoản giáo viên test"""
    
    # Kiểm tra xem đã có giáo viên test chưa
    existing = Staff.query.filter_by(email='gv1@gmail.com').first()
    if existing:
        return f"Tài khoản gv1@gmail.com đã tồn tại! ID: {existing.id}, Position: {existing.position}"
    
    # Tạo giáo viên mới
    teacher = Staff(
        name='Giáo viên Test',
        position='teacher',
        contact_info='gv1@gmail.com',
        email='gv1@gmail.com',
        phone='0123456789',
        password=generate_password_hash('123456')
    )
    
    db.session.add(teacher)
    db.session.commit()
    
    return f"✅ Đã tạo tài khoản giáo viên test:<br>Email: gv1@gmail.com<br>Password: 123456<br>ID: {teacher.id}<br><a href='/login'>Đăng nhập ngay</a>"


import random

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
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    students = Child.query.all()
    albums = StudentAlbum.query.join(Child).order_by(StudentAlbum.date_created.desc()).all()
    
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