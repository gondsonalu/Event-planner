"""
Admin Blueprint - Phase 6
Handles administrative tasks, system-wide overview, audit logging,
user management (delete/deactivate with orphan protection), and event reassignment.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app import db, limiter
from app.utils.decorators import role_required
from app.utils.audit_helper import log_action
from app.models.user import User, UserRole
from app.models.event import Event, EventStatus
from app.models.approval import Approval
from app.models.audit import AuditLog
from app.models.config import SystemConfiguration
from app.utils.search import apply_search_and_pagination
import re
import bleach
import pandas as pd
import hashlib
import io
import os
from flask import send_file
from datetime import datetime
import phonenumbers
from phonenumbers import NumberParseException
import dns.resolver
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)


# ── Admin Dashboard ─────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@role_required('Admin')
def dashboard():
    """System-wide overview for Administrators with aggregated stats."""
    # Real Metrics
    user_count = User.query.count()
    event_count = Event.query.count()
    pending_count = Event.query.filter(Event.status.in_([
        EventStatus.Pending_Faculty, EventStatus.Pending_Head, EventStatus.Pending_Admin
    ])).count()
    
    # Total budget of approved events
    total_budget = db.session.query(func.sum(Event.budget)).filter(
        Event.status == EventStatus.Approved
    ).scalar() or 0.0

    escalated_events = Event.query.options(joinedload(Event.creator)).filter_by(
        status=EventStatus.Pending_Admin
    ).all()
    
    escalated_count = len(escalated_events)
    approved_count = Event.query.filter(Event.status == EventStatus.Approved).count()

    # Recent Events with Joined Loads (Optimization)
    recent_events = Event.query.options(
        joinedload(Event.creator)
    ).order_by(Event.created_at.desc()).limit(10).all()

    # Escalated Events
    escalated_events = Event.query.filter_by(status=EventStatus.Pending_Admin).options(joinedload(Event.creator)).all()

    # Recent Audit Logs
    recent_logs = AuditLog.query.options(
        joinedload(AuditLog.user)
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()

    # Security Alert Check (Task #21)
    integrity_compromised = False
    last_verified_hash = SystemConfiguration.get_setting('last_verified_hash', '')
    if last_verified_hash:
        hasher = hashlib.sha256()
        logs = AuditLog.query.order_by(AuditLog.timestamp.asc()).all()
        for log in logs:
            log_data = f"{log.id}|{log.timestamp}|{log.user_id}|{log.action_type}|{log.details}"
            hasher.update(log_data.encode('utf-8'))
        if hasher.hexdigest() != last_verified_hash:
            integrity_compromised = True

    return render_template('admin/dashboard.html',
                           user_count=user_count,
                           event_count=event_count,
                           pending_count=pending_count,
                           escalated_count=escalated_count,
                           approved_count=approved_count,
                           total_budget=total_budget,
                           recent_events=recent_events,
                           escalated_events=escalated_events,
                           recent_logs=recent_logs,
                           integrity_compromised=integrity_compromised)


# ── Audit Logs ──────────────────────────────────────────────────────
@admin_bp.route('/audit-logs')
@login_required
@role_required('Admin')
def audit_logs():
    """Viewable only by Admins. Display filterable table of all actions."""
    query = AuditLog.query.options(joinedload(AuditLog.user))

    pagination, search_query = apply_search_and_pagination(
        query,
        AuditLog,
        search_fields=['details', 'action_type', 'entity_type'],
        filter_params={'action_type': request.args.get('action_type')}
    )

    return render_template('admin/audit_logs.html',
                           pagination=pagination,
                           search_query=search_query)


@admin_bp.route('/audit/export')
@login_required
@role_required('Admin')
def export_audit_logs():
    """Export Audit Logs to Excel."""
    logs = AuditLog.query.options(joinedload(AuditLog.user)).order_by(AuditLog.timestamp.desc()).all()
    
    data = []
    for log in logs:
        data.append({
            'Timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'User': log.user.username if log.user else 'System/Deleted',
            'Action': log.action_type,
            'Entity': f"{log.entity_type} ({log.entity_id})" if log.entity_type else 'N/A',
            'Details': log.details,
            'IP Address': log.ip_address
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Audit Logs')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'Audit_Logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@admin_bp.route('/audit/verify')
@login_required
@role_required('Admin')
def verify_audit_integrity():
    """Verify integrity of Audit logs using SHA-256 hashing."""
    logs = AuditLog.query.order_by(AuditLog.timestamp.asc()).all()
    
    # Calculate current master hash
    hasher = hashlib.sha256()
    for log in logs:
        log_data = f"{log.id}|{log.timestamp}|{log.user_id}|{log.action_type}|{log.details}"
        hasher.update(log_data.encode('utf-8'))
    
    current_hash = hasher.hexdigest()
    last_verified_hash = SystemConfiguration.get_setting('last_verified_hash', '')
    
    if not last_verified_hash:
        # First time verification, save the current hash
        SystemConfiguration.set_setting('last_verified_hash', current_hash, "Last verified audit trail hash")
        flash("Initial integrity hash established. Audit Trail Integrity Verified.", "success")
        return redirect(url_for('admin.audit_logs'))
    
    if current_hash == last_verified_hash:
        flash("Audit Trail Integrity Verified.", "success")
    else:
        # Log this mismatch
        log_action('INTEGRITY_FAILURE', 'SYSTEM', 0, "TAMPERING DETECTED: Log integrity compromised.")
        flash("TAMPERING DETECTED: Log integrity compromised.", "danger")
    
    return redirect(url_for('admin.audit_logs'))


@admin_bp.route('/audit/clear', methods=['POST'])
@login_required
@role_required('Admin')
def clear_audit_logs():
    """Clear all audit logs after archiving to CSV."""
    confirm_text = request.form.get('confirm_text')
    if confirm_text != 'DELETE':
        flash("Confirmation failed. Type 'DELETE' to confirm clearing logs.", "warning")
        return redirect(url_for('admin.audit_logs'))

    # Archive to CSV first
    import csv
    from io import StringIO
    
    logs = AuditLog.query.options(joinedload(AuditLog.user)).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Timestamp', 'User', 'Action', 'Entity', 'Details', 'IP'])
    
    for l in logs:
        cw.writerow([l.timestamp, l.user.username if l.user else 'N/A', l.action_type, f"{l.entity_type}({l.entity_id})", l.details, l.ip_address])
    
    backup_dir = os.path.join('instance', 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    filename = f"audit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(os.path.join(backup_dir, filename), 'w') as f:
        f.write(si.getvalue())

    # Log the action BEFORE clearing
    log_action('CLEAR_AUDIT', 'SYSTEM', 0, f"Admin cleared audit logs. Backup saved as {filename}")
    db.session.commit()
    
    # Get all log IDs except the very last one (which is the CLEAR_AUDIT log)
    last_log = AuditLog.query.order_by(AuditLog.id.desc()).first()
    if last_log:
        AuditLog.query.filter(AuditLog.id != last_log.id).delete()
        db.session.commit()
        
        # Reset integrity hash because logs changed
        hasher = hashlib.sha256()
        log_data = f"{last_log.id}|{last_log.timestamp}|{last_log.user_id}|{last_log.action_type}|{last_log.details}"
        hasher.update(log_data.encode('utf-8'))
        SystemConfiguration.set_setting('last_verified_hash', hasher.hexdigest())

    flash(f"Audit logs cleared. Backup saved to {filename}.", "success")
    return redirect(url_for('admin.audit_logs'))


# ── User Management ────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@role_required('Admin')
def list_users():
    """List all users with search and pagination."""
    query = User.query
    pagination, search_query = apply_search_and_pagination(
        query,
        User,
        search_fields=['username', 'email', 'department']
    )
    return render_template('admin/manage_users.html',
                           pagination=pagination,
                           search_query=search_query)


@admin_bp.route('/manage-users')
@login_required
@role_required('Admin')
def manage_users():
    """Alias for list_users."""
    return list_users()

@admin_bp.route('/users/export')
@login_required
@role_required('Admin')
def export_users():
    """Export Users to Excel."""
    users = User.query.order_by(User.username).all()
    
    data = []
    for user in users:
        data.append({
            'User ID': user.id,
            'Username': user.username,
            'Full Name': user.full_name,
            'Email': user.email,
            'Role': user.role.value if user.role else 'N/A',
            'Department': user.department,
            'Contact Method': user.contact_number,
            'Status': 'Active' if user.is_active else 'Inactive',
            'Last Login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Users')
    
    output.seek(0)
    
    # Audit log the export
    log_action('EXPORT', 'SYSTEM', current_user.id, "Admin exported user list to Excel.")
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'User_Directory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
@limiter.limit("10 per minute")
def create_user():
    """Admin can create new user accounts."""
    role_map = {
        'Student': UserRole.Student,
        'Faculty': UserRole.Faculty,
        'Department Head': UserRole.DeptHead,
        'Admin': UserRole.Admin,
        'Guest': UserRole.Guest
    }
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        role_val = request.form.get('role')
        department = request.form.get('department')
        country_code = request.form.get('country_code')
        phone_raw = request.form.get('contact_number')

        errors = []

        # 1. Basic Validation
        if not all([username, password, confirm_password, email, full_name, role_val, department, country_code, phone_raw]):
            errors.append("All fields are required.")
        
        # 2. Username Uniqueness
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists.")

        # 3. Email Uniqueness and Format
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Invalid email format.")

        # 4. Password Match
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # 5. Password Strength (Section 12.3)
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
            errors.append("Password must contain mixed case letters (uppercase and lowercase) and numbers.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character.")

        # 6. Data Sanitization (XSS Prevention)
        full_name = bleach.clean(full_name)
        department = bleach.clean(department)

        # 7. Email Domain Validation (Section 12.4)
        domain = email.split('@')[-1] if '@' in email else ''
        allowed_tlds = {
            'com', 'net', 'org', 'co', 'info', 'xyz', 'biz', 'ai', 'io', 'app', 'tech', 'site', 'online', 'shop', 'dev',
            'uk', 'de', 'in', 'us', 'ca', 'br', 'fr', 'jp', 'ru', 'tv',
            'edu', 'gov', 'pro', 'club', 'blog', 'store', 'studio', 'solutions', 'global', 'agency'
        }
        tld = domain.split('.')[-1].lower() if '.' in domain else ''
        if tld not in allowed_tlds:
            errors.append("Invalid email domain TLD. Please use a recognized professional extension.")
        else:
            try:
                dns.resolver.resolve(domain, 'MX')
            except:
                errors.append("Invalid email domain: No mail server found.")

        # 8. Contact Number Validation
        full_number = f"{country_code}{phone_raw}"
        try:
            parsed_number = phonenumbers.parse(full_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                errors.append("Invalid phone number format for selected country.")
            else:
                final_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            errors.append("Could not parse phone number.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template('admin/create_user.html', 
                                   values=request.form, 
                                   roles=role_map.keys())

        # 9. Success: Create User
        new_user = User(
            username=username,
            full_name=full_name,
            email=email,
            role=role_map[role_val],
            department=department,
            contact_number=final_phone,
            is_active=True
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        # 10. Audit Logging
        log_action('CREATE_USER', 'USER', new_user.id, 
                   f"Admin created user {username} with role {role_val}.")
        flash(f"User '{username}' created successfully.", "success")
        return redirect(url_for('admin.list_users'))

    return render_template('admin/create_user.html', roles=role_map.keys())

@admin_bp.route('/update_role/<int:user_id>', methods=['POST'])
@login_required
@role_required('Admin')
def update_role(user_id):
    """Update a user's role."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot change your own role.", "danger")
        return redirect(url_for('admin.list_users'))

    new_role_val = request.form.get('new_role')
    
    # Map string value back to Enum
    role_map = {
        'Student': UserRole.Student,
        'Faculty': UserRole.Faculty,
        'Department Head': UserRole.DeptHead,
        'Admin': UserRole.Admin,
        'Guest': UserRole.Guest
    }
    
    if new_role_val in role_map:
        old_role = user.role.value
        user.role = role_map[new_role_val]
        db.session.commit()
        log_action('EDIT', 'USER', user_id, f"Role updated from {old_role} to {new_role_val} for {user.username}")
        flash(f"Role updated successfully for {user.username}.", "success")
    else:
        flash("Invalid role selected.", "danger")
        
    return redirect(url_for('admin.list_users'))


