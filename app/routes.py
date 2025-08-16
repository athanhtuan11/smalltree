from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, jsonify, current_app
from app.models import db, Activity, Curriculum, Child, AttendanceRecord, Staff, BmiRecord, ActivityImage, Supplier, Product
from app.forms import EditProfileForm, ActivityCreateForm, ActivityEditForm, SupplierForm, ProductForm
from app.menu_ai import get_ai_menu_suggestions
from calendar import monthrange
from datetime import datetime, date, timedelta
import io, zipfile, os, json, re, secrets
from werkzeug.security import generate_password_hash, check_password_hash
from docx import Document
from docx.shared import Pt

# Enhanced AI imports - Multi-AI support
try:
    from app.enhanced_menu_ai import get_ai_menu_suggestions_enhanced
    ENHANCED_MENU_AI_AVAILABLE = True
    print("✅ Enhanced Menu AI imported successfully")
except ImportError as e:
    ENHANCED_MENU_AI_AVAILABLE = False
    print(f"⚠️ Enhanced Menu AI not available: {e}")

try:
    from app.enhanced_curriculum_ai import get_ai_curriculum_suggestions_enhanced  
    ENHANCED_CURRICULUM_AI_AVAILABLE = True
    print("✅ Enhanced Curriculum AI imported successfully")
except ImportError as e:
    ENHANCED_CURRICULUM_AI_AVAILABLE = False
    print(f"⚠️ Enhanced Curriculum AI not available: {e}")

# Enhanced Security imports
from .security_utils import (
    sanitize_input, validate_age_group, validate_menu_count, 
    validate_ip_address, is_sql_injection_attempt, 
    log_security_event, check_rate_limit, clean_rate_limit_storage
)

