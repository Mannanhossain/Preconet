# app/routes/call_history.py
# app/routes/call_history.py
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import db, User, CallHistory, Attendance   # ✅ FIXED


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
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).isoformat()
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except:
        return str(dt)


def parse_datetime(val):
    if val is None:
        return None

    # numeric timestamp
    if isinstance(val, (int, float)):
        v = int(val)
        if v > 1e10:  # ms
            return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)

    # string parsing
    if isinstance(val, str):
        s = val.strip()
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except:
            pass

        try:
            v = int(s)
            if v > 1e10:
                return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).replace(tzinfo=None)
            return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)
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
    try:
        page = max(1, int(request.args.get("page", 1)))
    except:
        page = 1
    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except:
        per_page = DEFAULT_PER_PAGE

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
# 1) SYNC CALL HISTORY
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
            number = entry.get("number")
            if not raw_ts or not number:
                errors.append({"entry": entry, "error": "Missing timestamp or number"})
                continue

            ts = parse_datetime(raw_ts)
            if not ts:
                errors.append({"entry": entry, "error": "Invalid timestamp"})
                continue

            ts_norm = ts.replace(microsecond=0)

            # Extract fields correctly (match model)
            formatted = entry.get("formatted_number") or ""
            call_type = entry.get("call_type") or "unknown"
            duration = entry.get("duration", 0)
            try:
                duration = int(duration)
            except:
                duration = 0
            name = entry.get("name") or ""

            # Duplicate detection (simple)
            exists = CallHistory.query.filter_by(
                user_id=user_id,
                number=number,
                timestamp=ts_norm,
                duration=duration,
                call_type=call_type,
            ).first()

            if exists:
                continue

            rec = CallHistory(
                user_id=user_id,
                number=number,
                formatted_number=formatted,
                call_type=call_type,
                timestamp=ts_norm,
                duration=duration,
                name=name,
            )

            db.session.add(rec)
            saved += 1

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": "DB commit failed", "detail": str(e)}), 500

        # Update user sync time (optional)
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
        from_param = request.args.get("from")
        to_param = request.args.get("to")

        from_date = datetime.utcnow() - timedelta(days=max(days, 0))

        q = CallHistory.query.filter(CallHistory.user_id == user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type != "all":
            q = q.filter(CallHistory.call_type == call_type)

        if from_param:
            dt = parse_datetime(from_param)
            if dt:
                q = q.filter(CallHistory.timestamp >= dt)

        if to_param:
            dt = parse_datetime(to_param)
            if dt:
                q = q.filter(CallHistory.timestamp <= dt)

        q = q.order_by(CallHistory.timestamp.desc())

        items, meta = paginate(q)

        data = [{
            "id": r.id,
            "number": r.number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "timestamp": iso(r.timestamp),
            "duration": r.duration,
            "name": r.name,
            "created_at": iso(r.created_at),
        } for r in items]

        return jsonify({
            "user_id": user_id,
            "total": meta["total"],
            "call_history": data,
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

        data = [{
            "id": r.id,
            "number": r.number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "timestamp": iso(r.timestamp),
            "duration": r.duration,
            "name": r.name,
            "created_at": iso(r.created_at)
        } for r in items]

        # summary
        total_calls = db.session.query(func.count(CallHistory.id)).filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).scalar()

        total_duration = db.session.query(func.coalesce(func.sum(CallHistory.duration), 0)).filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).scalar()

        return jsonify({
            "user_id": user_id,
            "user_name": user.name,
            "total_calls": total_calls,
            "total_duration_seconds": int(total_duration),
            "call_history": data,
            "meta": meta
        }), 200

    except Exception as e:
        current_app.logger.exception("Failed admin_user_call_history")
        return jsonify({"error": str(e)}), 500

