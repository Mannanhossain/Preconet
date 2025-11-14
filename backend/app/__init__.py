from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from .models import db, bcrypt
from config import Config
import os

jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # ✅ Register blueprints FIRST (before static routes)
    from .routes import super_admin, admin, users
    app.register_blueprint(super_admin.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)

    # ✅ Frontend folder now inside backend
    FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend')

    # ✅ Test route - check if API is working
    @app.route('/')
    def home():
        return jsonify({
            "status": "running", 
            "message": "Call Manager Pro API is running!",
            "endpoints": {
                "health": "/api/health",
                "admin_login": "/api/admin/login",
                "super_admin_login": "/api/superadmin/login"
            }
        })

    # ✅ Health check
    @app.route('/api/health')
    def health():
        return jsonify({
            "status": "running",
            "message": "✅ Flask backend is healthy!"
        }), 200

    # ✅ Serve super_admin dashboard - ONLY specific files
    @app.route('/super_admin')
    def serve_super_admin():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), 'index.html')

    # ✅ Serve admin dashboard - ONLY specific files  
    @app.route('/admin')
    def serve_admin():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'admin'), 'index.html')

    # ✅ Serve super_admin login page
    @app.route('/super_admin/login.html')
    def serve_super_admin_login():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), 'login.html')

    # ✅ Serve admin login page
    @app.route('/admin/login.html')
    def serve_admin_login():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'admin'), 'login.html')

    # ✅ Serve static files for super_admin (CSS, JS, images) - ONLY for actual files
    @app.route('/super_admin/<path:filename>')
    def serve_super_admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), filename)

    # ✅ Serve static files for admin (CSS, JS, images) - ONLY for actual files
    @app.route('/admin/<path:filename>')
    def serve_admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, 'admin'), filename)

    return app
