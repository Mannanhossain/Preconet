# from .super_admin import bp as super_admin_bp
# from .admin import bp as admin_bp
# from .users import bp as users_bp

# __all__ = ['super_admin_bp', 'admin_bp', 'users_bp']

from flask import Flask
from flask_jwt_extended import JWTManager
from app.models import db

def create_app():
    app = Flask(__name__)
    
    # App configuration
    app.config.from_pyfile('config.py')
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # ✅ CORRECT: Import the blueprint variables directly
    from app.routes import users_bp, admin_bp, super_admin_bp
    
    # Register blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(super_admin_bp)
    
    return app