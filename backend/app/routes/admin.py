from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, Admin, User
from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# 🟢 ADMIN DASHBOARD STATS
@bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def admin_dashboard_stats():
    try:
        current_admin_id = get_jwt_identity()
        admin = Admin.query.get(int(current_admin_id))

        if not admin:
            return jsonify({"error": "Unauthorized"}), 401

        # Count users created by this admin
        total_users = User.query.filter_by(admin_id=admin.id).count()
        active_users = User.query.filter_by(admin_id=admin.id, is_active=True).count()
        expired_users = User.query.filter(
            User.admin_id == admin.id,
            User.expiry_date < datetime.utcnow()
        ).count()

        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "expired_users": expired_users,
            "user_limit": admin.user_limit,
            "expiry_date": admin.expiry_date.isoformat()
        }

        return jsonify({"stats": stats}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
