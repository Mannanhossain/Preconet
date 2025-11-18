# app/routes/call_analytics.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, case
from app.models import db, User, Admin, CallHistory, Attendance

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

        admin_id = get_jwt_identity()
        try:
            admin_id = int(admin_id)
        except Exception:
            return jsonify({"error": "Invalid admin identity"}), 401

        admin = Admin.query.get(admin_id)
        if not admin or not getattr(admin, "is_active", True):
            return jsonify({"error": "Admin inactive"}), 403

        # get users under this admin
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

        # Global counts
        total_calls_q = db.session.query(func.count(CallHistory.id)).filter(CallHistory.user_id.in_(user_ids))
        incoming_q = db.session.query(func.count(CallHistory.id)).filter(CallHistory.user_id.in_(user_ids), CallHistory.call_type == "incoming")
        outgoing_q = db.session.query(func.count(CallHistory.id)).filter(CallHistory.user_id.in_(user_ids), CallHistory.call_type == "outgoing")
        missed_q = db.session.query(func.count(CallHistory.id)).filter(CallHistory.user_id.in_(user_ids), CallHistory.call_type == "missed")
        rejected_q = db.session.query(func.count(CallHistory.id)).filter(CallHistory.user_id.in_(user_ids), CallHistory.call_type == "rejected")
        total_duration_q = db.session.query(func.coalesce(func.sum(CallHistory.duration), 0)).filter(CallHistory.user_id.in_(user_ids))

        total_calls = int(total_calls_q.scalar() or 0)
        incoming = int(incoming_q.scalar() or 0)
        outgoing = int(outgoing_q.scalar() or 0)
        missed = int(missed_q.scalar() or 0)
        rejected = int(rejected_q.scalar() or 0)
        total_duration = int(total_duration_q.scalar() or 0)

        # Daily trend - last N days (default 7)
        days = parse_int_query("days", 7, min_v=1, max_v=90)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days - 1)

        # Group by date
        # Note: use database date conversion. For portability we use func.date()
        trend_rows = db.session.query(
            func.date(CallHistory.timestamp).label("d"),
            func.count(CallHistory.id).label("cnt")
        ).filter(
            CallHistory.user_id.in_(user_ids),
            CallHistory.timestamp >= datetime.combine(start_date, datetime.min.time())
        ).group_by(func.date(CallHistory.timestamp)) \
         .order_by(func.date(CallHistory.timestamp)).all()

        # Build labels & values for all days in range
        labels = []
        values = []
        trend_map = {row.d: int(row.cnt) for row in trend_rows}
        for i in range(days):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime("%d %b"))
            values.append(trend_map.get(day, 0))

        # Per-user summary (incoming/outgoing/missed, total duration)
        # Use SQL aggregation joined with users to get names
        # We use conditional sum via case expressions for counts per type
        incoming_case = func.sum(case([(CallHistory.call_type == "incoming", 1)], else_=0))
        outgoing_case = func.sum(case([(CallHistory.call_type == "outgoing", 1)], else_=0))
        missed_case = func.sum(case([(CallHistory.call_type == "missed", 1)], else_=0))

        summary_rows = db.session.query(
            User.id.label("user_id"),
            User.name.label("user_name"),
            func.count(CallHistory.id).label("total_calls"),
            func.coalesce(func.sum(CallHistory.duration), 0).label("total_duration"),
            incoming_case.label("incoming"),
            outgoing_case.label("outgoing"),
            missed_case.label("missed")
        ).join(CallHistory, CallHistory.user_id == User.id) \
         .filter(User.id.in_(user_ids)) \
         .group_by(User.id, User.name) \
         .order_by(func.count(CallHistory.id).desc()) \
         .all()

        user_summary = []
        for r in summary_rows:
            user_summary.append({
                "user_id": int(r.user_id),
                "user_name": r.user_name,
                "incoming": int(r.incoming or 0),
                "outgoing": int(r.outgoing or 0),
                "missed": int(r.missed or 0),
                "total_calls": int(r.total_calls or 0),
                "total_duration": f"{int(r.total_duration or 0)}s"
            })

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
# Admin: get analytics for a single user (paginated)
# GET /api/admin/user-call-analytics/<user_id>
# -------------------------------------------------------
@bp.route("/admin/user-call-analytics/<int:user_id>", methods=["GET"])
@jwt_required()
def admin_user_call_analytics(user_id):
    try:
        if not admin_required():
            return jsonify({"error": "Admin access only"}), 403

        admin_id = get_jwt_identity()
        try:
            admin_id = int(admin_id)
        except Exception:
            return jsonify({"error": "Invalid admin identity"}), 401

        admin = Admin.query.get(admin_id)
        if not admin or not getattr(admin, "is_active", True):
            return jsonify({"error": "Admin inactive"}), 403

        user = User.query.get(user_id)
        if not user or user.admin_id != admin_id:
            return jsonify({"error": "Unauthorized (not your user)"}), 403

        # pagination
        page = parse_int_query("page", 1, min_v=1)
        per_page = parse_int_query("per_page", 25, min_v=1, max_v=200)

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

        # summary for range
        total_calls = db.session.query(func.count(CallHistory.id)).filter(
            CallHistory.user_id == user_id,
            CallHistory.timestamp >= from_dt
        ).scalar() or 0

        total_duration = db.session.query(func.coalesce(func.sum(CallHistory.duration), 0)).filter(
            CallHistory.user_id == user_id,
            CallHistory.timestamp >= from_dt
        ).scalar() or 0

        return jsonify({
            "user_id": user_id,
            "user_name": user.name,
            "performance": user.performance_score,
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
# User: my call analytics (paginated)
# GET /api/user/my-call-analytics
# -------------------------------------------------------
@bp.route("/user/my-call-analytics", methods=["GET"])
@jwt_required()
def user_my_call_analytics():
    try:
        user_id = get_jwt_identity()
        try:
            user_id = int(user_id)
        except Exception:
            return jsonify({"error": "Invalid identity"}), 401

        page = parse_int_query("page", 1, min_v=1)
        per_page = parse_int_query("per_page", 25, min_v=1, max_v=200)
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

        user = User.query.get(user_id)

        return jsonify({
            "user_id": user_id,
            "performance": getattr(user, "performance_score", None),
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
