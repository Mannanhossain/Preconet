from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, SuperAdmin, Admin, User, ActivityLog, UserRole
from datetime import datetime
import re

bp = Blueprint("super_admin", __name__, url_prefix="/api/superadmin")


# =========================================================
# AUTO-CREATE DEFAULT SUPER ADMIN
# =========================================================
def create_default_super_admin():
    default_email = "superadmin@preconet.com"
    default_password = "Super@123"

    existing = SuperAdmin.query.filter_by(email=default_email).first()
    if existing:
        print("✔ Default SuperAdmin already exists.")
        return

    super_admin = SuperAdmin(
        name="Master Super Admin",
        email=default_email,
    )
    super_admin.set_password(default_password)

    db.session.add(super_admin)
    db.session.commit()

    print("🔥 Default SuperAdmin created:")
    print("   Email:", default_email)
    print("   Password:", default_password)


# =========================================================
# HELPERS
# =========================================================
def _validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def _safe_actor_role(role_field):
    try:
        return role_field.value  # if enum
    except:
        return str(role_field)


# =========================================================
# REGISTER SUPER ADMIN (ONLY ONCE)
# =========================================================
@bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error": "name, email and password are required"}), 400

        if not _validate_email(email):
            return jsonify({"error": "invalid email format"}), 400

        if SuperAdmin.query.first():
            return jsonify({"error": "super admin already exists"}), 400

        super_admin = SuperAdmin(name=name, email=email)
        super_admin.set_password(password)

        db.session.add(super_admin)
        db.session.commit()

        return jsonify({"message": "Super admin created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================================
# LOGIN SUPER ADMIN
# =========================================================
@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "email and password required"}), 400

        super_admin = SuperAdmin.query.filter_by(email=email).first()
        if not super_admin or not super_admin.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_access_token(
            identity=str(super_admin.id), additional_claims={"role": "super_admin"}
        )

        return jsonify(
            {
                "access_token": token,
                "user": {
                    "id": super_admin.id,
                    "name": super_admin.name,
                    "email": super_admin.email,
                    "role": "super_admin",
                },
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# CREATE ADMIN
# =========================================================
@bp.route("/create-admin", methods=["POST"])
@jwt_required()
def create_admin():
    try:
        current_super_admin_id = int(get_jwt_identity())
        if not SuperAdmin.query.get(current_super_admin_id):
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json() or {}
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        user_limit = int(data.get("user_limit", 10))
        expiry_date_str = data.get("expiry_date")

        if not name or not email or not password or not expiry_date_str:
            return jsonify(
                {"error": "name, email, password and expiry_date are required"}), 400

        if not _validate_email(email):
            return jsonify({"error": "invalid email format"}), 400

        if Admin.query.filter_by(email=email).first():
            return jsonify({"error": "email already exists"}), 400

        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "expiry_date must be YYYY-MM-DD"}), 400

        admin = Admin(
            name=name,
            email=email,
            user_limit=user_limit,
            expiry_date=expiry_date,
            created_by=current_super_admin_id,
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        log = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_super_admin_id,
            action=f"Created admin: {admin.name}",
            target_type="admin",
            target_id=admin.id,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({"message": "Admin created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =========================================================
# GET ALL ADMINS
# =========================================================
@bp.route("/admins", methods=["GET"])
@jwt_required()
def get_admins():
    try:
        admins = Admin.query.order_by(Admin.created_at.desc()).all()
        admin_list = []

        for admin in admins:
            user_count = User.query.filter_by(admin_id=admin.id).count()
            admin_list.append(
                {
                    "id": admin.id,
                    "name": admin.name,
                    "email": admin.email,
                    "user_limit": admin.user_limit,
                    "expiry_date": admin.expiry_date.isoformat(),
                    "created_at": admin.created_at.isoformat(),
                    "last_login": admin.last_login.isoformat()
                    if admin.last_login
                    else None,
                    "is_active": admin.is_active,
                    "user_count": user_count,
                    "is_expired": admin.is_expired(),
                }
            )

        return jsonify({"admins": admin_list}), 200

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
            "total_users": User.query.count(),
            "active_admins": Admin.query.filter_by(is_active=True).count(),
            "expired_admins": Admin.query.filter(Admin.expiry_date < datetime.utcnow()).count(),
        }

        return jsonify({"stats": stats}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# ACTIVITY LOGS
# =========================================================
@bp.route("/logs", methods=["GET"])
@jwt_required()
def get_logs():
    try:
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()

        data = [
            {
                "id": log.id,
                "actor_role": _safe_actor_role(log.actor_role),
                "actor_id": log.actor_id,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]

        return jsonify({"logs": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
