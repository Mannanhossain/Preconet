# app/__init__.py

from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import inspect, text
import os

from app.models import db, bcrypt, SuperAdmin
from config import Config

jwt = JWTManager()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ------------------------------------------
    # INITIALIZE EXTENSIONS
    # ------------------------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # ------------------------------------------
    # 🔧 AUTO-FIX DATABASE (Render Safe)
    # ------------------------------------------
    with app.app_context():
        try:
            db.session.execute(text(
                "ALTER TABLE attendances "
                "ADD COLUMN IF NOT EXISTS external_id VARCHAR(64);"
            ))
            db.session.commit()
            print("🔧 AUTO-FIX: external_id column ensured.")
        except Exception as e:
            print("⚠️ AUTO-FIX ERROR:", e)

    # ------------------------------------------
    # REGISTER BLUEPRINTS
    # ------------------------------------------
    # ------------------------------------------
# REGISTER BLUEPRINTS
# ------------------------------------------
from app.routes.super_admin import bp as super_admin_bp
from app.routes.admin import bp as admin_bp
from app.routes.users import bp as users_bp
from app.routes.fix import bp as fix_bp
from app.routes.attendance import bp as attendance_bp
from app.routes.call_history import bp as call_history_bp
from app.routes.admin_attendance import bp as admin_attendance_bp
from app.routes.admin_call_history import bp as admin_call_history_bp   # ⭐ NEW

# Register all
app.register_blueprint(super_admin_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(users_bp)
app.register_blueprint(fix_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(call_history_bp)
app.register_blueprint(admin_attendance_bp)
app.register_blueprint(admin_call_history_bp)    # ⭐ NEW


    # ------------------------------------------
    # DATABASE INITIALIZATION + DEFAULT SUPER ADMIN
    # ------------------------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if not tables:
            print("⚙️ No tables detected → Creating DB...")
            db.create_all()
            print("✅ Database created")

        # Default Super Admin
        if not SuperAdmin.query.first():
            print("⚙️ Creating default super admin...")
            sa = SuperAdmin(name="Super Admin", email="super@callmanager.com")
            sa.set_password("admin123")
            db.session.add(sa)
            db.session.commit()
            print("✅ Default SuperAdmin READY")

    # ------------------------------------------
    # FRONTEND ROUTES
    # ------------------------------------------
    FRONTEND_PATH = os.path.abspath(os.path.join(os.getcwd(), "frontend"))
    print("📁 FRONTEND PATH:", FRONTEND_PATH)

    @app.route("/")
    def home():
        return jsonify({
            "status": "running",
            "message": "Call Manager Pro Backend is LIVE!"
        })

    @app.route("/api/health")
    def health():
        return jsonify({"status": "running", "database": "connected"}), 200

    # SUPER ADMIN PANEL
    @app.route("/super_admin/login.html")
    def super_admin_login_page():
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), "login.html")

    @app.route("/super_admin/<path:filename>")
    def super_admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), filename)

    # ADMIN PANEL
    @app.route("/admin/login.html")
    def admin_login_page():
        return send_from_directory(os.path.join(FRONTEND_PATH, "admin"), "login.html")

    @app.route("/admin/<path:filename>")
    def admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, "admin"), filename)

    return app
