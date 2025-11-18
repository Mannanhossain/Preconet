# app/routes/attendance.py
import os
import base64
import imghdr
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func

from extensions import db
from ..models import User, Attendance, CallHistory  # adjust import path to your project

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

# Configuration constants (tweak as needed)
UPLOAD_ROOT = os.environ.get("ATTENDANCE_UPLOAD_FOLDER", "uploads/attendance")
MAX_IMAGE_BYTES = int(os.environ.get("ATTENDANCE_MAX_IMAGE_BYTES", 5 * 1024 * 1024))  # 5 MB
ALLOWED_IMAGE_TYPES = {"jpeg", "png", "gif"}  # imghdr returns 'jpeg' for both jpg/jpeg
ALLOWED_IMAGE_EXT = {"jpeg": ".jpg", "png": ".png", "gif": ".gif"}
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 200

# Ensure upload folder exists
os.makedirs(UPLOAD_ROOT, exist_ok=True)


# -------------------------
# Helpers
# -------------------------
def iso(dt):
    if dt is None:
        return None
    try:
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            return dt.isoformat()
        except Exception:
            return str(dt)


def parse_datetime(value):
    """
    Accept ISO strings or integer timestamps in ms or seconds.
    Returns a timezone-naive UTC datetime or None.
    """
    if value is None:
        return None

    # numeric types (ms or seconds)
    if isinstance(value, (int, float)):
        v = int(value)
        if v > 10**10:  # likely milliseconds
            return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).replace(tzinfo=None)
        else:
            return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)

    # strings
    if isinstance(value, str):
        s = value.strip()
        # ISO format (allow trailing Z)
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            # convert to naive UTC if tz aware
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except Exception:
            pass

        # numeric string
        try:
            v = int(s)
            if v > 10**10:
                return datetime.fromtimestamp(v / 1000.0, tz=timezone.utc).replace(tzinfo=None)
            else:
                return datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)
        except Exception:
            return None

    return None


def ensure_user_folder(user_id):
    safe_user = str(int(user_id))
    folder = os.path.join(UPLOAD_ROOT, safe_user)
    os.makedirs(folder, exist_ok=True)
    return folder


def save_base64_image(base64_str, user_id):
    """
    Safely decode a base64 image and save it to disk.
    Returns relative path on success or None on failure.
    """
    if not base64_str:
        return None

    try:
        # Remove data URI prefix if present
        if base64_str.startswith("data:"):
            base64_str = base64_str.split(",", 1)[1]

        data = base64.b64decode(base64_str)
    except Exception:
        return None

    if len(data) > MAX_IMAGE_BYTES:
        return None

    # Determine image type
    img_type = imghdr.what(None, h=data)
    if img_type not in ALLOWED_IMAGE_TYPES:
        return None

    ext = ALLOWED_IMAGE_EXT.get(img_type, ".img")

    # Generate a safe filename
    filename = f"{uuid.uuid4().hex}{ext}"
    folder = ensure_user_folder(user_id)
    path = os.path.join(folder, filename)

    try:
        with open(path, "wb") as f:
            f.write(data)
    except Exception:
        return None

    # Return path relative to project root
    return path


