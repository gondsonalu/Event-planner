"""
Event Submission Form - Phase 2
WTForms implementation with strict validation matching Section 10.2.
Grouped into logical field sets: Basic, Audience, Technical, Security, Budget.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DateTimeLocalField, DateField,
    IntegerField, FloatField, SelectField, BooleanField, SubmitField, TimeField
)
from wtforms.validators import (
    DataRequired, NumberRange, ValidationError, Length, Optional
)
from datetime import datetime, date


# ── Choice constants ────────────────────────────────────────────────
EVENT_TYPE_CHOICES = [
    ('', '— Select Event Type —'),
    ('Seminar', 'Seminar'),
    ('Workshop', 'Workshop'),
    ('Conference', 'Conference'),
    ('Cultural', 'Cultural Event'),
    ('Sports', 'Sports Event'),
    ('Technical', 'Technical Fest'),
    ('Guest_Lecture', 'Guest Lecture'),
    ('Competition', 'Competition'),
    ('Other', 'Other'),
]

AUDIENCE_TYPE_CHOICES = [
    ('', '— Select Audience Type —'),
    ('Students', 'Students'),
    ('Faculty', 'Faculty'),
    ('Mixed', 'Mixed (Students & Faculty)'),
    ('External', 'External Guests'),
    ('Open', 'Open to All'),
]


class EventSubmissionForm(FlaskForm):
    """
    Multi-section event submission form.
    Each field group aligns with Section 10.2 UI layout.
    """

    # ── Section 1: Basic Information ────────────────────────────────
    title = StringField(
        'Event Title',
        validators=[
            DataRequired(message='Event title is required.'),
            Length(min=3, max=200, message='Title must be 3–200 characters.')
        ],
        render_kw={'placeholder': 'e.g. Annual Tech Symposium 2026'}
    )

    description = TextAreaField(
        'Event Description',
        validators=[
            DataRequired(message='Please provide a description of the event.'),
            Length(min=10, max=5000, message='Description must be 10–5000 characters.')
        ],
        render_kw={'placeholder': 'Describe the purpose, agenda, and expected outcomes…', 'rows': 4}
    )

    event_type = SelectField(
        'Event Type',
        choices=EVENT_TYPE_CHOICES,
        validators=[DataRequired(message='Please select an event type.')]
    )

    venue = StringField(
        'Venue | Location',
        validators=[
            DataRequired(message='Venue is required.'),
            Length(max=200)
        ],
        render_kw={'placeholder': 'e.g. Main Auditorium, Block A'}
    )

    event_date = DateField(
        'Event Date',
        validators=[DataRequired(message='Event date is required.')],
        format='%Y-%m-%d'
    )

    start_time = TimeField(
        'Start Time',
        validators=[DataRequired(message='Start time is required.')]
    )

    end_time = TimeField(
        'End Time',
        validators=[DataRequired(message='End time is required.')]
    )

    # ── Section 2: Audience ─────────────────────────────────────────
    audience_type = SelectField(
        'Target Audience',
        choices=AUDIENCE_TYPE_CHOICES,
        validators=[DataRequired(message='Please select an audience type.')]
    )

    audience_size = IntegerField(
        'Expected Audience Size',
        validators=[
            DataRequired(message='Expected audience size is required.'),
            NumberRange(min=1, max=50000, message='Audience size must be between 1 and 50,000.')
        ],
        render_kw={'placeholder': 'e.g. 200'}
    )

    is_external_audience = BooleanField('Includes External Guests')

    # ── Section 3: Technical Requirements ───────────────────────────
    requires_projector = BooleanField('Projector | Display')
    requires_microphone = BooleanField('Microphone | Sound System')
    requires_live_streaming = BooleanField('Live Streaming Setup')

    technical_requirements = TextAreaField(
        'Additional Technical Notes',
        validators=[Optional(), Length(max=2000)],
        render_kw={'placeholder': 'Any other technical needs…', 'rows': 3}
    )

    # ── Section 4: Security Requirements ────────────────────────────
    requires_security = BooleanField('Security Personnel Required')

    security_requirements = TextAreaField(
        'Security Details',
        validators=[Optional(), Length(max=2000)],
        render_kw={'placeholder': 'Describe specific security requirements if any…', 'rows': 3}
    )

    # ── Section 5: Budget ───────────────────────────────────────────
    budget = FloatField(
        'Estimated Budget (₹)',
        validators=[
            DataRequired(message='Budget estimate is required.'),
            NumberRange(min=0.0, max=10000000.0, message='Budget must be between ₹0 and ₹1,00,00,000.')
        ],
        render_kw={'placeholder': 'e.g. 25000'}
    )

    budget_breakdown = TextAreaField(
        'Budget Breakdown (Optional)',
        validators=[Optional(), Length(max=3000)],
        render_kw={'placeholder': 'Itemized breakdown: Catering ₹5000, Printing ₹2000…', 'rows': 3}
    )

    # ── Section 6: Emergency ────────────────────────────────────────
    is_urgent = BooleanField('Mark as Urgent (Event within 7 days)')

    # ── Submit ──────────────────────────────────────────────────────
    submit = SubmitField('Submit Event Proposal')

    # ── Custom Validators ───────────────────────────────────────────

    def validate_event_date(self, field):
        """Event date must be today or in the future."""
        if field.data and field.data < date.today():
            raise ValidationError('Event date cannot be in the past.')

    def validate_start_time(self, field):
        """Combine with event_date and check if in the past."""
        if self.event_date.data and field.data:
            start_dt = datetime.combine(self.event_date.data, field.data)
            if start_dt <= datetime.now():
                raise ValidationError('Start time cannot be in the past.')

    def validate_end_time(self, field):
        """End time must be after start time on the selected date."""
        if self.event_date.data and self.start_time.data and field.data:
            start_dt = datetime.combine(self.event_date.data, self.start_time.data)
            end_dt = datetime.combine(self.event_date.data, field.data)
            
            if end_dt <= start_dt:
                raise ValidationError('End time must be after start time on the selected date.')
