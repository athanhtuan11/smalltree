from flask import Flask, request, session, jsonify
from app.models import db, Activity
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate = Migrate(app, db)

    # Enable CSRF Protection 
    csrf = CSRFProtect(app)
    
    # Note: AI endpoints sẽ cần sử dụng CSRF token hoặc được handle riêng
    
    # Initialize Gemini service
    from app.gemini_service import gemini_service
    gemini_service.init_app(app)
    
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