from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.models import db, bcrypt, SuperAdmin
from config import Config
from sqlalchemy import inspect
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

    # ------------------------------------------
    # REGISTER BLUEPRINTS
    # ------------------------------------------
    from app.routes import super_admin, admin, users
    app.register_blueprint(super_admin.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)

    # ------------------------------------------
    # AUTO DATABASE CREATION
    # ------------------------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        # SQLAlchemy table name is plural (super_admins)
        if "super_admins" not in tables:
            print("⚙️ Creating missing database tables...")
            db.create_all()
            print("✅ Tables created successfully!")

        # Create default Super Admin if missing
        if not SuperAdmin.query.first():
            super_admin = SuperAdmin(
                name="Super Admin",
                email="super@callmanager.com"
            )
            super_admin.set_password("admin123")
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Default Super Admin created: super@callmanager.com / admin123")

    # ------------------------------------------
    # FRONTEND PATH
    # ------------------------------------------
    FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend')

    # ------------------------------------------
    # ROOT API MESSAGE
    # ------------------------------------------
    @app.route('/')
    def home():
        return jsonify({
            "status": "running",
            "message": "Call Manager Pro API is running!",
            "endpoints": {
                "health": "/api/health",
                "super_admin_login": "/api/superadmin/login",
                "admin_login": "/api/admin/login",
                "admin_dashboard": "/admin",
                "super_admin_dashboard": "/super_admin"
            }
        })

    # ------------------------------------------
    # HEALTH
    # ------------------------------------------
    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "running",
            "message": "✅ Flask backend connected and healthy!"
        }), 200

    # ------------------------------------------
    # DASHBOARD ROUTES
    # ------------------------------------------

    @app.route('/super_admin')
    def super_admin_dashboard():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), 'index.html')

    @app.route('/admin')
    def admin_dashboard():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'admin'), 'index.html')

    # LOGIN PAGES
    @app.route('/super_admin/login.html')
    def super_admin_login_page():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), 'login.html')

    @app.route('/admin/login.html')
    def admin_login_page():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'admin'), 'login.html')

    # ------------------------------------------
    # STATIC FILE SERVING
    # ------------------------------------------

    @app.route('/super_admin/<path:filename>')
    def super_admin_static(filename):
        folder = os.path.join(FRONTEND_PATH, 'super_admin')
        return send_from_directory(folder, filename)

    @app.route('/admin/<path:filename>')
    def admin_static(filename):
        folder = os.path.join(FRONTEND_PATH, 'admin')
        return send_from_directory(folder, filename)

    return app