# ── All Events ──────────────────────────────────────────────────────
@admin_bp.route('/all-reports')
@login_required
@role_required('Admin')
def all_events():
    """View all events in the system with advanced filtering."""
    query = Event.query.options(joinedload(Event.creator))
    
    # ── Advanced Filters ──────────────────────────────────────────
    status = request.args.get('status')
    event_type = request.args.get('event_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if status and status != 'All':
        query = query.filter(Event.status == status)
    
    if event_type and event_type != 'All':
        query = query.filter(Event.event_type == event_type)
        
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Event.event_date >= sd)
        except ValueError: pass
        
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Event.event_date <= ed)
        except ValueError: pass

    pagination, search_query = apply_search_and_pagination(
        query, Event, search_fields=['title', 'venue']
    )
    return render_template('admin/all_events.html',
                           pagination=pagination,
                           search_query=search_query,
                           current_status=status,
                           current_type=event_type,
                           start_date=start_date,
                           end_date=end_date)


@admin_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_event(event_id):
    """Admin can delete any event. Cascade handles approvals."""
    event = Event.query.get_or_404(event_id)
    title = event.title
    ref_id = event.reference_id

    # Audit Logging
    log_action('DELETE', 'EVENT', event_id, f"Admin deleted event: {title} (Ref: {ref_id})")
    
    db.session.delete(event)
    db.session.commit()
    
    flash(f"Event '{title}' ({ref_id}) deleted successfully.", "success")
    return redirect(url_for('admin.all_events'))


