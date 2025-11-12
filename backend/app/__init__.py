# from flask import Flask, jsonify
# from flask_jwt_extended import JWTManager
# from flask_migrate import Migrate
# from flask_cors import CORS
# from app.models import db, bcrypt, SuperAdmin
# from config import Config
# from sqlalchemy import inspect

# jwt = JWTManager()
# migrate = Migrate()

# def create_app(config_class=Config):
#     app = Flask(__name__)
#     app.config.from_object(config_class)

#     # Initialize extensions
#     db.init_app(app)
#     bcrypt.init_app(app)
#     jwt.init_app(app)
#     migrate.init_app(app, db)
#     CORS(app)

#     # Register blueprints
#     from app.routes import super_admin, admin, users
#     app.register_blueprint(super_admin.bp)
#     app.register_blueprint(admin.bp)
#     app.register_blueprint(users.bp)

#     # ✅ Create tables automatically if missing
#     with app.app_context():
#         inspector = inspect(db.engine)
#         tables = inspector.get_table_names()
#         if "super_admin" not in tables:
#             print("⚙️ Creating missing database tables...")
#             db.create_all()
#             print("✅ Tables created successfully!")

#             # ✅ Add default Super Admin
#             if not SuperAdmin.query.first():
#                 super_admin = SuperAdmin(
#                     name="Super Admin",
#                     email="super@callmanager.com"
#                 )
#                 super_admin.set_password("admin123")
#                 db.session.add(super_admin)
#                 db.session.commit()
#                 print("✅ Default Super Admin created: super@callmanager.com / admin123")

#     # Health check route
#     @app.route("/api/health")
#     def health():
#         return jsonify({
#             "status": "running",
#             "message": "✅ Flask backend connected and healthy!"
#         }), 200

#     return app
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
    
    # Register blueprints
    from .routes import super_admin, admin, users
    app.register_blueprint(super_admin.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)
    
    # --- Define absolute frontend paths ---
    BASE_DIR = os.path.abspath(os.path.join(app.root_path, '..'))
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
    
    # --- Serve Super Admin pages ---
    @app.route('/')
    def serve_super_admin():
        return send_from_directory(os.path.join(FRONTEND_DIR, 'super_admin'), 'index.html')
    
    @app.route('/super_admin/login.html')
    def serve_super_admin_login():
        return send_from_directory(os.path.join(FRONTEND_DIR, 'super_admin'), 'login.html')
    
    # --- Serve Admin pages ---
    @app.route('/admin')
    def serve_admin():
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), 'index.html')
    
    @app.route('/admin/login.html')
    def serve_admin_login():
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), 'login.html')
    
    # --- Serve static files for Super Admin ---
    @app.route('/js/<path:filename>')
    def serve_super_admin_js(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'super_admin', 'js'), filename)
    
    @app.route('/css/<path:filename>')
    def serve_super_admin_css(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'super_admin', 'css'), filename)
    
    @app.route('/assets/<path:filename>')
    def serve_super_admin_assets(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'super_admin', 'assets'), filename)
    
    # --- Serve static files for Admin ---
    @app.route('/admin/js/<path:filename>')
    def serve_admin_js(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin', 'js'), filename)
    
    @app.route('/admin/css/<path:filename>')
    def serve_admin_css(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin', 'css'), filename)
    
    @app.route('/admin/assets/<path:filename>')
    def serve_admin_assets(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'admin', 'assets'), filename)

    # --- API Health Check ---
    @app.route('/api/health')
    def health():
        return jsonify({
            "status": "running",
            "message": "✅ Flask backend is healthy"
        }), 200

    # --- SPA fallback for frontend routing ---
    @app.errorhandler(404)
    def not_found(e):
        path = os.path.join(FRONTEND_DIR, 'super_admin', 'index.html')
        if 'admin' in str(e):
            path = os.path.join(FRONTEND_DIR, 'admin', 'index.html')
        return send_from_directory(os.path.dirname(path), os.path.basename(path))
    
    return app
