"""
Department Head Blueprint - Phase 6
Handles Department Head final approval with search, pagination, audit logging,
comment sanitization, and rate limiting for approver tier.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone
from app import limiter
from app.models.event import Event, EventStatus
from app.models.approval import Approval, ApprovalDecision, ApprovalLevel
from app.utils.decorators import role_required
from app.utils.workflow import transition_status
from app.utils.search import apply_search_and_pagination
from app.utils.audit_helper import log_action
from app.utils.security import sanitize_comment

dept_head_bp = Blueprint('dept_head', __name__)


@dept_head_bp.route('/dashboard')
@login_required
@role_required('Department Head')
def dashboard():
    """List events pending department head approval with search and pagination."""
    query = Event.query.options(
        joinedload(Event.creator)
    ).filter_by(status=EventStatus.Pending_Head)

    pagination, search_query = apply_search_and_pagination(
        query,
        Event,
        search_fields=['title', 'venue']
    )

    # Calculate stats
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Approved Today (Task #13)
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    approved_today = Approval.query.filter(
        Approval.approver_id == current_user.id,
        Approval.level == ApprovalLevel.DepartmentHead,
        Approval.decision == ApprovalDecision.Approved,
        Approval.timestamp >= start_of_day
    ).count()

    rejected_count = Approval.query.filter(
        Approval.approver_id == current_user.id,
        Approval.level == ApprovalLevel.DepartmentHead,
        Approval.decision == ApprovalDecision.Rejected
    ).count()

    return render_template('dept_head/dept_head_dashboard.html',
                           pagination=pagination,
                           search_query=search_query,
                           pending_count=pagination.total,
                           approved_count=approved_today,
                           rejected_count=rejected_count)


@dept_head_bp.route('/review/<int:event_id>', methods=['GET'])
@login_required
@role_required('Department Head')
def review(event_id):
    """View details and decision form for an event."""
    event = Event.query.options(joinedload(Event.creator)).get_or_404(event_id)
    if event.status != EventStatus.Pending_Head:
        flash("This event is not awaiting your review.", "warning")
        return redirect(url_for('dept_head.dashboard'))

    return render_template('dept_head/review.html', event=event)


@dept_head_bp.route('/decide/<int:event_id>', methods=['POST'])
@login_required
@role_required('Department Head')
@limiter.limit("100 per day", error_message="You have reached your daily review limit. Please try again tomorrow.")
def decide(event_id):
    """Process the approval decision with sanitized comments and audit logging."""
    event = Event.query.get_or_404(event_id)
    decision = request.form.get('decision')
    raw_comments = request.form.get('comments', '')

    # Sanitize comments before processing
    comments = sanitize_comment(raw_comments)

    success, message = transition_status(event, decision, current_user, comments)
    if success:
        # Map decision to audit action type
        if decision == 'Approve':
            audit_action = 'APPROVE'
        elif decision == 'Reject':
            audit_action = 'REJECT'
        else:
            audit_action = 'STATUS_CHANGE'

        log_action(
            audit_action,
            'EVENT',
            event.id,
            f"Dept Head {current_user.username} decision: {decision}. Comments: {comments}"
        )
        flash(message, "success")
    else:
        flash(message, "danger")
        return redirect(url_for('dept_head.review', event_id=event.id))

    return redirect(url_for('dept_head.dashboard'))
@dept_head_bp.route('/escalate/<int:event_id>', methods=['POST'])
@login_required
@role_required('Department Head')
def escalate(event_id):
    """Forward an exceptional case to Admin review."""
    event = Event.query.get_or_404(event_id)
    reason = request.form.get('escalation_reason', '')
    
    if not reason:
        flash("Reason for escalation is required.", "warning")
        return redirect(url_for('dept_head.review', event_id=event.id))
        
    event.status = EventStatus.Pending_Admin
    event.escalated_to_admin = True
    event.escalation_reason = reason
    event.current_approver_role = 'Admin'
    
    # Audit trail
    log_action('ESC_TO_ADMIN', 'EVENT', event.id, f"Dept Head escalated event: {reason}")
    
    from app import db
    db.session.commit()
    
    flash("Event escalated to Admin successfully.", "info")
    return redirect(url_for('dept_head.dashboard'))
