# app/routes/admin_call_history.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models import db, User, CallHistory

bp = Blueprint("admin_call_history", __name__, url_prefix="/api/admin/call-history")


# --------------------------------------------------
# Require Admin Role
# --------------------------------------------------
def admin_required(fn):
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# --------------------------------------------------
# Pagination Helper
# --------------------------------------------------
def paginate(query):
    page = int(request.args.get("page", 1))
    per_page = min(200, max(1, int(request.args.get("per_page", 25))))
    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    return pag.items, {
        "page": pag.page,
        "pages": pag.pages,
        "total": pag.total,
        "has_next": pag.has_next
    }


# --------------------------------------------------
#  ADMIN → VIEW USER CALL HISTORY
# --------------------------------------------------
@bp.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def admin_user_calls(user_id):
    admin_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Ensure user belongs to admin
    if user.admin_id != admin_id:
        return jsonify({"error": "Unauthorized"}), 403

    days = int(request.args.get("days", 30))
    from_date = datetime.utcnow() - timedelta(days=days)

    q = CallHistory.query.filter(
        CallHistory.user_id == user_id,
        CallHistory.created_at >= from_date
    ).order_by(CallHistory.timestamp.desc())

    items, meta = paginate(q)

    # summary data
    total_calls = q.count()
    total_duration = db.session.query(
        func.coalesce(func.sum(CallHistory.duration), 0)
    ).filter(
        CallHistory.user_id == user_id,
        CallHistory.created_at >= from_date
    ).scalar()

    return jsonify({
        "user_id": user_id,
        "user_name": user.name,
        "total_calls": total_calls,
        "total_duration_seconds": int(total_duration or 0),
        "call_history": [item.to_dict() for item in items],
        "meta": meta
    }), 200
