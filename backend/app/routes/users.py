from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from ..models import db, User, ActivityLog, UserRole
from datetime import datetime

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if email already exists
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # In real scenario, admin would create users
        return jsonify({'error': 'Please contact admin for registration'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        
        if not user or not user.check_password(data.get('password')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'role': 'user'}
        )
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role': 'user',
                'performance_score': user.performance_score
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/performance', methods=['POST'])
@jwt_required()
def update_performance():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        if 'performance_score' in data:
            user.performance_score = data['performance_score']
        
        # Log activity
        activity = ActivityLog(
            actor_role=UserRole.USER,
            actor_id=current_user_id,
            action=f'Updated performance score to {user.performance_score}',
            target_type='user',
            target_id=user.id
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Performance updated successfully',
            'performance_score': user.performance_score
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'performance_score': user.performance_score,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500