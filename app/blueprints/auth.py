"""
Auth Blueprint - Phase 6
Handles user registration, login, logout, CSRF token refresh,
and profile settings with rate limiting and session security.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from urllib.parse import urlparse
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import phonenumbers
from phonenumbers import NumberParseException
from app import db, limiter
from app.models.user import User, UserRole
from app.forms.auth_form import LoginForm, RegistrationForm
from app.utils.audit_helper import log_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour", error_message="Too many registration attempts. Please try again later.")
def register():
    """User registration with rate limiting."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        phone_raw = request.form.get('contact_number')
        country_code = request.form.get('country_code', '+91')
        
        full_number = f"{country_code}{phone_raw}"
        
        try:
            parsed_number = phonenumbers.parse(full_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                flash('Invalid phone number length or format for the selected country.', 'danger')
                return redirect(url_for('auth.register'))
            
            final_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            flash('Could not parse phone number. Please check country code and digits.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=form.username.data,
            email=form.email.data,
            role=UserRole.Student,
            department=form.department.data,
            contact_number=final_phone
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Mark as new user if last_login is None
        session['is_new_user'] = True
        user.last_login = datetime.now()
        db.session.add(user)
        db.session.commit()

        # Log the user in directly after registration
        session.permanent = True
        login_user(user)

        # AUDIT LOG
        log_action('CREATE', 'USER', user.id, f"Registered new user: {user.username}")

        flash('Registration successful! Welcome to EventFlow.', 'success')
        return redirect(url_for('events.student_dashboard'))

    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per hour", error_message="Too many login attempts. Please try again later.")
def login():
    """User login with rate limiting and active-status check."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))

        # Check if user account is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))

        session.permanent = True
        
        # Check if first time login
        session['is_new_user'] = (user.last_login is None)
        user.last_login = datetime.now()
        db.session.commit()
        
        login_user(user, remember=form.remember.data)

        # AUDIT LOG
        log_action('LOGIN', 'USER', user.id, f"User logged in: {user.username}")

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.role.value == 'Admin':
                next_page = url_for('admin.dashboard')
            elif user.role.value == 'Department Head':
                next_page = url_for('dept_head.dashboard')
            elif user.role.value == 'Faculty':
                next_page = url_for('faculty.dashboard')
            else:
                next_page = url_for('events.student_dashboard')

        flash(f'Logged in successfully as {user.role.value}.', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout with audit logging."""
    log_action('LOGOUT', 'USER', current_user.id, f"User logged out: {current_user.username}")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """
    Endpoint for AJAX to fetch a fresh CSRF token without page reload.
    Used by the CSRF lifecycle modal for long-lived forms.
    """
    return jsonify({'csrf_token': generate_csrf()})


@auth_bp.route('/profile-settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    """User profile and settings page."""
    if request.method == 'POST':
        # Handle Personal Info Update
        if 'update_info' in request.form:
            email = request.form.get('email')
            department = request.form.get('department')
            contact_number = request.form.get('contact_number')
            
            if email:
                current_user.email = email
            if department:
                current_user.department = department
            if contact_number:
                current_user.contact_number = contact_number
                
            db.session.commit()
            log_action('UPDATE_PROFILE', 'USER', current_user.id, f"User {current_user.username} updated profile info.")
            flash('Profile information updated successfully!', 'success')
            
        # Handle Password Update
        elif 'update_password' in request.form:
            old_password = request.form.get('old_pass')
            new_password = request.form.get('new_pass')
            confirm_password = request.form.get('confirm_pass')
            
            if not current_user.check_password(old_password):
                flash('Incorrect current password.', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
            elif len(new_password) < 8:
                flash('New password must be at least 8 characters long.', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                log_action('CHANGE_PASSWORD', 'USER', current_user.id, f"User {current_user.username} changed their password.")
                flash('Password updated successfully!', 'success')
                
        return redirect(url_for('auth.profile_settings'))
        
    return render_template('auth/profile_settings.html')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/profile/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    if 'profile_photo' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('auth.profile_settings'))
    file = request.files['profile_photo']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('auth.profile_settings'))
    if file and allowed_file(file.filename):
        file.seek(0, os.SEEK_END)
        size = file.tell()
        if size > 2 * 1024 * 1024:
            flash('File too large. Maximum size is 2MB.', 'danger')
            return redirect(url_for('auth.profile_settings'))
        file.seek(0)
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"user_{current_user.id}_{int(datetime.now().timestamp())}.{ext}")
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        current_user.profile_photo = filename
        db.session.commit()
        flash('Profile photo updated successfully', 'success')
    else:
        flash('Invalid file type. Only JPG and PNG are allowed.', 'danger')
    return redirect(url_for('auth.profile_settings'))
