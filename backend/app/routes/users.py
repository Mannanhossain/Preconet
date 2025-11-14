from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, User, ActivityLog, UserRole, Admin
from datetime import datetime
import re

bp = Blueprint('users', __name__, url_prefix='/api/users')


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None


# 🟢 USER CREATION (Admin Creates User)
@bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    try:
        current_admin_id = int(get_jwt_identity())
        admin = Admin.query.get(current_admin_id)

        if not admin or not admin.is_active:
            return jsonify({'error': 'Admin access required'}), 403

        if admin.is_expired():
            return jsonify({'error': 'Admin account has expired'}), 403

        data = request.get_json()

        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        # Check admin's user limit
        current_user_count = User.query.filter_by(admin_id=admin.id).count()
        if current_user_count >= admin.user_limit:
            return jsonify({'error': 'User limit reached'}), 400

        user = User(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            admin_id=admin.id,
            performance_score=data.get('performance_score', 0.0)
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()   # Commit before logging so target_id exists

        # Log activity
        activity = ActivityLog(
            actor_role=UserRole.ADMIN,
            actor_id=current_admin_id,
            action=f'Created user: {user.email}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 🟢 USER LOGIN
@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account deactivated'}), 401

        user.last_login = datetime.utcnow()
        db.session.commit()

        token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': 'user'}
        )

        return jsonify({
            'access_token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role': 'user',
                'performance_score': user.performance_score,
                'last_sync': user.last_sync.isoformat() if user.last_sync else None
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 UPDATE PERFORMANCE SCORE
@bp.route('/performance', methods=['POST'])
@jwt_required()
def update_performance():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user or not user.is_active:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        score = data.get('performance_score')

        if score is None:
            return jsonify({'error': 'performance_score is required'}), 400

        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            return jsonify({'error': 'Performance score must be between 0 and 100'}), 400

        user.performance_score = score
        db.session.commit()

        # Log
        activity = ActivityLog(
            actor_role=UserRole.USER,
            actor_id=user_id,
            action=f'Updated performance score to {score}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': 'Performance updated',
            'performance_score': user.performance_score
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 🟢 GET USER PROFILE
@bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'performance_score': user.performance_score,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'last_sync': user.last_sync.isoformat() if user.last_sync else None,
                'sync_summary': user.get_sync_summary() if hasattr(user, 'get_sync_summary') else {}
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 🟢 SYNC USER DATA (Flutter App)
@bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_data():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}

        # Use helper method if exists
        if hasattr(user, 'update_sync_data'):
            user.update_sync_data(
                analytics=data.get('analytics'),
                call_history=data.get('call_history'),
                attendance=data.get('attendance'),
                contacts=data.get('contacts')
            )
        else:
            if 'analytics' in data: user.analytics_data = data['analytics']
            if 'call_history' in data: user.call_history = data['call_history']
            if 'attendance' in data: user.attendance = data['attendance']
            if 'contacts' in data: user.contacts = data['contacts']
            user.last_sync = datetime.utcnow()

        db.session.commit()

        activity = ActivityLog(
            actor_role=UserRole.USER,
            actor_id=user_id,
            action='Synced user data',
            target_type='user',
            target_id=user_id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': 'Data synced successfully',
            'last_sync': user.last_sync.isoformat(),
            'summary': user.get_sync_summary() if hasattr(user, 'get_sync_summary') else {}
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 🟢 GET SYNC STATUS
@bp.route('/sync-status', methods=['GET'])
@jwt_required()
def get_sync_status():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'sync_status': {
                'last_sync': user.last_sync.isoformat() if user.last_sync else None,
                'has_analytics': user.analytics_data is not None,
                'has_call_history': user.call_history is not None,
                'has_attendance': user.attendance is not None,
                'has_contacts': user.contacts is not None,
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
