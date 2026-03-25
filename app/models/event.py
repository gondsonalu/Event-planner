"""
Event Model - Phase 2
Defines the Event SQLAlchemy model with all fields from Section 13.3.2:
Basic Info, Audience, Technical, Security, Budget, and Status.
"""
from enum import Enum as PyEnum
from app import db
from datetime import datetime, timezone


class EventStatus(PyEnum):
    """Approval workflow status enum."""
    Draft = 'Draft'
    Pending_Faculty = 'Pending_Faculty'
    Pending_Head = 'Pending_Head'
    Approved = 'Approved'
    Rejected = 'Rejected'
    Changes_Requested = 'Changes_Requested'
    Withdrawn = 'Withdrawn'
    Pending_Admin = 'Pending_Admin'


class Event(db.Model):
    """Event model representing an event submission for approval."""
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)

    # ── Basic Info ──────────────────────────────────────────────────
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default='Seminar')

    # ── Audience ────────────────────────────────────────────────────
    audience_type = db.Column(db.String(50), nullable=False, default='Students')
    audience_size = db.Column(db.Integer, nullable=False, default=0)
    is_external_audience = db.Column(db.Boolean, default=False)

    # ── Technical Requirements ──────────────────────────────────────
    requires_projector = db.Column(db.Boolean, default=False)
    requires_microphone = db.Column(db.Boolean, default=False)
    requires_live_streaming = db.Column(db.Boolean, default=False)
    technical_requirements = db.Column(db.Text, nullable=True)

    # ── Security Requirements ───────────────────────────────────────
    requires_security = db.Column(db.Boolean, default=False)
    security_requirements = db.Column(db.Text, nullable=True)

    # ── Budget ──────────────────────────────────────────────────────
    budget = db.Column(db.Float, nullable=False, default=0.0)
    budget_breakdown = db.Column(db.Text, nullable=True)

    # ── Status & Approval ───────────────────────────────────────────
    status = db.Column(
        db.Enum(EventStatus),
        default=EventStatus.Pending_Faculty,
        nullable=False,
        index=True
    )
    current_approver_role = db.Column(db.String(50), nullable=True, default='Faculty')
    rejection_reason = db.Column(db.Text, nullable=True)
    is_urgent = db.Column(db.Boolean, default=False, nullable=False)
    escalated_to_admin = db.Column(db.Boolean, default=False, nullable=False)
    escalation_reason = db.Column(db.Text, nullable=True)

    # ── Relationships ───────────────────────────────────────────────
    # ForeignKey to User in Phase 3
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    # ── Metadata / Timestamps ───────────────────────────────────────
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<Event #{self.id} "{self.title}" [{self.status.value}]>'

    @property
    def reference_id(self):
        """Human-readable reference ID, e.g. EVT-0042."""
        return f'EVT-{self.id:04d}'

    @property
    def is_pending(self):
        """True if event is in any pending approval state."""
        return self.status in (
            EventStatus.Pending_Faculty,
            EventStatus.Pending_Head
        )

    @property
    def duration_hours(self):
        """Calculate event duration in hours."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 1)
        return 0
