from app import create_app, db
app = create_app('dev')
with app.app_context():
    print(f"DATABASE_URI: {db.engine.url}")
