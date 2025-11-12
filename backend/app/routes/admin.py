from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, Admin, User, ActivityLog, UserRole
from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


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

        # ✅ Convert id to string for JWT
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

        # Check if email exists
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            admin_id=admin.id
        )
        user.set_password(data.get('password', '123456'))  # Default password

        db.session.add(user)

        # Log activity
        activity = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=current_user_id,
            action=f'Created user: {user.name}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({'message': 'User created successfully'}), 201

    except Exception as e:
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
        user_list = []

        for user in users:
            user_list.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'performance_score': user.performance_score,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            })

        return jsonify({'users': user_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 GET SINGLE USER
@bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        admin = Admin.query.get(current_user_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        user = User.query.filter_by(id=user_id, admin_id=admin.id).first_or_404()

        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'is_active': user.is_active,
            'performance_score': user.performance_score,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }

        return jsonify({'user': user_data}), 200

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

        user = User.query.filter_by(id=user_id, admin_id=admin.id).first_or_404()
        data = request.get_json()

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'performance_score' in data:
            user.performance_score = data['performance_score']

        # Log activity
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

        user = User.query.filter_by(id=user_id, admin_id=admin.id).first_or_404()

        # Log activity
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
        expired_users = User.query.filter(
            User.admin_id == admin.id,
            User.expiry_date < datetime.utcnow()
        ).count() if hasattr(User, 'expiry_date') else 0

        users = User.query.filter_by(admin_id=admin.id).all()
        total_performance = sum(user.performance_score for user in users)
        avg_performance = round(total_performance / len(users), 2) if users else 0

        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'expired_users': expired_users,
            'avg_performance': avg_performance,
            'user_limit': admin.user_limit,
            'remaining_slots': max(0, admin.user_limit - total_users)
        }

        return jsonify({'stats': stats}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
