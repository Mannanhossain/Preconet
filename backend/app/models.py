from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.types import Text
import json

db = SQLAlchemy()
bcrypt = Bcrypt()


# -------------------------
# ENUM
# -------------------------
class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


# -------------------------
# CUSTOM JSON TYPE (works for SQLite)
# -------------------------
class JSONType(Text):
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


# -------------------------
# SUPER ADMIN MODEL
# -------------------------
class SuperAdmin(db.Model):
    __tablename__ = 'super_admins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


# -------------------------
# ADMIN MODEL
# -------------------------
class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_limit = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.DateTime, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey('super_admins.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    creator = db.relationship('SuperAdmin', backref=db.backref('admins', lazy=True))

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_expired(self):
        return datetime.utcnow() > self.expiry_date


# -------------------------
# USER MODEL
# -------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))

    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    performance_score = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Sync data fields (compatible with PostgreSQL + SQLite)
    analytics_data = db.Column(JSONType, nullable=True)
    call_history = db.Column(JSONType, nullable=True)
    attendance = db.Column(JSONType, nullable=True)
    contacts = db.Column(JSONType, nullable=True)

    last_sync = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_sync_data(self, analytics=None, call_history=None, attendance=None, contacts=None):
        """Helper method for updating sync data"""
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
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "analytics_records": len(self.analytics_data) if self.analytics_data else 0,
            "call_records": len(self.call_history) if self.call_history else 0,
            "attendance_records": len(self.attendance) if self.attendance else 0,
            "contact_records": len(self.contacts) if self.contacts else 0,
        }


# -------------------------
# ACTIVITY LOG MODEL
# -------------------------
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_role = db.Column(db.Enum(UserRole), nullable=False)
    actor_id = db.Column(db.Integer, nullable=False)

    action = db.Column(db.String(255), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
