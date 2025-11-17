from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
from ..models import db, User, Admin, ActivityLog, UserRole, CallHistory
import re

bp = Blueprint("users", __name__, url_prefix="/api/users")

# =========================================================
# VALIDATORS
# =========================================================
def validate_email(email: str):
    pattern = r"^[^@]+@[^@]+\.[^@]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone: str):
    pattern = r"^\+?[0-9]{10,15}$"
    return re.match(pattern, phone) is not None


# =========================================================
# ADMIN → CREATE USER
# =========================================================
@bp.route("/register", methods=["POST"])
@jwt_required()
def register():
    try:
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access only"}), 403

        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin or not admin.is_active:
            return jsonify({"error": "Admin inactive"}), 403

        if admin.is_expired():
            return jsonify({"error": "Admin subscription expired"}), 403

        data = request.get_json() or {}

        # Required fields
        for f in ["name", "email", "password"]:
            if not data.get(f):
                return jsonify({"error": f"{f} is required"}), 400

        if not validate_email(data["email"]):
            return jsonify({"error": "Invalid email"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 400

        # Check admin user limit
        count = User.query.filter_by(admin_id=admin.id).count()
        if count >= admin.user_limit:
            return jsonify({"error": "Admin user limit reached"}), 400

        user = User(
            name=data["name"],
            email=data["email"],
            phone=data.get("phone"),
            admin_id=admin.id,
            performance_score=float(data.get("performance_score", 0))
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        # Log activity
        log = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=admin_id,
            action=f"Created user {user.email}",
            target_type="user",
            target_id=user.id
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================================
# USER LOGIN
# =========================================================
@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email & password required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        if not user.is_active:
            return jsonify({"error": "Account deactivated"}), 401

        user.last_login = datetime.utcnow()
        db.session.commit()

        token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": "user"}
        )

        return jsonify({
            "access_token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": "user",
                "performance_score": user.performance_score,
                "last_sync": user.last_sync.isoformat() if user.last_sync else None
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# UPDATE PERFORMANCE SCORE
# =========================================================
@bp.route("/performance", methods=["POST"])
@jwt_required()
def update_performance():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user or not user.is_active:
            return jsonify({"error": "Unauthorized"}), 401

        score = request.json.get("performance_score")
        if score is None:
            return jsonify({"error": "performance_score required"}), 400

        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            return jsonify({"error": "Score must be 0–100"}), 400

        user.performance_score = score
        db.session.commit()

        # Log
        log = ActivityLog(
            actor_role=UserRole.USER,
            actor_id=user_id,
            action=f"Updated performance → {score}",
            target_type="user",
            target_id=user_id
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "message": "Performance updated",
            "performance_score": score
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================================
# GET PROFILE
# =========================================================
@bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "performance_score": user.performance_score,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "last_sync": user.last_sync.isoformat() if user.last_sync else None,
                "sync_summary": user.get_sync_summary()
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# SYNC BASIC (ONLY LAST SYNC TIME)
# =========================================================
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_data():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        user.last_sync = datetime.utcnow()
        db.session.commit()

        # Log
        log = ActivityLog(
            actor_role=UserRole.USER,
            actor_id=user_id,
            action="Synced basic user data",
            target_type="user",
            target_id=user_id
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "message": "Data synced",
            "last_sync": user.last_sync.isoformat(),
            "summary": user.get_sync_summary()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================================
# SYNC STATUS
# =========================================================
@bp.route("/sync-status", methods=["GET"])
@jwt_required()
def sync_status():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        return jsonify({
            "sync_status": {
                "last_sync": user.last_sync.isoformat() if user.last_sync else None,
                "call_history_count": CallHistory.query.filter_by(user_id=user.id).count(),
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# SYNC CALL HISTORY
# =========================================================
@bp.route("/sync-call-history", methods=["POST"])
@jwt_required()
def sync_call_history():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        call_logs = data.get("call_history", [])

        for entry in call_logs:
            record = CallHistory(
                user_id=user_id,
                number=entry.get("number"),
                call_type=entry.get("call_type"),
                timestamp=entry.get("timestamp"),
                duration=entry.get("duration"),
                name=entry.get("name", "")
            )
            db.session.add(record)

        user = User.query.get(user_id)
        user.last_sync = datetime.utcnow()

        db.session.commit()

        return jsonify({"message": "Call history synced"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
