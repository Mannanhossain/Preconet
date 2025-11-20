# app/routes/admin_call_analytics.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from sqlalchemy import func, case
from app.models import db, User, Admin, CallHistory

bp = Blueprint("admin_call_analytics", __name__, url_prefix="/api/admin")


# ----------------------------- HELPERS -----------------------------
def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


def iso(dt):
    try:
        return dt.isoformat() if dt else None
    except:
        return str(dt)


def parse_int(name, default, min_v=None, max_v=None):
    try:
        v = int(request.args.get(name, default))
    except:
        v = default

    if min_v is not None:
        v = max(v, min_v)
    if max_v is not None:
        v = min(v, max_v)

    return v


# ===================================================================
# ADMIN – GLOBAL CALL ANALYTICS
# GET /api/admin/call-analytics
# ===================================================================
@bp.route("/call-analytics", methods=["GET"])
@jwt_required()
def admin_call_analytics():
    try:
        if not admin_required():
            return jsonify({"error": "Admin access only"}), 403

        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)

        if not admin or not admin.is_active:
            return jsonify({"error": "Admin inactive"}), 403

        # Get all users belonging to admin
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

        base = CallHistory.query.filter(CallHistory.user_id.in_(user_ids))

        # --------- GLOBAL COUNTS ---------
        total_calls = base.count()
        incoming = base.filter(CallHistory.call_type == "incoming").count()
        outgoing = base.filter(CallHistory.call_type == "outgoing").count()
        missed = base.filter(CallHistory.call_type == "missed").count()
        rejected = base.filter(CallHistory.call_type == "rejected").count()

        total_duration = base.with_entities(
            func.coalesce(func.sum(CallHistory.duration), 0)
        ).scalar() or 0

        # --------- TREND LAST X DAYS ---------
        days = parse_int("days", 7, min_v=1, max_v=90)

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
        ).order_by(
            func.date(CallHistory.timestamp)
        ).all()

        trend_map = {row[0]: row[1] for row in trend_rows}

        labels = [(start + timedelta(days=i)).strftime("%d %b") for i in range(days)]
        values = [trend_map.get(start + timedelta(days=i), 0) for i in range(days)]

        # --------- USER SUMMARY ---------
        incoming_case = func.sum(case((CallHistory.call_type == "incoming", 1), else_=0))
        outgoing_case = func.sum(case((CallHistory.call_type == "outgoing", 1), else_=0))
        missed_case = func.sum(case((CallHistory.call_type == "missed", 1), else_=0))

        summary = db.session.query(
            User.id,
            User.name,
            incoming_case,
            outgoing_case,
            missed_case,
            func.sum(func.coalesce(CallHistory.duration, 0)),
            func.count(CallHistory.id)
        ).outerjoin(
            CallHistory, CallHistory.user_id == User.id
        ).filter(
            User.id.in_(user_ids)
        ).group_by(
            User.id, User.name
        ).order_by(
            func.count(CallHistory.id).desc()
        ).all()

        result = [{
            "user_id": r[0],
            "user_name": r[1],
            "incoming": int(r[2] or 0),
            "outgoing": int(r[3] or 0),
            "missed": int(r[4] or 0),
            "total_duration": f"{int(r[5] or 0)}s",
            "total_calls": int(r[6] or 0)
        } for r in summary]

        return jsonify({
            "total_calls": total_calls,
            "incoming": incoming,
            "outgoing": outgoing,
            "missed": missed,
            "rejected": rejected,
            "total_duration": total_duration,
            "daily_series": {"labels": labels, "values": values},
            "user_summary": result
        }), 200

    except Exception as e:
        current_app.logger.exception("call_analytics error")
        return jsonify({"error": str(e)}), 500


# ===================================================================
# ADMIN – PER USER ANALYTICS
# GET /api/admin/user-call-analytics/<user_id>
# ===================================================================
@bp.route("/user-call-analytics/<int:user_id>", methods=["GET"])
@jwt_required()
def admin_user_call_analytics(user_id):
    try:
        if not admin_required():
            return jsonify({"error": "Admin only"}), 403

        admin_id = int(get_jwt_identity())

        user = User.query.get(user_id)
        if not user or user.admin_id != admin_id:
            return jsonify({"error": "Unauthorized"}), 403

        days = parse_int("days", 30)
        page = parse_int("page", 1)
        per_page = parse_int("per_page", 25)

        from_dt = datetime.utcnow() - timedelta(days=days)

        q = CallHistory.query.filter(
            CallHistory.user_id == user_id,
            CallHistory.timestamp >= from_dt
        ).order_by(CallHistory.timestamp.desc())

        pag = q.paginate(page=page, per_page=per_page, error_out=False)

        items = [{
            "id": c.id,
            "phone_number": c.phone_number,
            "formatted_number": c.formatted_number,
            "contact_name": c.contact_name,
            "call_type": c.call_type,
            "duration": c.duration,
            "timestamp": iso(c.timestamp)
        } for c in pag.items]

        return jsonify({
            "user_id": user.id,
            "user_name": user.name,
            "records": items,
            "meta": {
                "page": pag.page,
                "per_page": pag.per_page,
                "total": pag.total,
                "pages": pag.pages
            }
        })

    except Exception as e:
        current_app.logger.exception("user_analytics error")
        return jsonify({"error": str(e)}), 500
