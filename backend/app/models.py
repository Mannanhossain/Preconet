# app/models.py  (corrected)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum
import json
import uuid
from sqlalchemy.types import Text, TypeDecorator
from sqlalchemy.dialects import postgresql as pg_types
from sqlalchemy import JSON as SA_JSON

db = SQLAlchemy()
bcrypt = Bcrypt()


# -------------------------
# Helpers
# -------------------------
def now():
    # naive UTC datetime (consistent across models)
    return datetime.utcnow()


# =========================================================
# ENUM: User Roles
# =========================================================
class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


# =========================================================
# JSONType: fallback for SQLite (TypeDecorator)
# =========================================================
class JSONType(TypeDecorator):
    """
    Fallback JSON type for SQLite. Serializes to TEXT.
    """
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        try:
            return json.dumps(value)
        except Exception:
            # Last-resort: stringify
            return json.dumps(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            # If stored as simple string, return it as-is
            try:
                return json.loads(value.replace("'", '"'))
            except Exception:
                return value


def JSONAuto():
    """
    Return a JSON-compatible column type:
      - prefer SQLAlchemy / PostgreSQL JSON if available
      - fallback to JSONType (TEXT) for SQLite or unknown
    This function avoids accessing db.engine at import time in a fragile way.
    """
    try:
        # SA_JSON is SQLAlchemy's JSON type; it maps to native JSON in PG
        return SA_JSON
    except Exception:
        return JSONType


# =========================================================
# SUPER ADMIN
# =========================================================
class SuperAdmin(db.Model):
    __tablename__ = "super_admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now)

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
    # make expiry_date nullable to avoid commit errors when not provided
    expiry_date = db.Column(db.DateTime, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("super_admins.id"), nullable=False)
    creator = db.relationship("SuperAdmin", backref=db.backref("admins", lazy=True))

    created_at = db.Column(db.DateTime, default=now)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    users = db.relationship(
        "User",
        backref="admin",
        cascade="all, delete-orphan",
        lazy=True
    )

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_expired(self):
        return self.expiry_date is not None and datetime.utcnow() > self.expiry_date


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

    created_at = db.Column(db.DateTime, default=now)
    last_login = db.Column(db.DateTime)
    last_sync = db.Column(db.DateTime)

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
# ATTENDANCE MODEL (string PK as you had it)
# =========================================================
def gen_uuid():
    return uuid.uuid4().hex


class Attendance(db.Model):
    __tablename__ = "attendances"

    # keep string id but generate by default to avoid missing id errors
    id = db.Column(db.String(64), primary_key=True, default=gen_uuid)
    external_id = db.Column(db.String(64), index=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(500))

    image_path = db.Column(db.String(1024))
    status = db.Column(db.String(50), default="present", index=True)

    synced = db.Column(db.Boolean, default=False)
    sync_timestamp = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=now)

    user = db.relationship("User", backref=db.backref("attendance_records", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "external_id": self.external_id,
            "user_id": self.user_id,
            "check_in": self.check_in.isoformat() if self.check_in else None,
            "check_out": self.check_out.isoformat() if self.check_out else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "image_path": self.image_path,
            "status": self.status,
            "synced": self.synced,
            "sync_timestamp": self.sync_timestamp.isoformat() if self.sync_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =========================================================
# CALL HISTORY MODEL
# =========================================================
class CallHistory(db.Model):
    __tablename__ = "call_history"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Use names that match your client & routes: phone_number & contact_name
    phone_number = db.Column(db.String(50))
    formatted_number = db.Column(db.String(100))
    call_type = db.Column(db.String(20))  # incoming/outgoing/missed/rejected

    timestamp = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    contact_name = db.Column(db.String(150))

    created_at = db.Column(db.DateTime, default=now)

    user = db.relationship("User", backref=db.backref("call_history_records", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "phone_number": self.phone_number,
            "formatted_number": self.formatted_number,
            "call_type": self.call_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration": self.duration,
            "contact_name": self.contact_name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =========================================================
# CALL METRICS (optional separate table)
# =========================================================
class CallMetrics(db.Model):
    __tablename__ = "call_metrics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    total_calls = db.Column(db.Integer, default=0)
    incoming_calls = db.Column(db.Integer, default=0)
    outgoing_calls = db.Column(db.Integer, default=0)
    missed_calls = db.Column(db.Integer, default=0)
    rejected_calls = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Integer, default=0)
    period_days = db.Column(db.Integer, default=0)

    sync_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now)


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

    extra_data = db.Column(JSONAuto(), nullable=True)

    timestamp = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "actor_role": self.actor_role.value if self.actor_role else None,
            "actor_id": self.actor_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "extra_data": self.extra_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
