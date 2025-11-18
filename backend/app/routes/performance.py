from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from ..models import User

performance_bp = Blueprint("admin_performance", __name__, url_prefix="/api/admin")


# ----------------------------
# Admin access check helper
# ----------------------------
def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


# ==========================================================
#  🔥 ADMIN — PERFORMANCE ANALYTICS
# ==========================================================
@performance_bp.route("/performance", methods=["GET"])
@jwt_required()
def admin_performance():
    # Reject non-admins
    if not admin_required():
        return jsonify({"error": "Admin only"}), 403

    admin_id = int(get_jwt_identity())

    # Fetch all users belonging to this admin
    users = (
        User.query
        .filter_by(admin_id=admin_id)
        .order_by(User.performance_score.desc())
        .limit(50)  # safety limit
        .all()
    )

    labels = [u.name for u in users]
    values = [round(u.performance_score, 2) for u in users]

    return jsonify({
        "labels": labels,
        "values": values,
        "count": len(users)
    }), 200
