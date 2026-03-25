from flask import Blueprint, render_template, current_app, redirect, url_for, request
from flask_login import login_required, current_user
from app.utils.decorators import role_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """System Home Page."""
    return render_template('main/index.html', status="Operational")

@main_bp.route('/get-started')
def get_started():
    """Dynamic starting point redirection."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.path))
    
    # Redirection based on role
    if current_user.role.name == 'Student':
        return redirect(url_for('events.student_dashboard'))
    elif current_user.role.name == 'Faculty':
        return redirect(url_for('faculty.dashboard'))
    elif current_user.role.name == 'DeptHead':
        return redirect(url_for('dept_head.dashboard'))
    elif current_user.role.name == 'Admin':
        return redirect(url_for('admin.dashboard'))
    
    return redirect(url_for('main.index'))

@main_bp.route('/about')
def about():
    """Project Information Page."""
    return render_template('main/about.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Generic dashboard entry point - redirects to role-specific dashboard."""
    return redirect(url_for('main.get_started'))

@main_bp.route('/dashboard/student')
@login_required
@role_required('Student')
def student_dashboard():
    return redirect(url_for('events.student_dashboard'))

@main_bp.route('/dashboard/faculty')
@login_required
@role_required('Faculty')
def faculty_dashboard():
    return redirect(url_for('faculty.dashboard'))

@main_bp.route('/dashboard/dept-head')
@login_required
@role_required('Department Head')
def dept_head_dashboard():
    return redirect(url_for('dept_head.dashboard'))

@main_bp.route('/help')
def help():
    """System Help and Support Page."""
    return render_template('main/help_support.html')
