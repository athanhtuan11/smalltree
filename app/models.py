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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Tên sản phẩm
    category = db.Column(db.String(50), nullable=False)  # 'fresh' hoặc 'dry'
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # kg, lít, gói...
    usual_quantity = db.Column(db.Float)  # Số lượng thường dùng
    storage_condition = db.Column(db.String(100))  # Điều kiện bảo quản
    shelf_life_days = db.Column(db.Integer)  # Thời hạn sử dụng (ngày)
    notes = db.Column(db.Text)  # Ghi chú
    created_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    supplier = db.relationship('Supplier', backref=db.backref('products', lazy=True))