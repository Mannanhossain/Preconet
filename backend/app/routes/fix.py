from flask import Blueprint, jsonify
from ..models import db

bp = Blueprint('fix', __name__, url_prefix='/api/fix')

@bp.route('/admin-table', methods=['GET'])
def fix_admin_table():
    try:
        # Add missing columns safely
        db.session.execute("""
            ALTER TABLE admins
            ADD COLUMN IF NOT EXISTS user_limit INTEGER DEFAULT 10;
        """)

        db.session.execute("""
            ALTER TABLE admins
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
        """)

        db.session.execute("""
            ALTER TABLE admins
            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
        """)

        db.session.commit()
        return jsonify({"message": "Admin table fixed!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
