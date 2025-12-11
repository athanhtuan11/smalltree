
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# ================== LỚP HỌC ==================
class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Có thể mở rộng thêm các trường khác nếu cần
class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    
    # Thông tin phụ huynh chi tiết (thay thế parent_contact cũ)
    father_name = db.Column(db.String(100))  # Họ và tên Bố
    father_phone = db.Column(db.String(20))  # Số điện thoại Bố
    mother_name = db.Column(db.String(100))  # Họ và tên Mẹ
    mother_phone = db.Column(db.String(20))  # Số điện thoại Mẹ
    
    # Deprecated: Giữ lại tạm để không mất data cũ trên server, sẽ xóa sau
    parent_contact = db.Column(db.String(100), nullable=True)
    
    class_name = db.Column(db.String(100))
    birth_date = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Chưa điểm danh')
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    password = db.Column(db.String(100))
    student_code = db.Column(db.String(20), unique=True, nullable=True)
    avatar = db.Column(db.String(300))  # Đường dẫn ảnh đại diện học sinh
    is_active = db.Column(db.Boolean, default=True)  # Ẩn học sinh khi nghỉ học

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
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)  # Null = cho tất cả khách vãng lai
    class_obj = db.relationship('Class', backref=db.backref('activities', lazy=True))
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
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    material = db.Column(db.String(200), nullable=True)
    # Relationship
    class_obj = db.relationship('Class', backref=db.backref('curriculums', lazy=True))
    
    # Unique constraint để tránh trùng lặp tuần + lớp
    __table_args__ = (db.UniqueConstraint('week_number', 'class_id', name='unique_week_class'),)

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    breakfast = db.Column(db.String(20))
    lunch = db.Column(db.String(20))
    snack = db.Column(db.String(20))
    toilet = db.Column(db.String(10))
    toilet_times = db.Column(db.Integer)
    note = db.Column(db.String(255))
    __table_args__ = (db.UniqueConstraint('child_id', 'date', name='uq_attendance_child_date'),)

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
    price = db.Column(db.Float, nullable=True)  # Giá cả (VNĐ) theo đơn vị
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

class Menu(db.Model):
    """Model cho thực đơn hàng tuần"""
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)  # Tuần thứ mấy trong năm
    year = db.Column(db.Integer, nullable=False, default=2025)
    
    # Thứ 2
    monday_morning = db.Column(db.Text)
    monday_snack = db.Column(db.Text)
    monday_dessert = db.Column(db.Text)
    monday_lunch = db.Column(db.Text)
    monday_afternoon = db.Column(db.Text)
    monday_lateafternoon = db.Column(db.Text)
    
    # Thứ 3
    tuesday_morning = db.Column(db.Text)
    tuesday_snack = db.Column(db.Text)
    tuesday_dessert = db.Column(db.Text)
    tuesday_lunch = db.Column(db.Text)
    tuesday_afternoon = db.Column(db.Text)
    tuesday_lateafternoon = db.Column(db.Text)
    
    # Thứ 4
    wednesday_morning = db.Column(db.Text)
    wednesday_snack = db.Column(db.Text)
    wednesday_dessert = db.Column(db.Text)
    wednesday_lunch = db.Column(db.Text)
    wednesday_afternoon = db.Column(db.Text)
    wednesday_lateafternoon = db.Column(db.Text)
    
    # Thứ 5
    thursday_morning = db.Column(db.Text)
    thursday_snack = db.Column(db.Text)
    thursday_dessert = db.Column(db.Text)
    thursday_lunch = db.Column(db.Text)
    thursday_afternoon = db.Column(db.Text)
    thursday_lateafternoon = db.Column(db.Text)
    
    # Thứ 6
    friday_morning = db.Column(db.Text)
    friday_snack = db.Column(db.Text)
    friday_dessert = db.Column(db.Text)
    friday_lunch = db.Column(db.Text)
    friday_afternoon = db.Column(db.Text)
    friday_lateafternoon = db.Column(db.Text)
    
    # Thứ 7
    saturday_morning = db.Column(db.Text)
    saturday_snack = db.Column(db.Text)
    saturday_dessert = db.Column(db.Text)
    saturday_lunch = db.Column(db.Text)
    saturday_afternoon = db.Column(db.Text)
    saturday_lateafternoon = db.Column(db.Text)
    
    # Metadata
    created_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    
    # Unique constraint để tránh trùng lặp tuần
    __table_args__ = (db.UniqueConstraint('week_number', 'year', name='unique_week_year'),)
    
    def to_dict(self):
        """Convert Menu object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'week_number': self.week_number,
            'year': self.year,
            'data': {
                'mon': {
                    'morning': self.monday_morning or '',
                    'snack': self.monday_snack or '',
                    'dessert': self.monday_dessert or '',
                    'lunch': self.monday_lunch or '',
                    'afternoon': self.monday_afternoon or '',
                    'lateafternoon': self.monday_lateafternoon or ''
                },
                'tue': {
                    'morning': self.tuesday_morning or '',
                    'snack': self.tuesday_snack or '',
                    'dessert': self.tuesday_dessert or '',
                    'lunch': self.tuesday_lunch or '',
                    'afternoon': self.tuesday_afternoon or '',
                    'lateafternoon': self.tuesday_lateafternoon or ''
                },
                'wed': {
                    'morning': self.wednesday_morning or '',
                    'snack': self.wednesday_snack or '',
                    'dessert': self.wednesday_dessert or '',
                    'lunch': self.wednesday_lunch or '',
                    'afternoon': self.wednesday_afternoon or '',
                    'lateafternoon': self.wednesday_lateafternoon or ''
                },
                'thu': {
                    'morning': self.thursday_morning or '',
                    'snack': self.thursday_snack or '',
                    'dessert': self.thursday_dessert or '',
                    'lunch': self.thursday_lunch or '',
                    'afternoon': self.thursday_afternoon or '',
                    'lateafternoon': self.thursday_lateafternoon or ''
                },
                'fri': {
                    'morning': self.friday_morning or '',
                    'snack': self.friday_snack or '',
                    'dessert': self.friday_dessert or '',
                    'lunch': self.friday_lunch or '',
                    'afternoon': self.friday_afternoon or '',
                    'lateafternoon': self.friday_lateafternoon or ''
                },
                'sat': {
                    'morning': self.saturday_morning or '',
                    'snack': self.saturday_snack or '',
                    'dessert': self.saturday_dessert or '',
                    'lunch': self.saturday_lunch or '',
                    'afternoon': self.saturday_afternoon or '',
                    'lateafternoon': self.saturday_lateafternoon or ''
                }
            },
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }

# ================== DỊCH VỤ THEO THÁNG ==================
class MonthlyService(db.Model):
    """Lưu trữ thông tin dịch vụ (tiếng anh, steamax) của học sinh theo tháng"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: "2025-11"
    has_english = db.Column(db.Boolean, default=True, nullable=False)  # Học tiếng anh
    has_steamax = db.Column(db.Boolean, default=True, nullable=False)   # STEAMAX
    created_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    
    # Relationship
    child = db.relationship('Child', backref=db.backref('monthly_services', lazy=True))
    
    # Unique constraint: một học sinh chỉ có một record cho mỗi tháng
    __table_args__ = (db.UniqueConstraint('child_id', 'month', name='unique_child_month'),)

