"""
Workflow Engine - Phase 6
Handles state transitions, approval record creation,
and comment sanitization. Enforces permission checks per role.
"""
from app import db
from app.models.event import EventStatus
from app.models.approval import Approval, ApprovalDecision, ApprovalLevel
from app.utils.security import sanitize_comment
from flask_login import current_user


def transition_status(event, decision_str, user, comments=None):
    """
    State machine logic for event approval workflow.
    Validates permissions, sanitizes comments, and updates event status.
    
    Args:
        event: Event model instance
        decision_str: String decision ('Approve', 'Reject', 'Changes_Requested')
        user: User model instance performing the action
        comments: Optional text comments (will be sanitized)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Map string decision to Enum
    decision_map = {
        'Approve': ApprovalDecision.Approved,
        'Reject': ApprovalDecision.Rejected,
        'Changes_Requested': ApprovalDecision.Changes_Requested
    }
    decision = decision_map.get(decision_str)

    if not decision:
        return False, "Invalid decision type."

    # Validate: user cannot approve their own event
    if event.created_by == user.id:
        return False, "You cannot approve an event you created."

    # Sanitize comments
    if comments:
        comments = sanitize_comment(comments)

    # ── Status Transition Logic ─────────────────────────────────────
    old_status = event.status
    new_status = old_status
    level = None

    if old_status == EventStatus.Pending_Faculty:
        if user.role.name != 'Faculty':
            return False, "Only Faculty can approve at this level."
        level = ApprovalLevel.Faculty

        if decision == ApprovalDecision.Approved:
            new_status = EventStatus.Pending_Head
            event.current_approver_role = 'Department Head'
        elif decision == ApprovalDecision.Rejected:
            new_status = EventStatus.Rejected
            event.current_approver_role = None
        elif decision == ApprovalDecision.Changes_Requested:
            new_status = EventStatus.Changes_Requested
            event.current_approver_role = 'Student'

    elif old_status == EventStatus.Pending_Head:
        if user.role.name != 'DeptHead':
            return False, "Only Department Head can approve at this level."
        level = ApprovalLevel.DepartmentHead

        if decision == ApprovalDecision.Approved:
            new_status = EventStatus.Approved
            event.current_approver_role = None
        elif decision == ApprovalDecision.Rejected:
            new_status = EventStatus.Rejected
            event.current_approver_role = None
        elif decision == ApprovalDecision.Changes_Requested:
            new_status = EventStatus.Changes_Requested
            event.current_approver_role = 'Student'

    else:
        return False, f"Event is not in a reviewable state (Current: {old_status.value})."

    # Enforce comments for Reject / Changes_Requested
    if decision in [ApprovalDecision.Rejected, ApprovalDecision.Changes_Requested] and not comments:
        return False, "Comments are required for rejections or change requests."

    # Update Event
    event.status = new_status
    if decision == ApprovalDecision.Rejected:
        event.rejection_reason = comments

    # Create Approval Record
    approval = Approval(
        event_id=event.id,
        approver_id=user.id,
        level=level,
        decision=decision,
        comments=comments
    )

    db.session.add(approval)
    try:
        db.session.commit()
        return True, f"Event transitioned to {new_status.value}."
    except Exception as e:
        db.session.rollback()
        return False, str(e)
