import enum
from datetime import datetime, timezone
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(enum.Enum):
    Student = 'Student'
    Faculty = 'Faculty'
    DeptHead = 'Department Head'
    Admin = 'Admin'
    Guest = 'Guest'

class UserRoleType(db.TypeDecorator):
    """
    Custom Type to map Enum values (with spaces) to/from the database.
    """
    impl = db.String(50)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, UserRole):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        for member in UserRole:
            if member.value == value or member.name == value:
                return member
        return UserRole.Student

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(UserRoleType, default=UserRole.Student, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True, default='default.jpg')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    events = db.relationship('Event', backref='creator', lazy=True, foreign_keys='Event.created_by')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} [{self.role.name}]>'
