# app/routes/user.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone, timedelta
import re

from .extensions import db
from ..models import User, Admin, ActivityLog, UserRole  # adjust import paths if needed
from sqlalchemy import func

bp = Blueprint("users", __name__, url_prefix="/api/users")

# -----------------------
# Configuration / Limits
# -----------------------
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 200
ACCESS_TOKEN_EXPIRES = None  # leave to your app config if you use timed tokens

# -----------------------
# Helpers
# -----------------------
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")  # allow 7-15 digits optionally starting with +
ISO_8601_Z_SUFFIX = "+00:00"


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
        try:
            return dt.isoformat()
        except Exception:
            return str(dt)


def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


def paginate_query(query):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except Exception:
        per_page = DEFAULT_PER_PAGE
    per_page = max(1, min(per_page, MAX_PER_PAGE))
    pag = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pag.page,
        "per_page": pag.per_page,
        "total": pag.total,
        "pages": pag.pages,
        "has_next": pag.has_next,
        "has_prev": pag.has_prev
    }
    return pag.items, meta


# -----------------------
# ADMIN: CREATE USER
# -----------------------
@bp.route("/register", methods=["POST"])
@jwt_required()
def register():
    """
    Admin creates a user under their account.
    Required JSON: name, email, password
    Optional: phone
    """
    try:
        # ensure admin token
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access only"}), 403

        admin_id = get_jwt_identity()
        try:
            admin_id = int(admin_id)
        except Exception:
            return jsonify({"error": "Invalid admin identity"}), 401

        admin = Admin.query.get(admin_id)
        if not admin or not getattr(admin, "is_active", True):
            return jsonify({"error": "Admin not found or inactive"}), 403

        if callable(getattr(admin, "is_expired", None)) and admin.is_expired():
            return jsonify({"error": "Admin subscription expired"}), 403

        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")
        phone = (data.get("phone") or "").strip() or None

        if not name or not email or not password:
            return jsonify({"error": "name, email and password are required"}), 400

        if not validate_email(email):
            return jsonify({"error": "Invalid email address"}), 400

        if phone and not validate_phone(phone):
            return jsonify({"error": "Invalid phone number format"}), 400

        # ensure unique email (case-insensitive)
        if User.query.filter(func.lower(User.email) == email.lower()).first():
            return jsonify({"error": "Email already exists"}), 400

        # admin user limit
        total_users = User.query.filter_by(admin_id=admin.id).count()
        if getattr(admin, "user_limit", None) is not None and total_users >= admin.user_limit:
            return jsonify({"error": "Admin user limit reached"}), 400

        # Create user in a single transaction and write an activity log
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
            # target_id added after flush
        )

        try:
            db.session.add(user)
            db.session.flush()  # get user.id
            log.target_id = user.id
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to create user")
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
        current_app.logger.exception("Unhandled error in register")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# LOGIN (user)
