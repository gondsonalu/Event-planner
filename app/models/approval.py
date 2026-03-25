"""
Approval Model - Phase 4
Tracks the decision history for event workflows.
"""
from enum import Enum as PyEnum
from datetime import datetime, timezone
from app import db


class ApprovalDecision(PyEnum):
    Approved = 'Approved'
    Rejected = 'Rejected'
    Changes_Requested = 'Changes_Requested'


class ApprovalLevel(PyEnum):
    Faculty = 'Faculty'
    DepartmentHead = 'DepartmentHead'


class Approval(db.Model):
    """Stores a log of every approval decision made for an event."""
    __tablename__ = 'approvals'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    level = db.Column(db.Enum(ApprovalLevel), nullable=False)
    decision = db.Column(db.Enum(ApprovalDecision), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    event = db.relationship('Event', backref=db.backref('approvals', lazy=True, cascade="all, delete-orphan"))
    approver = db.relationship('User', backref=db.backref('decisions_made', lazy=True))

    def __repr__(self):
        return f'<Approval Event {self.event_id} - Level {self.level.value} - Decision {self.decision.value}>'
