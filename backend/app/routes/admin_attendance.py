# app/routes/admin_attendance.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.models import db, Attendance, User

bp = Blueprint("admin_attendance", __name__, url_prefix="/api/admin/attendance")


def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


@bp.route("", methods=["GET"])
@jwt_required()
def list_attendance():
    """
    Admin can view all attendance records for users under their account.
    Supports pagination:
    /api/admin/attendance?page=1&per_page=25
    """
    if not admin_required():
        return jsonify({"error": "Admin access only"}), 403

    try:
        admin_id = int(get_jwt_identity())

        # pagination
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 25)), 200)

        # get all users under admin
        user_list = User.query.filter_by(admin_id=admin_id).all()
        user_ids = [u.id for u in user_list]

        # fetch attendance records
        query = Attendance.query.filter(Attendance.user_id.in_(user_ids)) \
                                .order_by(Attendance.created_at.desc())

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # prepare response data
        rows = []
        for a in paginated.items:
            user = next((u for u in user_list if u.id == a.user_id), None)
            rows.append({
                "id": a.id,
                "user_id": a.user_id,
                "user_name": user.name if user else None,
                "check_in": a.check_in.isoformat() if a.check_in else None,
                "check_out": a.check_out.isoformat() if a.check_out else None,
                "status": a.status
            })

        return jsonify({
            "attendance": rows,
            "total": paginated.total,
            "page": paginated.page,
            "pages": paginated.pages
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500
