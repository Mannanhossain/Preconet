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
    # FIXED FRONTEND PATH (IMPORTANT!!)
    # ------------------------------------------
    # Your project structure:
    # backend/
    #   app/
    #   frontend/
    #       super_admin/
    #
    # So the correct full path is:
    # ROOT/backend/frontend
    #
    FRONTEND_PATH = os.path.join(os.getcwd(), "backend", "frontend")
    print("🔥 FRONTEND PATH:", FRONTEND_PATH)

    # ------------------------------------------
    # SUPER ADMIN UI ROUTES (WORKING)
    # ------------------------------------------
    @app.route("/super_admin")
    def super_admin_home():
        # default page → login.html
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), "login.html")

    @app.route("/super_admin/<path:filename>")
    def super_admin_static(filename):
        return send_from_directory(os.path.join(FRONTEND_PATH, "super_admin"), filename)

    # ------------------------------------------
    # API HOME
    # ------------------------------------------
    @app.route("/")
    def home():
        return jsonify({
            "message": "Call Manager Pro Backend is LIVE!",
            "super_admin_ui": "/super_admin/login.html",
            "status": "running"
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
    # FIRST TIME SETUP (CREATE DEFAULT SUPER ADMIN)
    # ------------------------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if not tables:
            print("⚙️ Creating database tables...")
            db.create_all()
            print("✅ Tables created.")

        # Create default SuperAdmin if missing
        if not SuperAdmin.query.first():
            print("⚙️ Creating default Super Admin...")
            super_admin = SuperAdmin(
                name="Super Admin",
                email="super@callmanager.com"
            )
            super_admin.set_password("admin123")
            db.session.add(super_admin)
            db.session.commit()
            print("✅ Default Super Admin ready: super@callmanager.com / admin123")

    return app
