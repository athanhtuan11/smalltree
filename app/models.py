from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    parent_contact = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(100))
    birth_date = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Chưa điểm danh')
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    password = db.Column(db.String(100))
    student_code = db.Column(db.String(20), unique=True, nullable=True)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    password = db.Column(db.String(100))

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(200))  # Đường dẫn hình nền
    images = db.relationship('ActivityImage', backref='activity', lazy=True)

class ActivityImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)

class Curriculum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    material = db.Column(db.String(200), nullable=True)

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)

class BmiRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Tên cơ sở
    address = db.Column(db.String(500), nullable=False)  # Địa chỉ
    phone = db.Column(db.String(20))  # Số điện thoại
    contact_person = db.Column(db.String(100))  # Tên người liên hệ/giao hàng
    supplier_type = db.Column(db.String(50), nullable=False)  # 'fresh' hoặc 'dry'
    registration_number = db.Column(db.String(100))  # Số đăng ký kinh doanh
    food_safety_cert = db.Column(db.String(200))  # Giấy chứng nhận ATTP
    created_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Product(db.Model):
    # Relationship: product.supplier -> Supplier
    supplier = db.relationship('Supplier')
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Tên sản phẩm
    category = db.Column(db.String(50), nullable=False)  # 'fresh' hoặc 'dry'
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # kg, lít, gói...
    # usual_quantity = db.Column(db.Float)  # Đã bỏ trường số lượng thường dùng
    is_active = db.Column(db.Boolean, default=True)

# ================== MÓN ĂN VÀ NGUYÊN LIỆU ==================
class Dish(db.Model):
    meal_times = db.Column(db.JSON, default=list)  # Lưu các bữa dùng: ["morning", "snack", ...]
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)  # Thêm trường này để lọc món ăn đang hoạt động
    # Relationship: dish.ingredients -> list of DishIngredient
    ingredients = db.relationship('DishIngredient', backref='dish', lazy=True, cascade="all, delete-orphan")

class DishIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    # Relationship: dish_ingredient.product -> Product
    product = db.relationship('Product')
    notes = db.Column(db.Text)  # Ghi chú
    created_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    

class StudentAlbum(db.Model):
    """Album cá nhân của học sinh để theo dõi quá trình phát triển"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)  # Tiêu đề album/mốc phát triển
    description = db.Column(db.Text)  # Mô tả
    date_created = db.Column(db.Date, nullable=False)  # Ngày tạo
    milestone_type = db.Column(db.String(50))  # Loại mốc: 'academic', 'social', 'physical', 'creative', 'other'
    school_year = db.Column(db.String(20))  # Năm học: 2024-2025
    semester = db.Column(db.String(10))  # Học kỳ: HK1, HK2
    age_at_time = db.Column(db.String(10))  # Độ tuổi khi chụp: "3 tuổi 2 tháng"
    created_by = db.Column(db.String(100))  # Người tạo: teacher, admin
    is_shared_with_parents = db.Column(db.Boolean, default=True)  # Chia sẻ với phụ huynh
    
    # Relationship
    student = db.relationship('Child', backref=db.backref('albums', lazy=True))
    photos = db.relationship('StudentPhoto', backref='album', lazy=True, cascade='all, delete-orphan')

class StudentPhoto(db.Model):
    """Ảnh trong album của học sinh"""
    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('student_album.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(200))  # Tên file gốc
    caption = db.Column(db.Text)  # Chú thích ảnh
    upload_date = db.Column(db.DateTime, nullable=False)
    file_size = db.Column(db.Integer)  # Kích thước file (bytes)
    image_order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị trong album
    is_cover_photo = db.Column(db.Boolean, default=False)  # Ảnh đại diện album

class StudentProgress(db.Model):
    """Theo dõi tiến bộ học tập và phát triển của học sinh"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    evaluation_date = db.Column(db.Date, nullable=False)
    skill_category = db.Column(db.String(50), nullable=False)  # 'language', 'motor', 'social', 'cognitive', 'self_care'
    skill_name = db.Column(db.String(200), nullable=False)  # Tên kỹ năng cụ thể
    level_achieved = db.Column(db.String(20))  # 'excellent', 'good', 'developing', 'needs_support'
    notes = db.Column(db.Text)  # Ghi chú chi tiết
    teacher_name = db.Column(db.String(100))  # Giáo viên đánh giá
    
    # Relationship
    student = db.relationship('Child', backref=db.backref('progress_records', lazy=True))