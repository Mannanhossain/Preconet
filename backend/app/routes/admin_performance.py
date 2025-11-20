# app/routes/admin_performance.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_performance", __name__, url_prefix="/api/admin")


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

    else:  # default = month
        start = today - timedelta(days=30)
        end = today + timedelta(days=1)

    return start, end


@bp.route("/performance", methods=["GET"])
@jwt_required()
def performance():
    admin_id = get_jwt_identity()

    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    filter_type = request.args.get("range", "today")
    start, end = get_date_range(filter_type)

    # -------------------------------
    # User-wise performance summary
    # -------------------------------
    data = (
        db.session.query(
            User.id,
            User.name,
            func.count(CallHistory.id).label("total_calls"),
            func.sum(
                func.case(
                    [(CallHistory.call_type == "outgoing", 1)], else_=0
                )
            ).label("total_outgoing"),
            func.sum(
                func.case(
                    [(CallHistory.call_type == "incoming", 1)], else_=0
                )
            ).label("total_incoming"),
            func.sum(
                func.case(
                    [(CallHistory.call_type == "missed", 1)], else_=0
                )
            ).label("total_missed"),
        )
        .join(CallHistory, CallHistory.user_id == User.id)
        .filter(
            and_(
                CallHistory.timestamp >= start,
                CallHistory.timestamp < end
            )
        )
        .group_by(User.id)
        .all()
    )

    results = [
        {
            "user_id": r[0],
            "name": r[1],
            "total_calls": r[2],
            "incoming": r[4],
            "outgoing": r[3],
            "missed": r[5]
        }
        for r in data
    ]

    return jsonify({
        "range": filter_type,
        "results": results
    })
