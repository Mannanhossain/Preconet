from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, cast, Date
from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_call_analytics", __name__, url_prefix="/api/admin")


# ======================================================
# POST /api/admin/call-analytics/sync
# ======================================================
@bp.route("/call-analytics/sync", methods=["POST"])
@jwt_required()
def sync_call_analytics():
    admin_id = get_jwt_identity()

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Empty payload"}), 400

        print("📥 Received analytics sync:", data)

        return jsonify({"message": "Analytics synced successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================================
# GET /api/admin/call-analytics
# ======================================================
@bp.route("/call-analytics", methods=["GET"])
@jwt_required()
def get_call_analytics():
    try:
        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin:
            return jsonify({"error": "Unauthorized"}), 401

        # ======================================================
        # TOTAL CALLS (Admin-wise)
        # ======================================================

        total_incoming = (
            db.session.query(func.count())
            .select_from(CallHistory)
            .join(User, User.id == CallHistory.user_id)
            .filter(
                CallHistory.call_type == "incoming",
                User.admin_id == admin_id
            )
            .scalar() or 0
        )

        total_outgoing = (
            db.session.query(func.count())
            .select_from(CallHistory)
            .join(User, User.id == CallHistory.user_id)
            .filter(
                CallHistory.call_type == "outgoing",
                User.admin_id == admin_id
            )
            .scalar() or 0
        )

        total_missed = (
            db.session.query(func.count())
            .select_from(CallHistory)
            .join(User, User.id == CallHistory.user_id)
            .filter(
                CallHistory.call_type.in_(["missed", "rejected"]),
                User.admin_id == admin_id
            )
            .scalar() or 0
        )

        total_calls = (
            db.session.query(func.count())
            .select_from(CallHistory)
            .join(User, User.id == CallHistory.user_id)
            .filter(User.admin_id == admin_id)
            .scalar() or 0
        )

        total_duration = (
            db.session.query(func.coalesce(func.sum(CallHistory.duration), 0))
            .select_from(CallHistory)
            .join(User, User.id == CallHistory.user_id)
            .filter(User.admin_id == admin_id)
            .scalar() or 0
        )

        # ======================================================
        # DAILY TREND (Admin-wise)
        # ======================================================
        daily_trend = (
            db.session.query(
                cast(CallHistory.timestamp, Date).label("date"),
                func.count().label("count")
            )
            .select_from(CallHistory)
            .join(User, User.id == CallHistory.user_id)
            .filter(User.admin_id == admin_id)
            .group_by(cast(CallHistory.timestamp, Date))
            .order_by(cast(CallHistory.timestamp, Date))
            .all()
        )

        trend_list = [
            {"date": str(row.date), "count": int(row.count)}
            for row in daily_trend
        ]

        # ======================================================
        # USER-WISE SUMMARY (Admin-wise)
        # ======================================================
        users = (
            db.session.query(User.id, User.name)
            .filter(User.admin_id == admin_id)
            .all()
        )

        user_summary = []

        for user in users:

            incoming = (
                db.session.query(func.count())
                .filter(
                    CallHistory.user_id == user.id,
                    CallHistory.call_type == "incoming"
                )
                .scalar() or 0
            )

            outgoing = (
                db.session.query(func.count())
                .filter(
                    CallHistory.user_id == user.id,
                    CallHistory.call_type == "outgoing"
                )
                .scalar() or 0
            )

            missed = (
                db.session.query(func.count())
                .filter(
                    CallHistory.user_id == user.id,
                    CallHistory.call_type.in_(["missed", "rejected"])
                )
                .scalar() or 0
            )

            duration = (
                db.session.query(func.coalesce(func.sum(CallHistory.duration), 0))
                .filter(CallHistory.user_id == user.id)
                .scalar() or 0
            )

            user_summary.append({
                "user_id": user.id,
                "user_name": user.name,
                "incoming": incoming,
                "outgoing": outgoing,
                "missed": missed,
                "total_duration": duration
            })

        # ======================================================
        # RETURN RESPONSE TO FLUTTER
        # ======================================================
        return jsonify({
            "total_calls": total_calls,
            "incoming": total_incoming,
            "outgoing": total_outgoing,
            "missed": total_missed,
            "total_duration": total_duration,
            "daily_trend": trend_list,
            "user_summary": user_summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
