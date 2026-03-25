"""
Events Blueprint - Phase 6
Handles event creation, submission, editing, withdrawal, and deletion.
Includes XSS sanitization, rate limiting, urgent flag support, and audit logging.
"""
from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, current_app, request
)
from app import db, limiter
from app.models.event import Event, EventStatus
from app.forms.event_form import EventSubmissionForm
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.utils.search import apply_search_and_pagination
from app.utils.audit_helper import log_action
from app.utils.security import sanitize_html, sanitize_plain_text
from sqlalchemy.orm import joinedload
from datetime import datetime

events_bp = Blueprint('events', __name__)


# ── Student Dashboard ───────────────────────────────────────────────
@events_bp.route('/dashboard')
@login_required
def student_dashboard():
    """List events created by the current student with search and pagination."""
    query = Event.query.filter_by(created_by=current_user.id)

    # Stats
    total_count = Event.query.filter_by(created_by=current_user.id).count()
    pending_count = Event.query.filter_by(created_by=current_user.id).filter(
        Event.status.in_([EventStatus.Pending_Faculty, EventStatus.Pending_Head])
    ).count()
    approved_count = Event.query.filter_by(
        created_by=current_user.id
    ).filter_by(status=EventStatus.Approved).count()

    pagination, search_query = apply_search_and_pagination(
        query,
        Event,
        search_fields=['title', 'description', 'venue'],
        filter_params={'status': request.args.get('status')}
    )

    # Calculate percentages for UI
    pending_percent = (pending_count / total_count * 100) if total_count > 0 else 0
    approved_percent = (approved_count / total_count * 100) if total_count > 0 else 0

    return render_template('student/student_dashboard.html',
                           role='Student',
                           pagination=pagination,
                           search_query=search_query,
                           total_count=total_count,
                           pending_count=pending_count,
                           approved_count=approved_count,
                           pending_percent=pending_percent,
                           approved_percent=approved_percent,
                           event_statuses=list(EventStatus))


# ── Create Event Form ──────────────────────────────────────────────
@events_bp.route('/create', methods=['GET'])
@login_required
@role_required('Student')
def create_event():
    """GET /events/create — Render the empty event submission form."""
    form = EventSubmissionForm()
    return render_template('student/create_report.html', form=form)


# ── Submit Event (Rate Limited) ────────────────────────────────────
@events_bp.route('/submit', methods=['POST'])
@login_required
@role_required('Student')
@limiter.limit("5 per day", error_message="You have reached your daily limit for event submissions (5 events per day). Please try again tomorrow.")
def submit_event():
    """POST /events/submit — Validate, sanitize, and persist a new event."""
    form = EventSubmissionForm()

    if form.validate_on_submit():
        try:
            event = Event(
                # Basic Info — sanitized
                title=sanitize_plain_text(form.title.data.strip()),
                description=sanitize_html(form.description.data.strip()),
                event_type=form.event_type.data,
                venue=sanitize_plain_text(form.venue.data.strip()),
                event_date=form.event_date.data,
                start_time=datetime.combine(form.event_date.data, form.start_time.data),
                end_time=datetime.combine(form.event_date.data, form.end_time.data),
                # Audience
                audience_type=form.audience_type.data,
                audience_size=form.audience_size.data,
                is_external_audience=form.is_external_audience.data,
                # Technical
                requires_projector=form.requires_projector.data,
                requires_microphone=form.requires_microphone.data,
                requires_live_streaming=form.requires_live_streaming.data,
                technical_requirements=sanitize_html(
                    form.technical_requirements.data.strip()
                    if form.technical_requirements.data else None
                ),
                # Security
                requires_security=form.requires_security.data,
                security_requirements=sanitize_html(
                    form.security_requirements.data.strip()
                    if form.security_requirements.data else None
                ),
                # Budget
                budget=form.budget.data,
                budget_breakdown=sanitize_html(
                    form.budget_breakdown.data.strip()
                    if form.budget_breakdown.data else None
                ),
                # Status & Ownership
                status=EventStatus.Pending_Faculty,
                is_urgent=form.is_urgent.data,
                created_by=current_user.id
            )

            db.session.add(event)
            db.session.commit()

            # AUDIT LOG
            log_action('CREATE', 'EVENT', event.id, f"Created event: {event.title}")

            flash(f'Event "{event.title}" submitted successfully! Ref: {event.reference_id}', 'success')
            return redirect(url_for('events.confirmation', event_id=event.id))

        except Exception as exc:
            db.session.rollback()
            current_app.logger.error('Database error on event creation: %s', str(exc))
            flash('An error occurred while saving. Please try again.', 'danger')

    return render_template('student/create_report.html', form=form)


