# app/routes/attendance.py
import os
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Attendance  # adjust relative import to your project layout

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

# Uploads folder - ensure it's created by your app or here
UPLOAD_ROOT = os.environ.get("ATTENDANCE_UPLOAD_FOLDER", "uploads/attendance")


def ensure_user_folder(user_id):
    folder = os.path.join(UPLOAD_ROOT, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def parse_datetime(value):
    """Accept ISO strings or integer timestamps in ms or seconds.
       Returns datetime or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # treat as milliseconds if > 10^10 else seconds
        try:
            v = int(value)
            if v > 10**10:
                return datetime.fromtimestamp(v / 1000.0)
            return datetime.fromtimestamp(v)
        except Exception:
            return None
    if isinstance(value, str):
        # try ISO first
        try:
            # handle Z suffix as UTC
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            # try to parse numeric string timestamp
            try:
                v = int(value)
                if v > 10**10:
                    return datetime.fromtimestamp(v / 1000.0)
                return datetime.fromtimestamp(v)
            except Exception:
                return None
    return None


def save_base64_image(base64_str, user_id, record_id):
    """Save base64 image, return path or None on failure."""
    if not base64_str:
        return None
    try:
        # handle "data:image/..;base64," prefix if present
        if base64_str.startswith("data:"):
            base64_str = base64_str.split(",", 1)[1]

        data = base64.b64decode(base64_str)
    except Exception:
        return None

    folder = ensure_user_folder(user_id)
    filename = f"{record_id}.jpg"
    path = os.path.join(folder, filename)

    try:
        with open(path, "wb") as f:
            f.write(data)
    except Exception:
        return None

    # return path relative to project root (so you can serve or store)
    return path


@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_attendance():
    try:
        identity = get_jwt_identity()
        # If you stored identity as string, cast to int safely
        try:
            user_id = int(identity)
        except Exception:
            return jsonify({"error": "Invalid user identity"}), 401

        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 403

        payload = request.get_json(silent=True)
        if not payload or "records" not in payload:
            return jsonify({"error": "No records provided"}), 400

        records = payload.get("records", [])
        sync_ts_ms = payload.get("sync_timestamp")  # optional top-level
        sync_ts = parse_datetime(sync_ts_ms) if sync_ts_ms else datetime.utcnow()

        synced_ids = []
        saved = 0
        errors = []

        for r in records:
            # accept multiple id keys
            rec_id = r.get("id") or r.get("record_id") or str(datetime.utcnow().timestamp()).replace(".", "")
            # avoid duplicate DB PK insertion - check if exists
            existing = Attendance.query.get(rec_id)
            if existing:
                # optionally update if client sends newer info (update check_out, status, etc.)
                # update only minimal fields to avoid overwriting server-side stored image_path
                try:
                    ci = parse_datetime(r.get("check_in") or r.get("check_in_time") or r.get("checkin_time"))
                    co = parse_datetime(r.get("check_out") or r.get("checkout_time") or r.get("checkouttime"))
                    if ci: existing.check_in = ci
                    if co: existing.check_out = co
                    if r.get("latitude") is not None:
                        existing.latitude = float(r.get("latitude"))
                    if r.get("longitude") is not None:
                        existing.longitude = float(r.get("longitude"))
                    if r.get("address") is not None:
                        existing.address = r.get("address")
                    if r.get("status") is not None:
                        existing.status = r.get("status")
                    existing.sync_timestamp = sync_ts
                    db.session.add(existing)
                    db.session.flush()
                    synced_ids.append(rec_id)
                except Exception as e:
                    errors.append({"id": rec_id, "error": str(e)})
                continue

            # parse times
            check_in = parse_datetime(r.get("check_in") or r.get("check_in_time") or r.get("checkin_time"))
            check_out = parse_datetime(r.get("check_out") or r.get("checkout_time") or r.get("checkouttime"))

            if not check_in:
                # require check_in at minimum
                errors.append({"id": rec_id, "error": "missing or invalid check_in"})
                continue

            lat = r.get("latitude") or r.get("lat")
            lng = r.get("longitude") or r.get("lng")

            # accept address variations
            address = r.get("address") or r.get("location") or r.get("place")

            image_base64 = r.get("image") or r.get("image_base64") or r.get("photo")

            # save image (best-effort)
            image_path = None
            if image_base64:
                image_path = save_base64_image(image_base64, user_id, rec_id)

            attendance = Attendance(
                id=str(rec_id),
                user_id=user_id,
                check_in=check_in,
                check_out=check_out,
                latitude=float(lat) if lat not in (None, "") else None,
                longitude=float(lng) if lng not in (None, "") else None,
                address=address,
                image_path=image_path,
                status=r.get("status", "present"),
                synced=True,          # mark synced because client sent it; server persisted it
                sync_timestamp=sync_ts,
                created_at=datetime.utcnow()
            )

            db.session.add(attendance)
            try:
                db.session.flush()  # fail early on PK/constraint errors
                synced_ids.append(str(rec_id))
                saved += 1
            except Exception as e:
                db.session.rollback()
                errors.append({"id": rec_id, "error": str(e)})
                # continue saving other records
                continue

        # update user's last_sync
        user.last_sync = datetime.utcnow()
        db.session.add(user)

        db.session.commit()

        response = {
            "success": True,
            "synced_count": saved,
            "synced_ids": synced_ids,
            "errors": errors
        }
        return jsonify(response), 200

    except Exception as e:
        # fallback error
        db.session.rollback()
        current_app.logger.exception("Attendance sync error")
        return jsonify({"error": str(e)}), 500
