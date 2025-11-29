# app/routes/admin_call_analytics.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, cast, Date, case, and_
from app.models import db, CallHistory, User, Admin

bp = Blueprint("admin_call_analytics", __name__, url_prefix="/api/admin")


def _get_time_bounds(filter_type: str):
    """Return (start_time, end_time) in UTC naive datetimes or (None, None) if no filter."""
    now = datetime.utcnow()
    if not filter_type:
        return None, None

    if filter_type == "today":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
        return start, end

    if filter_type == "week":
        start = now - timedelta(days=7)
        return start, None

    if filter_type == "month":
        start = now - timedelta(days=30)
        return start, None

    return None, None


@bp.route("/call-analytics/sync", methods=["POST"])
@jwt_required()
def sync_call_analytics():
    admin_id = get_jwt_identity()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Empty payload"}), 400

        # Temporary debug/logging — keep or remove as desired
        current_app = None
        try:
            # avoid importing current_app at top; keep robust if not available
            from flask import current_app as _ca
            current_app = _ca
        except:
            current_app = None

        if current_app:
            current_app.logger.debug("📥 Received analytics sync: %s", data)

        return jsonify({"message": "Analytics synced successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/call-analytics", methods=["GET"])
@jwt_required()
def get_call_analytics():
    try:
        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({"error": "Unauthorized"}), 401

        # read filter param: today | week | month
        filter_type = request.args.get("filter", None)
        start_time, end_time = _get_time_bounds(filter_type or "")

        # base join condition for admin users
        user_join_condition = User.id == CallHistory.user_id
        admin_filter = User.admin_id == admin_id

        # build common time filter expression
        time_filters = []
        if start_time:
            time_filters.append(CallHistory.timestamp >= start_time)
        if end_time:
            time_filters.append(CallHistory.timestamp < end_time)

        # ======================================================
        # TOTALS (single aggregated queries)
        # ======================================================

        totals_q = (
            db.session.query(
                func.count().label("total_calls"),
                func.coalesce(func.sum(case([(CallHistory.call_type == "incoming", 1)], else_=0)), 0).label("incoming"),
                func.coalesce(func.sum(case([(CallHistory.call_type == "outgoing", 1)], else_=0)), 0).label("outgoing"),
                func.coalesce(func.sum(case([(CallHistory.call_type.in_(["missed", "rejected"]), 1)], else_=0)), 0).label("missed"),
                func.coalesce(func.sum(CallHistory.duration), 0).label("total_duration")
            )
            .select_from(CallHistory)
            .join(User, user_join_condition)
            .filter(admin_filter)
        )

        if time_filters:
            totals_q = totals_q.filter(and_(*time_filters))

        totals_row = totals_q.one()

        total_calls = int(totals_row.total_calls or 0)
        total_incoming = int(totals_row.incoming or 0)
        total_outgoing = int(totals_row.outgoing or 0)
        total_missed = int(totals_row.missed or 0)
        total_duration = int(totals_row.total_duration or 0)

        # ======================================================
        # DAILY TREND
        # ======================================================
        daily_q = (
            db.session.query(
                cast(CallHistory.timestamp, Date).label("date"),
                func.count().label("count")
            )
            .select_from(CallHistory)
            .join(User, user_join_condition)
            .filter(admin_filter)
        )

        if time_filters:
            daily_q = daily_q.filter(and_(*time_filters))

        daily_q = daily_q.group_by(cast(CallHistory.timestamp, Date)).order_by(cast(CallHistory.timestamp, Date))
        daily_trend = [{"date": str(row.date), "count": int(row.count)} for row in daily_q.all()]

        # ======================================================
        # USER-WISE SUMMARY (single aggregated query)
        # ======================================================
        # We produce for each user: incoming_count, outgoing_count, missed_count, total_duration
        user_agg_q = (
            db.session.query(
                User.id.label("user_id"),
                User.name.label("user_name"),
                func.coalesce(func.sum(case([(and_(CallHistory.call_type == "incoming"), 1)], else_=0)), 0).label("incoming"),
                func.coalesce(func.sum(case([(and_(CallHistory.call_type == "outgoing"), 1)], else_=0)), 0).label("outgoing"),
                func.coalesce(func.sum(case([(and_(CallHistory.call_type.in_(["missed", "rejected"])), 1)], else_=0)), 0).label("missed"),
                func.coalesce(func.sum(CallHistory.duration), 0).label("total_duration")
            )
            .select_from(User)
            .outerjoin(CallHistory, CallHistory.user_id == User.id)
            .filter(User.admin_id == admin_id)
            .group_by(User.id, User.name)
        )

        # apply time filters to the callhistory side using correlated conditions
        if time_filters:
            # join uses CallHistory table alias; apply time restrictions by adding conditions to the query.
            # SQLAlchemy will place these in WHERE (applies to outerjoin as well; users without calls will still appear due to outerjoin).
            user_agg_q = user_agg_q.filter(or_(CallHistory.id == None, and_(*time_filters)))

        user_summary_rows = user_agg_q.all()

        user_summary = []
        for row in user_summary_rows:
            user_summary.append({
                "user_id": int(row.user_id),
                "user_name": row.user_name,
                "incoming": int(row.incoming or 0),
                "outgoing": int(row.outgoing or 0),
                "missed": int(row.missed or 0),
                "total_duration": int(row.total_duration or 0)
            })

        # ======================================================
        # RETURN RESPONSE
        # ======================================================
        return jsonify({
            "total_calls": total_calls,
            "incoming": total_incoming,
            "outgoing": total_outgoing,
            "missed": total_missed,
            "total_duration": total_duration,
            "daily_trend": daily_trend,
            "user_summary": user_summary
        }), 200

    except Exception as e:
        # avoid leaking DB internals in production; returning message here for debugging
        return jsonify({"error": str(e)}), 500
