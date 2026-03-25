import enum
from datetime import datetime, timezone
from app import db

class AuditAction(enum.Enum):
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    CREATE = 'CREATE'
    EDIT = 'EDIT'
    APPROVE = 'APPROVE'
    REJECT = 'REJECT'
    DELETE = 'DELETE'
    STATUS_CHANGE = 'STATUS_CHANGE'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action_type = db.Column(db.String(20), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)
    previous_hash = db.Column(db.String(64), nullable=True)

    # Relationship
    user = db.relationship('User', backref='audit_logs', lazy=True)

    def __repr__(self):
        return f'<AuditLog {self.action_type} by User {self.user_id} at {self.timestamp}>'
