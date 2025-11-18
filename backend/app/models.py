# app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum
import json
from sqlalchemy.types import Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import event

db = SQLAlchemy()
bcrypt = Bcrypt()


# -----------------------
# ENUMS
# -----------------------
class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


# -----------------------
# JSON fallback for SQLite
# -----------------------
class JSONType(Text):
    """Simple JSON column compatible with SQLite by storing JSON as text."""
    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value is not None else None


def JSONAuto():
    """Return PostgreSQL JSON type when available, otherwise fallback."""
    try:
        # during import time db.engine may not be available, so guard
        engine_name = db.engine.name if hasattr(db, "engine") else None
        return JSON if engine_name and engine_name != "sqlite" else JSONType
    except Exception:
        return JSONType


# -----------------------
# Shared utilities
# -----------------------
def now():
    return datetime.utcnow()


# -----------------------
# SUPER ADMIN
# -----------------------
class SuperAdmin(db.Model):
    __tablename__ = "super_admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=now, nullable=False)

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)


# -----------------------
# ADMIN
# -----------------------
class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    user_limit = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.DateTime, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey("super_admins.id"), nullable=False)
    creator = db.relationship("SuperAdmin", backref=db.backref("admins", lazy="dynamic"))

    created_at = db.Column(db.DateTime, default=now, nullable=False)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # relationship to User
    users = db.relationship("User", backref="admin", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return datetime.utcnow() > self.expiry_date


# -----------------------
# USER
# -----------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(20))
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    performance_score = db.Column(db.Float, default=0.0, nullable=False)

    created_at = db.Column(db.DateTime, default=now, nullable=False)
    last_login = db.Column(db.DateTime)
    last_sync = db.Column(db.DateTime)

    # additional metadata column example (JSON)
    meta = db.Column(JSONAuto(), nullable=True)

    # relationships:
    # - attendance_records
    # - call_history_records
    # created via backrefs in the child models

    # PASSWORD HELPERS
    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_sync_time(self):
        self.last_sync = datetime.utcnow()

    def get_sync_summary(self):
        """Return small summary for dashboard; safe even if models not yet created."""
        # Import locally to avoid circular issues during import time if necessary
        total_calls = 0
        total_attendance = 0
        try:
            total_calls = CallHistory.query.filter_by(user_id=self.id).count()
        except Exception:
            total_calls = 0
        try:
            total_attendance = Attendance.query.filter_by(user_id=self.id).count()
        except Exception:
            total_attendance = 0

        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "call_records": total_calls,
            "attendance_records": total_attendance,
        }


# -----------------------
# ATTENDANCE
# -----------------------
class Attendance(db.Model):
    """
    Attendance record. Primary key is string (keeps compatibility with client-provided IDs).
    `external_id` is optional normalized ID for migration convenience.
    """
    __tablename__ = "attendances"

    id = db.Column(db.String(64), primary_key=True)          # client-supplied id (keep for compatibility)
    external_id = db.Column(db.String(64), index=True, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = db.relationship("User", backref=db.backref("attendance_records", lazy="dynamic"))

    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=True)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(500), nullable=True)

    image_path = db.Column(db.String(1024), nullable=True)
    status = db.Column(db.String(50), default="present", index=True, nullable=False)

    synced = db.Column(db.Boolean, default=False, nullable=False)
    sync_timestamp = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "external_id": self.external_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "check_in": self.check_in.isoformat() if self.check_in else None,
            "check_out": self.check_out.isoformat() if self.check_out else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "image_path": self.image_path,
            "status": self.status,
            "synced": self.synced,
            "sync_timestamp": self.sync_timestamp.isoformat() if self.sync_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# -----------------------
# CALL HISTORY
# -----------------------
class CallHistory(db.Model):
    """
    Call history. Use DateTime for timestamp (converted from epoch ms on ingest).
    """
    __tablename__ = "call_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = db.relationship("User", backref=db.backref("call_history_records", lazy="dynamic"))

    # phone fields
    number = db.Column(db.String(50), nullable=True)
    formatted_number = db.Column(db.String(100), nullable=True)
    call_type = db.Column(db.String(20), nullable=True)   # incoming/outgoing/missed/rejected

    # store as DateTime (convert on write)
    timestamp = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)       # seconds
    name = db.Column(db.String(150), nullable=True)

    sync_timestamp = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "number": self.number,
            "formatted_number": self.formatted_number,
            "call_type": self.call_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration": self.duration,
            "name": self.name,
            "sync_timestamp": self.sync_timestamp.isoformat() if self.sync_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# -----------------------
# ACTIVITY LOG
# -----------------------
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    actor_role = db.Column(db.Enum(UserRole), nullable=False)
    actor_id = db.Column(db.Integer, nullable=False)

    action = db.Column(db.String(255), nullable=False)

    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)

    metadata = db.Column(JSONAuto(), nullable=True)   # optional JSON for extra context
    timestamp = db.Column(db.DateTime, default=now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "actor_role": self.actor_role.value if self.actor_role else None,
            "actor_id": self.actor_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# -----------------------
# Convenience / Event helpers
# -----------------------
@event.listens_for(User, "after_insert")
def user_after_insert(mapper, connection, target):
    """
    Optional: create ActivityLog entry when a new user is created by admin code.
    This will only run if the app code uses session.add(user) + commit.
    If you want more context (actor_id), create ActivityLog directly in route handlers.
    """
    try:
        # avoid adding logs automatically if not desired; keep minimal default
        pass
    except Exception:
        # silent - don't break user creation flow
        pass


# -----------------------
# Backwards-compat helper:
# convert legacy epoch-ms integers to datetime when creating a CallHistory record
# (useful in create APIs — not automatically applied by ORM)
# -----------------------
def epoch_ms_to_datetime(ms):
    """Convert epoch milliseconds or seconds to datetime (UTC)."""
    if ms is None:
        return None
    try:
        ms = int(ms)
        # heuristics: if > 10**12 treat as ms, else seconds
        if ms > 10**12:
            return datetime.utcfromtimestamp(ms / 1000.0)
        if ms > 10**10:  # probably ms but just in case
            return datetime.utcfromtimestamp(ms / 1000.0)
        return datetime.utcfromtimestamp(ms)
    except Exception:
        return None