# ── Workflow Analytics ──────────────────────────────────────────────
@admin_bp.route('/workflow-analytics')
@login_required
@role_required('Admin')
def workflow_analytics():
    """Workflow analytics dashboard."""
    return render_template('admin/workflow_analytics.html')


# ── Delete User (Orphan-Safe) ───────────────────────────────────────
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_user(user_id):
    """
    Delete a user but preserve their event history.
    Sets created_by to NULL so events show as "Deleted User" in templates.
    This prevents orphaned records or cascading deletes.
    """
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for('admin.list_users'))

    username = user.username
    user_role = user.role.value

    # ORPHAN PROTECTION: Set created_by to NULL on all events by this user
    events_by_user = Event.query.filter_by(created_by=user.id).all()
    for event in events_by_user:
        event.created_by = None  # Will display as "Deleted User" in templates

    # ORPHAN PROTECTION: Set approver reference to NULL on approvals
    approvals_by_user = Approval.query.filter_by(approver_id=user.id).all()
    for approval in approvals_by_user:
        approval.approver_id = None

    # ORPHAN PROTECTION: Nullify audit log user references
    audit_logs_by_user = AuditLog.query.filter_by(user_id=user.id).all()
    for log in audit_logs_by_user:
        log.user_id = None

    db.session.delete(user)
    db.session.commit()

    log_action('DELETE', 'USER', user_id,
               f"Deleted user: {username} ({user_role}). "
               f"{len(events_by_user)} events preserved with NULL creator.")
    flash(f"User '{username}' deleted. {len(events_by_user)} event(s) preserved.", "success")
    return redirect(url_for('admin.list_users'))


