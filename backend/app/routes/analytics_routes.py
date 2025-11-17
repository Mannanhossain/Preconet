from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from extensions import db
from ..models import User   # FIXED: added missing import

analytics_bp = Blueprint('analytics', __name__)

# ---------------------------
#   DATABASE MODELS
# ---------------------------

class UserAnalytics(db.Model):
    __tablename__ = 'user_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    total_calls = db.Column(db.Integer, default=0)
    incoming_calls = db.Column(db.Integer, default=0)
    outgoing_calls = db.Column(db.Integer, default=0)
    missed_calls = db.Column(db.Integer, default=0)
    rejected_calls = db.Column(db.Integer, default=0)

    total_duration = db.Column(db.Integer, default=0)
    incoming_duration = db.Column(db.Integer, default=0)
    outgoing_duration = db.Column(db.Integer, default=0)

    period_days = db.Column(db.Integer, default=0)
    sync_timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('analytics', lazy=True))


class CallHistory(db.Model):
    __tablename__ = 'call_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    phone_number = db.Column(db.String(20), nullable=False)
    formatted_number = db.Column(db.String(50))

    call_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, default=0)
    contact_name = db.Column(db.String(100))

    sync_timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('call_history', lazy=True))


class CallMetrics(db.Model):
    __tablename__ = 'call_metrics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    total_calls = db.Column(db.Integer, default=0)
    incoming_calls = db.Column(db.Integer, default=0)
    outgoing_calls = db.Column(db.Integer, default=0)
    missed_calls = db.Column(db.Integer, default=0)
    rejected_calls = db.Column(db.Integer, default=0)

    total_duration = db.Column(db.Integer, default=0)
    period_days = db.Column(db.Integer, default=0)

    sync_timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('call_metrics', lazy=True))


# ---------------------------
#   SYNC ANALYTICS
# ---------------------------

@analytics_bp.route('/api/user/sync-analytics', methods=['POST'])
@jwt_required()
def sync_analytics():
    try:
        user_id = get_jwt_identity()
        data = request.json or {}

        sync_raw = data.get("sync_timestamp")
        if not sync_raw:
            return jsonify({"error": "sync_timestamp missing"}), 400

        sync_dt = datetime.fromtimestamp(sync_raw / 1000)

        analytics = UserAnalytics(
            user_id=user_id,
            total_calls=data.get("total_calls", 0),
            incoming_calls=data.get("incoming_calls", 0),
            outgoing_calls=data.get("outgoing_calls", 0),
            missed_calls=data.get("missed_calls", 0),
            rejected_calls=data.get("rejected_calls", 0),
            total_duration=data.get("total_duration", 0),
            incoming_duration=data.get("incoming_duration", 0),
            outgoing_duration=data.get("outgoing_duration", 0),
            period_days=data.get("period_days", 0),
            sync_timestamp=sync_dt
        )

        db.session.add(analytics)
        db.session.commit()

        return jsonify({"message": "Analytics synced successfully", "analytics_id": analytics.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------------
#   SYNC CALL HISTORY
# ---------------------------

@analytics_bp.route('/api/user/sync-call-history', methods=['POST'])
@jwt_required()
def sync_call_history():
    try:
        user_id = get_jwt_identity()
        data = request.json or {}

        call_list = data.get("call_history", [])
        sync_raw = data.get("sync_timestamp")

        if not sync_raw:
            sync_raw = datetime.utcnow().timestamp() * 1000

        sync_dt = datetime.fromtimestamp(sync_raw / 1000)

        saved = 0

        for item in call_list:

            ts_raw = item.get("timestamp")
            if not ts_raw:
                continue  # skip invalid

            call_ts = datetime.fromtimestamp(ts_raw / 1000)

            call = CallHistory(
                user_id=user_id,
                phone_number=item.get("number", ""),
                formatted_number=item.get("formatted_number", ""),
                call_type=item.get("call_type", "unknown"),
                timestamp=call_ts,
                duration=item.get("duration", 0),
                contact_name=item.get("name", ""),
                sync_timestamp=sync_dt
            )
            db.session.add(call)
            saved += 1

        # Save metrics summary
        metrics = data.get("metrics")
        if metrics:
            metrics_rec = CallMetrics(
                user_id=user_id,
                total_calls=metrics.get("total_calls", 0),
                incoming_calls=metrics.get("incoming_calls", 0),
                outgoing_calls=metrics.get("outgoing_calls", 0),
                missed_calls=metrics.get("missed_calls", 0),
                rejected_calls=metrics.get("rejected_calls", 0),
                total_duration=metrics.get("total_duration", 0),
                period_days=data.get("period_days", 0),
                sync_timestamp=sync_dt
            )
            db.session.add(metrics_rec)

        db.session.commit()

        return jsonify({"message": "Call history synced successfully", "calls_saved": saved}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------------
#   ADMIN — USER ANALYTICS
# ---------------------------

@analytics_bp.route('/api/admin/user-analytics/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_analytics(user_id):
    try:
        days = request.args.get("days", 30, type=int)
        from_date = datetime.utcnow() - timedelta(days=days)

        analytics = UserAnalytics.query.filter_by(user_id=user_id) \
            .filter(UserAnalytics.created_at >= from_date).order_by(UserAnalytics.created_at.desc()).all()

        output = [{
            "id": a.id,
            "total_calls": a.total_calls,
            "incoming_calls": a.incoming_calls,
            "outgoing_calls": a.outgoing_calls,
            "missed_calls": a.missed_calls,
            "rejected_calls": a.rejected_calls,
            "total_duration": a.total_duration,
            "sync_timestamp": a.sync_timestamp.isoformat()
        } for a in analytics]

        return jsonify({
            "user_id": user_id,
            "analytics": output,
            "summary": {
                "records": len(output),
                "total_calls": sum(i["total_calls"] for i in output),
                "total_duration": sum(i["total_duration"] for i in output)
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
#   USER MY ANALYTICS
# ---------------------------

@analytics_bp.route('/api/user/my-analytics', methods=['GET'])
@jwt_required()
def get_my_analytics():
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 30, type=int)
        from_date = datetime.utcnow() - timedelta(days=days)

        analytics = UserAnalytics.query.filter_by(user_id=user_id) \
            .filter(UserAnalytics.created_at >= from_date).all()

        output = [{
            "total_calls": a.total_calls,
            "incoming_calls": a.incoming_calls,
            "outgoing_calls": a.outgoing_calls,
            "missed_calls": a.missed_calls,
            "rejected_calls": a.rejected_calls,
            "total_duration": a.total_duration,
            "sync_timestamp": a.sync_timestamp.isoformat()
        } for a in analytics]

        return jsonify({
            "user_id": user_id,
            "data": output,
            "total_records": len(output)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
