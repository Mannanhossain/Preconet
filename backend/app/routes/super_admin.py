from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, SuperAdmin, Admin, User, ActivityLog, UserRole
from datetime import datetime

bp = Blueprint('super_admin', __name__, url_prefix='/api/superadmin')

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if super admin already exists
        if SuperAdmin.query.first():
            return jsonify({'error': 'Super admin already exists'}), 400
        
        super_admin = SuperAdmin(
            name=data.get('name'),
            email=data.get('email')
        )
        super_admin.set_password(data.get('password'))
        
        db.session.add(super_admin)
        db.session.commit()
        
        return jsonify({'message': 'Super admin created successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        super_admin = SuperAdmin.query.filter_by(email=data.get('email')).first()
        
        if not super_admin or not super_admin.check_password(data.get('password')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        access_token = create_access_token(
            identity=super_admin.id,
            additional_claims={'role': 'super_admin'}
        )
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': super_admin.id,
                'name': super_admin.name,
                'email': super_admin.email,
                'role': 'super_admin'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/create-admin', methods=['POST'])
@jwt_required()
def create_admin():
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        # Check if email already exists
        if Admin.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        admin = Admin(
            name=data.get('name'),
            email=data.get('email'),
            user_limit=data.get('user_limit', 10),
            expiry_date=datetime.strptime(data.get('expiry_date'), '%Y-%m-%d'),
            created_by=current_user_id
        )
        admin.set_password(data.get('password'))
        
        db.session.add(admin)
        
        # Log activity
        activity = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_user_id,
            action=f'Created admin: {admin.name}',
            target_type='admin',
            target_id=admin.id
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({'message': 'Admin created successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/admins', methods=['GET'])
@jwt_required()
def get_admins():
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        admins = Admin.query.all()
        admin_list = []
        
        for admin in admins:
            user_count = User.query.filter_by(admin_id=admin.id).count()
            admin_list.append({
                'id': admin.id,
                'name': admin.name,
                'email': admin.email,
                'user_limit': admin.user_limit,
                'expiry_date': admin.expiry_date.isoformat(),
                'created_at': admin.created_at.isoformat(),
                'last_login': admin.last_login.isoformat() if admin.last_login else None,
                'is_active': admin.is_active,
                'user_count': user_count,
                'is_expired': admin.is_expired()
            })
        
        return jsonify({'admins': admin_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/admin/<int:admin_id>', methods=['GET'])
@jwt_required()
def get_admin(admin_id):
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        admin = Admin.query.get_or_404(admin_id)
        user_count = User.query.filter_by(admin_id=admin_id).count()
        
        admin_data = {
            'id': admin.id,
            'name': admin.name,
            'email': admin.email,
            'user_limit': admin.user_limit,
            'expiry_date': admin.expiry_date.isoformat(),
            'created_at': admin.created_at.isoformat(),
            'last_login': admin.last_login.isoformat() if admin.last_login else None,
            'is_active': admin.is_active,
            'user_count': user_count,
            'is_expired': admin.is_expired()
        }
        
        return jsonify({'admin': admin_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/update-admin/<int:admin_id>', methods=['PUT'])
@jwt_required()
def update_admin(admin_id):
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        admin = Admin.query.get_or_404(admin_id)
        data = request.get_json()
        
        if 'name' in data:
            admin.name = data['name']
        if 'email' in data:
            admin.email = data['email']
        if 'user_limit' in data:
            admin.user_limit = data['user_limit']
        if 'expiry_date' in data:
            admin.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
        if 'is_active' in data:
            admin.is_active = data['is_active']
        
        # Log activity
        activity = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_user_id,
            action=f'Updated admin: {admin.name}',
            target_type='admin',
            target_id=admin.id
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({'message': 'Admin updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/delete-admin/<int:admin_id>', methods=['DELETE'])
@jwt_required()
def delete_admin(admin_id):
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        admin = Admin.query.get_or_404(admin_id)
        
        # Check if admin has users
        user_count = User.query.filter_by(admin_id=admin_id).count()
        if user_count > 0:
            return jsonify({'error': 'Cannot delete admin with existing users'}), 400
        
        # Log activity
        activity = ActivityLog(
            actor_role=UserRole.SUPER_ADMIN,
            actor_id=current_user_id,
            action=f'Deleted admin: {admin.name}',
            target_type='admin',
            target_id=admin.id
        )
        db.session.add(activity)
        
        db.session.delete(admin)
        db.session.commit()
        
        return jsonify({'message': 'Admin deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs', methods=['GET'])
@jwt_required()
def get_logs():
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        log_list = []
        for log in logs.items:
            log_list.append({
                'id': log.id,
                'actor_role': log.actor_role.value,
                'actor_id': log.actor_id,
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'timestamp': log.timestamp.isoformat()
            })
        
        return jsonify({
            'logs': log_list,
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    try:
        current_user_id = get_jwt_identity()
        current_super_admin = SuperAdmin.query.get(current_user_id)
        
        if not current_super_admin:
            return jsonify({'error': 'Unauthorized'}), 401
        
        total_admins = Admin.query.count()
        total_users = User.query.count()
        active_admins = Admin.query.filter_by(is_active=True).count()
        expired_admins = Admin.query.filter(Admin.expiry_date < datetime.utcnow()).count()
        
        stats = {
            'total_admins': total_admins,
            'total_users': total_users,
            'active_admins': active_admins,
            'expired_admins': expired_admins
        }
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500