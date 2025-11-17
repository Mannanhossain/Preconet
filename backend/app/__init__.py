from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import inspect
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
    # REGISTER BLUEPRINTS
    # ------------------------------------------
    from app.routes.super_admin import bp as super_admin_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.users import bp as users_bp
    from app.routes.fix import bp as fix_bp

    app.register_blueprint(super_admin_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(fix_bp)

    # ------------------------------------------
    # DATABASE INITIALIZATION (SAFE FOR RENDER)
    # ------------------------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        # First-run database initialization
        if not tables:
            print("⚙️ No tables detected → Creating database...")
            db.create_all()
            print("✅ Database tables created")

        # Default SuperAdmin (only if missing)
        if not SuperAdmin.query.first():
            print("⚙️ Creating default Super Admin account...")
            super_admin = SuperAdmin(
                name="Super Admin",
                email="super@callmanager.com"
            )
            super_admin.set_password("admin123")
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Default Super Admin ready (super@callmanager.com / admin123)")

    # ------------------------------------------
    # FRONTEND STATIC PATH
    # ------------------------------------------
    FRONTEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

    # ------------------------------------------
    # ROOT ENDPOINT
    # ------------------------------------------
    @app.route("/")
    def home():
        return jsonify({
            "status": "running",
            "message": "Call Manager Pro Backend is LIVE!",
            "routes": {
                "health": "/api/health",
                "super_admin_login": "/api/superadmin/login",
                "admin_login": "/api/admin/login",
                "user_login": "/api/users/login"
            }
        })

    # ------------------------------------------
    # HEALTH CHECK
    # ------------------------------------------
    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "running",
            "database": "connected",
            "message": "Backend healthy!"
        }), 200

    # ------------------------------------------
    # SUPER ADMIN DASHBOARD
    # ------------------------------------------
    @app.route("/super_admin")
    def super_admin_dashboard():
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), "index.html")

    @app.route("/super_admin/<path:filename>")
    def super_admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), filename)

    @app.route("/super_admin/login.html")
    def super_admin_login_page():
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), "login.html")

    # ------------------------------------------
    # ADMIN DASHBOARD
    # ------------------------------------------
    @app.route("/admin")
    def admin_dashboard():
        return send_from_directory(os.path.join(FRONTEND_PATH, "admin"), "index.html")

    @app.route("/admin/<path:filename>")
    def admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, "admin"), filename)

    @app.route("/admin/login.html")
    def admin_login_page():
        return send_from_directory(os.path.join(FRONTEND_PATH, "admin"), "login.html")

    return app