def admin_required(fn):
    """Decorator to require role=admin in JWT claims"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def paginate_query(query):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except Exception:
        per_page = DEFAULT_PER_PAGE
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    pag = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pag.page,
        "per_page": pag.per_page,
        "total": pag.total,
        "pages": pag.pages,
        "has_next": pag.has_next,
        "has_prev": pag.has_prev,
    }
    return pag.items, meta


def calculate_performance(user_id):
    """
    Simple performance heuristic. Adjust weights as needed.
    - attendance on-time rate (60%)
    - call answered rate (40%)
    """
    total_att = db.session.query(func.count(Attendance.id)).filter_by(user_id=user_id).scalar() or 0
    ontime_att = db.session.query(func.count(Attendance.id)).filter(
        Attendance.user_id == user_id, Attendance.status == "on-time"
    ).scalar() or 0
    att_score = (ontime_att / total_att * 100) if total_att else 0

    total_calls = db.session.query(func.count(CallHistory.id)).filter_by(user_id=user_id).scalar() or 0
    answered_calls = db.session.query(func.count(CallHistory.id)).filter(
        CallHistory.user_id == user_id, CallHistory.duration > 0
    ).scalar() or 0
    call_score = (answered_calls / total_calls * 100) if total_calls else 0

    combined = (att_score * 0.6) + (call_score * 0.4)
    return round(combined, 2)


# -------------------------
# Endpoints
# -------------------------

@bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_attendance():
    """
    Client sync endpoint.
    Accepts JSON:
    {
        "sync_timestamp": <ms timestamp optional>,
        "records": [ { "check_in": ..., "check_out": ..., "latitude": ..., "longitude": ..., "address": ..., "image": <base64>, "status": ... }, ... ]
    }
    Returns: synced_count, errors list, saved_ids (DB-generated)
    """
    try:
        identity = get_jwt_identity()
        try:
            user_id = int(identity)
        except Exception:
            return jsonify({"error": "Invalid user identity"}), 401

        user = User.query.get(user_id)
        if not user or not getattr(user, "is_active", True):
            return jsonify({"error": "User not found or inactive"}), 403

        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Invalid or missing JSON body"}), 400

        records = payload.get("records", [])
        if not isinstance(records, list):
            return jsonify({"error": "'records' must be a list"}), 400

        sync_raw = payload.get("sync_timestamp")
        sync_dt = parse_datetime(sync_raw) if sync_raw else datetime.utcnow()

        saved = 0
        created_ids = []
        errors = []

        # Use a transaction; commit at the end (or at safe intervals if huge batch)
        for r in records:
            # parse check_in/check_out
            check_in = parse_datetime(r.get("check_in") or r.get("check_in_time") or r.get("checkin_time"))
            if not check_in:
                # client must supply check_in for a valid attendance record
                errors.append({"error": "missing_or_invalid_check_in", "record": r})
                continue

            check_out = parse_datetime(r.get("check_out") or r.get("check_out_time") or r.get("checkout_time"))

            # Normalization: round check_in to second to avoid float mismatch, use UTC-naive
            check_in_norm = check_in.replace(microsecond=0)

            # Duplicate detection: same user + same check_in timestamp (second precision)
            existing = Attendance.query.filter_by(user_id=user_id, check_in=check_in_norm).first()
            if existing:
                # optionally update allowed fields if client provided new info
                try:
                    updated = False
                    if check_out and (not existing.check_out or check_out > existing.check_out):
                        existing.check_out = check_out.replace(microsecond=0)
                        updated = True

                    if r.get("latitude") is not None:
                        existing.latitude = float(r.get("latitude"))
                        updated = True
                    if r.get("longitude") is not None:
                        existing.longitude = float(r.get("longitude"))
                        updated = True
                    if r.get("address") is not None:
                        existing.address = r.get("address")
                        updated = True
                    if r.get("status") is not None:
                        existing.status = r.get("status")
                        updated = True

                    # if client sent an image and record had none, save it (best-effort)
                    if r.get("image") and not existing.image_path:
                        saved_path = save_base64_image(r.get("image"), user_id)
                        if saved_path:
                            existing.image_path = saved_path
                            updated = True

                    if updated:
                        existing.sync_timestamp = sync_dt
                        existing.updated_at = datetime.utcnow()
                        db.session.add(existing)
                        db.session.flush()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.exception("Failed to update existing attendance")
                    errors.append({"error": "failed_updating_existing", "detail": str(e)})
                continue

            # New attendance
            lat = r.get("latitude") or r.get("lat")
            lng = r.get("longitude") or r.get("lng")
            try:
                lat_val = float(lat) if lat not in (None, "") else None
            except Exception:
                lat_val = None
            try:
                lng_val = float(lng) if lng not in (None, "") else None
            except Exception:
                lng_val = None

            address = r.get("address") or r.get("location") or r.get("place")
            status = r.get("status") or "present"

            # save image safely (best effort)
            image_path = None
            if r.get("image"):
                image_path = save_base64_image(r.get("image"), user_id)

            attendance = Attendance(
                user_id=user_id,
                check_in=check_in_norm,
                check_out=(check_out.replace(microsecond=0) if check_out else None),
                latitude=lat_val,
                longitude=lng_val,
                address=address,
                image_path=image_path,
                status=status,
                synced=True,
                sync_timestamp=sync_dt,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            try:
                db.session.add(attendance)
                db.session.flush()  # get id and catch constraint issues early
                created_ids.append(attendance.id)
                saved += 1
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception("Failed to persist attendance record")
                errors.append({"error": "db_insert_failed", "detail": str(e)})
                # after rollback we need to re-open a transaction for next records
                continue

        # update user's last_sync and performance
        try:
            user.last_sync = datetime.utcnow()
            # Recalculate performance and persist (optional: you can make this async if heavy)
            user.performance_score = calculate_performance(user.id)
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update user after attendance sync")
            # don't fail whole response - return what we have
            return jsonify({
                "message": "Partial success",
                "synced_count": saved,
                "created_ids": created_ids,
                "errors": errors,
                "warning": "Failed to update user.last_sync or performance"
            }), 207  # 207 Multi-Status

        return jsonify({
            "message": "Attendance sync complete",
            "synced_count": saved,
            "created_ids": created_ids,
            "errors": errors
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Attendance sync error")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------
# Listing endpoints
# -------------------------

@bp.route("/me", methods=["GET"])
@jwt_required()
def list_my_attendance():
    """
    List current user's attendance (paginated).
    Query params: page, per_page, from, to (ISO or timestamp)
    """
    try:
        user_id = int(get_jwt_identity())
        page_from = request.args.get("from")
        page_to = request.args.get("to")
        q = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.check_in.desc())

        if page_from:
            dt = parse_datetime(page_from)
            if dt:
                q = q.filter(Attendance.check_in >= dt)
        if page_to:
            dt = parse_datetime(page_to)
            if dt:
                q = q.filter(Attendance.check_in <= dt)

        items, meta = paginate_query(q)
        out = []
        for a in items:
            out.append({
                "id": a.id,
                "check_in": iso(a.check_in),
                "check_out": iso(a.check_out) if getattr(a, "check_out", None) else None,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "address": a.address,
                "image_path": a.image_path,
                "status": a.status,
                "sync_timestamp": iso(a.sync_timestamp),
                "created_at": iso(a.created_at),
                "updated_at": iso(getattr(a, "updated_at", None))
            })

        return jsonify({"user_id": user_id, "attendance": out, "meta": meta}), 200

    except Exception as e:
        current_app.logger.exception("List my attendance failed")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


@bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def admin_list_user_attendance(user_id):
    """
    Admin: list attendance for a user (requires admin role in JWT).
    Admin identity must match user.admin_id (ownership).
    """
    try:
        admin_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # ownership: the admin who owns the user must match identity (assuming admin's id equals JWT identity)
        # If your admin identity is different, adapt this check.
        if getattr(user, "admin_id", None) != admin_id:
            return jsonify({"error": "Unauthorized access to user data"}), 403

        q = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.check_in.desc())

        page_from = request.args.get("from")
        page_to = request.args.get("to")
        if page_from:
            dt = parse_datetime(page_from)
            if dt:
                q = q.filter(Attendance.check_in >= dt)
        if page_to:
            dt = parse_datetime(page_to)
            if dt:
                q = q.filter(Attendance.check_in <= dt)

        items, meta = paginate_query(q)
        out = [{
            "id": a.id,
            "check_in": iso(a.check_in),
            "check_out": iso(a.check_out) if getattr(a, "check_out", None) else None,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "address": a.address,
            "image_path": a.image_path,
            "status": a.status,
            "sync_timestamp": iso(a.sync_timestamp),
            "created_at": iso(a.created_at),
            "updated_at": iso(getattr(a, "updated_at", None))
        } for a in items]

        return jsonify({"user_id": user_id, "attendance": out, "meta": meta}), 200

    except Exception as e:
        current_app.logger.exception("Admin list attendance failed")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


@bp.route("/record/<int:record_id>", methods=["GET"])
@jwt_required()
def get_record(record_id):
    """
    Retrieve a single attendance record.
    Ownership enforced: user can fetch own records, admin can fetch if owns user.
    """
    try:
        identity = int(get_jwt_identity())
        claims = get_jwt()
        record = Attendance.query.get(record_id)
        if not record:
            return jsonify({"error": "Record not found"}), 404

        # allow if owner
        if record.user_id == identity:
            pass
        else:
            # allow if admin and owns the user
            if claims.get("role") == "admin":
                # check ownership
                user = User.query.get(record.user_id)
                if not user or getattr(user, "admin_id", None) != identity:
                    return jsonify({"error": "Unauthorized"}), 403
            else:
                return jsonify({"error": "Unauthorized"}), 403

        out = {
            "id": record.id,
            "user_id": record.user_id,
            "check_in": iso(record.check_in),
            "check_out": iso(record.check_out),
            "latitude": record.latitude,
            "longitude": record.longitude,
            "address": record.address,
            "image_path": record.image_path,
            "status": record.status,
            "sync_timestamp": iso(record.sync_timestamp),
            "created_at": iso(record.created_at),
            "updated_at": iso(getattr(record, "updated_at", None))
        }
        return jsonify(out), 200

    except Exception as e:
        current_app.logger.exception("Get attendance record failed")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


@bp.route("/image/<int:record_id>", methods=["GET"])
@jwt_required()
def get_record_image(record_id):
    """
    Return the saved image file for an attendance record if exists.
    Same ownership rules as get_record.
    """
    try:
        identity = int(get_jwt_identity())
        claims = get_jwt()
        record = Attendance.query.get(record_id)
        if not record or not record.image_path:
            return jsonify({"error": "Image not found"}), 404

        # same ownership check as get_record
        if record.user_id == identity:
            pass
        else:
            if claims.get("role") == "admin":
                user = User.query.get(record.user_id)
                if not user or getattr(user, "admin_id", None) != identity:
                    return jsonify({"error": "Unauthorized"}), 403
            else:
                return jsonify({"error": "Unauthorized"}), 403

        # ensure file path is inside UPLOAD_ROOT for security
        abspath = os.path.abspath(record.image_path)
        if not abspath.startswith(os.path.abspath(UPLOAD_ROOT)):
            current_app.logger.warning("Image path outside upload root: %s", abspath)
            return jsonify({"error": "Invalid image path"}), 400

        if not os.path.exists(abspath):
            return jsonify({"error": "Image file missing"}), 404

        return send_file(abspath, conditional=True)

    except Exception as e:
        current_app.logger.exception("Get attendance image failed")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# -------------------------
# Optional: Delete record (admin or owner)
# -------------------------
@bp.route("/record/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_record(record_id):
    try:
        identity = int(get_jwt_identity())
        claims = get_jwt()
        record = Attendance.query.get(record_id)
        if not record:
            return jsonify({"error": "Record not found"}), 404

        # owner or admin-owner
        if record.user_id == identity:
            permitted = True
        elif claims.get("role") == "admin":
            user = User.query.get(record.user_id)
            permitted = user and getattr(user, "admin_id", None) == identity
        else:
            permitted = False

        if not permitted:
            return jsonify({"error": "Unauthorized"}), 403

        # delete image file safely
        try:
            if record.image_path:
                p = os.path.abspath(record.image_path)
                if p.startswith(os.path.abspath(UPLOAD_ROOT)) and os.path.exists(p):
                    os.remove(p)
        except Exception:
            current_app.logger.exception("Failed to remove attendance image file")

        try:
            db.session.delete(record)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to delete attendance record")
            return jsonify({"error": "Failed to delete record"}), 500

        return jsonify({"message": "Record deleted"}), 200

    except Exception as e:
        current_app.logger.exception("Delete attendance record failed")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500