# ================== USER ACTIVITY TRACKING ==================
class UserActivity(db.Model):
    """Ghi nhận hoạt động của người dùng để phân tích và theo dõi"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # NULL nếu là khách vãng lai
    user_type = db.Column(db.String(20), nullable=False)  # 'guest', 'parent', 'teacher', 'admin'
    user_name = db.Column(db.String(100))  # Tên hiển thị
    action = db.Column(db.String(50), nullable=False)  # 'login', 'view', 'create', 'edit', 'delete', 'download'
    resource_type = db.Column(db.String(50))  # 'student', 'activity', 'menu', 'product', 'attendance', etc.
    resource_id = db.Column(db.Integer)  # ID của resource bị tác động
    description = db.Column(db.String(500))  # Mô tả chi tiết hành động
    ip_address = db.Column(db.String(50))  # Địa chỉ IP
    user_agent = db.Column(db.String(500))  # Trình duyệt / thiết bị
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<UserActivity {self.user_type} - {self.action} - {self.resource_type}>'

# ================== FLASHCARD SYSTEM ==================
class Deck(db.Model):
    """Bộ thẻ flashcard (Animals, Colors, Numbers...)"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # "Con vật", "Màu sắc"
    description = db.Column(db.String(500))
    age_group = db.Column(db.String(10), nullable=False)  # "1-3", "3-5", "5-7"
    cover_image = db.Column(db.String(300))  # Hình bìa
    created_by = db.Column(db.Integer, db.ForeignKey('staff.id'))  # Giáo viên tạo
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)  # Hiển thị hay ẩn
    order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị
    
    cards = db.relationship('Card', backref='deck', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Deck {self.title} - {self.age_group}>'

class Card(db.Model):
    """Thẻ flashcard trong một bộ"""
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=False)
    front_text = db.Column(db.String(255), nullable=False)  # "Dog", "Con chó"
    back_text = db.Column(db.String(255))  # Giải thích thêm (optional)
    image_url = db.Column(db.String(300), nullable=False)  # Hình minh họa
    audio_url = db.Column(db.String(300))  # File âm thanh (optional)
    order = db.Column(db.Integer, default=0)  # Thứ tự trong bộ
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    progress = db.relationship('CardProgress', backref='card', lazy=True)
    
    def __repr__(self):
        return f'<Card {self.front_text}>'

class CardProgress(db.Model):
    """Tiến độ học của học sinh cho từng thẻ (Anki-style spaced repetition)"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'))  # NULL nếu khách
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    ease_level = db.Column(db.Integer, default=0)  # 0=new, 1=hard, 2=good, 3=easy
    repetitions = db.Column(db.Integer, default=0)  # Số lần ôn
    next_review = db.Column(db.DateTime)  # Thời điểm ôn lại
    last_reviewed = db.Column(db.DateTime)  # Lần ôn gần nhất
    interval_days = db.Column(db.Integer, default=1)  # Khoảng cách ôn (ngày)
    
    child = db.relationship('Child', backref=db.backref('card_progress', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('child_id', 'card_id', name='unique_child_card'),)
    
    def __repr__(self):
        return f'<CardProgress child={self.child_id} card={self.card_id} ease={self.ease_level}>'

class DeckProgress(db.Model):
    """Tiến độ tổng thể của học sinh cho từng bộ thẻ"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'))
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=False)
    learned_cards = db.Column(db.Integer, default=0)  # Số thẻ đã học
    total_score = db.Column(db.Integer, default=0)  # Tổng điểm
    stars = db.Column(db.Integer, default=0)  # Số sao kiếm được
    last_studied = db.Column(db.DateTime)  # Lần học gần nhất
    completion_date = db.Column(db.DateTime)  # Ngày hoàn thành bộ thẻ
    streak_days = db.Column(db.Integer, default=0)  # Số ngày học liên tục
    
    child = db.relationship('Child', backref=db.backref('deck_progress', lazy=True))
    deck = db.relationship('Deck', backref=db.backref('progress', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('child_id', 'deck_id', name='unique_child_deck'),)
    
    def __repr__(self):
        return f'<DeckProgress child={self.child_id} deck={self.deck_id} learned={self.learned_cards}>'