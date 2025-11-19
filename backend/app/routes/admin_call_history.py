# app/routes/admin_call_history.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.models import db, User, CallHistory

bp = Blueprint("admin_call_history", __name__, url_prefix="/api/admin/call-history")

DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 200


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def iso(dt):
    if not dt:
        return None
    try:
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).isoformat()
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except:
        return str(dt)


def admin_required(fn):
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
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


# ---------------------------------------------------------
# 📌 ADMIN — VIEW ALL USERS' CALL HISTORY
# ---------------------------------------------------------
@bp.route("", methods=["GET"])
@jwt_required()
@admin_required
def admin_all_call_history():
    try:
        admin_id = int(get_jwt_identity())

        # Filters
        user_id = request.args.get("user_id", type=int)
        call_type = request.args.get("type", "all")
        search = request.args.get("search", "").strip()
        days = request.args.get("days", 30, type=int)

        from_date = datetime.utcnow() - timedelta(days=max(days, 0))

        # Base query restricted to admin users
        q = CallHistory.query.join(User).filter(User.admin_id == admin_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if user_id:
            q = q.filter(CallHistory.user_id == user_id)

        if call_type != "all":
            q = q.filter(CallHistory.call_type == call_type)

        if search:
            like = f"%{search}%"
            q = q.filter(
                (CallHistory.phone_number.ilike(like)) |
                (CallHistory.contact_name.ilike(like))
            )

        q = q.order_by(CallHistory.timestamp.desc())

        # Pagination
        items, meta = paginate(q)

        # Format for frontend
        data = [{
            "id": r.id,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else None,

            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,
            "contact_name": r.contact_name,

            "call_type": r.call_type,
            "duration": r.duration,
            "timestamp": iso(r.timestamp),
            "created_at": iso(r.created_at)
        } for r in items]

        # Summary Counts
        total_calls = q.count()
        total_duration = db.session.query(func.coalesce(func.sum(CallHistory.duration), 0)).filter(
            CallHistory.user_id.in_(
                db.session.query(User.id).filter(User.admin_id == admin_id)
            )
        ).scalar()

        return jsonify({
            "admin_id": admin_id,
            "total_calls": total_calls,
            "total_duration_seconds": int(total_duration),
            "call_history": data,
            "meta": meta
        }), 200

    except Exception as e:
        current_app.logger.exception("admin_all_call_history failed")
        return jsonify({"error": str(e)}), 500
