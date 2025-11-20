# app/routes/call_history.py
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func

from app.models import db, User, CallHistory

bp = Blueprint("call_history", __name__, url_prefix="/api/call-history")

DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 200


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def iso(dt):
    if not dt:
        return None
    try:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except:
        return str(dt)


def parse_datetime(val):
    """Accept ISO string or ms timestamp"""
    if isinstance(val, (int, float)):
        # milliseconds → seconds
        if val > 1e10:
            return datetime.utcfromtimestamp(val / 1000.0)
        return datetime.utcfromtimestamp(val)

    if isinstance(val, str):
        try:
            if val.endswith("Z"):
                val = val[:-1] + "+00:00"
            dt = datetime.fromisoformat(val)
            return dt.replace(tzinfo=None)
        except:
            pass

        # try numeric string
        try:
            num = int(val)
            if num > 1e10:
                return datetime.utcfromtimestamp(num / 1000.0)
            return datetime.utcfromtimestamp(num)
        except:
            return None

    return None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def paginate(query):
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = request.args.get("per_page", default=DEFAULT_PER_PAGE, type=int)
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    return pag.items, {
        "page": pag.page,
        "per_page": pag.per_page,
        "total": pag.total,
        "pages": pag.pages,
        "has_next": pag.has_next,
        "has_prev": pag.has_prev,
    }


# -------------------------------------------------
# 1) SYNC CALL HISTORY (Mobile → Server)
# -------------------------------------------------
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_call_history():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 403

        payload = request.get_json(silent=True) or {}
        call_list = payload.get("call_history", [])

        if not isinstance(call_list, list):
            return jsonify({"error": "'call_history' must be a list"}), 400

        saved = 0
        errors = []

        for entry in call_list:
            raw_ts = entry.get("timestamp")
            phone_number = entry.get("number")

            if not raw_ts or not phone_number:
                errors.append({"entry": entry, "error": "Missing timestamp or phone_number"})
                continue

            ts = parse_datetime(raw_ts)
            if not ts:
                errors.append({"entry": entry, "error": "Invalid timestamp format"})
                continue

            ts_norm = ts.replace(microsecond=0)

            formatted = entry.get("formatted_number") or ""
            call_type = entry.get("call_type") or "unknown"
            contact_name = entry.get("name") or ""

            # Duration must be integer
            try:
                duration = int(entry.get("duration", 0))
            except:
                duration = 0

            # -------------------------------------------------
            # 🔥 FIXED DUPLICATE DETECTION (NO DB TYPE ERRORS)
            # Uses DATE(timestamp) instead of full comparison
            # -------------------------------------------------
            exists = CallHistory.query.filter(
                CallHistory.user_id == user_id,
                CallHistory.phone_number == phone_number,
                CallHistory.call_type == call_type,
                CallHistory.duration == duration,
                func.date(CallHistory.timestamp) == ts_norm.date()
            ).first()

            if exists:
                continue

            rec = CallHistory(
                user_id=user_id,
                phone_number=phone_number,
                formatted_number=formatted,
                call_type=call_type,
                timestamp=ts_norm,
                duration=duration,
                contact_name=contact_name
            )

            db.session.add(rec)
            saved += 1

        db.session.commit()

        # Update user's last sync time
        user.last_sync = datetime.utcnow()
        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Call history synced",
            "records_saved": saved,
            "errors": errors
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error in call history sync")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------------------------------
# 2) USER — MY CALL HISTORY
# -------------------------------------------------
@bp.route("/my", methods=["GET"])
@jwt_required()
def my_call_history():
    try:
        user_id = int(get_jwt_identity())

        days = request.args.get("days", 30, type=int)
        call_type = request.args.get("call_type", "all")

        from_date = datetime.utcnow() - timedelta(days=max(days, 0))

        q = CallHistory.query.filter(CallHistory.user_id == user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type != "all":
            q = q.filter(CallHistory.call_type == call_type)

        q = q.order_by(CallHistory.timestamp.desc())

        items, meta = paginate(q)

        return jsonify({
            "user_id": user_id,
            "total": meta["total"],
            "call_history": [r.to_dict() for r in items],
            "meta": meta
        }), 200

    except Exception as e:
        current_app.logger.exception("Failed my_call_history")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# 3) ADMIN — USER CALL HISTORY
# -------------------------------------------------
@bp.route("/admin/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def admin_user_call_history(user_id):
    try:
        admin_id = int(get_jwt_identity())

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.admin_id != admin_id:
            return jsonify({"error": "Unauthorized"}), 403

        days = request.args.get("days", 30, type=int)
        call_type = request.args.get("call_type", "all")

        from_date = datetime.utcnow() - timedelta(days=max(days, 0))

        q = CallHistory.query.filter(CallHistory.user_id == user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type != "all":
            q = q.filter(CallHistory.call_type == call_type)

        q = q.order_by(CallHistory.timestamp.desc())

        items, meta = paginate(q)

        total_calls = q.count()
        total_duration = db.session.query(func.coalesce(func.sum(CallHistory.duration), 0)).filter(
            CallHistory.user_id == user_id
        ).scalar()

        return jsonify({
            "user_id": user_id,
            "user_name": user.name,
            "total_calls": total_calls,
            "total_duration_seconds": int(total_duration),
            "call_history": [r.to_dict() for r in items],
            "meta": meta
        }), 200

    except Exception as e:
        current_app.logger.exception("Failed admin_user_call_history")
        return jsonify({"error": str(e)}), 500
