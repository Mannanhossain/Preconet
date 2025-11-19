# app/routes/admin_attendance.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from app.models import db, Attendance, User

bp = Blueprint("admin_attendance", __name__, url_prefix="/api/admin/attendance")


# -----------------------------
# Helper: check if token is admin
# -----------------------------
def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


# -----------------------------
# Get Attendance (Admin View)
# -----------------------------
@bp.route("", methods=["GET"])
@jwt_required()
def get_attendance():
    # check admin role
    if not admin_required():
        return jsonify({"error": "Admin access only"}), 403

    # get admin id from JWT
    admin_id = int(get_jwt_identity())

    # pagination
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))
    except:
        page = 1
        per_page = 25

    per_page = max(1, min(per_page, 100))

    # get users under this admin
    user_ids = [u.id for u in User.query.filter_by(admin_id=admin_id).all()]

    if not user_ids:
        return jsonify({"attendance": [], "meta": {"total": 0}})

    # fetch attendance for all these users
    q = Attendance.query.filter(Attendance.user_id.in_(user_ids)).order_by(
        Attendance.check_in.desc()
    )

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)

    # include user name
    results = []
    users = {u.id: u.name for u in User.query.filter(User.id.in_(user_ids)).all()}

    for a in paginated.items:
        results.append({
            "id": a.id,
            "user_id": a.user_id,
            "user_name": users.get(a.user_id, "Unknown"),
            "check_in": a.check_in.isoformat() if a.check_in else None,
            "check_out": a.check_out.isoformat() if a.check_out else None,
            "status": a.status,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "address": a.address,
        })

    return jsonify({
        "attendance": results,
        "meta": {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "total": paginated.total,
            "pages": paginated.pages,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
        }
    }), 200


# -----------------------------
# Debug: view all attendance
# -----------------------------
@bp.route("/debug", methods=["GET"])
def debug_att():
    data = [a.to_dict() for a in Attendance.query.all()]
    return jsonify(data)


# -----------------------------
# Debug: list all users
# -----------------------------
@bp.route("/debug_users", methods=["GET"])
def debug_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "admin_id": u.admin_id
    } for u in users])
