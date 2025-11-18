from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from extensions import db
from ..models import User, CallHistory, Attendance
from sqlalchemy import func

analytics_bp = Blueprint("analytics", __name__)


# ------------------------------------------------
# Helper Functions
# ------------------------------------------------
def iso(dt):
    if not dt:
        return None
    try:
        return dt.isoformat()
    except:
        return str(dt)


def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


def calculate_performance(user_id):
    """ Heuristic performance calculation (attendance + calls) """

    # Attendance performance
    total_att = db.session.query(func.count(Attendance.id)).filter_by(user_id=user_id).scalar() or 0
    on_time = db.session.query(func.count(Attendance.id)).filter(
        Attendance.user_id == user_id,
        Attendance.status == "on-time"
    ).scalar() or 0
    att_score = (on_time / total_att * 100) if total_att else 0

    # Call performance
    total_calls = db.session.query(func.count(CallHistory.id)).filter_by(user_id=user_id).scalar() or 0
    answered = db.session.query(func.count(CallHistory.id)).filter(
        CallHistory.user_id == user_id,
        CallHistory.duration > 0
    ).scalar() or 0
    call_score = (answered / total_calls * 100) if total_calls else 0

    return round(att_score * 0.6 + call_score * 0.4, 2)


def paginate(query, serializer):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except:
        page = 1

    try:
        per_page = min(200, max(10, int(request.args.get("per_page", 25))))
    except:
        per_page = 25

    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [serializer(i) for i in result.items],
        "meta": {
            "page": result.page,
            "per_page": result.per_page,
            "total": result.total,
            "pages": result.pages,
            "has_next": result.has_next,
        }
    }


# ------------------------------------------------
# 1️⃣ USER SYNC CALL HISTORY
# ------------------------------------------------
@analytics_bp.route("/api/user/sync-call-history", methods=["POST"])
@jwt_required()
def sync_call_history():
    try:
        user_id = get_jwt_identity()
        data = request.json or {}

        call_list = data.get("call_history", [])
        sync_raw = data.get("sync_timestamp") or (datetime.utcnow().timestamp() * 1000)
        sync_dt = datetime.fromtimestamp(sync_raw / 1000)

        saved = 0

        for item in call_list:
            ts_raw = item.get("timestamp")
            number = item.get("number")

            if not ts_raw or not number:
                continue

            call_ts = datetime.fromtimestamp(ts_raw / 1000)

            # *** Duplicate Prevention ***
            exists = CallHistory.query.filter_by(
                user_id=user_id,
                timestamp=call_ts,
                phone_number=number
            ).first()

            if exists:
                continue

            call = CallHistory(
                user_id=user_id,
                phone_number=number,
                formatted_number=item.get("formatted_number", ""),
                call_type=item.get("call_type", "unknown"),
                timestamp=call_ts,
                duration=item.get("duration", 0),
                contact_name=item.get("name", ""),
                sync_timestamp=sync_dt,
            )

            db.session.add(call)
            saved += 1

        db.session.commit()

        # Update user last_sync
        user = User.query.get(user_id)
        user.last_sync = datetime.utcnow()
        user.performance_score = calculate_performance(user_id)
        db.session.commit()

        return jsonify({
            "message": "Call history synced",
            "calls_saved": saved
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------
# 2️⃣ USER SYNC ANALYTICS SUMMARY
# ------------------------------------------------
@analytics_bp.route("/api/user/sync-analytics", methods=["POST"])
@jwt_required()
def sync_analytics():
    try:
        user_id = get_jwt_identity()
        data = request.json or {}

        sync_raw = data.get("sync_timestamp")
        if not sync_raw:
            return jsonify({"error": "sync_timestamp missing"}), 400

        sync_dt = datetime.fromtimestamp(sync_raw / 1000)

        # Update user performance directly (no need to store separate analytics summary)
        user = User.query.get(user_id)
        user.last_sync = datetime.utcnow()
        user.performance_score = calculate_performance(user_id)

        db.session.commit()

        return jsonify({"message": "Analytics synced"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------
# 3️⃣ ADMIN — GET USER FULL ANALYTICS (SECURE)
# ------------------------------------------------
@analytics_bp.route("/api/admin/user-analytics/<int:user_id>", methods=["GET"])
@jwt_required()
def admin_user_analytics(user_id):
    if not admin_required():
        return jsonify({"error": "Admin only"}), 403

    admin_id = get_jwt_identity()

    user = User.query.get(user_id)
    if not user or user.admin_id != admin_id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        days = request.args.get("days", 30, type=int)
        from_date = datetime.utcnow() - timedelta(days=days)

        query = CallHistory.query.filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).order_by(CallHistory.created_at.desc())

        def serialize(c):
            return {
                "id": c.id,
                "number": c.phone_number,
                "name": c.contact_name,
                "duration": c.duration,
                "call_type": c.call_type,
                "timestamp": iso(c.timestamp),
                "created_at": iso(c.created_at),
            }

        paginated = paginate(query, serialize)

        # summary
        total_calls = db.session.query(func.count(CallHistory.id)).filter_by(user_id=user_id).scalar() or 0
        total_duration = db.session.query(func.sum(CallHistory.duration)).filter_by(user_id=user_id).scalar() or 0

        return jsonify({
            "user_id": user_id,
            "performance": user.performance_score,
            "analytics": paginated["items"],
            "meta": paginated["meta"],
            "summary": {
                "total_calls": total_calls,
                "total_duration": total_duration
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------
# 4️⃣ USER — MY ANALYTICS (SECURE)
# ------------------------------------------------
@analytics_bp.route("/api/user/my-analytics", methods=["GET"])
@jwt_required()
def my_analytics():
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 30, type=int)
        from_date = datetime.utcnow() - timedelta(days=days)

        query = CallHistory.query.filter(
            CallHistory.user_id == user_id,
            CallHistory.created_at >= from_date
        ).order_by(CallHistory.created_at.desc())

        def serialize(c):
            return {
                "id": c.id,
                "number": c.phone_number,
                "name": c.contact_name,
                "duration": c.duration,
                "call_type": c.call_type,
                "timestamp": iso(c.timestamp)
            }

        paginated = paginate(query, serialize)

        return jsonify({
            "user_id": user_id,
            "performance": User.query.get(user_id).performance_score,
            "data": paginated["items"],
            "meta": paginated["meta"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
