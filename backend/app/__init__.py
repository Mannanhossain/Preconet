from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.models import db, bcrypt
from config import Config

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
    
    # ✅ Import blueprints (routes)
    from app.routes import super_admin, admin, users
    app.register_blueprint(super_admin.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)

    # ✅ Root route
    @app.route('/')
    def home():
        return jsonify({
            "status": "running",
            "message": "✅ Flask Backend API is live and connected successfully!",
            "routes": {
                "super_admin": "/api/super_admin/",
                "admin": "/api/admin/",
                "users": "/api/users/",
                "health": "/api/health"
            }
        }), 200

    # ✅ Health check route (for Postman test)
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "running",
            "message": "Flask backend is connected and healthy"
        }), 200

    return app
