from flask import Blueprint, render_template

event_bp = Blueprint('event', __name__)

@event_bp.route('/create')
def create():
    return render_template('event/create.html')
