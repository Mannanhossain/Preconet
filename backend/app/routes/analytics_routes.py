# app/routes/call_analytics.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from sqlalchemy import func, case
from app.models import db, User, Admin, CallHistory

bp = Blueprint("call_analytics", __name__, url_prefix="/api")

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"

def iso(dt):
    if not dt:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)

def parse_int_query(name, default, min_v=None, max_v=None):
    try:
        v = int(request.args.get(name, default))
    except Exception:
        v = default
    if min_v is not None:
        v = max(min_v, v)
    if max_v is not None:
        v = min(max_v, v)
    return v


# -------------------------------------------------------
# Admin: aggregate call analytics across admin's users
# GET /api/admin/call-analytics
# -------------------------------------------------------
@bp.route("/admin/call-analytics", methods=["GET"])
@jwt_required()
def admin_call_analytics():
    try:
        if not admin_required():
            return jsonify({"error": "Admin access only"}), 403

        admin_id = int(get_jwt_identity())
        admin = Admin.query.get(admin_id)
        if not admin or not getattr(admin, "is_active", True):
            return jsonify({"error": "Admin inactive"}), 403

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

        # Global aggregation
        total_calls = db.session.query(func.count(CallHistory.id)) \
            .filter(CallHistory.user_id.in_(user_ids)).scalar() or 0
        incoming = db.session.query(func.count(CallHistory.id)) \
            .filter(CallHistory.user_id.in_(user_ids),
                    CallHistory.call_type == "incoming").scalar() or 0
        outgoing = db.session.query(func.count(CallHistory.id)) \
            .filter(CallHistory.user_id.in_(user_ids),
                    CallHistory.call_type == "outgoing").scalar() or 0
        missed = db.session.query(func.count(CallHistory.id)) \
            .filter(CallHistory.user_id.in_(user_ids),
                    CallHistory.call_type == "missed").scalar() or 0
        rejected = db.session.query(func.count(CallHistory.id)) \
            .filter(CallHistory.user_id.in_(user_ids),
                    CallHistory.call_type == "rejected").scalar() or 0
        total_duration = db.session.query(
            func.coalesce(func.sum(CallHistory.duration), 0)
        ).filter(CallHistory.user_id.in_(user_ids)).scalar() or 0

        # Trends
        days = parse_int_query("days", 7, min_v=1, max_v=90)
        end = datetime.utcnow().date()
        start = end - timedelta(days=days - 1)

        trend_rows = db.session.query(
            func.date(CallHistory.timestamp).label("d"),
            func.count(CallHistory.id)
        ).filter(
            CallHistory.user_id.in_(user_ids),
            CallHistory.timestamp >= datetime.combine(start, datetime.min.time())
        ).group_by(func.date(CallHistory.timestamp)) \
         .order_by(func.date(CallHistory.timestamp)).all()

        trend_map = {row[0]: row[1] for row in trend_rows}

        labels = [(start + timedelta(days=i)).strftime("%d %b") for i in range(days)]
        values = [trend_map.get(start + timedelta(days=i), 0) for i in range(days)]

        # Per-user summary
        incoming_case = func.sum(case([(CallHistory.call_type == "incoming", 1)], else_=0))
        outgoing_case = func.sum(case([(CallHistory.call_type == "outgoing", 1)], else_=0))
        missed_case = func.sum(case([(CallHistory.call_type == "missed", 1)], else_=0))

        summary_rows = db.session.query(
            User.id,
            User.name,
            func.count(CallHistory.id),
            func.coalesce(func.sum(CallHistory.duration), 0),
            incoming_case,
            outgoing_case,
            missed_case
        ).join(CallHistory, CallHistory.user_id == User.id) \
         .filter(User.id.in_(user_ids)) \
         .group_by(User.id, User.name) \
         .order_by(func.count(CallHistory.id).desc()).all()

        user_summary = [{
            "user_id": int(r[0]),
            "user_name": r[1],
            "incoming": int(r[4] or 0),
            "outgoing": int(r[5] or 0),
            "missed": int(r[6] or 0),
            "total_calls": int(r[2] or 0),
            "total_duration": f"{int(r[3] or 0)}s"
        } for r in summary_rows]

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
        current_app.logger.exception("admin_call_analytics error")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# Admin: User analytics (paginated)