# Rate limiting cho AI endpoints - Security enhancement
ai_request_timestamps = {}
AI_RATE_LIMIT_SECONDS = 10  # Chỉ cho phép 1 request AI mỗi 10 giây/user
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from PIL import Image

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
        morning_slots = ['morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
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
                            from docx.shared import Inches
                            run_logo.add_picture(logo_path, width=Inches(1.2))
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
        morning_slots = ['morning_1', 'morning_2', 'morning_3', 'morning_4', 'morning_5', 'morning_6']
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
            from werkzeug.security import generate_password_hash
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
        from werkzeug.security import generate_password_hash
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
            from werkzeug.security import generate_password_hash
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
            data = json.loads(week.content)
        except Exception:
            data = {}
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
    """Xuất quy trình an toàn thực phẩm 3 bước theo template có sẵn với dữ liệu thực đơn."""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    # Lấy thực đơn của tuần
    week = Curriculum.query.filter_by(week_number=week_number).first()
    if not week:
        flash('Không tìm thấy thực đơn!', 'danger')
        return redirect(url_for('main.menu'))
    
    import json
    from openpyxl import Workbook
    from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
    from io import BytesIO
    import zipfile
    from datetime import datetime, timedelta
    
    menu_data = json.loads(week.content)
    
    # Tạo danh sách món ăn và nguyên liệu từ thực đơn
    dishes = []
    fresh_ingredients = []
    dry_ingredients = []
    
    for day_data in menu_data.values():
        for meal in day_data.values():
            if meal:
                dish_list = [dish.strip() for dish in meal.split(',') if dish.strip()]
                dishes.extend(dish_list)
                
                # Phân loại nguyên liệu (dựa trên tên món)
                for dish in dish_list:
                    if any(x in dish.lower() for x in ['rau', 'cà', 'thịt', 'cá', 'tôm', 'trứng']):
                        fresh_ingredients.append(dish)
                    elif any(x in dish.lower() for x in ['gạo', 'bún', 'bánh', 'sữa', 'đường']):
                        dry_ingredients.append(dish)
    
    # Loại bỏ trùng lặp
    dishes = list(set(dishes))
    fresh_ingredients = list(set(fresh_ingredients))
    dry_ingredients = list(set(dry_ingredients))
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        
        # BƯỚC 1.1: Tiếp nhận thực phẩm tươi - Theo đúng template gốc
        wb1 = Workbook()
        ws1 = wb1.active
        ws1.title = "Kiểm tra thực phẩm tươi"
        
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        # Định dạng border
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Dòng 1: Header chính
        ws1['A1'] = "Tên cơ sở:"
        ws1['F1'] = "KIỂM TRA TRƯỚC KHI CHẾ BIẾN THỨC ĂN"
        ws1['N1'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws1.merge_cells('F1:L1')
        ws1['F1'].alignment = Alignment(horizontal='center', vertical='center')
        ws1['F1'].font = Font(bold=True, size=12)
        
        # Dòng 2
        ws1['A2'] = "Người kiểm tra:"
        ws1['N2'] = "Mẫu số 1"
        
        # Dòng 3  
        ws1['A3'] = f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')}"
        
        # Dòng 4
        ws1['A4'] = "Địa điểm kiểm tra: LỚP MNDL NGÔI SAO NHỎ"
        
        # Dòng 6
        ws1['A6'] = "I. Thực phẩm tươi sống, đông lạnh: thịt, cá, rau, củ, quả..."
        ws1['N6'] = "Bước 1.1"
        ws1['A6'].font = Font(bold=True)
        
        # Header bảng chính - dòng 7
        headers_row1 = ['STT', 'Tên thực phẩm', '', 'Thời gian nhập\n(ngày, giờ)', 'Khối lượng\n(kg/lít)', 'Nơi cung cấp', '', 'Số chứng từ/\nSố hóa đơn', 'Giấy đăng ký\nvới thú y', 'Giấy kiểm dịch', 'Kiểm tra cảm quan\n(màu, mùi vị, trạng thái, bảo quản...)', '', 'Xét nghiệm nhanh (nếu có)\n(vi sinh, hóa lý)', '', 'Biện pháp xử lý/\nGhi chú']
        for i, header in enumerate(headers_row1, 1):
            cell = ws1.cell(row=7, column=i, value=header)
            cell.font = Font(bold=True, size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            cell.border = thin_border
        
        # Merge các cell cần thiết cho header
        ws1.merge_cells('B7:C7')  # Tên thực phẩm
        ws1.merge_cells('F7:G7')  # Nơi cung cấp
        ws1.merge_cells('K7:L7')  # Kiểm tra cảm quan
        ws1.merge_cells('M7:N7')  # Xét nghiệm nhanh
        
        # Sub-headers - dòng 8
        sub_headers = ['', '', '', '', '', 'Tên cơ sở', 'Địa chỉ, điện thoại', 'Tên người giao hàng', '', '', 'Đạt', 'Không đạt', 'Đạt', 'Không đạt', '']
        for i, header in enumerate(sub_headers, 1):
            cell = ws1.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="E6F3E6", end_color="E6F3E6", fill_type="solid")
            cell.border = thin_border
        
        # Số thứ tự cột - dòng 9
        for i in range(1, 16):
            cell = ws1.cell(row=9, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu thực phẩm tươi
        for i, ingredient in enumerate(fresh_ingredients[:20], 1):
            row_num = 9 + i
            data_row = [
                i,  # STT
                ingredient,  # Tên thực phẩm
                '',  # Merge với B
                f"{week_start.strftime('%d/%m/%Y')}, 05h:30",  # Thời gian nhập
                '',  # Khối lượng - để trống
                'Thực phẩm tươi sống',  # Tên cơ sở
                '',  # Địa chỉ - để trống
                '',  # Tên người giao hàng
                '',  # Số chứng từ
                '',  # Giấy đăng ký
                'X',  # Đạt cảm quan
                '',  # Không đạt cảm quan
                '',  # Đạt xét nghiệm
                '',  # Không đạt xét nghiệm
                ''   # Ghi chú
            ]
            
            for j, value in enumerate(data_row, 1):
                cell = ws1.cell(row=row_num, column=j, value=value)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
                if j == 1:  # STT
                    cell.font = Font(bold=True)
                if j == 11 and value == 'X':  # Đánh dấu X
                    cell.font = Font(bold=True, color="00AA00")
            
            # Merge cell cho tên thực phẩm
            ws1.merge_cells(f'B{row_num}:C{row_num}')
        
        # Thiết lập độ rộng cột
        column_widths = [5, 15, 5, 12, 10, 15, 15, 12, 10, 10, 8, 8, 8, 8, 12]
        for i, width in enumerate(column_widths, 1):
            ws1.column_dimensions[chr(64 + i)].width = width
        
        # Thiết lập chiều cao dòng
        ws1.row_dimensions[7].height = 40
        ws1.row_dimensions[8].height = 25
        
        # Chữ ký - dòng cuối
        signature_row = 32
        ws1.cell(row=signature_row, column=5, value="Bếp trưởng")
        ws1.cell(row=signature_row, column=11, value="Chủ trường")
        ws1.cell(row=signature_row+1, column=5, value="(Ký, ghi họ tên)")
        ws1.cell(row=signature_row+1, column=11, value="(Ký, ghi họ tên)")
        ws1.cell(row=signature_row+4, column=5, value="Nguyễn Thị Minh Tâm")
        ws1.cell(row=signature_row+4, column=11, value="Nguyễn Thị Minh Tâm")
        
        # Định dạng chữ ký
        for row in [signature_row, signature_row+1, signature_row+4]:
            for col in [5, 11]:
                cell = ws1.cell(row=row, column=col)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if row == signature_row:
                    cell.font = Font(bold=True)
        
        file1_buffer = BytesIO()
        wb1.save(file1_buffer)
        file1_buffer.seek(0)
        zipf.writestr(f"Bước 1.1 - Tiếp nhận thực phẩm tươi - Tuần {week_number}.xlsx", file1_buffer.read())
        
        # BƯỚC 1.2: Tiếp nhận thực phẩm khô - Theo đúng template gốc với format đẹp
        wb2 = Workbook()
        ws2 = wb2.active
        ws2.title = "Kiểm tra thực phẩm khô"
        
        # Dòng 1: Header chính
        ws2['A1'] = "Tên cơ sở:"
        ws2['E1'] = "KIỂM TRA TRƯỚC KHI CHẾ BIẾN THỨC ĂN"
        ws2['N1'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws2.merge_cells('E1:L1')
        ws2['E1'].alignment = Alignment(horizontal='center', vertical='center')
        ws2['E1'].font = Font(bold=True, size=12)
        
        # Dòng 2
        ws2['A2'] = "Người kiểm tra:"
        ws2['N2'] = "Mẫu số 1"
        
        # Dòng 3  
        ws2['A3'] = f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')}"
        
        # Dòng 4
        ws2['A4'] = "Địa điểm kiểm tra: LỚP MNDL NGÔI SAO NHỎ"
        
        # Dòng 6
        ws2['A6'] = "II. Thực phẩm khô và thực phẩm bao gói sẵn, phụ gia thực phẩm"
        ws2['N6'] = "Bước 1.2"
        ws2['A6'].font = Font(bold=True)
        
        # Header bảng chính - dòng 7
        headers2_row1 = ['STT', 'Tên thực phẩm', '', 'Tên cơ sở\nsản xuất', 'Địa chỉ\nsản xuất', 'Thời gian nhập\n(ngày, giờ)', 'Khối lượng\n(kg/lít)', 'Nơi cung cấp', '', '', 'Hạn sử dụng', 'Điều kiện bảo quản\n(T° thường/ lạnh...)', 'Chứng từ,\nhóa đơn', 'Kiểm tra cảm quan\n(nhãn, bao bì, bảo quản, hạn sử dụng...)', '', 'Biện pháp xử lý/\nGhi chú']
        for i, header in enumerate(headers2_row1, 1):
            cell = ws2.cell(row=7, column=i, value=header)
            cell.font = Font(bold=True, size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            cell.border = thin_border
        
        # Merge các cell cần thiết cho header
        ws2.merge_cells('B7:C7')  # Tên thực phẩm
        ws2.merge_cells('H7:J7')  # Nơi cung cấp
        ws2.merge_cells('N7:O7')  # Kiểm tra cảm quan
        
        # Sub-headers - dòng 8
        sub_headers2 = ['', '', '', '', '', '', '', 'Tên cơ sở', 'Tên chủ giao hàng', 'Địa chỉ,\nđiện thoại', '', '', '', 'Đạt', 'Không đạt', '']
        for i, header in enumerate(sub_headers2, 1):
            cell = ws2.cell(row=8, column=i, value=header)
            cell.font = Font(bold=True, size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="E6F3E6", end_color="E6F3E6", fill_type="solid")
            cell.border = thin_border
        
        # Số thứ tự cột - dòng 9
        for i in range(1, 17):
            cell = ws2.cell(row=9, column=i, value=i)
            cell.font = Font(bold=True, size=8)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
            cell.border = thin_border
        
        # Điền dữ liệu thực phẩm khô
        for i, ingredient in enumerate(dry_ingredients[:20], 1):
            row_num = 9 + i
            data_row = [
                i,  # STT
                ingredient,  # Tên thực phẩm
                '',  # Merge với B
                '',  # Tên cơ sở sản xuất - để trống
                'Ba Đình2, thị trấn Nam Ban, Lâm Hà, Lâm Đồng',  # Địa chỉ sản xuất
                f"{week_start.strftime('%d/%m/%Y')}, 07:00",  # Thời gian nhập
                '',  # Khối lượng - để trống
                'Tạp hoá Tám Loan',  # Tên cơ sở cung cấp
                'Nguyễn Khắc Tám',  # Tên chủ giao hàng
                'Ba Đình2, thị trấn Nam Ban, Lâm Hà, Lâm Đồng',  # Địa chỉ
                'Đảm bảo',  # Hạn sử dụng
                'Kho lương thực',  # Điều kiện bảo quản
                '',  # Chứng từ - để trống
                '',  # Đạt - để trống cho người dùng tick
                '',  # Không đạt - để trống
                ''   # Ghi chú
            ]
            
            for j, value in enumerate(data_row, 1):
                cell = ws2.cell(row=row_num, column=j, value=value)
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = thin_border
                if j == 1:  # STT
                    cell.font = Font(bold=True)
            
            # Merge cell cho tên thực phẩm
            ws2.merge_cells(f'B{row_num}:C{row_num}')
        
        # Thiết lập độ rộng cột
        column_widths2 = [5, 12, 5, 12, 15, 12, 10, 12, 12, 15, 10, 12, 8, 8, 8, 12]
        for i, width in enumerate(column_widths2, 1):
            ws2.column_dimensions[chr(64 + i)].width = width
        
        # Thiết lập chiều cao dòng
        ws2.row_dimensions[7].height = 40
        ws2.row_dimensions[8].height = 25
        
        # Chữ ký - dòng cuối
        signature_row2 = 32
        ws2.cell(row=signature_row2, column=5, value="Bếp trưởng")
        ws2.cell(row=signature_row2, column=11, value="Chủ trường")
        ws2.cell(row=signature_row2+1, column=5, value="(Ký, ghi họ tên)")
        ws2.cell(row=signature_row2+1, column=11, value="(Ký, ghi họ tên)")
        ws2.cell(row=signature_row2+4, column=5, value="Nguyễn Thị Minh Tâm")
        ws2.cell(row=signature_row2+4, column=11, value="Nguyễn Thị Minh Tâm")
        
        # Định dạng chữ ký
        for row in [signature_row2, signature_row2+1, signature_row2+4]:
            for col in [5, 11]:
                cell = ws2.cell(row=row, column=col)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if row == signature_row2:
                    cell.font = Font(bold=True)
        
        file2_buffer = BytesIO()
        wb2.save(file2_buffer)
        file2_buffer.seek(0)
        zipf.writestr(f"Bước 1.2 - Tiếp nhận thực phẩm khô - Tuần {week_number}.xlsx", file2_buffer.read())
        
        # BƯỚC 2.1: Kiểm tra khi chế biến thức ăn - Theo đúng template gốc
        wb3 = Workbook()
        ws3 = wb3.active
        ws3.title = "Kiểm tra chế biến"
        
        # Dòng 1: Header chính
        ws3['A1'] = "Tên cơ sở:"
        ws3['D1'] = "KIỂM TRA KHI CHẾ BIẾN THỨC ĂN"
        ws3['K1'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws3.merge_cells('D1:I1')
        
        # Dòng 2
        ws3['A2'] = "Người kiểm tra:"
        ws3['K2'] = "Mẫu số 2"
        
        # Dòng 3  
        ws3['A3'] = f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')}"
        
        # Dòng 4
        ws3['A4'] = "Địa điểm kiểm tra: LỚP MNDL NGÔI SAO NHỎ"
        
        # Dòng 5
        ws3['K5'] = "Bước 2"
        
        # Header bảng chính - dòng 6
        headers3_row1 = ['TT', 'Ca/bữa ăn (Bữa ăn, giờ ăn...)', 'Tên món ăn', 'Nguyên liệu chính để chế biến (tên, số lượng...)', 'Số lượng/ số suất ăn', 'Thời gian sơ chế xong (ngày, giờ)', 'Thời gian chế biến xong (ngày, giờ)', 'Kiểm tra điều kiện vệ sinh (từ thời điểm bắt đầu sơ chế, chế biến cho đến khi thức ăn được chế biến xong)', '', '', 'Kiểm tra cảm quan thức ăn (màu, mùi, vị, trạng thái, bảo quản...)', '', 'Biện pháp xử lý /Ghi chú']
        for i, header in enumerate(headers3_row1, 1):
            ws3.cell(row=6, column=i, value=header)
            ws3.cell(row=6, column=i).font = Font(bold=True)
        
        # Sub-headers - dòng 7
        ws3.cell(row=7, column=8, value="Người tham gia chế biến")
        ws3.cell(row=7, column=9, value="Trang thiết bị dụng cụ") 
        ws3.cell(row=7, column=10, value="Khu vực chế biến và phụ trợ")
        ws3.cell(row=7, column=11, value="Đạt")
        ws3.cell(row=7, column=12, value="Không đạt")
        
        # Số thứ tự cột - dòng 8
        for i in range(1, 14):
            ws3.cell(row=8, column=i, value=i)
            ws3.cell(row=8, column=i).font = Font(bold=True)
        
        # Điền dữ liệu món ăn theo ca
        row_num = 9
        meal_times = {
            'morning': ('Sáng', '6:00', '6:30'),
            'lunch': ('Canh trưa', '9:20', '9:50'), 
            'snack': ('Mặn trưa', '10:20', '10:50'),
            'afternoon': ('Xế', '1:30', '2:00'),
            'lateafternoon': ('Chiều', '3:30', '4:00'),
            'dessert': ('Tráng miệng', '11:30', '12:00')
        }
        
        stt = 1
        # Duyệt qua từng ngày trong tuần
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        for day_key in days:
            if day_key in menu_data:
                for meal_key, (ca_name, start_time, end_time) in meal_times.items():
                    if menu_data[day_key].get(meal_key):
                        dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                        for dish in dishes:
                            ws3.cell(row=row_num, column=1, value=stt)  # TT
                            ws3.cell(row=row_num, column=2, value=ca_name)  # Ca/bữa ăn
                            ws3.cell(row=row_num, column=3, value=dish)  # Tên món ăn
                            ws3.cell(row=row_num, column=4, value="")  # Nguyên liệu - để trống cho người dùng điền
                            ws3.cell(row=row_num, column=5, value="15")  # Số suất ăn
                            ws3.cell(row=row_num, column=6, value=start_time)  # Thời gian sơ chế
                            ws3.cell(row=row_num, column=7, value=end_time)  # Thời gian chế biến xong
                            ws3.cell(row=row_num, column=8, value="Gọn gàng, sạch sẽ")  # Người tham gia
                            ws3.cell(row=row_num, column=9, value="Đầy đủ, hợp vệ sinh")  # Trang thiết bị
                            ws3.cell(row=row_num, column=10, value="Đảm bảo vệ sinh")  # Khu vực chế biến
                            ws3.cell(row=row_num, column=11, value="X")  # Đạt
                            ws3.cell(row=row_num, column=12, value="")  # Không đạt
                            ws3.cell(row=row_num, column=13, value="")  # Ghi chú
                            
                            row_num += 1
                            stt += 1
                            
                            if row_num > 30:  # Giới hạn số dòng
                                break
                    if row_num > 30:
                        break
                if row_num > 30:
                    break
        
        # Chữ ký - dòng cuối
        signature_row3 = max(row_num + 2, 32)
        ws3.cell(row=signature_row3, column=4, value="Bếp trưởng")
        ws3.cell(row=signature_row3, column=10, value="Chủ trường")
        ws3.cell(row=signature_row3+1, column=4, value="(Ký, ghi họ tên)")
        ws3.cell(row=signature_row3+1, column=10, value="(Ký, ghi họ tên)")
        ws3.cell(row=signature_row3+4, column=4, value="Nguyễn Thị Minh Tâm")
        ws3.cell(row=signature_row3+4, column=10, value="Nguyễn Thị Minh Tâm")
        
        file3_buffer = BytesIO()
        wb3.save(file3_buffer)
        file3_buffer.seek(0)
        zipf.writestr(f"Bước 2.1 - Kiểm tra khi chế biến - Tuần {week_number}.xlsx", file3_buffer.read())
        
        # BƯỚC 2.2: Kiểm tra trước khi ăn - Theo đúng template gốc
        wb4 = Workbook()
        ws4 = wb4.active
        ws4.title = "Kiểm tra trước khi ăn"
        
        # Dòng 1: Header chính
        ws4['A1'] = "Tên cơ sở:"
        ws4['B1'] = "LỚP MNDL NGÔI SAO NHỎ"
        ws4['D1'] = "KIỂM TRA TRƯỚC KHI ĂN"
        ws4['I1'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws4.merge_cells('D1:H1')
        
        # Dòng 2
        ws4['A2'] = "Người kiểm tra:"
        ws4['B2'] = "Nguyễn Thị Minh Tâm"
        ws4['I2'] = "Mẫu số 3"
        
        # Dòng 3  
        ws4['A3'] = f"Thời gian kiểm tra: {week_start.strftime('%d/%m/%Y')}"
        
        # Dòng 4
        ws4['A4'] = "Địa điểm kiểm tra: LỚP MNDL NGÔI SAO NHỎ"
        
        # Dòng 5
        ws4['I5'] = "Bước 3"
        
        # Header bảng chính - dòng 6
        headers4_row1 = ['TT', 'Ca/bữa ăn (Bữa ăn, giờ ăn...)', 'Tên món ăn', 'Số lượng suất ăn', 'Thời gian chia món ăn xong (ngày, giờ)', 'Thời gian bắt đầu ăn (ngày, giờ)', 'Dụng cụ chia, chứa đựng, che đậy, bảo quản thức ăn', 'Kiểm tra cảm quan món ăn (màu, mùi, vị, trạng thái, bảo quản...)', '', 'Biện pháp xử lý /Ghi chú']
        for i, header in enumerate(headers4_row1, 1):
            ws4.cell(row=6, column=i, value=header)
            ws4.cell(row=6, column=i).font = Font(bold=True)
        
        # Sub-headers - dòng 7
        ws4.cell(row=7, column=8, value="Đạt")
        ws4.cell(row=7, column=9, value="Không đạt")
        
        # Số thứ tự cột - dòng 8
        for i in range(1, 11):
            ws4.cell(row=8, column=i, value=i)
            ws4.cell(row=8, column=i).font = Font(bold=True)
        
        # Điền dữ liệu món ăn theo ca
        row_num = 9
        meal_times_4 = {
            'morning': ('Sáng', '6:30', '6:45'),
            'lunch': ('Canh trưa', '10:00', '10:15'), 
            'snack': ('Mặn trưa', '10:00', '10:15'),
            'afternoon': ('Xế', '2:10', '2:30'),
            'lateafternoon': ('Chiều', '3:30', '3:45'),
            'dessert': ('Tráng miệng', '11:30', '11:45')
        }
        
        stt = 1
        # Duyệt qua từng ngày trong tuần
        for day_key in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']:
            if day_key in menu_data:
                for meal_key, (ca_name, chia_time, eat_time) in meal_times_4.items():
                    if menu_data[day_key].get(meal_key):
                        dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                        for dish in dishes:
                            ws4.cell(row=row_num, column=1, value=stt)  # TT
                            ws4.cell(row=row_num, column=2, value=ca_name)  # Ca/bữa ăn
                            ws4.cell(row=row_num, column=3, value=dish)  # Tên món ăn
                            ws4.cell(row=row_num, column=4, value="15")  # Số suất ăn
                            ws4.cell(row=row_num, column=5, value=chia_time)  # Thời gian chia món
                            ws4.cell(row=row_num, column=6, value=eat_time)  # Thời gian bắt đầu ăn
                            ws4.cell(row=row_num, column=7, value="Inox")  # Dụng cụ
                            ws4.cell(row=row_num, column=8, value="X")  # Đạt
                            ws4.cell(row=row_num, column=9, value="")  # Không đạt
                            ws4.cell(row=row_num, column=10, value="")  # Ghi chú
                            
                            row_num += 1
                            stt += 1
                            
                            if row_num > 30:  # Giới hạn số dòng
                                break
                    if row_num > 30:
                        break
                if row_num > 30:
                    break
        
        # Chữ ký - dòng cuối
        signature_row4 = max(row_num + 2, 32)
        ws4.cell(row=signature_row4, column=3, value="Bếp trưởng")
        ws4.cell(row=signature_row4, column=8, value="Phó hiệu trưởng")
        ws4.cell(row=signature_row4+1, column=3, value="(Ký, ghi họ tên)")
        ws4.cell(row=signature_row4+1, column=8, value="(Ký, ghi họ tên)")
        ws4.cell(row=signature_row4+4, column=3, value="Nguyễn Thị Minh Tâm")
        ws4.cell(row=signature_row4+4, column=8, value="Nguyễn Thị Minh Tâm")
        
        file4_buffer = BytesIO()
        wb4.save(file4_buffer)
        file4_buffer.seek(0)
        zipf.writestr(f"Bước 2.2 - Kiểm tra trước khi ăn - Tuần {week_number}.xlsx", file4_buffer.read())
        
        # BƯỚC 3: Lưu hủy mẫu thực phẩm - Theo đúng template gốc
        wb5 = Workbook()
        ws5 = wb5.active
        ws5.title = "Lưu hủy mẫu thực phẩm"
        
        # Dòng 1: Header chính
        ws5['E1'] = "MẪU BIỂU THEO DÕI LƯU VÀ HỦY MẪU THỨC ĂN LƯU"
        ws5['L1'] = "Số: 1246/QĐ - Bộ Y Tế"
        ws5.merge_cells('E1:K1')
        
        # Dòng 2
        ws5['A2'] = "Tên cơ sở:"
        ws5['C2'] = "LỚP MNDL NGÔI SAO NHỎ"
        ws5['L2'] = "Mẫu 5"
        
        # Dòng 3
        ws5['A3'] = "Người kiểm tra:"
        
        # Dòng 4
        ws5['A4'] = f"Ngày in: {week_start.strftime('%d/%m/%Y')}"
        
        # Dòng 5
        ws5['A5'] = "Địa điểm kiểm tra:"
        ws5['D5'] = "LỚP MNDL NGÔI SAO NHỎ"
        ws5['H5'] = "Ngày tiếp phẩm:"
        ws5['J5'] = f"{week_start.strftime('%d/%m/%Y')}"
        
        # Dòng 6
        ws5['L6'] = "Bước 3"
        
        # Header bảng chính - dòng 7
        headers5_row1 = ['TT', 'Tên mẫu thức ăn', '', '', 'Bữa ăn (giờ ăn...)', 'Số lượng suất ăn', 'Khối lượng/ thể tích mẫu (gam/ml)', 'Dụng cụ chứa mẫu thức ăn lưu', 'Nhiệt độ bảo quản mẫu (°C)', 'Thời gian lấy mẫu (giờ, ngày, tháng, năm)', 'Thời gian hủy mẫu (giờ, ngày, tháng, năm)', 'Ghi chú (chất lượng mẫu thức ăn lưu...)', 'Người lưu mẫu (ký và ghi rõ họ tên)', 'Người hủy mẫu (ký và ghi rõ họ tên)']
        for i, header in enumerate(headers5_row1, 1):
            ws5.cell(row=7, column=i, value=header)
            ws5.cell(row=7, column=i).font = Font(bold=True)
        
        # Số thứ tự cột - dòng 8
        for i in range(1, 15):
            ws5.cell(row=8, column=i, value=i)
            ws5.cell(row=8, column=i).font = Font(bold=True)
        
        # Điền dữ liệu lưu hủy mẫu
        row_num = 9
        meal_times_5 = {
            'morning': 'Sáng',
            'lunch': 'Canh trưa', 
            'snack': 'Mặn trưa',
            'afternoon': 'Xế',
            'lateafternoon': 'Chiều',
            'dessert': 'Tráng miệng'
        }
        
        stt = 1
        # Duyệt qua từng ngày trong tuần
        for day_key in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']:
            if day_key in menu_data:
                # Chỉ lưu mẫu các bữa chính
                for meal_key in ['morning', 'lunch', 'snack', 'afternoon']:
                    if menu_data[day_key].get(meal_key):
                        dishes = [d.strip() for d in menu_data[day_key][meal_key].split(',') if d.strip()]
                        for dish in dishes:
                            ws5.cell(row=row_num, column=1, value=stt)  # TT
                            ws5.cell(row=row_num, column=2, value=dish)  # Tên mẫu thức ăn
                            ws5.cell(row=row_num, column=5, value=meal_times_5[meal_key])  # Bữa ăn
                            ws5.cell(row=row_num, column=6, value="15")  # Số lượng suất ăn
                            ws5.cell(row=row_num, column=7, value="100")  # Khối lượng mẫu
                            ws5.cell(row=row_num, column=8, value="Hộp Thuỷ Tinh")  # Dụng cụ chứa
                            ws5.cell(row=row_num, column=9, value="4")  # Nhiệt độ bảo quản
                            ws5.cell(row=row_num, column=10, value=f"{week_start.strftime('%d/%m/%Y')}, 06:30")  # Thời gian lấy mẫu
                            ws5.cell(row=row_num, column=11, value=f"{week_start.strftime('%d/%m/%Y')}, 06:30")  # Thời gian hủy mẫu
                            ws5.cell(row=row_num, column=12, value="Đảm bảo")  # Ghi chú
                            ws5.cell(row=row_num, column=13, value="Nguyễn Thị Minh Tâm")  # Người lưu mẫu
                            ws5.cell(row=row_num, column=14, value="Nguyễn Thị Minh Tâm")  # Người hủy mẫu
                            
                            row_num += 1
                            stt += 1
                            
                            if row_num > 30:  # Giới hạn số dòng
                                break
                    if row_num > 30:
                        break
                if row_num > 30:
                    break
        
        # Chữ ký - dòng cuối
        signature_row5 = max(row_num + 3, 35)
        ws5.cell(row=signature_row5, column=2, value="Người quản lý cơ sở")
        ws5.cell(row=signature_row5, column=6, value="Người thực hiện lưu mẫu")
        ws5.cell(row=signature_row5, column=12, value="Người thực hiện huỷ mẫu")
        ws5.cell(row=signature_row5+1, column=2, value="(Ký, ghi họ tên)")
        ws5.cell(row=signature_row5+1, column=6, value="(Ký, ghi họ tên)")
        ws5.cell(row=signature_row5+1, column=12, value="(Ký, ghi họ tên)")
        ws5.cell(row=signature_row5+4, column=1, value="Nguyễn Thị Minh Tâm")
        ws5.cell(row=signature_row5+4, column=6, value="Nguyễn Thị Minh Tâm")
        ws5.cell(row=signature_row5+4, column=12, value="Nguyễn Thị Minh Tâm")
        
        file5_buffer = BytesIO()
        wb5.save(file5_buffer)
        file5_buffer.seek(0)
        zipf.writestr(f"Bước 3 - Lưu hủy mẫu thực phẩm - Tuần {week_number}.xlsx", file5_buffer.read())
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer, 
        download_name=f"Quy_trinh_3_buoc_tuan_{week_number}.zip", 
        as_attachment=True,
        mimetype='application/zip'
    )

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
    print(f"🔐 [DEBUG] User role: {current_role}, Session: {dict(session)}")
    
    if session.get('role') not in ['admin', 'teacher']:
        print(f"🔐 [DEBUG] Access denied for role: {current_role}")
        return redirect_no_permission()
    
    form = ProductForm()
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
            usual_quantity=form.usual_quantity.data,
            storage_condition=form.storage_condition.data,
            shelf_life_days=form.shelf_life_days.data,
            notes=form.notes.data,
            created_date=datetime.utcnow()
        )
        db.session.add(product)
        db.session.commit()
        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('main.products'))
    else:
        # Debug form validation errors
        if request.method == 'POST':
            print(f"🔍 [DEBUG] Form validation failed!")
            for field, errors in form.errors.items():
                print(f"🔍 [DEBUG] Field '{field}': {errors}")
            print(f"🔍 [DEBUG] Suppliers count: {len(suppliers)}")
    
    return render_template('new_product.html', form=form)

@main.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    """Sửa thông tin sản phẩm"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    # Lấy danh sách nhà cung cấp cho dropdown
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('main.products'))
    
    return render_template('edit_product.html', form=form, product=product)

@main.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Xóa sản phẩm"""
    if session.get('role') != 'admin':
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
        
        # 🚀 TRY ENHANCED MULTI-AI FIRST!
        try:
            if ENHANCED_MENU_AI_AVAILABLE:
                print(f"🚀 [MULTI-AI] Using Enhanced Menu AI with Groq fallback for {user_role}")
                suggestions = get_ai_menu_suggestions_enhanced(
                    age_group=age_group,
                    dietary_requirements=dietary_requirements,
                    available_ingredients=available_ingredients,
                    use_multi_ai=True  # Enable Multi-AI fallback
                )
                print(f"✅ [MULTI-AI SUCCESS] Enhanced Menu AI completed for {user_role}")
            else:
                print(f"🔄 [FALLBACK] Using original Menu AI for {user_role}")
                suggestions = get_ai_menu_suggestions(age_group, dietary_requirements, count, available_ingredients)
        except Exception as multi_ai_error:
            print(f"⚠️ [MULTI-AI FALLBACK] Enhanced AI failed: {multi_ai_error}")
            print(f"🔄 [FALLBACK] Trying original Menu AI for {user_role}")
            suggestions = get_ai_menu_suggestions(age_group, dietary_requirements, count, available_ingredients)
        
        # Log successful operation
        print(f"✅ [SUCCESS] Menu generated for {user_role} - Age: {age_group}, Ingredients: {len(available_ingredients)} chars")
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'age_group': age_group,
            'security_info': f"Generated securely for {user_role}"
        })
    except Exception as e:
        # Enhanced error logging với security context
        error_msg = str(e)
        print(f"❌ [ERROR] Menu generation failed for {user_role} from {user_ip}: {error_msg}")
        
        # Don't expose internal errors to client
        return jsonify({
            'success': False,
            'error': 'Đã xảy ra lỗi khi tạo thực đơn. Vui lòng thử lại sau.'
        }), 500

@main.route('/ai/create-menu-from-suggestions', methods=['POST'])
def create_menu_from_ai_suggestions():
    """Tạo thực đơn mới từ gợi ý AI"""
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Không có quyền truy cập'}), 403
    
    try:
        # Lấy data từ AI
        ai_data = request.json
        if not ai_data or not ai_data.get('success'):
            return jsonify({'error': 'Dữ liệu AI không hợp lệ'}), 400
            
        # Tính tuần hiện tại
        from datetime import datetime
        now = datetime.now()
        week_number = now.isocalendar()[1]  # Tuần trong năm
        
        # Kiểm tra tham số overwrite
        overwrite = ai_data.get('overwrite', False)
        
        # Kiểm tra xem tuần này đã có thực đơn chưa
        existing_menu = Curriculum.query.filter_by(week_number=week_number).first()
        if existing_menu and not overwrite:
            return jsonify({
                'error': f'Tuần {week_number} đã có thực đơn. Bạn có muốn ghi đè không?',
                'week_number': week_number,
                'existing': True
            }), 409
        
        # Trích xuất dữ liệu thực đơn từ AI suggestions
        suggestions = ai_data.get('suggestions', [])
        weekly_menu = extract_weekly_menu_from_suggestions(suggestions)
        
        if existing_menu and overwrite:
            # Cập nhật thực đơn hiện có
            existing_menu.content = json.dumps(weekly_menu, ensure_ascii=False)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Đã cập nhật thực đơn tuần {week_number} thành công',
                'week_number': week_number,
                'overwritten': True
            })
        else:
            # Tạo thực đơn mới
            new_menu = Curriculum(
                week_number=week_number,
                content=json.dumps(weekly_menu, ensure_ascii=False)
            )
            
            db.session.add(new_menu)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Đã tạo thực đơn tuần {week_number} thành công',
                'week_number': week_number
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

