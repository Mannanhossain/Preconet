from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Attendance
from datetime import datetime
import uuid

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_attendance():
    try:
        data = request.get_json()

        if not data or "records" not in data:
            return jsonify({"error": "Invalid request format"}), 400

        user_id = int(get_jwt_identity())
        records = data["records"]

        for rec in records:

            # FIX: convert check_in/check_out safely
            check_in = None
            if "check_in" in rec:
                check_in = datetime.fromtimestamp(int(rec["check_in"]) / 1000)

            check_out = None
            if "check_out" in rec and rec["check_out"]:
                check_out = datetime.fromtimestamp(int(rec["check_out"]) / 1000)

            # FIX: address instead of location
            address = rec.get("location")

            new_rec = Attendance(
                id = rec.get("id") or uuid.uuid4().hex,
                external_id = rec.get("id"),
                user_id = user_id,
                check_in = check_in,
                check_out = check_out,
                latitude = rec.get("latitude"),
                longitude = rec.get("longitude"),
                address = address,
                image_path = rec.get("imagePath"),
                status = rec.get("status", "present"),
                synced = True,
                sync_timestamp = datetime.utcnow()
            )

            db.session.add(new_rec)

        db.session.commit()

        return jsonify({"status": "success", "message": "Attendance synced"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500