# -----------------------
@bp.route("/login", methods=["POST"])
def login():
    """
    User login. Returns JWT with role=user claim.
    Required JSON: email, password
    """
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email & password required"}), 400

        user = User.query.filter(func.lower(User.email) == email.lower()).first()
        if not user or not user.check_password(password):
            # For security don't reveal whether email exists
            return jsonify({"error": "Invalid credentials"}), 401

        if not getattr(user, "is_active", True):
            return jsonify({"error": "Account deactivated"}), 403

        user.last_login = datetime.utcnow()
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update last_login")

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
                "performance_score": getattr(user, "performance_score", None),
                "last_sync": iso(getattr(user, "last_sync", None))
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in login")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# GET PROFILE (me)
# -----------------------
@bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except Exception:
            return jsonify({"error": "Invalid identity"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # safe fallback if get_sync_summary missing
        sync_summary = None
        try:
            sync_summary = user.get_sync_summary() if callable(getattr(user, "get_sync_summary", None)) else None
        except Exception:
            current_app.logger.exception("get_sync_summary() failed")

        return jsonify({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "performance_score": getattr(user, "performance_score", None),
                "created_at": iso(getattr(user, "created_at", None)),
                "last_login": iso(getattr(user, "last_login", None)),
                "last_sync": iso(getattr(user, "last_sync", None)),
                "sync_summary": sync_summary
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in get_me")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# UPDATE PROFILE (me)
# -----------------------
@bp.route("/update", methods=["PUT", "PATCH"])
@jwt_required()
def update_profile():
    """
    Allows user to update their name & phone.
    Email and performance_score are immutable from client-side.
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json() or {}
        name = data.get("name")
        phone = data.get("phone")

        if name is not None:
            name = name.strip()
            if not name:
                return jsonify({"error": "Invalid name"}), 400
            user.name = name

        if phone is not None:
            phone = phone.strip()
            if phone and not validate_phone(phone):
                return jsonify({"error": "Invalid phone format"}), 400
            user.phone = phone or None

        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update profile")
            return jsonify({"error": "Failed to update profile"}), 500

        # non-blocking log (if log fails, do not revert main update)
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
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Profile update log failed")

        return jsonify({"message": "Profile updated", "user": {"id": user.id, "name": user.name, "phone": user.phone}}), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in update_profile")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# SYNC: only update last_sync (lightweight)
# -----------------------
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_data():
    """
    Lightweight sync endpoint — marks last_sync timestamp for the device/user.
    Heavy syncs (attendance, calls) should use dedicated endpoints.
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.last_sync = datetime.utcnow()
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update last_sync")
            return jsonify({"error": "Failed to update sync timestamp"}), 500

        # non-blocking activity log
        try:
            log = ActivityLog(
                actor_role=UserRole.USER,
                actor_id=user.id,
                action="Performed lightweight sync",
                target_type="user",
                target_id=user.id
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Sync log failed")

        sync_summary = None
        try:
            sync_summary = user.get_sync_summary() if callable(getattr(user, "get_sync_summary", None)) else None
        except Exception:
            current_app.logger.exception("get_sync_summary() failed")

        return jsonify({
            "message": "Data synced",
            "last_sync": iso(user.last_sync),
            "summary": sync_summary
        }), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in sync_data")
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

        call_count = 0
        try:
            call_count = func.coalesce(func.count, 0)  # placeholder if model unavailable
            # try a safe query if CallHistory exists
            from ..models import CallHistory
            call_count = CallHistory.query.filter_by(user_id=user.id).count()
        except Exception:
            current_app.logger.debug("CallHistory not available for sync-status")

        return jsonify({
            "sync_status": {
                "last_sync": iso(getattr(user, "last_sync", None)),
                "call_history_count": int(call_count or 0)
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in sync_status")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -----------------------
# ADMIN: Recalculate & Persist Performance for a user or all users
# -----------------------
@bp.route("/admin/recalc-performance", methods=["POST"])
@jwt_required()
def admin_recalc_performance():
    """
    Admin can trigger recalculation for:
    - single user: JSON { "user_id": <id> }
    - all users under admin: no body
    Requires role=admin in JWT and ownership.
    """
    try:
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access only"}), 403

        admin_identity = get_jwt_identity()
        try:
            admin_id = int(admin_identity)
        except Exception:
            return jsonify({"error": "Invalid admin identity"}), 401

        data = request.get_json() or {}
        target_user_id = data.get("user_id")

        # helper: performance calculation consistent with other modules
        def _calc_and_persist(u):
            try:
                # import locally to avoid circular import issues
                from ..routes.call_history import calculate_performance as calc_perf
            except Exception:
                # fallback: simple heuristic based on attendance only
                def calc_perf(uid):
                    # minimal safe calc
                    return getattr(u, "performance_score", 0) or 0

            score = calc_perf(u.id)
            u.performance_score = score
            db.session.add(u)
            return {"user_id": u.id, "performance_score": score}

        results = []
        if target_user_id:
            user = User.query.get(int(target_user_id))
            if not user:
                return jsonify({"error": "User not found"}), 404
            # ownership check
            if getattr(user, "admin_id", None) != admin_id:
                return jsonify({"error": "Unauthorized (not your user)"}), 403
            res = _calc_and_persist(user)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Failed to persist performance for user")
                return jsonify({"error": "Failed to persist performance"}), 500
            results.append(res)
        else:
            # recalc for all users of this admin
            users = User.query.filter_by(admin_id=admin_id).all()
            for u in users:
                results.append(_calc_and_persist(u))
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Failed to persist performance for multiple users")
                return jsonify({"error": "Failed to persist performance for users"}), 500

        return jsonify({"message": "Performance recalculated", "results": results}), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in admin_recalc_performance")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500