# ── Event Confirmation ─────────────────────────────────────────────
@events_bp.route('/confirmation/<int:event_id>')
@login_required
def confirmation(event_id):
    """GET /events/confirmation/<id> — Show submission success details."""
    event = Event.query.get_or_404(event_id)
    return render_template('events/confirmation.html', event=event)


@events_bp.route('/download-pdf/<int:event_id>')
@login_required
def download_pdf(event_id):
    """Generate and return the PDF report for a submitted event."""
    from flask import send_file
    from app.utils.pdf_helper import generate_event_pdf
    
    event = Event.query.get_or_404(event_id)
    
    # Permission check: Creator or Admin or Faculty (if reviewing)
    if event.created_by != current_user.id and current_user.role.value not in ['Admin', 'Faculty', 'Department Head']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.index'))
    
    pdf_buffer = generate_event_pdf(event)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Event_Report_{event.reference_id}.pdf",
        mimetype='application/pdf'
    )


# ── Edit Event Form ────────────────────────────────────────────────
@events_bp.route('/edit/<int:event_id>', methods=['GET'])
@login_required
@role_required('Student')
def edit_event(event_id):
    """GET /events/edit/<id> — Render the form to edit an event."""
    event = Event.query.get_or_404(event_id)

    if event.created_by != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('events.student_dashboard'))

    if event.status not in [EventStatus.Draft, EventStatus.Changes_Requested]:
        flash(f"Cannot edit event in status: {event.status.value}", "warning")
        return redirect(url_for('events.student_dashboard'))

    form = EventSubmissionForm(obj=event)
    return render_template('events/edit.html', form=form, event=event)


