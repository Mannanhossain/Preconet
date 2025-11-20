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


# ------------------------------------------------------
# Helpers
# ------------------------------------------------------
def iso(dt):
    if not dt:
        return None
    try:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except:
        return str(dt)


def parse_datetime(val):
    """Accepts ISO string OR timestamp (seconds/ms). Returns Python datetime."""
    if not val:
        return None

    if isinstance(val, (int, float)):  # timestamp
        v = int(val)
        if v > 1e10:  # milliseconds
            return datetime.utcfromtimestamp(v / 1000)
        return datetime.utcfromtimestamp(v)

    if isinstance(val, str):
        s = val.strip()

        # ISO → Python
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except:
            pass

        # numeric string
        try:
            v = int(s)
            if v > 1e10:
                return datetime.utcfromtimestamp(v / 1000)
            return datetime.utcfromtimestamp(v)
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
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(MAX_PER_PAGE, max(1, int(request.args.get("per_page", DEFAULT_PER_PAGE))))

    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    return pag.items, {
        "page": pag.page,
        "pages": pag.pages,
        "total": pag.total,
        "has_next": pag.has_next,
    }


# ------------------------------------------------------
# 1) MOBILE SYNC — FIXED TIMESTAMP ISSUE
# ------------------------------------------------------
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_call_history():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        payload = request.get_json(silent=True) or {}
        entries = payload.get("call_history", [])

        if not isinstance(entries, list):
            return jsonify({"error": "call_history must be a list"}), 400

        saved = 0
        errors = []

        for entry in entries:
            phone_number = entry.get("phone_number")
            raw_ts = entry.get("timestamp")

            if not phone_number or raw_ts is None:
                errors.append({"entry": entry, "error": "Missing timestamp or phone_number"})
                continue

            ts = parse_datetime(raw_ts)
            if not ts:
                errors.append({"entry": entry, "error": "Invalid timestamp"})
                continue

            # Normalize datetime (remove microseconds)
            ts_norm = ts.replace(microsecond=0)

            record_date = ts_norm.date()

            exists = CallHistory.query.filter(
                CallHistory.user_id == user_id,
                CallHistory.phone_number == phone_number,
                CallHistory.call_type == entry.get("call_type"),
                CallHistory.duration == int(entry.get("duration", 0)),
                (CallHistory.timestamp.cast(db.Date) == record_date)  # SAFE FILTER
            ).first()

            if exists:
                continue

            rec = CallHistory(
                user_id=user_id,
                phone_number=phone_number,
                formatted_number=entry.get("formatted_number"),
                call_type=entry.get("call_type"),
                duration=int(entry.get("duration", 0)),
                contact_name=entry.get("contact_name"),
                timestamp=ts_norm,
            )

            db.session.add(rec)
            saved += 1

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": "DB commit failed", "detail": str(e)}), 500

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
        current_app.logger.exception("call_history sync error")
        return jsonify({"error": "internal", "detail": str(e)}), 500


# ------------------------------------------------------
# 2) USER → MY CALL HISTORY
# ------------------------------------------------------
@bp.route("/my", methods=["GET"])
@jwt_required()
def my_calls():
    try:
        user_id = int(get_jwt_identity())
        days = int(request.args.get("days", 30))

        from_date = datetime.utcnow() - timedelta(days=days)

        q = CallHistory.query.filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).order_by(CallHistory.timestamp.desc())

        items, meta = paginate(q)

        return jsonify({
            "user_id": user_id,
            "call_history": [r.to_dict() for r in items],
            "meta": meta
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
