# app/routes/admin_call_analytics.py
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func, case
from datetime import datetime, timedelta

from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_call_analytics", __name__, url_prefix="/api/admin")


# -----------------------------
# Helper: check admin
# -----------------------------
def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


# -----------------------------
# ADMIN - CALL ANALYTICS
# GET /api/admin/call-analytics
# -----------------------------
@bp.route("/call-analytics", methods=["GET"])
@jwt_required()
def call_analytics():
    try:
        # Check admin
        if not admin_required():
            return jsonify({"error": "Admin access only"}), 403

        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin:
            return jsonify({"error": "Unauthorized"}), 401

        # Get admin users
        users = User.query.filter_by(admin_id=admin.id).all()
        user_ids = [u.id for u in users]

        if not user_ids:
            return jsonify({
                "total_calls": 0,
                "incoming": 0,
                "outgoing": 0,
                "missed": 0,
                "rejected": 0,
                "total_duration": 0,
                "daily_series": {"labels": [], "values": []},
                "user_summary": []
            }), 200

        # -----------------------------
        # GLOBAL TOTAL COUNTS
        # -----------------------------
        base = CallHistory.query.filter(CallHistory.user_id.in_(user_ids))

        total_calls = base.count()
        incoming = base.filter(CallHistory.call_type == "incoming").count()
        outgoing = base.filter(CallHistory.call_type == "outgoing").count()
        missed   = base.filter(CallHistory.call_type == "missed").count()
        rejected = base.filter(CallHistory.call_type == "rejected").count()

        total_duration = db.session.query(
            func.coalesce(func.sum(CallHistory.duration), 0)
        ).filter(CallHistory.user_id.in_(user_ids)).scalar() or 0

        # -----------------------------
        # TREND - LAST 7 DAYS
        # -----------------------------
        days = 7
        end = datetime.utcnow().date()
        start = end - timedelta(days=days - 1)

        trend_rows = db.session.query(
            func.date(CallHistory.timestamp),
            func.count(CallHistory.id)
        ).filter(
            CallHistory.user_id.in_(user_ids),
            CallHistory.timestamp >= datetime.combine(start, datetime.min.time())
        ).group_by(
            func.date(CallHistory.timestamp)
        ).order_by(func.date(CallHistory.timestamp)).all()

        trend_map = {row[0]: row[1] for row in trend_rows}

        labels = [(start + timedelta(days=i)).strftime("%d %b") for i in range(days)]
        values = [trend_map.get(start + timedelta(days=i), 0) for i in range(days)]

        # -----------------------------
        # USER SUMMARY
        # -----------------------------
        incoming_case = func.sum(case([(CallHistory.call_type == "incoming", 1)], else_=0))
        outgoing_case = func.sum(case([(CallHistory.call_type == "outgoing", 1)], else_=0))
        missed_case   = func.sum(case([(CallHistory.call_type == "missed", 1)], else_=0))

        summary_rows = db.session.query(
            User.id,
            User.name,
            incoming_case,
            outgoing_case,
            missed_case,
            func.coalesce(func.sum(CallHistory.duration), 0),
            func.count(CallHistory.id)
        ).outerjoin(
            CallHistory, CallHistory.user_id == User.id
        ).filter(
            User.id.in_(user_ids)
        ).group_by(
            User.id, User.name
        ).order_by(func.count(CallHistory.id).desc()).all()

        user_summary = [{
            "user_id": r[0],
            "user_name": r[1],
            "incoming": int(r[2] or 0),
            "outgoing": int(r[3] or 0),
            "missed": int(r[4] or 0),
            "total_duration": f"{int(r[5] or 0)}s",
            "total_calls": int(r[6] or 0)
        } for r in summary_rows]

        # -----------------------------
        # FINAL OUTPUT
        # -----------------------------
        return jsonify({
            "total_calls": total_calls,
            "incoming": incoming,
            "outgoing": outgoing,
            "missed": missed,
            "rejected": rejected,
            "total_duration": total_duration,
            "daily_series": {"labels": labels, "values": values},
            "user_summary": user_summary
        }), 200

    except Exception as e:
        current_app.logger.exception("call_analytics error")
        return jsonify({"error": str(e)}), 500
