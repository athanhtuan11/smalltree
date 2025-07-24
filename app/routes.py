from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from app.models import db, Activity, Curriculum, Child, AttendanceRecord, Staff, BmiRecord, ActivityImage
from app.forms import EditProfileForm, ActivityForm
from calendar import monthrange
from datetime import datetime, date, timedelta
import io, zipfile, os, json, re
from werkzeug.security import generate_password_hash, check_password_hash
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from PIL import Image

main = Blueprint('main', __name__)

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
    return render_template('gallery.html', title='Gallery', mobile=mobile)

@main.route('/contact')
def contact():
    mobile = is_mobile()
    return render_template('contact.html', title='Contact Us', mobile=mobile)

@main.route('/activities/new', methods=['GET', 'POST'])
def new_activity():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    form = ActivityForm()
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
    show_sensitive = role == 'admin'
    if role == 'parent':
        user = Child.query.get(user_id)
        role_display = 'Phụ huynh'
        full_name = user.parent_contact if user else ''
    elif role == 'teacher':
        user = Staff.query.get(user_id)
        role_display = 'Giáo viên'
        full_name = user.name if user else ''
    elif role == 'admin':
        user = None
        role_display = 'Admin'
        full_name = 'Admin'
    if not user and role != 'admin':
        flash('Không tìm thấy thông tin tài khoản!', 'danger')
        return redirect(url_for('main.about'))
    mobile = is_mobile()
    # Hide sensitive info for non-admins
    return render_template('profile.html', user={
        'full_name': full_name,
        'email': user.email if user and show_sensitive else 'Ẩn',
        'phone': user.phone if user and show_sensitive else 'Ẩn',
        'role_display': role_display
    }, mobile=mobile)

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
    show_sensitive = session.get('role') == 'admin'
    def mask_student(s):
        return {
            'id': s.id,
            'name': s.name,
            'email': s.email if show_sensitive else 'Ẩn',
            'phone': s.phone if show_sensitive else 'Ẩn',
            'student_code': s.student_code if show_sensitive else 'Ẩn',
            'class_name': s.class_name if show_sensitive else 'Ẩn',
            'parent_contact': s.parent_contact if show_sensitive else 'Ẩn',
        }
    masked_students = [mask_student(s) for s in students]
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

@main.route('/activities/<title>/edit', methods=['GET', 'POST'])
def edit_activity(title):
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    from urllib.parse import unquote
    title = unquote(title.replace('-', ' '))
    post = Activity.query.filter_by(title=title).first()
    if not post:
        flash('Không tìm thấy bài viết để chỉnh sửa!', 'danger')
        return redirect(url_for('main.activities'))
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.description = request.form.get('content')
        background_file = request.files.get('background')
        image_url = post.image
        if background_file and background_file.filename:
            allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.jfif'}
            ext = os.path.splitext(background_file.filename)[1].lower()
            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', background_file.filename)
            if ext not in allowed_ext:
                flash('Chỉ cho phép tải lên các file ảnh có đuôi: .jpg, .jpeg, .png, .gif, .jfif!', 'danger')
                return render_template('edit_activity.html', post=post, title='Chỉnh sửa hoạt động', mobile=is_mobile())
            filename = 'bg_' + datetime.now().strftime('%Y%m%d%H%M%S') + '_' + safe_filename
            save_path = os.path.join('app', 'static', 'images', filename)
            # Resize background
            img = Image.open(background_file)
            img.thumbnail((1200, 800))
            img.save(save_path)
            image_url = url_for('static', filename=f'images/{filename}')
            post.image = image_url
        # Lưu nhiều ảnh hoạt động
        files = request.files.getlist('images')
        activity_dir = os.path.join('app', 'static', 'images', 'activities', str(post.id))
        os.makedirs(activity_dir, exist_ok=True)
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
                    rel_path = f'images/activities/{post.id}/{img_filename}'
                    db.session.add(ActivityImage(filename=img_filename, filepath=rel_path, upload_date=datetime.now(), activity_id=post.id))
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Lỗi upload ảnh: {file.filename} - {e}")
                    traceback.print_exc()
                    flash(f"Lỗi upload ảnh: {file.filename} - {e}", 'danger')
                    continue
        db.session.commit()
        flash('Đã cập nhật bài viết!', 'success')
        return redirect(url_for('main.activities'))
    mobile = is_mobile()
    return render_template('edit_activity.html', post=post, title='Chỉnh sửa hoạt động', mobile=mobile)

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
    if session.get('role') not in ['admin', 'teacher']:
        return redirect_no_permission()
    img = ActivityImage.query.get_or_404(image_id)
    # Xoá file vật lý
    img_path = os.path.join('app', 'static', img.filepath)
    if os.path.exists(img_path):
        os.remove(img_path)
    db.session.delete(img)
    db.session.commit()
    flash('Đã xoá ảnh hoạt động!', 'success')
    return redirect(url_for('main.edit_activity', id=id))