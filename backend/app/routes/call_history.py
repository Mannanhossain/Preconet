# app/routes/call_history.py
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from ..models import User, CallHistory, CallMetrics, Attendance  # adjust if your models live elsewhere

bp = Blueprint("call_history", __name__, url_prefix="/api/call-history")

# Pagination limits
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 200

# -------------------------
# Helpers
# -------------------------
def iso(dt):
    if dt is None:
        return None
    try:
        # return UTC ISO string
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).isoformat()
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        try:
            return dt.isoformat()
        except Exception:
            return str(dt)


def parse_datetime(value):
    """
    Accepts:
      - integer/float ms or seconds
      - ISO string (with or without Z / timezone)
    Returns naive UTC datetime or None
    """
    if value is None:
        return None
    # numeric
    if isinstance(value, (int, float)):
        v = int(value)
        if v > 10**10:
            return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)
    # string
    if isinstance(value, str):
        s = value.strip()
        # ISO (allow trailing Z)
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except Exception:
            pass
        # numeric-string fallback
        try:
            v = int(s)
            if v > 10**10:
                return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).replace(tzinfo=None)
            return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)
        except Exception:
            return None
    return None


def admin_required(fn):
    """Decorator: require JWT claim role==admin"""
    @wraps(fn)
    def wrapper(*a, **kw):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*a, **kw)
    return wrapper


def paginate(query):
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
        "has_prev": pag.has_prev,
    }
    return pag.items, meta


def calculate_performance(user_id):
    """
    Simple heuristic: attendance (60%) + call answered rate (40%).
    Keeps consistent with other modules.
    """
    total_att = db.session.query(func.count(Attendance.id)).filter_by(user_id=user_id).scalar() or 0
    ontime_att = db.session.query(func.count(Attendance.id)).filter(
        Attendance.user_id == user_id, Attendance.status == "on-time"
    ).scalar() or 0
    att_score = (ontime_att / total_att * 100) if total_att else 0

    total_calls = db.session.query(func.count(CallHistory.id)).filter_by(user_id=user_id).scalar() or 0
    answered = db.session.query(func.count(CallHistory.id)).filter(
        CallHistory.user_id == user_id, CallHistory.duration > 0
    ).scalar() or 0
    call_score = (answered / total_calls * 100) if total_calls else 0

    return round(att_score * 0.6 + call_score * 0.4, 2)


# -------------------------
# 1) SYNC CALL HISTORY (user -> server)
# -------------------------
@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_call_history():
    """
    Body example:
    {
      "sync_timestamp": <ms timestamp optional>,
      "call_history": [
        {"timestamp": <ms>, "number": "...", "formatted_number": "...", "call_type": "incoming|outgoing|missed", "duration": 12, "name": "..."},
        ...
      ],
      "metrics": { "total_calls": ..., "incoming_calls": ..., "total_duration": ..., "period_days": ... }  # optional
    }
    """
    try:
        user_identity = get_jwt_identity()
        try:
            user_id = int(user_identity)
        except Exception:
            return jsonify({"error": "Invalid user identity"}), 401

        user = User.query.get(user_id)
        if not user or not getattr(user, "is_active", True):
            return jsonify({"error": "User not found or inactive"}), 403

        payload = request.get_json(silent=True) or {}
        call_list = payload.get("call_history", [])
        metrics_payload = payload.get("metrics", {})

        sync_ts_ms = payload.get("sync_timestamp")
        sync_ts = parse_datetime(sync_ts_ms) if sync_ts_ms else datetime.utcnow()

        if not isinstance(call_list, list):
            return jsonify({"error": "'call_history' must be an array"}), 400

        saved = 0
        errors = []
        # Batch strategy: add to session, commit once at end to minimize transactions
        for entry in call_list:
            # validate minimal fields
            ts_raw = entry.get("timestamp")
            number = entry.get("number") or entry.get("phone_number")
            if not ts_raw or not number:
                # skip invalid entry but record error
                errors.append({"entry": entry, "error": "missing timestamp or number"})
                continue

            ts = parse_datetime(ts_raw)
            if not ts:
                errors.append({"entry": entry, "error": "invalid timestamp"})
                continue

            # Normalize: second precision
            ts_norm = ts.replace(microsecond=0)

            # Defensive extraction with types
            duration = entry.get("duration", 0)
            try:
                duration = int(duration or 0)
            except Exception:
                duration = 0

            call_type = entry.get("call_type", "unknown")
            formatted_number = entry.get("formatted_number") or entry.get("formattedNumber") or ""
            contact_name = entry.get("name") or entry.get("contact_name") or ""

            # Duplicate prevention: combine multiple fields to reduce false positives
            exists = CallHistory.query.filter_by(
                user_id=user_id,
                phone_number=number,
                timestamp=ts_norm,
                duration=duration,
                call_type=call_type
            ).first()

            if exists:
                continue

            rec = CallHistory(
                user_id=user_id,
                phone_number=number,
                formatted_number=formatted_number,
                call_type=call_type,
                timestamp=ts_norm,
                duration=duration,
                contact_name=contact_name,
                sync_timestamp=sync_ts
            )

            db.session.add(rec)
            saved += 1

        # Save metrics summary (optional)
        if metrics_payload and isinstance(metrics_payload, dict):
            try:
                cm = CallMetrics(
                    user_id=user_id,
                    total_calls=int(metrics_payload.get("total_calls", 0)),
                    incoming_calls=int(metrics_payload.get("incoming_calls", 0)),
                    outgoing_calls=int(metrics_payload.get("outgoing_calls", 0)),
                    missed_calls=int(metrics_payload.get("missed_calls", 0)),
                    rejected_calls=int(metrics_payload.get("rejected_calls", 0)),
                    total_duration=int(metrics_payload.get("total_duration", 0)),
                    period_days=int(metrics_payload.get("period_days", 0)),
                    sync_timestamp=sync_ts
                )
                db.session.add(cm)
            except Exception as e:
                current_app.logger.exception("Invalid metrics payload")
                # don't fail entire sync for metrics parsing error
                errors.append({"metrics_error": str(e)})

        # Commit once
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.exception("DB commit failed during call sync")
            return jsonify({"error": "DB error", "detail": str(e)}), 500

        # Update user metadata: last_sync and performance (best-effort)
        try:
            user.last_sync = datetime.utcnow()
            user.performance_score = calculate_performance(user.id)
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update user meta after call sync")
            # do not consider sync as failed; return partial success
            return jsonify({
                "message": "Partial success",
                "records_saved": saved,
                "errors": errors,
                "warning": "Failed to update user.last_sync or performance"
            }), 207

        return jsonify({"message": "Call history synced", "records_saved": saved, "errors": errors}), 200

    except Exception as e:
        current_app.logger.exception("Unhandled error in sync_call_history")
        db.session.rollback()
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------
# 2) USER — MY CALL HISTORY (paginated + filters)
# -------------------------
@bp.route("/my", methods=["GET"])
@jwt_required()
def my_call_history():
    """
    Query params:
      - days (int) default 30
      - call_type (all|incoming|outgoing|missed)
      - page, per_page
      - from (ISO or ms), to (ISO or ms)
    """
    try:
        user_id = int(get_jwt_identity())

        days = request.args.get("days", 30, type=int)
        call_type = request.args.get("call_type", "all")
        from_param = request.args.get("from")
        to_param = request.args.get("to")

        from_date = datetime.utcnow() - timedelta(days=max(0, days))

        q = CallHistory.query.filter(CallHistory.user_id == user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type and call_type != "all":
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
            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "timestamp": iso(r.timestamp),
            "duration": r.duration,
            "contact_name": r.contact_name,
            "created_at": iso(r.created_at)
        } for r in items]

        return jsonify({"user_id": user_id, "total": meta["total"], "call_history": data, "meta": meta}), 200

    except Exception as e:
        current_app.logger.exception("Failed in my_call_history")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------
