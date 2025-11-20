# app/routes/call_history.py

import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import SQLAlchemyError

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


def parse_timestamp(ts_value):
    """
    Convert timestamp input from:
    - ISO string
    - epoch seconds
    - epoch milliseconds
    - and return datetime OR None
    """
    if ts_value is None:
        return None

    if isinstance(ts_value, (int, float)):
        try:
            # milliseconds
            if ts_value > 1e10:
                return datetime.utcfromtimestamp(ts_value / 1000)
            # seconds
            return datetime.utcfromtimestamp(ts_value)
        except:
            return None

    if isinstance(ts_value, str):
        try:
            if ts_value.endswith("Z"):
                ts_value = ts_value[:-1] + "+00:00"
            dt = datetime.fromisoformat(ts_value)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
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
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", DEFAULT_PER_PAGE, type=int), MAX_PER_PAGE)
    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    return pag.items, {
        "page": pag.page,
        "per_page": pag.per_page,
        "total": pag.total,
        "pages": pag.pages,
        "has_next": pag.has_next,
        "has_prev": pag.has_prev
    }


# -------------------------------------------------
# 1) SYNC CALL HISTORY (MOBILE → SERVER)
# -------------------------------------------------
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_call_history():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user or not user.is_active:
            return jsonify({"error": "User inactive or missing"}), 403

        payload = request.get_json(silent=True) or {}
        call_list = payload.get("call_history", [])

        if not isinstance(call_list, list):
            return jsonify({"error": "'call_history' must be a list"}), 400

        saved = 0
        errors = []

        for entry in call_list:
            phone_number = entry.get("phone_number")
            call_type = entry.get("call_type")
            duration = entry.get("duration", 0)
            timestamp_raw = entry.get("timestamp")

            if not phone_number or not timestamp_raw:
                errors.append({"entry": entry, "error": "Missing timestamp or phone_number"})
                continue

            dt = parse_timestamp(timestamp_raw)
            if not dt:
                errors.append({"entry": entry, "error": "Invalid timestamp format"})
                continue

            # ➤ Normalize timestamp (DROP microseconds)
            dt = dt.replace(microsecond=0)

            formatted_number = entry.get("formatted_number") or ""
            contact_name = entry.get("contact_name") or ""

            # ----------------------------------------------------
            # SAFE DUPLICATE CHECK (No timestamp comparison!)
            # ----------------------------------------------------
            duplicate = CallHistory.query.filter(
                CallHistory.user_id == user_id,
                CallHistory.phone_number == phone_number,
                CallHistory.call_type == call_type,
                CallHistory.duration == int(duration)
            ).first()

            if duplicate:
                continue

            new_record = CallHistory(
                user_id=user_id,
                phone_number=phone_number,
                formatted_number=formatted_number,
                call_type=call_type,
                duration=int(duration),
                timestamp=dt,
                contact_name=contact_name
            )

            db.session.add(new_record)
            saved += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "DB commit failed", "detail": str(e)}), 500

        # Update sync time
        user.last_sync = datetime.utcnow()
        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Call history synced",
            "records_saved": saved,
            "errors": errors
        }), 200

    except Exception as e:
        current_app.logger.exception("CALL HISTORY SYNC ERROR")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------------------------------
# 2) USER — FETCH MY CALL HISTORY
# -------------------------------------------------
@bp.route("/my", methods=["GET"])
@jwt_required()
def my_call_history():
    try:
        user_id = int(get_jwt_identity())

        q = CallHistory.query.filter_by(user_id=user_id).order_by(CallHistory.timestamp.desc())

        items, meta = paginate(q)

        data = [r.to_dict() for r in items]

        return jsonify({
            "user_id": user_id,
            "call_history": data,
            "meta": meta
        })

    except Exception as e:
        current_app.logger.exception("MY CALL HISTORY ERROR")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# 3) ADMIN — FETCH SPECIFIC USER CALL HISTORY
# -------------------------------------------------
@bp.route("/admin/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def admin_user_call_history(user_id):
    try:
        q = CallHistory.query.filter_by(user_id=user_id).order_by(CallHistory.timestamp.desc())

        items, meta = paginate(q)

        return jsonify({
            "user_id": user_id,
            "call_history": [r.to_dict() for r in items],
            "meta": meta
        })

    except Exception as e:
        current_app.logger.exception("ADMIN CALL HISTORY ERROR")
        return jsonify({"error": str(e)}), 500