# ── Update Event ───────────────────────────────────────────────────
@events_bp.route('/update/<int:event_id>', methods=['POST'])
@login_required
@role_required('Student')
def update_event(event_id):
    """POST /events/update/<id> — Update an existing event with sanitization and audit logging."""
    event = Event.query.get_or_404(event_id)

    if event.created_by != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('events.student_dashboard'))

    form = EventSubmissionForm()
    if form.validate_on_submit():
        try:
            # Manually update with sanitization instead of populate_obj
            event.title = sanitize_plain_text(form.title.data.strip())
            event.description = sanitize_html(form.description.data.strip())
            event.event_type = form.event_type.data
            event.venue = sanitize_plain_text(form.venue.data.strip())
            event.event_date = form.event_date.data
            event.start_time = datetime.combine(form.event_date.data, form.start_time.data)
            event.end_time = datetime.combine(form.event_date.data, form.end_time.data)
            event.audience_type = form.audience_type.data
            event.audience_size = form.audience_size.data
            event.is_external_audience = form.is_external_audience.data
            event.requires_projector = form.requires_projector.data
            event.requires_microphone = form.requires_microphone.data
            event.requires_live_streaming = form.requires_live_streaming.data
            event.technical_requirements = sanitize_html(
                form.technical_requirements.data.strip()
                if form.technical_requirements.data else None
            )
            event.requires_security = form.requires_security.data
            event.security_requirements = sanitize_html(
                form.security_requirements.data.strip()
                if form.security_requirements.data else None
            )
            event.budget = form.budget.data
            event.budget_breakdown = sanitize_html(
                form.budget_breakdown.data.strip()
                if form.budget_breakdown.data else None
            )
            event.is_urgent = form.is_urgent.data

            # Reset status to Pending Faculty on resubmission
            event.status = EventStatus.Pending_Faculty
            event.current_approver_role = 'Faculty'

            db.session.commit()

            # AUDIT LOG
            log_action('EDIT', 'EVENT', event.id, f"Updated event: {event.title}")

            flash("Event updated and resubmitted for approval.", "success")
            return redirect(url_for('events.confirmation', event_id=event.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Event update error: %s', str(e))
            flash("Update failed. Please try again.", "danger")

    return render_template('events/edit.html', form=form, event=event)


# ── Route Aliases ──────────────────────────────────────────────────
@events_bp.route('/my-reports')
@login_required
def my_reports():
    """History of reports for the current user."""
    query = Event.query.filter_by(created_by=current_user.id).order_by(Event.created_at.desc())
    pagination, search_query = apply_search_and_pagination(
        query,
        Event,
        search_fields=['title', 'reference_id']
    )
    return render_template('student/my_reports.html', 
                           pagination=pagination, 
                           search_query=search_query)

@events_bp.route('/my-events')
@login_required
def my_events():
    """Alias for my_reports."""
    return my_reports()


@events_bp.route('/new')
@login_required
@role_required('Student')
def create():
    """Alias for create_event."""
    return create_event()


# ── Track Event Status ─────────────────────────────────────────────
@events_bp.route('/track-status')
@login_required
def track_status_all():
    """
    Dedicated route for 'Track Status' (Task #6).
    Focuses on workflow state visualization for all events of the user.
    """
    query = Event.query.filter_by(created_by=current_user.id)
    pagination, search_query = apply_search_and_pagination(
        query,
        Event,
        search_fields=['title', 'reference_id']
    )
    return render_template('student/track_status_list.html', 
                           pagination=pagination, 
                           search_query=search_query)

@events_bp.route('/track-status/<int:event_id>')
@login_required
def track_status(event_id):
    """View status of a specific event with progress focus."""
    event = Event.query.get_or_404(event_id)
    if event.created_by != current_user.id and current_user.role.value != 'Admin':
        flash("Unauthorized.", "danger")
        return redirect(url_for('events.student_dashboard'))

    # Update for Task 6: Ensure template handles visualization
    return render_template('student/track_status.html', event=event)


# ── Delete Event ───────────────────────────────────────────────────
@events_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete a draft or rejected event."""
    event = Event.query.get_or_404(event_id)

    # Permission check
    if event.created_by != current_user.id and current_user.role.value != 'Admin':
        flash("Unauthorized.", "danger")
        return redirect(url_for('events.student_dashboard'))

    # Status check — only drafts or rejected events can be deleted
    if event.status not in [EventStatus.Draft, EventStatus.Rejected]:
        flash("Only drafts or rejected events can be deleted.", "warning")
        return redirect(url_for('events.student_dashboard'))

    title = event.title
    db.session.delete(event)
    db.session.commit()

    log_action('DELETE', 'EVENT', event_id, f"Deleted event: {title}")
    flash(f"Event '{title}' deleted.", "success")
    return redirect(url_for('events.student_dashboard'))


# ── Withdraw Event (Phase 6 Edge Case) ─────────────────────────────
@events_bp.route('/withdraw/<int:event_id>', methods=['POST'])
@login_required
def withdraw_event(event_id):
    """
    Withdraw an event ONLY if status is Draft or Pending Faculty.
    Prevents withdrawal if Approved.
    Logs the withdrawal action to audit trail.
    """
    event = Event.query.get_or_404(event_id)

    # Ownership check
    if event.created_by != current_user.id:
        flash("You can only withdraw your own events.", "danger")
        return redirect(url_for('events.student_dashboard'))

    # Cannot withdraw an approved event
    if event.status == EventStatus.Approved:
        flash("Cannot withdraw an already approved event.", "warning")
        return redirect(url_for('events.student_dashboard'))

    # Only Draft or Pending Faculty can be withdrawn
    if event.status not in [EventStatus.Draft, EventStatus.Pending_Faculty]:
        flash(f"Withdrawal is only allowed for Draft or Pending Faculty status. Current: {event.status.value}", "warning")
        return redirect(url_for('events.student_dashboard'))

    old_status = event.status.value
    event.status = EventStatus.Withdrawn
    event.current_approver_role = None
    db.session.commit()

    log_action('STATUS_CHANGE', 'EVENT', event_id,
               f"Withdrew event: {event.title} (was {old_status})")
    flash(f"Event '{event.title}' has been withdrawn.", "info")
    return redirect(url_for('events.student_dashboard'))
