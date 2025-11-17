from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum
import json
from sqlalchemy.types import Text
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()
bcrypt = Bcrypt()

# =========================================================
# ENUM ROLE
# =========================================================
class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


# =========================================================
# CUSTOM JSON TYPE (SQLite Compatible)
# =========================================================
class JSONType(Text):
    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value is not None else None


def JSONAuto():
    """Use PostgreSQL JSON when available; fallback to JSONType for SQLite."""
    try:
        return JSON if db.engine.name != "sqlite" else JSONType
    except:
        return JSONType


# =========================================================
# SUPER ADMIN MODEL
# =========================================================
class SuperAdmin(db.Model):
    __tablename__ = "super_admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # PASSWORD HANDLERS
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


# =========================================================
# ADMIN MODEL
# =========================================================
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    user_limit = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.DateTime, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey("super_admins.id"), nullable=False)
    creator = db.relationship("SuperAdmin", backref=db.backref("admins", lazy=True))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # ADMIN → USERS
    users = db.relationship(
        "User",
        backref="admin",
        cascade="all, delete-orphan",
        lazy=True
    )

    # PASSWORD HANDLERS
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_expired(self):
        return datetime.utcnow() > self.expiry_date


# =========================================================
# USER MODEL
# =========================================================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(20))

    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)

    is_active = db.Column(db.Boolean, default=True)
    performance_score = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_sync = db.Column(db.DateTime)

    # PASSWORD HANDLERS
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_sync_time(self):
        self.last_sync = datetime.utcnow()

    def get_sync_summary(self):
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "call_records": CallHistory.query.filter_by(user_id=self.id).count(),
            "attendance_records": Attendance.query.filter_by(user_id=self.id).count(),
        }


# =========================================================
# ATTENDANCE MODEL
# =========================================================
class Attendance(db.Model):
    __tablename__ = "attendances"

    id = db.Column(db.String(64), primary_key=True)  # UUID from Flutter
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(500))

    image_path = db.Column(db.String(1024))
    status = db.Column(db.String(50), default="present")

    synced = db.Column(db.Boolean, default=False)
    sync_timestamp = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("attendance_records", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat() if self.check_out else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "image_path": self.image_path,
            "status": self.status,
            "synced": self.synced,
            "sync_timestamp": self.sync_timestamp.isoformat() if self.sync_timestamp else None,
            "created_at": self.created_at.isoformat(),
        }


# =========================================================
# CALL HISTORY MODEL
# =========================================================
class CallHistory(db.Model):
    __tablename__ = "call_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    number = db.Column(db.String(50))
    call_type = db.Column(db.String(20))        # incoming/outgoing/missed/rejected
    timestamp = db.Column(db.BigInteger)        # Epoch milliseconds
    duration = db.Column(db.Integer)
    name = db.Column(db.String(150))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("call_history_records", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "number": self.number,
            "call_type": self.call_type,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }


# =========================================================
# ACTIVITY LOG MODEL
# =========================================================
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    actor_role = db.Column(db.Enum(UserRole), nullable=False)
    actor_id = db.Column(db.Integer, nullable=False)

    action = db.Column(db.String(255), nullable=False)

    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
