import os
import sys

# Add parent directory to sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.event import Event
from app.models.approval import Approval
from app.models.audit import AuditLog
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("Starting system reset...")
    admin_user = User.query.filter_by(role=UserRole.Admin).first()
    
    if not admin_user:
        print("Error: No Admin user found!")
        # Alternatively, create an admin user
        admin_user = User(
            username='admin',
            email='admin@example.com',
            role=UserRole.Admin
        )
        admin_user.set_password('password')
        db.session.add(admin_user)
        db.session.commit()
        print("Created new default admin user.")
        
    admin_id = admin_user.id
    print(f"Preserving Admin User ID: {admin_id}")
    
    # Reset Admin credentials
    admin_user.username = 'admin'
    admin_user.password_hash = generate_password_hash('password')
    
    deleted_count = 0
    users_to_delete = User.query.filter(User.id != admin_id).all()
    
    for u in users_to_delete:
        # Nullify foreign keys for Events created by this user
        events = Event.query.filter_by(created_by=u.id).all()
        for e in events:
            e.created_by = None
            
        # Nullify foreign keys for Approvals by this user
        approvals = Approval.query.filter_by(approver_id=u.id).all()
        for a in approvals:
            a.approver_id = None
            
        # Nullify audit logs
        logs = AuditLog.query.filter_by(user_id=u.id).all()
        for l in logs:
            l.user_id = None
            
        db.session.delete(u)
        deleted_count += 1
        
    db.session.commit()
    print(f"System reset complete. Deleted {deleted_count} non-admin users.")
    print("Admin credentials reset to admin:password")
