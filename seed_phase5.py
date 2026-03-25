"""
Seed Phase 5 - Data Population Script
Creates 50+ dummy events for testing search, pagination, and audit logging.
Currency: Indian Rupee (₹)
"""
import random
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models.user import User, UserRole
from app.models.event import Event, EventStatus
from app.models.audit import AuditLog

def seed_phase5():
    app = create_app()
    with app.app_context():
        print("Cleaning up old audit logs and events for fresh seed...")
        # Optional: AuditLog.query.delete()
        # db.session.commit()

        # Get some users
        students = User.query.filter_by(role=UserRole.Student).all()
        if not students:
            print("No students found. Please run Phase 4 seed first.")
            return

        titles = [
            "Tech Symposium", "Annual Cultural Fest", "Cricket Tournament", 
            "Web Development Workshop", "AI & ML Seminar", "Design Thinking Workshop",
            "Photography Contest", "Music Night", "Dance Competition", "Hackathon 2026",
            "Startup Pitch Day", "Coding Challenge", "Robotics Exhibition",
            "Green Campus Drive", "Health Awareness Camp", "Career Fair",
            "Poetry Slam", "Drama Performance", "Gaming Tournament", "Chess Open"
        ]
        
        venues = ["Main Auditorium", "Block A Room 101", "Open Ground", "Computer Lab 3", "Conference Hall", "Mini Theater"]
        types = ["Workshop", "Seminar", "Competition", "Cultural", "Sports"]

        print(f"Seeding 60 events across {len(students)} students...")
        
        for i in range(60):
            creator = random.choice(students)
            title = f"{random.choice(titles)} vol.{i+1}"
            status = random.choice(list(EventStatus))
            
            # Currency in INR
            budget = random.randint(5000, 250000)
            
            event_date = datetime.now().date() + timedelta(days=random.randint(7, 60))
            
            event = Event(
                title=title,
                description=f"Automated test event description for {title}. This event involves various activities.",
                event_type=random.choice(types),
                venue=random.choice(venues),
                event_date=event_date,
                start_time=datetime.combine(event_date, datetime.min.time().replace(hour=10)),
                end_time=datetime.combine(event_date, datetime.min.time().replace(hour=17)),
                audience_type="Students",
                audience_size=random.randint(50, 500),
                budget=float(budget),
                budget_breakdown=f"Catering: ₹{budget*0.4:.0f}, Printing: ₹{budget*0.1:.0f}, Equipment: ₹{budget*0.5:.0f}",
                status=status,
                created_by=creator.id,
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
            )
            
            db.session.add(event)
            db.session.flush() # Get ID
            
            # Add audit log for creation
            log = AuditLog(
                user_id=creator.id,
                action_type='CREATE',
                entity_type='EVENT',
                entity_id=event.id,
                timestamp=event.created_at,
                ip_address="127.0.0.1",
                details=f"Seeded event: {title}"
            )
            db.session.add(log)

        db.session.commit()
        print("Successfully seeded 60 events with audit logs.")

if __name__ == "__main__":
    seed_phase5()