# ── Reassign Events ────────────────────────────────────────────────
@admin_bp.route('/reassign-events', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def reassign_events():
    """
    Reassign pending events from a deactivated/deleted user to a new approver.
    Useful when a faculty/dept head account is deactivated.
    """
    if request.method == 'POST':
        old_user_id = request.form.get('old_user_id')
        new_user_id = request.form.get('new_user_id')

        if not old_user_id or not new_user_id:
            flash("Please select both source and destination users.", "warning")
        elif old_user_id == new_user_id:
            flash("Source and destination users cannot be the same.", "warning")
        else:
            # Reassign created events
            events = Event.query.filter_by(created_by=int(old_user_id)).all()
            reassign_count = len(events)
            for e in events:
                e.created_by = int(new_user_id)

            db.session.commit()
            log_action('REASSIGN', 'USER', int(old_user_id),
                       f"Reassigned {reassign_count} events to user ID {new_user_id}")
            flash(f"Successfully reassigned {reassign_count} event(s).", "success")
            return redirect(url_for('admin.dashboard'))

    users = User.query.order_by(User.username).all()
    return render_template('admin/reassign_events.html', users=users)


# ── Toggle User Active Status ──────────────────────────────────────
@admin_bp.route('/users/toggle-status/<int:user_id>', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_user_status(user_id):
    """Toggle user active status (activate/deactivate)."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot deactivate yourself.", "warning")
    else:
        user.is_active = not user.is_active
        db.session.commit()

        action = "Activated" if user.is_active else "Deactivated"
        log_action('STATUS_CHANGE', 'USER', user_id,
                   f"{action} user: {user.username}")
        flash(f"User '{user.username}' has been {action.lower()}.", "info")
    return redirect(url_for('admin.list_users'))


# ── Export Events as CSV ────────────────────────────────────────────
@admin_bp.route('/export/events')
@login_required
@role_required('Admin')
def export_reports():
    """Export all events as CSV."""
    import csv
    from io import StringIO
    from flask import Response

    events = Event.query.options(joinedload(Event.creator)).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Reference', 'Title', 'Creator', 'Status', 'Date', 'Budget (₹)', 'Urgent'])

    for event in events:
        cw.writerow([
            event.reference_id,
            event.title,
            event.creator.username if event.creator else 'Deleted User',
            event.status.value,
            event.event_date.strftime('%Y-%m-%d'),
            event.budget,
            'Yes' if event.is_urgent else 'No'
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=event_reports.csv"}
    )


@admin_bp.route('/config/maintenance/toggle', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_maintenance_mode():
    """Toggle maintenance mode status."""
    current_mode = SystemConfiguration.get_setting('maintenance_mode', False)
    new_mode = not current_mode
    SystemConfiguration.set_setting('maintenance_mode', new_mode)
    
    msg = request.form.get('maintenance_message')
    if msg:
        SystemConfiguration.set_setting('maintenance_message', msg)
        
    status = "ENABLED" if new_mode else "DISABLED"
    log_action('CONFIG_CHANGE', 'SYSTEM', 0, f"Maintenance mode {status}")
    flash(f"Maintenance mode {status}.", "success")
    
    return redirect(url_for('admin.system_settings'))


# ── System Settings ────────────────────────────────────────────────
@admin_bp.route('/system-settings')
@login_required
@role_required('Admin')
def system_settings():
    """System settings page."""
    maintenance_mode = SystemConfiguration.get_setting('maintenance_mode', False)
    maintenance_message = SystemConfiguration.get_setting('maintenance_message', '')
    return render_template('admin/system_settings.html', 
                           title="System Settings",
                           maintenance_mode=maintenance_mode,
                           maintenance_message=maintenance_message)
