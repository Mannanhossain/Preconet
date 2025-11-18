# app/routes/fix.py
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import inspect, text
from .extensions import db
from ..models import Admin

bp = Blueprint('fix', __name__, url_prefix='/api/fix')

# ENV secret required for DB fixes
SUPER_ADMIN_SECRET = "MANNAN_DB_FIX_2025"   # change this & keep in .env


def admin_required():
    claims = get_jwt()
    return claims.get("role") == "admin"


@bp.route('/admin-table', methods=['POST'])
@jwt_required()
def fix_admin_table():
    """
    SAFE VERSION:
    - Requires JWT admin
    - Requires super_admin_key in POST body
    - Checks columns safely before adding
    """

    # 1) Ensure admin role
    if not admin_required():
        return jsonify({"error": "Admin access only"}), 403

    # 2) Ensure requester is SUPER ADMIN
    body = request.get_json() or {}
    if body.get("super_admin_key") != SUPER_ADMIN_SECRET:
        return jsonify({"error": "Invalid super admin key"}), 403

    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('admins')]

        results = []

        # Helper
        def add_column_if_missing(col_name, ddl):
            if col_name not in columns:
                db.session.execute(text(ddl))
                results.append(f"Added column: {col_name}")
            else:
                results.append(f"Column already exists: {col_name}")

        # 3) FIX COLUMNS ONE BY ONE SAFELY
        add_column_if_missing(
            "user_limit",
            "ALTER TABLE admins ADD COLUMN user_limit INTEGER DEFAULT 10;"
        )

        add_column_if_missing(
            "is_active",
            "ALTER TABLE admins ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"
        )

        add_column_if_missing(
            "last_login",
            "ALTER TABLE admins ADD COLUMN last_login TIMESTAMP;"
        )

        db.session.commit()

        return jsonify({
            "message": "Admin table check complete",
            "changes": results
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Admin table fix error")
        return jsonify({"error": str(e)}), 500
