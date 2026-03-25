from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app.models.event import Event
from app.models.audit import AuditLog
from sqlalchemy.orm import joinedload
from datetime import datetime
import pandas as pd
import io
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/report/download')
@login_required
def download_my_report():
    """Generate Excel report of current user's events."""
    events = Event.query.filter_by(created_by=current_user.id).all()
    
    data = []
    for event in events:
        data.append({
            'Reference ID': event.reference_id,
            'Title': event.title,
            'Status': event.status.value,
            'Event Date': event.event_date.strftime('%Y-%m-%d'),
            'Venue': event.venue,
            'Budget (₹)': event.budget,
            'Created At': event.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='My Events')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'My_Events_Report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )
