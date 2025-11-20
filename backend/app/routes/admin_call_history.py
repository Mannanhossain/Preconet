# app/routes/admin_all_call_history.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func
from app.models import db, User, CallHistory

bp = Blueprint("admin_all_call_history", __name__, url_prefix="/api/admin")


def admin_required(fn):
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


@bp.route("/all-call-history", methods=["GET"])
@jwt_required()
@admin_required
def all_call_history():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))

        query = (
            db.session.query(CallHistory, User)
            .join(User, CallHistory.user_id == User.id)
            .order_by(CallHistory.timestamp.desc())
        )

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        data = []
        for rec, user in paginated.items:
            data.append({
                "id": rec.id,
                "user_id": rec.user_id,
                "user_name": user.name,
                "phone_number": rec.phone_number,
                "formatted_number": rec.formatted_number,
                "contact_name": rec.contact_name,
                "call_type": rec.call_type,
                "duration": rec.duration,
                "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
                "created_at": rec.created_at.isoformat() if rec.created_at else None,
            })

        return jsonify({
            "call_history": data,
            "meta": {
                "page": paginated.page,
                "per_page": paginated.per_page,
                "total": paginated.total,
                "pages": paginated.pages,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev,
            }
        })

    except Exception as e:
        return jsonify({"error": "Internal error", "detail": str(e)}), 500
