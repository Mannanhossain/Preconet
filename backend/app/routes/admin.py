from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, Admin, User, ActivityLog, UserRole, SuperAdmin
from datetime import datetime
import re

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

# 🟢 ADMIN LOGIN
@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        admin = Admin.query.filter_by(email=data.get('email')).first()

        if not admin or not admin.check_password(data.get('password')):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not admin.is_active:
            return jsonify({'error': 'Account deactivated'}), 401

        if admin.is_expired():
            return jsonify({'error': 'Account expired'}), 401

        # Update last login
        admin.last_login = datetime.utcnow()
        db.session.commit()

        # ✅ Convert ID to string for JWT
        access_token = create_access_token(
            identity=str(admin.id),
            additional_claims={'role': 'admin'}
        )

        return jsonify({
            'access_token': access_token,
            'user': {
                'id': admin.id,
                'name': admin.name,
                'email': admin.email,
                'role': 'admin',
                'user_limit': admin.user_limit,
                'expiry_date': admin.expiry_date.isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 CREATE USER
@bp.route('/create-user', methods=['POST'])
@jwt_required()
def create_user():
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        if admin.is_expired():
            return jsonify({'error': 'Admin account expired'}), 401

        # Check user limit
        user_count = User.query.filter_by(admin_id=admin.id).count()
        if user_count >= admin.user_limit:
            return jsonify({'error': 'User limit reached'}), 400

        data = request.get_json()

        # Validation
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        # Email validation
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            admin_id=admin.id,
            is_active=True,
            performance_score=data.get('performance_score', 0.0)
        )
        user.set_password(data.get('password', '123456'))

        db.session.add(user)

        activity = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=current_user_id,
            action=f'Created user: {user.name}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'user_id': user.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 🟢 GET ALL USERS
@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        users = User.query.filter_by(admin_id=admin.id).all()
        user_list = [
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'performance_score': user.performance_score,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'last_sync': user.last_sync.isoformat() if user.last_sync else None,
                'has_sync_data': any([
                    user.analytics_data is not None,
                    user.call_history is not None,
                    user.attendance is not None,
                    user.contacts is not None
                ])
            }
            for user in users
        ]

        return jsonify({'users': user_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 UPDATE USER
@bp.route('/update-user/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        user = User.query.filter_by(id=user_id, admin_id=admin.id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            # Validate new email
            if not validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'error': 'Email already taken'}), 400
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'performance_score' in data:
            score = data['performance_score']
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                return jsonify({'error': 'Performance score must be between 0 and 100'}), 400
            user.performance_score = score

        activity = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=current_user_id,
            action=f'Updated user: {user.name}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 🟢 DELETE USER
@bp.route('/delete-user/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        user = User.query.filter_by(id=user_id, admin_id=admin.id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        activity = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=current_user_id,
            action=f'Deleted user: {user.name}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 🟢 DASHBOARD STATS
@bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        total_users = User.query.filter_by(admin_id=admin.id).count()
        active_users = User.query.filter_by(admin_id=admin.id, is_active=True).count()
        users = User.query.filter_by(admin_id=admin.id).all()

        total_performance = sum(user.performance_score or 0 for user in users)
        avg_performance = round(total_performance / len(users), 2) if users else 0

        # Sync statistics
        users_with_sync = User.query.filter(
            User.admin_id == admin.id,
            User.last_sync.isnot(None)
        ).count()

        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'expired_users': 0,  # You can add logic later if needed
            'avg_performance': avg_performance,
            'user_limit': admin.user_limit,
            'remaining_slots': max(0, admin.user_limit - total_users),
            'users_with_sync': users_with_sync,
            'sync_rate': round((users_with_sync / total_users) * 100, 2) if total_users > 0 else 0
        }

        return jsonify({'stats': stats}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 GET USER SYNC DATA (Your added functionality)
@bp.route('/user-data/<int:user_id>', methods=['GET'])
@jwt_required()
def admin_get_user_data(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        # Verify the user belongs to this admin
        user = User.query.filter_by(id=user_id, admin_id=admin.id).first()
        if not user:
            return jsonify({'error': 'User not found or access denied'}), 404

        # Log the data access activity
        activity = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=current_user_id,
            action=f'Accessed sync data for user: {user.name}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
            'analytics': user.analytics_data or {},
            'call_history': user.call_history or [],
            'attendance': user.attendance or {},
            'contacts': user.contacts or [],
            'last_sync': user.last_sync.isoformat() if user.last_sync else None,
            'sync_summary': user.get_sync_summary() if hasattr(user, 'get_sync_summary') else {}
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 GET ALL USERS SYNC STATUS
@bp.route('/users-sync-status', methods=['GET'])
@jwt_required()
def get_all_users_sync_status():
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        users = User.query.filter_by(admin_id=admin.id).all()
        
        sync_status_list = []
        for user in users:
            sync_info = {
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'last_sync': user.last_sync.isoformat() if user.last_sync else None,
                'has_analytics': user.analytics_data is not None,
                'has_call_history': user.call_history is not None,
                'has_attendance': user.attendance is not None,
                'has_contacts': user.contacts is not None,
                'days_since_sync': (
                    (datetime.utcnow() - user.last_sync).days 
                    if user.last_sync else None
                )
            }
            sync_status_list.append(sync_info)

        return jsonify({'users_sync_status': sync_status_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500