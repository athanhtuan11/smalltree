from flask import Flask
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

    # Thêm CSRFProtect
    csrf = CSRFProtect(app)

    # Inject csrf_token cho mọi template
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    from app.routes import main
    app.register_blueprint(main)
    return app