from flask import Flask
from app.models import db, Activity
from flask_migrate import Migrate
def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate = Migrate(app, db)
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app