@main.route('/ai/curriculum-suggestions', methods=['POST'])
def ai_curriculum_suggestions():
    """API endpoint để lấy gợi ý chương trình học từ Gemini AI"""
    
    # Role check
    user_role = session.get('role')
    if user_role not in ['admin', 'teacher']:
        return jsonify({
            'success': False,
            'error': 'Không có quyền truy cập. Vui lòng đăng nhập với tài khoản admin hoặc giáo viên.'
        }), 403
    
    # Rate Limiting
    user_ip = validate_ip_address(request.remote_addr)
    rate_allowed, wait_seconds = check_rate_limit(f"ai_curriculum_{user_ip}", AI_RATE_LIMIT_SECONDS)
    
    if not rate_allowed:
        log_security_event('RATE_LIMIT_EXCEEDED', f'Curriculum User: {user_role}, Wait: {wait_seconds}s', user_ip)
        return jsonify({
            'success': False,
            'error': f'Quá nhiều yêu cầu. Vui lòng chờ {wait_seconds} giây trước khi thử lại.'
        }), 429
    
    try:
        # Get and validate input
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Không có dữ liệu đầu vào'}), 400
        
        # Sanitize inputs
        age_group = sanitize_input(data.get('age_group', '2-3 tuổi'))
        week_number = int(data.get('week_number', 1))
        themes = sanitize_input(data.get('themes', ''))
        special_focus = sanitize_input(data.get('special_focus', ''))
        
        # Length limits để tránh abuse
        if len(themes) > 500:
            return jsonify({
                'success': False,
                'error': 'Chủ đề quá dài (tối đa 500 ký tự)'
            }), 400
            
        if len(special_focus) > 500:
            return jsonify({
                'success': False,
                'error': 'Trọng tâm đặc biệt quá dài (tối đa 500 ký tự)'
            }), 400
        
        # Validate age group - sử dụng cùng logic như Menu AI
        valid_age_groups = ['1-2 tuổi', '2-3 tuổi', '3-4 tuổi', '4-5 tuổi']
        if age_group not in valid_age_groups:
            age_group = '2-3 tuổi'  # Default fallback
        
        # Validate week number
        if not (1 <= week_number <= 53):
            return jsonify({'success': False, 'error': 'Số tuần phải từ 1-53'}), 400
        
        # Log security event
        log_security_event('CURRICULUM_AI_REQUEST', f'User: {user_role}, Age: {age_group}, Week: {week_number}', user_ip)
        
        # 🚀 TRY ENHANCED MULTI-AI FIRST!
        try:
            if ENHANCED_CURRICULUM_AI_AVAILABLE:
                print(f"🚀 [MULTI-AI] Using Enhanced Curriculum AI with Groq fallback for {user_role}")
                ai_result = get_ai_curriculum_suggestions_enhanced(
                    age_group=age_group,
                    week_number=week_number,
                    use_multi_ai=True  # Enable Multi-AI fallback
                )
                print(f"✅ [MULTI-AI SUCCESS] Enhanced Curriculum AI completed for {user_role}")
                print(f"🔍 [DEBUG] AI Result type: {type(ai_result)}")
                print(f"🔍 [DEBUG] AI Result success: {ai_result.get('success') if isinstance(ai_result, dict) else 'Not dict'}")
                
                # Handle the new structured format
                if isinstance(ai_result, dict) and ai_result.get('success'):
                    # Convert structured data to frontend format
                    print(f"🔍 [DEBUG] Converting structured data to frontend format")
                    curriculum_data = convert_structured_to_frontend_format(
                        ai_result, age_group, week_number, themes, special_focus
                    )
                    print(f"✅ [DEBUG] Frontend format conversion completed")
                else:
                    print(f"⚠️ [DEBUG] AI result not successful, using fallback format")
                    # Fallback for old format
                    curriculum_data = {
                        'week_number': week_number,
                        'age_group': age_group,
                        'themes': themes,
                        'special_focus': special_focus,
                        'daily_activities': ai_result if isinstance(ai_result, list) else [],
                        'materials': [],
                        'provider': 'enhanced_fallback'
                    }
            else:
                print(f"🔄 [FALLBACK] Using original Curriculum AI for {user_role}")
                # Import original curriculum AI service
                from app.curriculum_ai import curriculum_ai_service
                curriculum_data = curriculum_ai_service.generate_weekly_curriculum(
                    age_group=age_group,
                    week_number=week_number,
                    themes=themes if themes else None,
                    special_focus=special_focus if special_focus else None
                )
        except Exception as multi_ai_error:
            print(f"⚠️ [MULTI-AI FALLBACK] Enhanced Curriculum AI failed: {multi_ai_error}")
            print(f"🔄 [FALLBACK] Trying original Curriculum AI for {user_role}")
            # Import original curriculum AI service
            from app.curriculum_ai import curriculum_ai_service
            curriculum_data = curriculum_ai_service.generate_weekly_curriculum(
                age_group=age_group,
                week_number=week_number,
                themes=themes if themes else None,
                special_focus=special_focus if special_focus else None
            )
        
        # Log success
        print(f"✅ [SUCCESS] Curriculum generated for {user_role} - Age: {age_group}, Week: {week_number}")
        
        return jsonify({
            'success': True,
            'curriculum_data': curriculum_data,
            'age_group': age_group,
            'week_number': week_number
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ [ERROR] Curriculum generation failed for {user_role} from {user_ip}: {error_msg}")
        print(f"❌ [DEBUG] Exception type: {type(e)}")
        print(f"❌ [DEBUG] Full traceback:")
        import traceback
        traceback.print_exc()
        
        log_security_event('CURRICULUM_AI_ERROR', f'Error: {error_msg}', user_ip)
        
        # Enhanced error handling like Menu AI
        if "quota" in error_msg.lower() or "429" in error_msg:
            return jsonify({
                'success': False,
                'error': 'API đã hết quota. Vui lòng thử lại sau hoặc kiểm tra cấu hình API key.'
            }), 429
        else:
            # Don't expose internal errors to client
            return jsonify({
                'success': False,
                'error': f'Đã xảy ra lỗi khi tạo chương trình học: {error_msg}'
            }), 500


@main.route('/ai/create-curriculum-from-suggestions', methods=['POST'])
def ai_create_curriculum_from_suggestions():
    """API endpoint để tạo chương trình học từ suggestions AI"""
    
    # Role check
    user_role = session.get('role')
    if user_role not in ['admin', 'teacher']:
        return jsonify({
            'success': False,
            'error': 'Không có quyền truy cập'
        }), 403
    
    try:
        data = request.get_json()
        if not data or 'curriculum_data' not in data:
            return jsonify({'success': False, 'error': 'Không có dữ liệu chương trình học'}), 400
        
        curriculum_data = data['curriculum_data']
        
        # Handle both old and new format
        if 'week_info' in curriculum_data:
            # Old format
            week_number = curriculum_data.get('week_info', {}).get('week_number', 1)
            curriculum_content = curriculum_data.get('curriculum', {})
        else:
            # New format - get week_number directly and use structured_data
            week_number = curriculum_data.get('week_number', 1)
            if 'structured_data' in curriculum_data:
                curriculum_content = curriculum_data['structured_data']
            elif 'curriculum' in curriculum_data:
                curriculum_content = curriculum_data['curriculum']
            else:
                return jsonify({'success': False, 'error': 'Không tìm thấy dữ liệu chương trình học hợp lệ'}), 400
        
        # Check if week already exists
        existing = Curriculum.query.filter_by(week_number=week_number).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': f'Tuần {week_number} đã tồn tại. Vui lòng chọn tuần khác hoặc xóa tuần cũ trước.'
            }), 409
        else:
            # Create new curriculum with structured content
            new_curriculum = Curriculum(
                week_number=week_number,
                content=json.dumps(curriculum_content, ensure_ascii=False)
            )
            
            db.session.add(new_curriculum)
            db.session.commit()
            
            print(f"✅ [SUCCESS] Created curriculum week {week_number} with structured format")
            
            return jsonify({
                'success': True,
                'message': f'Đã tạo chương trình học tuần {week_number} thành công',
                'week_number': week_number
            })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [ERROR] Create Curriculum Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
    from werkzeug.security import generate_password_hash
    
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

@main.route('/ai-dashboard')
def ai_dashboard():
    """Trang dashboard AI với các tính năng LLM Farm"""
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    
    return render_template('ai_dashboard.html')