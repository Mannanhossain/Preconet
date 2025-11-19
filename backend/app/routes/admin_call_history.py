# app/routes/admin_call_history.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models import User, CallHistory

bp = Blueprint("admin_call_history", __name__, url_prefix="/api/admin/call-history")


# -----------------------
# Admin Access Required
# -----------------------
def admin_required():
    return get_jwt().get("role") == "admin"


# -----------------------
# Admin — Get All Call History (All Users)
# -----------------------
@bp.route("", methods=["GET"])
@jwt_required()
def get_all_call_history():
    if not admin_required():
        return jsonify({"error": "Admin access only"}), 403

    admin_id = int(get_jwt_identity())

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    call_type = request.args.get("type", "all")

    # Get all users of this admin
    user_ids = [u.id for u in User.query.filter_by(admin_id=admin_id).all()]

    q = CallHistory.query.filter(CallHistory.user_id.in_(user_ids))

    # Filter by call type
    if call_type != "all":
        q = q.filter(CallHistory.call_type == call_type)

    q = q.order_by(CallHistory.timestamp.desc())

    pag = q.paginate(page=page, per_page=per_page, error_out=False)

    results = []
    for r in pag.items:
        user = User.query.get(r.user_id)
        results.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user.name if user else None,
            "phone_number": r.number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "duration": r.duration,
            "contact_name": r.name,
            "timestamp": r.timestamp.isoformat(),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return jsonify({
        "call_history": results,
        "meta": {
            "page": pag.page,
            "per_page": pag.per_page,
            "total": pag.total,
            "pages": pag.pages,
            "has_next": pag.has_next,
            "has_prev": pag.has_prev
        }
    }), 200
