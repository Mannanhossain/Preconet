from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSON  # For PostgreSQL users

db = SQLAlchemy()
bcrypt = Bcrypt()

class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

class SuperAdmin(db.Model):
    __tablename__ = 'super_admin'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_limit = db.Column(db.Integer, nullable=False, default=10)
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('super_admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    creator = db.relationship('SuperAdmin', backref=db.backref('admins', lazy=True))
    users = db.relationship('User', backref='admin', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_expired(self):
        return datetime.utcnow() > self.expiry_date

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    performance_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Sync Data Fields
    analytics_data = db.Column(JSON, nullable=True)   # store summary counts
    call_history = db.Column(JSON, nullable=True)     # list of call objects
    attendance = db.Column(JSON, nullable=True)       # list or summary
    contacts = db.Column(JSON, nullable=True)         # contact list
    last_sync = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def update_sync_data(self, analytics=None, call_history=None, attendance=None, contacts=None):
        """Helper method to update sync data"""
        self.last_sync = datetime.utcnow()
        if analytics is not None:
            self.analytics_data = analytics
        if call_history is not None:
            self.call_history = call_history
        if attendance is not None:
            self.attendance = attendance
        if contacts is not None:
            self.contacts = contacts
    
    def get_sync_summary(self):
        """Get summary of synced data"""
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'analytics_records': len(self.analytics_data) if self.analytics_data else 0,
            'call_records': len(self.call_history) if self.call_history else 0,
            'attendance_records': len(self.attendance) if self.attendance else 0,
            'contact_records': len(self.contacts) if self.contacts else 0
        }

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    actor_role = db.Column(db.Enum(UserRole), nullable=False)
    actor_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)