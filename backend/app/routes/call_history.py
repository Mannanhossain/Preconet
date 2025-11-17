from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.models import db, User, CallHistory, CallMetrics      # FIXED
from sqlalchemy.exc import SQLAlchemyError

call_history_bp = Blueprint("call_history", __name__)

# ----------------------------------------------------------
# SYNC CALL HISTORY (FLUTTER → SERVER)
# ----------------------------------------------------------

@call_history_bp.route("/api/user/sync-call-history", methods=["POST"])
@jwt_required()
def sync_call_history():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        call_history_data = data.get("call_history", [])
        metrics_data = data.get("metrics", {})

        sync_ts_ms = data.get("sync_timestamp")
        if not sync_ts_ms:
            sync_ts_ms = datetime.utcnow().timestamp() * 1000     # FIXED

        sync_ts = datetime.fromtimestamp(sync_ts_ms / 1000)

        saved_records = 0

        for entry in call_history_data:

            ts_ms = entry.get("timestamp")
            if not ts_ms:
                continue   # FIXED: skip invalid rows

            ts = datetime.fromtimestamp(ts_ms / 1000)

            # -------- PREVENT DUPLICATES --------
            exists = CallHistory.query.filter_by(
                user_id=user_id,
                timestamp=ts,
                phone_number=entry.get("number", "")
            ).first()

            if exists:
                continue
            # ------------------------------------

            record = CallHistory(
                user_id=user_id,
                phone_number=entry.get("number", ""),
                formatted_number=entry.get("formatted_number", ""),
                call_type=entry.get("call_type", "unknown"),
                timestamp=ts,
                duration=entry.get("duration", 0),
                contact_name=entry.get("name", ""),
                sync_timestamp=sync_ts
            )

            db.session.add(record)
            saved_records += 1

        # Save summary metrics
        if metrics_data:
            metrics = CallMetrics(
                user_id=user_id,
                total_calls=metrics_data.get("total_calls", 0),
                incoming_calls=metrics_data.get("incoming_calls", 0),
                outgoing_calls=metrics_data.get("outgoing_calls", 0),
                missed_calls=metrics_data.get("missed_calls", 0),
                rejected_calls=metrics_data.get("rejected_calls", 0),
                total_duration=metrics_data.get("total_duration", 0),
                period_days=data.get("period_days", 0),
                sync_timestamp=sync_ts
            )
            db.session.add(metrics)

        db.session.commit()

        return jsonify({
            "message": "Call history synced successfully",
            "records_saved": saved_records
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------------
# USER — MY CALL HISTORY
# ----------------------------------------------------------

@call_history_bp.route("/api/user/my-call-history", methods=["GET"])
@jwt_required()
def my_call_history():
    try:
        user_id = get_jwt_identity()

        days = request.args.get("days", 30, type=int)
        call_type = request.args.get("call_type", "all")

        from_date = datetime.utcnow() - timedelta(days=days)

        q = CallHistory.query.filter_by(user_id=user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type != "all":
            q = q.filter_by(call_type=call_type)

        records = q.order_by(CallHistory.timestamp.desc()).all()

        data = [{
            "id": r.id,
            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,
            "call_type": r.call_type,
            "timestamp": r.timestamp.isoformat(),
            "duration": r.duration,
            "contact_name": r.contact_name
        } for r in records]

        return jsonify({
            "user_id": user_id,
            "total_records": len(data),
            "call_history": data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------------
# ADMIN — ANY USER CALL HISTORY
# ----------------------------------------------------------

@call_history_bp.route("/api/admin/user-call-history/<int:user_id>", methods=["GET"])
@jwt_required()
def admin_user_call_history(user_id):
    try:
        days = request.args.get("days", 30, type=int)
        call_type = request.args.get("call_type", "all")

        from_date = datetime.utcnow() - timedelta(days=days)

        q = CallHistory.query.filter_by(user_id=user_id)
        q = q.filter(CallHistory.created_at >= from_date)

        if call_type != "all":
            q = q.filter_by(call_type=call_type)

        records = q.order_by(CallHistory.timestamp.desc()).all()

        data = [{
            "id": r.id,
            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,     # FIXED
            "call_type": r.call_type,
            "timestamp": r.timestamp.isoformat(),
            "duration": r.duration,
            "contact_name": r.contact_name
        } for r in records]

        return jsonify({
            "user_id": user_id,
            "records": len(data),
            "history": data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------------
# ADMIN — ALL USERS LATEST CALLS
# ----------------------------------------------------------

@call_history_bp.route("/api/admin/all-call-history", methods=["GET"])
@jwt_required()
def all_users_call_history():
    try:
        days = request.args.get("days", 7, type=int)

        from_date = datetime.utcnow() - timedelta(days=days)

        records = CallHistory.query \
            .filter(CallHistory.created_at >= from_date) \
            .order_by(CallHistory.timestamp.desc()) \
            .limit(200).all()

        data = [{
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else "Unknown",
            "phone_number": r.phone_number,
            "formatted_number": r.formatted_number,
            "type": r.call_type,
            "timestamp": r.timestamp.isoformat(),
            "duration": r.duration
        } for r in records]

        return jsonify({
            "total": len(data),
            "latest_calls": data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