# 3) ADMIN — USER CALL HISTORY (secure + paginated + ownership)
# -------------------------
@bp.route("/admin/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def admin_user_call_history(user_id):
    """
    Admin can fetch call history for *their* users only.
    Admin identity must match user's admin_id (ownership).
    """
    try:
        admin_identity = get_jwt_identity()
        try:
            admin_id = int(admin_identity)
        except Exception:
            return jsonify({"error": "Invalid admin identity"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # ownership check (assumes admin_id stored on User)
        if getattr(user, "admin_id", None) != admin_id:
            return jsonify({"error": "Unauthorized access to this user's data"}), 403

        days = request.args.get("days", 30, type=int)
        call_type = request.args.get("call_type", "all")
        from_param = request.args.get("from")
        to_param = request.args.get("to")
        from_date = datetime.utcnow() - timedelta(days=max(0, days))

        q = CallHistory.query.filter(CallHistory.user_id == user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type and call_type != "all":
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
            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "timestamp": iso(r.timestamp),
            "duration": r.duration,
            "contact_name": r.contact_name,
            "created_at": iso(r.created_at)
        } for r in items]

        # summary for requested range
        total_calls = db.session.query(func.count(CallHistory.id)).filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).scalar() or 0

        total_duration = db.session.query(func.coalesce(func.sum(CallHistory.duration), 0)).filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).scalar() or 0

        return jsonify({
            "user_id": user_id,
            "user_name": user.name,
            "total_calls": total_calls,
            "total_duration_seconds": int(total_duration),
            "call_history": data,
            "meta": meta
        }), 200

    except Exception as e:
        current_app.logger.exception("Failed in admin_user_call_history")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------
# 4) ADMIN — LATEST CALLS ACROSS USERS (secure, limited)
# -------------------------
@bp.route("/admin/latest", methods=["GET"])
@jwt_required()
@admin_required
def admin_latest_calls():
    """
    Returns recent calls across admin's users.
    Query params: days (default 7), limit (max 500)
    """
    try:
        admin_identity = get_jwt_identity()
        try:
            admin_id = int(admin_identity)
        except Exception:
            return jsonify({"error": "Invalid admin identity"}), 401

        days = request.args.get("days", 7, type=int)
        limit = request.args.get("limit", 200, type=int)
        limit = max(1, min(limit, 500))

        from_date = datetime.utcnow() - timedelta(days=max(0, days))

        # join with user to enforce ownership and fetch name in same query
        records = (db.session.query(CallHistory)
                   .join(User, CallHistory.user_id == User.id)
                   .filter(User.admin_id == admin_id, CallHistory.created_at >= from_date)
                   .order_by(CallHistory.timestamp.desc())
                   .limit(limit)
                   .all())

        data = [{
            "user_id": r.user_id,
            "user_name": getattr(r.user, "name", "Unknown"),
            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "timestamp": iso(r.timestamp),
            "duration": r.duration,
            "created_at": iso(r.created_at)
        } for r in records]

        return jsonify({"total": len(data), "latest_calls": data}), 200

    except Exception as e:
        current_app.logger.exception("Failed in admin_latest_calls")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500
