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
    
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    from .routes import super_admin, admin, users
    app.register_blueprint(super_admin.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)

    # ✅ Frontend serving routes
    FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend')

    @app.route('/')
    def serve_super_admin():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), 'index.html')

    @app.route('/admin')
    def serve_admin():
        return send_from_directory(os.path.join(FRONTEND_PATH, 'admin'), 'index.html')

    # ✅ Serve static files
    @app.route('/<path:path>')
    def serve_static_files(path):
        file_path = os.path.join(FRONTEND_PATH, 'super_admin', path)
        if os.path.exists(file_path):
            return send_from_directory(os.path.join(FRONTEND_PATH, 'super_admin'), path)
        return jsonify({"error": "File not found"}), 404

    @app.route("/api/health")
    def health():
        return jsonify({"status": "running", "message": "✅ Flask backend is healthy!"}), 200

    return app
