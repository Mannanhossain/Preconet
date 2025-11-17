from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity
)
from datetime import datetime
from ..models import db, SuperAdmin, Admin, User, ActivityLog, UserRole
import re

bp = Blueprint("super_admin", __name__, url_prefix="/api/superadmin")


# =========================================================
# HELPERS
# =========================================================
def _validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email or "") is not None


def _safe_enum_value(role):
    """Convert enum to plain string"""
    try:
        return role.value
    except:
        return str(role)


# =========================================================
# LOGIN SUPER ADMIN
# =========================================================
@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    super_admin = SuperAdmin.query.filter_by(email=email).first()
    if not super_admin or not super_admin.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(
        identity=str(super_admin.id),
        additional_claims={"role": "super_admin"}
    )

    return jsonify({
        "access_token": token,
        "user": {
            "id": super_admin.id,
            "name": super_admin.name,
            "email": super_admin.email,
            "role": "super_admin",
        }
    }), 200


# =========================================================
# CREATE ADMIN
# =========================================================
@bp.route("/create-admin", methods=["POST"])
@jwt_required()
def create_admin():
    super_admin_id = get_jwt_identity()

    if not SuperAdmin.query.get(super_admin_id):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    user_limit = int(data.get("user_limit", 10))
    expiry_date = data.get("expiry_date")

    if not all([name, email, password, expiry_date]):
        return jsonify({"error": "All fields required"}), 400

    if not _validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if Admin.query.filter_by(email=email).first():
        return jsonify({"error": "Admin email already exists"}), 400

    try:
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
    except:
        return jsonify({"error": "expiry_date must be YYYY-MM-DD"}), 400

    new_admin = Admin(
        name=name,
        email=email,
        user_limit=user_limit,
        expiry_date=expiry_date,
        created_by=super_admin_id,
    )
    new_admin.set_password(password)

    db.session.add(new_admin)
    db.session.commit()

    # Activity Logging
    log = ActivityLog(
        actor_role=UserRole.SUPER_ADMIN,
        actor_id=super_admin_id,
        action=f"Created Admin: {name}",
        target_type="admin",
        target_id=new_admin.id
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Admin created successfully"}), 201


# =========================================================
# GET ALL ADMINS  (SUPERADMIN DASHBOARD)
# =========================================================
@bp.route("/admins", methods=["GET"])
@jwt_required()
def get_admins():
    try:
        admins = Admin.query.order_by(Admin.created_at.desc()).all()
        result = []

        for a in admins:
            user_count = User.query.filter_by(admin_id=a.id).count()

            result.append({
                "id": a.id,
                "name": a.name,
                "email": a.email,
                "user_limit": a.user_limit,
                "user_count": user_count,
                "is_active": a.is_active,
                "is_expired": a.is_expired(),
                "created_at": a.created_at.isoformat(),
                "last_login": a.last_login.isoformat() if a.last_login else None,
                "expiry_date": a.expiry_date.isoformat()
            })

        return jsonify({"admins": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# DASHBOARD STATS
# =========================================================
@bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    try:
        stats = {
            "total_admins": Admin.query.count(),
            "active_admins": Admin.query.filter_by(is_active=True).count(),
            "expired_admins": Admin.query.filter(Admin.expiry_date < datetime.utcnow()).count(),
            "total_users": User.query.count(),
        }

        return jsonify({"stats": stats}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# ACTIVITY LOGS
# =========================================================
@bp.route("/logs", methods=["GET"])
@jwt_required()
def activity_logs():
    try:
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()

        formatted = []
        for log in logs:
            formatted.append({
                "id": log.id,
                "action": log.action,
                "actor_role": _safe_enum_value(log.actor_role),
                "actor_id": log.actor_id,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "timestamp": log.timestamp.isoformat()
            })

        return jsonify({"logs": formatted}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
