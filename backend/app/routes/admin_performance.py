# app/routes/admin_performance.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, and_, or_, case
from datetime import datetime, timedelta

from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_performance", __name__, url_prefix="/api/admin")


# ---------------------------
# Helper: Date Range Filter
# ---------------------------
def get_date_range(filter_type):
    today = datetime.now().date()

    if filter_type == "today":
        start = today
        end = today + timedelta(days=1)

    elif filter_type == "week":
        start = today - timedelta(days=7)
        end = today + timedelta(days=1)

    elif filter_type == "month":
        start = today - timedelta(days=30)
        end = today + timedelta(days=1)

    else:
        start = datetime(2000, 1, 1).date()
        end = today + timedelta(days=1)

    # Convert to timestamp
    start_ts = int(datetime.combine(start, datetime.min.time()).timestamp())
    end_ts = int(datetime.combine(end, datetime.min.time()).timestamp())

    return start_ts, end_ts


# ---------------------------
# GET /api/admin/performance
# ---------------------------
@bp.route("/performance", methods=["GET"])
@jwt_required()
def performance():
    try:
        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin:
            return jsonify({"error": "Unauthorized"}), 401

        # Load filter
        filter_type = request.args.get("filter", "today")
        start_ts, end_ts = get_date_range(filter_type)

        # CASE expressions
        incoming_case = case((CallHistory.call_type == "incoming", 1), else_=0)
        outgoing_case = case((CallHistory.call_type == "outgoing", 1), else_=0)
        missed_case = case((CallHistory.call_type == "missed", 1), else_=0)
        rejected_case = case((CallHistory.call_type == "rejected", 1), else_=0)

        # USER PERFORMANCE
        user_data = (
            db.session.query(
                User.id,
                User.name,
                func.count(CallHistory.id).label("total_calls"),
                func.sum(CallHistory.duration).label("total_duration"),
                func.sum(incoming_case).label("incoming"),
                func.sum(outgoing_case).label("outgoing"),
                func.sum(missed_case).label("missed"),
                func.sum(rejected_case).label("rejected"),
            )
            .outerjoin(CallHistory, CallHistory.user_id == User.id)
            .filter(
                User.admin_id == admin_id,
                or_(
                    CallHistory.timestamp == None,
                    and_(CallHistory.timestamp >= start_ts,
                         CallHistory.timestamp < end_ts)
                )
            )
            .group_by(User.id)
            .all()
        )

        # Format response
        users_list = []
        for u in user_data:
            users_list.append({
                "user_id": u.id,
                "user_name": u.name,
                "total_calls": int(u.total_calls or 0),
                "total_duration_sec": int(u.total_duration or 0),
                "incoming": int(u.incoming or 0),
                "outgoing": int(u.outgoing or 0),
                "missed": int(u.missed or 0),
                "rejected": int(u.rejected or 0),
            })

        summary = {
            "total_calls": sum(u["total_calls"] for u in users_list),
            "total_duration_sec": sum(u["total_duration_sec"] for u in users_list),
            "total_users": len(users_list),
            "filter": filter_type
        }

        return jsonify({
            "summary": summary,
            "users": users_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
