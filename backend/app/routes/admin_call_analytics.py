# app/routes/admin_call_analytics.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_call_analytics", __name__, url_prefix="/api/admin")

# -------------------------
# Admin Call Analytics API
# -------------------------
@bp.route("/call-analytics", methods=["GET"])
@jwt_required()
def call_analytics():
    admin_id = get_jwt_identity()

    # Ensure admin exists
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    # --------- TOTAL COUNTS ----------
    total_incoming = db.session.query(func.count()).filter(CallHistory.call_type == "incoming").scalar()
    total_outgoing = db.session.query(func.count()).filter(CallHistory.call_type == "outgoing").scalar()
    total_missed   = db.session.query(func.count()).filter(CallHistory.call_type == "missed").scalar()
    total_calls    = db.session.query(func.count()).select_from(CallHistory).scalar()

    # --------- TREND DATA (Last 7 days) ----------
    trend = (
        db.session.query(
            func.date(CallHistory.timestamp),
            func.count()
        )
        .group_by(func.date(CallHistory.timestamp))
        .order_by(func.date(CallHistory.timestamp))
        .limit(7)
        .all()
    )

    trend_data = [
        {"date": str(row[0]), "count": row[1]}
        for row in trend
    ]

    # --------- USER SUMMARY ----------
    user_summary = (
        db.session.query(
            User.id,
            User.name,
            func.count(CallHistory.id)
        )
        .join(CallHistory, CallHistory.user_id == User.id)
        .group_by(User.id)
        .all()
    )

    user_rows = [
        {"user_id": u[0], "name": u[1], "total_calls": u[2]}
        for u in user_summary
    ]

    return jsonify({
        "total_incoming": total_incoming,
        "total_outgoing": total_outgoing,
        "total_missed": total_missed,
        "total_calls": total_calls,
        "trend": trend_data,
        "user_summary": user_rows
    })