# GET /api/admin/user-call-analytics/<user_id>
# -------------------------------------------------------
@bp.route("/admin/user-call-analytics/<int:user_id>", methods=["GET"])
@jwt_required()
def admin_user_call_analytics(user_id):
    try:
        if not admin_required():
            return jsonify({"error": "Admin access only"}), 403

        uid = int(get_jwt_identity())
        admin = Admin.query.get(uid)
        if not admin or not getattr(admin, "is_active", True):
            return jsonify({"error": "Admin inactive"}), 403

        user = User.query.get(user_id)
        if not user or user.admin_id != uid:
            return jsonify({"error": "Unauthorized"}), 403

        page = parse_int_query("page", 1)
        per_page = parse_int_query("per_page", 25)
        days = parse_int_query("days", 30, min_v=1, max_v=365)
        from_dt = datetime.utcnow() - timedelta(days=days)

        q = CallHistory.query.filter(
            CallHistory.user_id == user_id,
            CallHistory.timestamp >= from_dt
        ).order_by(CallHistory.timestamp.desc())

        pag = q.paginate(page=page, per_page=per_page, error_out=False)

        items = [{
            "id": c.id,
            "number": c.number,
            "formatted_number": getattr(c, "formatted_number", None),
            "name": getattr(c, "name", None),
            "call_type": c.call_type,
            "duration": c.duration,
            "timestamp": iso(c.timestamp),
            "created_at": iso(c.created_at)
        } for c in pag.items]

        total_calls = q.count()
        total_duration = db.session.query(
            func.coalesce(func.sum(CallHistory.duration), 0)
        ).filter(
            CallHistory.user_id == user_id,
            CallHistory.timestamp >= from_dt
        ).scalar() or 0

        return jsonify({
            "user_id": user_id,
            "user_name": user.name,
            "analytics": items,
            "meta": {
                "page": pag.page,
                "per_page": pag.per_page,
                "total": pag.total,
                "pages": pag.pages,
                "has_next": pag.has_next,
                "has_prev": pag.has_prev
            },
            "summary": {
                "total_calls": int(total_calls),
                "total_duration": int(total_duration)
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("admin_user_call_analytics error")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# User: My call analytics
# GET /api/user/my-call-analytics
# -------------------------------------------------------
@bp.route("/user/my-call-analytics", methods=["GET"])
@jwt_required()
def user_my_call_analytics():
    try:
        user_id = int(get_jwt_identity())

        page = parse_int_query("page", 1)
        per_page = parse_int_query("per_page", 25)
        days = parse_int_query("days", 30, min_v=1, max_v=365)

        from_dt = datetime.utcnow() - timedelta(days=days)

        q = CallHistory.query.filter(
            CallHistory.user_id == user_id,
            CallHistory.timestamp >= from_dt
        ).order_by(CallHistory.timestamp.desc())

        pag = q.paginate(page=page, per_page=per_page, error_out=False)

        items = [{
            "id": c.id,
            "number": c.number,
            "formatted_number": getattr(c, "formatted_number", None),
            "name": getattr(c, "name", None),
            "call_type": c.call_type,
            "duration": c.duration,
            "timestamp": iso(c.timestamp)
        } for c in pag.items]

        return jsonify({
            "user_id": user_id,
            "data": items,
            "meta": {
                "page": pag.page,
                "per_page": pag.per_page,
                "total": pag.total,
                "pages": pag.pages,
                "has_next": pag.has_next,
                "has_prev": pag.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.exception("user_my_call_analytics error")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------
# User: Sync analytics (Flutter calls this)
# POST /api/users/sync-analytics
# -------------------------------------------------------
@bp.route("/users/sync-analytics", methods=["POST"])
@jwt_required()
def user_sync_analytics():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        # You can store this data if needed — optional
        # For now only confirm success

        return jsonify({
            "success": True,
            "message": "Analytics synced successfully",
            "received": data
        }), 200

    except Exception as e:
        current_app.logger.exception("user_sync_analytics error")
        return jsonify({"error": str(e)}), 500
