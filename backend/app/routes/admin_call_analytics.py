# app/routes/admin_call_analytics_sync.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_call_analytics_sync", __name__, url_prefix="/api/admin")


@bp.route("/call-analytics/sync", methods=["POST"])
@jwt_required()
def admin_call_analytics_sync():
    try:
        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin:
            return jsonify({"error": "Unauthorized"}), 401

        # You don't need request body — analytics are auto-generated
        # But we accept body for future flexibility
        req_data = request.get_json() or {}

        # Total call statistics
        total_incoming = db.session.query(func.count()).filter(
            CallHistory.call_type == "incoming"
        ).scalar() or 0

        total_outgoing = db.session.query(func.count()).filter(
            CallHistory.call_type == "outgoing"
        ).scalar() or 0

        total_missed = db.session.query(func.count()).filter(
            CallHistory.call_type == "missed"
        ).scalar() or 0

        total_calls = db.session.query(func.count()).select_from(CallHistory).scalar() or 0

        total_duration = db.session.query(
            func.coalesce(func.sum(CallHistory.duration), 0)
        ).scalar() or 0

        # User-wise summary
        users = (
            db.session.query(
                User.id,
                User.name,
                func.count(CallHistory.id).label("total_calls"),
                func.coalesce(func.sum(CallHistory.duration), 0).label("total_duration")
            )
            .outerjoin(CallHistory, CallHistory.user_id == User.id)
            .filter(User.admin_id == admin_id)
            .group_by(User.id)
            .all()
        )

        user_summary = [
            {
                "user_id": u.id,
                "user_name": u.name,
                "total_calls": int(u.total_calls or 0),
                "total_duration": f"{int(u.total_duration or 0)}s"
            }
            for u in users
        ]

        return jsonify({
            "message": "Analytics generated successfully",
            "request_received": req_data,   # for debugging only
            "analytics": {
                "total_calls": total_calls,
                "incoming": total_incoming,
                "outgoing": total_outgoing,
                "missed": total_missed,
                "total_duration": total_duration,
                "user_summary": user_summary
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
