# app/routes/user.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone, timedelta
import re

from .extensions import db
from ..models import User, Admin, ActivityLog, UserRole
from sqlalchemy import func

bp = Blueprint("users", __name__, url_prefix="/api/users")

# -----------------------
# Configuration / Limits
# -----------------------
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 200

# -----------------------
# Helpers
# -----------------------
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


def validate_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email))


def validate_phone(phone: str) -> bool:
    return bool(phone and PHONE_RE.match(phone))


def iso(dt):
    if dt is None:
        return None
    try:
        if hasattr(dt, "astimezone") and dt.tzinfo:
            return dt.astimezone(timezone.utc).isoformat()
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return str(dt)


def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


# -----------------------
# ADMIN: CREATE USER
# -----------------------
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
            return jsonify({"error": "Admin not found or inactive"}), 403

        if admin.is_expired():
            return jsonify({"error": "Admin subscription expired"}), 403

        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")
        phone = (data.get("phone") or "").strip() or None

        if not name or not email or not password:
            return jsonify({"error": "name, email and password are required"}), 400

        if not validate_email(email):
            return jsonify({"error": "Invalid email"}), 400

        if phone and not validate_phone(phone):
            return jsonify({"error": "Invalid phone"}), 400

        if User.query.filter(func.lower(User.email) == email.lower()).first():
            return jsonify({"error": "Email already exists"}), 400

        total_users = User.query.filter_by(admin_id=admin.id).count()
        if total_users >= admin.user_limit:
            return jsonify({"error": "Admin user limit reached"}), 400

        user = User(
            name=name,
            email=email,
            phone=phone,
            admin_id=admin.id,
            created_at=datetime.utcnow()
        )
        user.set_password(password)

        log = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=admin.id,
            action=f"Created user {email}",
            target_type="user"
        )

        try:
            db.session.add(user)
            db.session.flush()
            log.target_id = user.id
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to create user", "detail": str(e)}), 500

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
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

# -----------------------
# LOGIN (user)
# -----------------------
@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email & password required"}), 400

        # 1. Get User
        user = User.query.filter(func.lower(User.email) == email.lower()).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        if not user.is_active:
            return jsonify({"error": "Account deactivated"}), 403

        # 2. 🔥 Get the Admin who created this user
        admin = Admin.query.get(user.admin_id)
        if not admin:
            return jsonify({"error": "Admin account removed"}), 403

        # 3. 🔥 BLOCK LOGIN IF ADMIN IS EXPIRED
        if admin.expiry_date and admin.expiry_date < datetime.utcnow().date():
            return jsonify({
                "error": "Your admin subscription has expired. Login is blocked."
            }), 403

        # 4. Update user last login
        try:
            user.last_login = datetime.utcnow()
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update last_login")

        # 5. Create JWT token
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
                "last_sync": iso(user.last_sync),
                "expiry_date": str(user.expiry_date) if user.expiry_date else None
            }
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500



# -----------------------
# GET PROFILE (me)
# -----------------------
@bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        summary = None
        try:
            summary = user.get_sync_summary()
        except:
            pass

        return jsonify({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "performance_score": user.performance_score,
                "created_at": iso(user.created_at),
                "last_login": iso(user.last_login),
                "last_sync": iso(user.last_sync),
                "sync_summary": summary
            }
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# UPDATE PROFILE
# -----------------------
@bp.route("/update", methods=["PUT", "PATCH"])
@jwt_required()
def update_profile():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json() or {}
        name = data.get("name")
        phone = data.get("phone")

        if name:
            name = name.strip()
            if not name:
                return jsonify({"error": "Invalid name"}), 400
            user.name = name

        if phone:
            phone = phone.strip()
            if phone and not validate_phone(phone):
                return jsonify({"error": "Invalid phone format"}), 400
            user.phone = phone or None

        # FIXED: Remove db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to update profile"}), 500

        try:
            log = ActivityLog(
                actor_role=UserRole.USER,
                actor_id=user.id,
                action="Updated profile",
                target_type="user",
                target_id=user.id
            )
            db.session.add(log)
            db.session.commit()
        except:
            db.session.rollback()

        return jsonify({
            "message": "Profile updated",
            "user": {"id": user.id, "name": user.name, "phone": user.phone}
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# SYNC (only update last_sync)
# -----------------------
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_data():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # FIXED
        user.last_sync = datetime.utcnow()

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Failed to update sync timestamp"}), 500

        summary = None
        try:
            summary = user.get_sync_summary()
        except:
            pass

        return jsonify({
            "message": "Data synced",
            "last_sync": iso(user.last_sync),
            "summary": summary
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# SYNC STATUS
# -----------------------
@bp.route("/sync-status", methods=["GET"])
@jwt_required()
def sync_status():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        from ..models import CallHistory
        count = CallHistory.query.filter_by(user_id=user.id).count()

        return jsonify({
            "sync_status": {
                "last_sync": iso(user.last_sync),
                "call_history_count": count
            }
        }), 200

    except Exception as e:
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

