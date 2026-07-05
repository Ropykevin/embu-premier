"""One-off script to create database tables and seed data."""
from app import create_app, db
from app.db_init import init_database

app = create_app()

with app.app_context():
    init_database(seed_sample_doctors=True)

print("Done. Restart the app with: python run.py")
