from flask import Blueprint, render_template, redirect, url_for, flash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    flash('Successfully logged out.', 'info')
    return redirect(url_for('main.index'))
