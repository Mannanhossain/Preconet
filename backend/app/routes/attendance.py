from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Attendance
from datetime import datetime

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_attendance():
    try:
        data = request.get_json()

        # Validate request
        if not data or "records" not in data:
            return jsonify({"error": "Invalid payload, 'records' missing"}), 400

        user_id = get_jwt_identity()
        records = data["records"]

        for rec in records:
            # Flutter Sends:
            # checkInTime   (ms)
            # checkOutTime  (ms)
            # latitude
            # longitude
            # location
            # imagePath
            # status

            check_in_ts = rec.get("checkInTime")
            check_out_ts = rec.get("checkOutTime")

            # Convert timestamps safely
            check_in = datetime.fromtimestamp(check_in_ts / 1000) if check_in_ts else None
            check_out = datetime.fromtimestamp(check_out_ts / 1000) if check_out_ts else None

            new_rec = Attendance(
                user_id=user_id,
                check_in=check_in,
                check_out=check_out,
                latitude=rec.get("latitude"),
                longitude=rec.get("longitude"),
                location=rec.get("location"),
                image_path=rec.get("imagePath"),
                status=rec.get("status")  # Important
            )

            db.session.add(new_rec)

        db.session.commit()

        return jsonify({"status": "success", "message": "Attendance synced successfully"}), 200

    except Exception as e:
        print("❌ Attendance Sync Error:", e)
        return jsonify({"error": "Internal server error"}), 500
