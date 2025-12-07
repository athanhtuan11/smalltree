from flask import Flask, request, session, jsonify
from app.models import db, Activity
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
import os
from dotenv import load_dotenv
import json
from datetime import datetime, date

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle SQLAlchemy objects"""
    def default(self, obj):
        # Handle Menu objects
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        # Handle datetime objects
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # Handle other SQLAlchemy model objects by trying to convert to dict
        if hasattr(obj, '__table__'):
            return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        return super().default(obj)

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key'
    
    # Configure custom JSON encoder to handle SQLAlchemy objects
    app.json_encoder = CustomJSONEncoder

    # Định nghĩa filter định dạng ngày tháng năm cho Jinja2 (đăng ký sau khi tạo app)
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y'):
        if not value:
            return ''
        try:
            from datetime import datetime, date
            if isinstance(value, (datetime, date)):
                return value.strftime(format.replace('d', '%d').replace('m', '%m').replace('Y', '%Y'))
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.strftime(format.replace('d', '%d').replace('m', '%m').replace('Y', '%Y'))
        except Exception:
            return value
    
    # Filter để chuyển timestamp về múi giờ Việt Nam (UTC+7)
    @app.template_filter('vietnam_time')
    def vietnam_time_filter(value, format='%H:%M:%S %d/%m/%Y'):
        if not value:
            return ''
        try:
            from datetime import datetime, timezone, timedelta
            # Nếu timestamp đã có timezone info
            if hasattr(value, 'tzinfo') and value.tzinfo is not None:
                # Chuyển về Việt Nam timezone (UTC+7)
                vietnam_tz = timezone(timedelta(hours=7))
                vietnam_time = value.astimezone(vietnam_tz)
                return vietnam_time.strftime(format)
            else:
                # Nếu là naive datetime, giả định nó đã ở UTC+7
                return value.strftime(format)
        except Exception as e:
            return str(value)
    
    # Luôn lấy SQLALCHEMY_DATABASE_URI từ config.py (mặc định là SQLite)
    app.config.from_object('config.Config')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate = Migrate(app, db)

    # Enable CSRF Protection with proper configuration
    # CSRF Protection - tạm thời tắt trong development do lỗi session initialization
    csrf = CSRFProtect(app)
    
    # Note: AI endpoints sẽ cần sử dụng CSRF token hoặc được handle riêng
    
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Jinja filter để xử lý URL ảnh (local vs R2)
    @app.template_filter('image_url')
    def image_url_filter(filepath):
        """Convert image filepath to proper URL (handles both local and R2)"""
        from flask import url_for
        if not filepath:
            return url_for('static', filename='images/default_avatar.png')
        # Nếu đã là URL đầy đủ (R2), trả về nguyên văn
        if filepath.startswith('http://') or filepath.startswith('https://'):
            return filepath
        # Nếu là đường dẫn local, thêm /static/
        return url_for('static', filename=filepath)
    
    # Jinja filter để đánh giá BMI cho trẻ em theo WHO
    @app.template_filter('assess_bmi')
    def assess_bmi_filter(student, bmi_value):
        """Đánh giá BMI theo tuổi của trẻ (dùng trong template) - WHO standards"""
        from app.routes import assess_child_growth_who
        from datetime import datetime
        
        if not student or not hasattr(student, 'birth_date') or not student.birth_date or not bmi_value:
            return 'Chưa có đủ thông tin'
        
        try:
            # Convert birth_date từ string hoặc date object sang datetime
            if isinstance(student.birth_date, str):
                birth_date_obj = datetime.strptime(student.birth_date, '%Y-%m-%d')
            else:
                birth_date_obj = student.birth_date
            
            # Tính age_months
            age_months = (datetime.now() - birth_date_obj).days // 30
            gender = getattr(student, 'gender', 'unknown')
            
            # Sử dụng WHO standards
            growth_data = assess_child_growth_who(age_months, gender, bmi=bmi_value)
            return growth_data['bmi']['assessment'] or 'Chưa có đủ thông tin'
        except Exception as e:
            print(f"[ERROR] Lỗi assess_bmi filter: {e}")
            return 'Chưa có đủ thông tin'
    
    # Jinja filter để đánh giá đầy đủ tăng trưởng (BMI, cân nặng, chiều cao)
    @app.template_filter('assess_growth')
    def assess_growth_filter(student, weight=None, height=None, bmi=None):
        """Đánh giá tăng trưởng đầy đủ theo WHO standards - trả về dict với 3 chỉ số"""
        from app.routes import assess_child_growth_who
        from datetime import datetime
        
        result = {
            'bmi': {'assessment': 'Chưa có đủ thông tin', 'badge': 'secondary'},
            'weight': {'assessment': 'Chưa có đủ thông tin', 'badge': 'secondary'},
            'height': {'assessment': 'Chưa có đủ thông tin', 'badge': 'secondary'}
        }
        
        if not student or not hasattr(student, 'birth_date') or not student.birth_date:
            return result
        
        try:
            # Convert birth_date
            if isinstance(student.birth_date, str):
                birth_date_obj = datetime.strptime(student.birth_date, '%Y-%m-%d')
            else:
                birth_date_obj = student.birth_date
            
            age_months = (datetime.now() - birth_date_obj).days // 30
            gender = getattr(student, 'gender', 'unknown')
            
            # Đánh giá theo WHO
            growth_data = assess_child_growth_who(age_months, gender, bmi=bmi, weight_kg=weight, height_cm=height)
            return growth_data
        except Exception as e:
            print(f"[ERROR] Lỗi assess_growth filter: {e}")
            return result

    from app.routes import main
    app.register_blueprint(main)
    
    # Enhanced Session Security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
    
    # Security Headers  
    @app.after_request
    def add_security_headers(response):
        # Prevent XSS attacks
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Cache control for sensitive pages
        if request.endpoint in ['main.ai_dashboard', 'main.accounts']:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
        return response
    
    return app