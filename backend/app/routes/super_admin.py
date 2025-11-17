from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, SuperAdmin, Admin, User, ActivityLog, UserRole
from datetime import datetime
import re

bp = Blueprint('super_admin', __name__, url_prefix='/api/superadmin')


# -------------------------
# helpers
# -------------------------
def _validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def _safe_actor_role(role_field):
    # activity.actor_role may be an Enum or a string in DB depending on your model
    try:
        return role_field.value  # Enum
    except Exception:
        return str(role_field)


# -------------------------
# Register SuperAdmin
# -------------------------
@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({'error': 'name, email and password are required'}), 400

        if not _validate_email(email):
            return jsonify({'error': 'invalid email format'}), 400

        # Only allow creating super admin if none exists
        if SuperAdmin.query.first():
            return jsonify({'error': 'super admin already exists'}), 400

        super_admin = SuperAdmin(name=name, email=email)
        super_admin.set_password(password)

        db.session.add(super_admin)
        db.session.commit()

        return jsonify({'message': 'Super admin created successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# -------------------------
# Login SuperAdmin
# -------------------------
@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'email and password required'}), 400

        super_admin = SuperAdmin.query.filter_by(email=email).first()
        if not super_admin or not super_admin.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        token = create_access_token(
            identity=str(super_admin.id),
            additional_claims={'role': 'super_admin'}
        )

        return jsonify({
            'access_token': token,
            'user': {
                'id': super_admin.id,
                'name': super_admin.name,
                'email': super_admin.email,
                'role': 'super_admin'
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# Create Admin
# -------------------------
@bp.route('/create-admin', methods=['POST'])
@jwt_required()
def create_admin():
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json() or {}
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        user_limit = int(data.get('user_limit', 10))
        expiry_date_str = data.get('expiry_date')

        if not name or not email or not password or not expiry_date_str:
            return jsonify({'error': 'name, email, password and expiry_date are required'}), 400

        if not _validate_email(email):
            return jsonify({'error': 'invalid email format'}), 400

        if Admin.query.filter_by(email=email).first():
            return jsonify({'error': 'email already exists'}), 400

        # parse expiry date safely (expecting yyyy-mm-dd)
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'expiry_date must be YYYY-MM-DD'}), 400

        admin = Admin(
            name=name,
            email=email,
            user_limit=user_limit,
            expiry_date=expiry_date,
            created_by=current_super_admin_id
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        # log after commit (admin.id available). safe to log now.
        activity = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_super_admin_id,
            action=f'Created admin: {admin.name}',
            target_type='admin',
            target_id=admin.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': 'Admin created successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# -------------------------
# Get Admins
# -------------------------
@bp.route('/admins', methods=['GET'])
@jwt_required()
def get_admins():
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        admins = Admin.query.order_by(Admin.created_at.desc()).all()
        admin_list = []
        for admin in admins:
            user_count = User.query.filter_by(admin_id=admin.id).count()
            admin_list.append({
                'id': admin.id,
                'name': admin.name,
                'email': admin.email,
                'user_limit': admin.user_limit,
                'expiry_date': admin.expiry_date.isoformat() if admin.expiry_date else None,
                'created_at': admin.created_at.isoformat() if admin.created_at else None,
                'last_login': admin.last_login.isoformat() if admin.last_login else None,
                'is_active': admin.is_active,
                'user_count': user_count,
                'is_expired': admin.is_expired() if hasattr(admin, 'is_expired') else False
            })

        return jsonify({'admins': admin_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# Get single admin
# -------------------------
@bp.route('/admin/<int:admin_id>', methods=['GET'])
@jwt_required()
def get_admin(admin_id):
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        admin = Admin.query.get_or_404(admin_id)
        user_count = User.query.filter_by(admin_id=admin_id).count()

        admin_data = {
            'id': admin.id,
            'name': admin.name,
            'email': admin.email,
            'user_limit': admin.user_limit,
            'expiry_date': admin.expiry_date.isoformat() if admin.expiry_date else None,
            'created_at': admin.created_at.isoformat() if admin.created_at else None,
            'last_login': admin.last_login.isoformat() if admin.last_login else None,
            'is_active': admin.is_active,
            'user_count': user_count,
            'is_expired': admin.is_expired() if hasattr(admin, 'is_expired') else False
        }

        return jsonify({'admin': admin_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# Update Admin
# -------------------------
@bp.route('/update-admin/<int:admin_id>', methods=['PUT'])
@jwt_required()
def update_admin(admin_id):
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        admin = Admin.query.get_or_404(admin_id)
        data = request.get_json() or {}

        if 'name' in data:
            admin.name = data['name']

        if 'email' in data:
            new_email = data['email']
            if not _validate_email(new_email):
                return jsonify({'error': 'invalid email format'}), 400
            # ensure uniqueness
            existing = Admin.query.filter(Admin.email == new_email, Admin.id != admin_id).first()
            if existing:
                return jsonify({'error': 'email already exists'}), 400
            admin.email = new_email

        if 'user_limit' in data:
            try:
                admin.user_limit = int(data['user_limit'])
            except Exception:
                return jsonify({'error': 'user_limit must be an integer'}, 400)

        if 'expiry_date' in data:
            try:
                admin.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'expiry_date must be YYYY-MM-DD'}), 400

        if 'is_active' in data:
            admin.is_active = bool(data['is_active'])

        db.session.commit()

        activity = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_super_admin_id,
            action=f'Updated admin: {admin.name}',
            target_type='admin',
            target_id=admin.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': 'Admin updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# -------------------------
# Delete Admin
# -------------------------
@bp.route('/delete-admin/<int:admin_id>', methods=['DELETE'])
@jwt_required()
def delete_admin(admin_id):
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        admin = Admin.query.get_or_404(admin_id)

        # Prevent deletion if admin has users
        if User.query.filter_by(admin_id=admin_id).count() > 0:
            return jsonify({'error': 'Cannot delete admin with existing users'}), 400

        # log before deletion (capture name)
        admin_name = admin.name
        activity_before = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_super_admin_id,
            action=f'Deleting admin: {admin_name}',
            target_type='admin',
            target_id=admin_id
        )
        db.session.add(activity_before)

        db.session.delete(admin)
        db.session.commit()

        # final confirmation log
        activity_after = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_super_admin_id,
            action=f'Deleted admin: {admin_name}',
            target_type='admin',
            target_id=admin_id
        )
        db.session.add(activity_after)
        db.session.commit()

        return jsonify({'message': 'Admin deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# -------------------------
# View logs (paginated)
# -------------------------
@bp.route('/logs', methods=['GET'])
@jwt_required()
def get_logs():
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        # cap per_page to avoid abuse
        per_page = min(max(1, per_page), 200)

        logs_pagination = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        log_list = []
        for log in logs_pagination.items:
            actor_role_value = _safe_actor_role(log.actor_role)
            log_list.append({
                'id': log.id,
                'actor_role': actor_role_value,
                'actor_id': log.actor_id,
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None
            })

        return jsonify({
            'logs': log_list,
            'total': logs_pagination.total,
            'pages': logs_pagination.pages,
            'current_page': page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# Super admin dashboard stats
# -------------------------
@bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    try:
        current_super_admin_id = int(get_jwt_identity())
        super_admin = SuperAdmin.query.get(current_super_admin_id)
        if not super_admin:
            return jsonify({'error': 'Unauthorized'}), 401

        stats = {
            'total_admins': Admin.query.count(),
            'total_users': User.query.count(),
            'active_admins': Admin.query.filter_by(is_active=True).count(),
            'expired_admins': Admin.query.filter(Admin.expiry_date < datetime.utcnow()).count()
        }

        return jsonify({'stats': stats}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
