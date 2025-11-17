from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from datetime import datetime
from ..models import db, Admin, User, Attendance, CallHistory, ActivityLog, UserRole
import re

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------
def validate_email(email):
    pattern = r"^[^@]+@[^@]+\.[^@]{2,}$"
    return re.match(pattern, email) is not None


# ---------------------------------------------------------
# ADMIN LOGIN
# ---------------------------------------------------------
@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}

        admin = Admin.query.filter_by(email=data.get("email")).first()

        if not admin or not admin.check_password(data.get("password")):
            return jsonify({"error": "Invalid credentials"}), 401

        if not admin.is_active:
            return jsonify({"error": "Account deactivated"}), 401

        if admin.is_expired():
            return jsonify({"error": "Account expired"}), 401

        # Track last login
        admin.last_login = datetime.utcnow()
        db.session.commit()

        token = create_access_token(
            identity=str(admin.id),
            additional_claims={"role": "admin"}
        )

        return jsonify({
            "access_token": token,
            "user": {
                "id": admin.id,
                "name": admin.name,
                "email": admin.email,
                "role": "admin",
                "user_limit": admin.user_limit,
                "expiry_date": admin.expiry_date.isoformat()
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# CREATE USER (FIXED)
# ---------------------------------------------------------
@bp.route("/create-user", methods=["POST"])
@jwt_required()
def create_user():
    try:
        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin or not admin.is_active:
            return jsonify({"error": "Unauthorized"}), 401

        if admin.is_expired():
            return jsonify({"error": "Admin expired"}), 401

        # Check user limit
        total_users = User.query.filter_by(admin_id=admin.id).count()
        if total_users >= admin.user_limit:
            return jsonify({"error": "User limit reached"}), 400

        data = request.get_json() or {}
        required = ["name", "email", "password"]

        for f in required:
            if not data.get(f):
                return jsonify({"error": f"{f} is required"}), 400

        if not validate_email(data["email"]):
            return jsonify({"error": "Invalid email"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already taken"}), 400

        # Create user
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data.get("phone"),
            admin_id=admin.id
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        # Activity Log
        log = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=admin_id,
            action=f"Created user {user.email}",
            target_type="user",
            target_id=user.id
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({"message": "User created", "user_id": user.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# GET ALL USERS
# ---------------------------------------------------------
@bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    try:
        admin_id = int(get_jwt_identity())
        users = User.query.filter_by(admin_id=admin_id).all()

        return jsonify({
            "users": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "phone": u.phone,
                    "is_active": u.is_active,
                    "performance_score": u.performance_score,
                    "created_at": u.created_at.isoformat(),
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                    "last_sync": u.last_sync.isoformat() if u.last_sync else None,
                    "has_sync_data": u.last_sync is not None
                }
                for u in users
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# DASHBOARD STATS
# ---------------------------------------------------------
@bp.route("/dashboard-stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    try:
        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        users = User.query.filter_by(admin_id=admin.id).all()
        total = len(users)
        active = sum(1 for u in users if u.is_active)
        synced = sum(1 for u in users if u.last_sync)

        avg_perf = round(
            sum(u.performance_score for u in users) / total, 2
        ) if total > 0 else 0

        return jsonify({
            "stats": {
                "total_users": total,
                "active_users": active,
                "expired_users": 0,
                "user_limit": admin.user_limit,
                "remaining_slots": admin.user_limit - total,
                "users_with_sync": synced,
                "sync_rate": round((synced / total) * 100, 2) if total else 0,
                "avg_performance": avg_perf,
                "performance_trend": [50, 60, 70, 65, 80, 75, 90]  # dummy trend
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# RECENT 10 USER SYNC (NEW)
# ---------------------------------------------------------
@bp.route("/recent-sync", methods=["GET"])
@jwt_required()
def recent_sync():
    try:
        admin_id = int(get_jwt_identity())

        users = (
            User.query
            .filter_by(admin_id=admin_id)
            .filter(User.last_sync.isnot(None))
            .order_by(User.last_sync.desc())
            .limit(10)
            .all()
        )

        return jsonify({
            "recent_sync": [
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "phone": u.phone,
                    "last_sync": u.last_sync.isoformat() if u.last_sync else None
                }
                for u in users
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# USER ATTENDANCE LIST
# ---------------------------------------------------------
@bp.route("/attendance", methods=["GET"])
@jwt_required()
def admin_attendance():
    try:
        admin_id = int(get_jwt_identity())

        records = (
            db.session.query(Attendance, User)
            .join(User, Attendance.user_id == User.id)
            .filter(User.admin_id == admin_id)
            .order_by(Attendance.created_at.desc())
            .all()
        )

        return jsonify({
            "attendance": [
                {
                    "id": a.id,
                    "user_name": u.name,
                    "check_in": a.check_in.isoformat(),
                    "check_out": a.check_out.isoformat() if a.check_out else None,
                    "status": a.status,
                    "address": a.address
                }
                for a, u in records
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# USER CALL HISTORY
# ---------------------------------------------------------
@bp.route("/user-call-history/<int:user_id>", methods=["GET"])
@jwt_required()
def user_call_history(user_id):
    try:
        calls = (
            CallHistory.query
            .filter_by(user_id=user_id)
            .order_by(CallHistory.timestamp.desc())
            .all()
        )

        return jsonify({
            "call_history": [
                {
                    "id": c.id,
                    "number": c.number,
                    "call_type": c.call_type,
                    "timestamp": c.timestamp,
                    "duration": c.duration,
                    "name": c.name,
                    "created_at": c.created_at.isoformat()
                }
                for c in calls
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# USER ATTENDANCE FULL LIST
# ---------------------------------------------------------
@bp.route("/user-attendance/<int:user_id>", methods=["GET"])
@jwt_required()
def user_attendance(user_id):
    try:
        records = Attendance.query.filter_by(user_id=user_id).all()

        return jsonify({
            "attendance": [a.to_dict() for a in records]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# PLACEHOLDER USER ANALYTICS
# ---------------------------------------------------------
@bp.route("/user-analytics/<int:user_id>", methods=["GET"])
@jwt_required()
def user_analytics(user_id):
    return jsonify({
        "analytics": {},
        "message": "Analytics not implemented yet"
    })
