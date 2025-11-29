from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import inspect
from datetime import datetime
import os

from app.models import db, bcrypt, SuperAdmin, Admin, User
from config import Config

jwt = JWTManager()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---------------------------
    # INITIALIZE EXTENSIONS
    # ---------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # ==========================================================
    # 🔥 GLOBAL TOKEN VALIDATION FOR ADMIN EXPIRY & USER BLOCKING
    # ==========================================================
    @app.before_request
    @jwt_required(optional=True)
    def global_subscription_checker():
        """
        This runs on EVERY authenticated route.
        Blocks:
        - Expired Admin
        - Users under expired Admin
        """

        jwt_data = get_jwt()
        identity = get_jwt_identity()

        if not identity:
            return  # Public route → ignore

        role = jwt_data.get("role")

        # --- ADMIN LOGIN CHECK ---
        if role == "admin":
            admin = Admin.query.get(int(identity))
            if admin and admin.expiry_date and admin.expiry_date < datetime.utcnow().date():
                return jsonify({"error": "Admin subscription expired"}), 403

        # --- USER LOGIN CHECK ---
        elif role == "user":
            user = User.query.get(int(identity))
            if not user:
                return jsonify({"error": "Invalid user"}), 403

            admin = Admin.query.get(user.admin_id)
            if admin and admin.expiry_date and admin.expiry_date < datetime.utcnow().date():
                return jsonify({"error": "Your admin subscription has expired"}), 403

        return  # Allow request

    # ---------------------------
    # REGISTER BLUEPRINTS
    # ---------------------------
    from app.routes.super_admin import bp as super_admin_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.users import bp as users_bp
    from app.routes.fix import bp as fix_bp
    from app.routes.attendance import bp as attendance_bp
    from app.routes.call_history import bp as call_history_bp
    from app.routes.admin_call_history import bp as admin_call_history_bp
    from app.routes.admin_attendance import bp as admin_attendance_bp
    from app.routes.admin_call_analytics import bp as admin_call_analytics_bp
    from app.routes.admin_performance import bp as admin_performance_bp
    from app.routes.admin_dashboard import admin_dashboard_bp


    app.register_blueprint(super_admin_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(fix_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(call_history_bp)
    app.register_blueprint(admin_call_history_bp)
    app.register_blueprint(admin_attendance_bp)
    app.register_blueprint(admin_call_analytics_bp)
    app.register_blueprint(admin_performance_bp)
    app.register_blueprint(admin_dashboard_bp)


    # ---------------------------
    # INITIAL DATABASE SETUP
    # ---------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if not tables:
            print("⚙ Creating DB tables...")
            db.create_all()
            print("✅ DB created")

    # ---------------------------
    # FRONTEND ROUTING
    # ---------------------------
    FRONTEND_PATH = os.path.abspath(os.path.join(os.getcwd(), "frontend"))

    @app.route("/")
    def home():
        return jsonify({"status": "running"})

    @app.route("/api/health")
    def health():
        return jsonify({"status": "running", "db": "connected"}), 200

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
