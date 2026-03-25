"""
Seed Script - Phase 4
Creates sample users and events to test the approval workflow.
"""
from app import create_app, db
from app.models.user import User, UserRole
from app.models.event import Event, EventStatus
from app.models.approval import Approval, ApprovalDecision, ApprovalLevel
from datetime import datetime, timedelta, date

def seed_data():
    app = create_app()
    with app.app_context():
        # 1. Create Users
        users = {
            'student': {'username': 'student_test', 'email': 'student@example.com', 'role': UserRole.Student, 'password': 'password123'},
            'faculty': {'username': 'faculty_test', 'email': 'faculty@example.com', 'role': UserRole.Faculty, 'password': 'password123'},
            'head': {'username': 'head_test', 'email': 'head@example.com', 'role': UserRole.DeptHead, 'password': 'password123'},
            'admin': {'username': 'admin_test', 'email': 'admin@example.com', 'role': UserRole.Admin, 'password': 'password123'}
        }

        created_users = {}
        for key, data in users.items():
            user = User.query.filter_by(username=data['username']).first()
            if not user:
                user = User(username=data['username'], email=data['email'], role=data['role'])
                user.set_password(data['password'])
                db.session.add(user)
                print(f"Created user: {data['username']}")
            created_users[key] = user

        db.session.commit()

        # 2. Clear existing events for clean test (optional, but good for repeatability)
        # db.session.query(Approval).delete()
        # db.session.query(Event).delete()
        # db.session.commit()

        # 3. Create Events
        
        # Event 1: Pending Faculty
        if not Event.query.filter_by(title="Annual Tech Symposium").first():
            e1 = Event(
                title="Annual Tech Symposium",
                description="A large scale technology symposium for students.",
                event_type="Seminar",
                venue="Main Auditorium",
                event_date=date.today() + timedelta(days=30),
                start_time=datetime.now() + timedelta(days=30),
                end_time=datetime.now() + timedelta(days=30, hours=4),
                status=EventStatus.Pending_Faculty,
                current_approver_role='Faculty',
                created_by=created_users['student'].id,
                budget=1500.0,
                audience_size=200
            )
            db.session.add(e1)

        # Event 2: Pending Dept Head (Approved by Faculty)
        if not Event.query.filter_by(title="Career Fair 2026").first():
            e2 = Event(
                title="Career Fair 2026",
                description="Connect with industry leaders and find internships.",
                event_type="Workshop",
                venue="Exhibition Hall",
                event_date=date.today() + timedelta(days=45),
                start_time=datetime.now() + timedelta(days=45),
                end_time=datetime.now() + timedelta(days=45, hours=8),
                status=EventStatus.Pending_Head,
                current_approver_role='Department Head',
                created_by=created_users['student'].id,
                budget=5000.0,
                audience_size=500
            )
            db.session.add(e2)
            db.session.flush() # Get ID
            
            # Faculty Approval Log
            app1 = Approval(
                event_id=e2.id,
                approver_id=created_users['faculty'].id,
                level=ApprovalLevel.Faculty,
                decision=ApprovalDecision.Approved,
                comments="Looks good, passed to Dept Head."
            )
            db.session.add(app1)

        # Event 3: Changes Requested by Faculty
        if not Event.query.filter_by(title="Music Under the Stars").first():
            e3 = Event(
                title="Music Under the Stars",
                description="An outdoor musical evening for the campus community.",
                event_type="Others",
                venue="Campus Terrace",
                event_date=date.today() + timedelta(days=15),
                start_time=datetime.now() + timedelta(days=15),
                end_time=datetime.now() + timedelta(days=15, hours=3),
                status=EventStatus.Changes_Requested,
                current_approver_role='Student',
                created_by=created_users['student'].id,
                budget=800.0,
                audience_size=100,
                rejection_reason="Please provide a more detailed budget breakdown."
            )
            db.session.add(e3)
            db.session.flush()
            
            # Faculty Change Request Log
            app2 = Approval(
                event_id=e3.id,
                approver_id=created_users['faculty'].id,
                level=ApprovalLevel.Faculty,
                decision=ApprovalDecision.Changes_Requested,
                comments="Please provide a more detailed budget breakdown."
            )
            db.session.add(app2)

        db.session.commit()
        print("Phase 4 seed data created successfully.")

if __name__ == "__main__":
    seed_data()
