"""
Approvals Blueprint - Phase 5
Handles secondary views for approval tracking and historical decisions 
with search and pagination. Fixes missing render_template NameError.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.utils.decorators import role_required
from app.models.event import Event, EventStatus
from app.models.approval import Approval, ApprovalDecision, ApprovalLevel
from app.utils.search import apply_search_and_pagination

approvals_bp = Blueprint('approvals', __name__)

@approvals_bp.route('/pending-faculty')
@login_required
@role_required('Faculty')
def pending_faculty():
    """Events awaiting Faculty Advisor review."""
    query = Event.query.options(joinedload(Event.creator)).filter_by(status=EventStatus.Pending_Faculty)
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('faculty/pending_faculty.html', 
                           pagination=pagination, 
                           search_query=search_query)

@approvals_bp.route('/faculty-approved')
@login_required
@role_required('Faculty')
def faculty_approved():
    """Historical record of events approved by the current Faculty Advisor."""
    query = Event.query.join(Approval).filter(
        Approval.approver_id == current_user.id,
        Approval.level == ApprovalLevel.Faculty,
        Approval.decision == ApprovalDecision.Approved
    )
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('faculty/faculty_approved.html', 
                           pagination=pagination, 
                           search_query=search_query)

@approvals_bp.route('/faculty-rejected')
@login_required
@role_required('Faculty')
def faculty_rejected():
    """Historical record of events rejected by the current Faculty Advisor."""
    query = Event.query.join(Approval).filter(
        Approval.approver_id == current_user.id,
        Approval.level == ApprovalLevel.Faculty,
        Approval.decision == ApprovalDecision.Rejected
    )
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('faculty/faculty_rejected.html', 
                           pagination=pagination, 
                           search_query=search_query)

@approvals_bp.route('/pending-dept')
@login_required
@role_required('Department Head')
def pending_dept():
    """Events awaiting Department Head final validation."""
    query = Event.query.options(joinedload(Event.creator)).filter_by(status=EventStatus.Pending_Head)
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('dept_head/pending_dept.html', 
                           pagination=pagination, 
                           search_query=search_query)

@approvals_bp.route('/dept-approved')
@login_required
@role_required('Department Head')
def dept_approved():
    """Historical record of events approved by the current Department Head."""
    query = Event.query.join(Approval).filter(
        Approval.approver_id == current_user.id,
        Approval.level == ApprovalLevel.DepartmentHead,
        Approval.decision == ApprovalDecision.Approved
    )
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('dept_head/dept_approved.html', 
                           pagination=pagination, 
                           search_query=search_query)

@approvals_bp.route('/dept-rejected')
@login_required
@role_required('Department Head')
def dept_rejected():
    """Historical record of events rejected by the current Department Head."""
    query = Event.query.join(Approval).filter(
        Approval.approver_id == current_user.id,
        Approval.level == ApprovalLevel.DepartmentHead,
        Approval.decision == ApprovalDecision.Rejected
    )
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('dept_head/dept_rejected.html', 
                           pagination=pagination, 
                           search_query=search_query)

@approvals_bp.route('/forward-admin')
@login_required
@role_required('Department Head')
def forward_admin():
    """View events ready to be forwarded for admin policy exceptions."""
    # Showing all events awaiting this dept head's final review that can be forwarded
    query = Event.query.options(joinedload(Event.creator)).filter_by(status=EventStatus.Pending_Head)
    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('dept_head/forward_admin.html', 
                          pagination=pagination, 
                          search_query=search_query)
