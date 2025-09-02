from flask import Flask, request, session, jsonify
from app.models import db, Activity
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
import os
from dotenv import load_dotenv

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

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
    
    # Luôn lấy SQLALCHEMY_DATABASE_URI từ config.py (mặc định là SQLite)
    app.config.from_object('config.Config')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate = Migrate(app, db)

    # Enable CSRF Protection 
    csrf = CSRFProtect(app)
    
    # Note: AI endpoints sẽ cần sử dụng CSRF token hoặc được handle riêng
    
    # Inject csrf_token cho templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

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