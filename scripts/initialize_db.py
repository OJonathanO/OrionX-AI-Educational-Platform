"""Initialize the database and create an admin user.

Usage:
    python scripts/initialize_db.py [--admin-email EMAIL] [--admin-password PASSWORD] [--admin-name NAME]
"""
import argparse
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import init_db, SessionLocal
from app.models import User, UserRole, UserPreference
from app.core.security import hash_password


def create_admin_user(db, email: str, password: str, full_name: str = "Administrator"):
    """Create an admin user if one doesn't already exist."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"Admin user '{email}' already exists.")
        return existing

    admin = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole.admin,
        is_active=True,
    )
    db.add(admin)
    db.flush()

    prefs = UserPreference(
        user_id=admin.id,
        preferred_subjects="[]",
        default_answer_style="detailed",
        learning_goals="",
    )
    db.add(prefs)
    db.commit()
    print(f"Admin user '{email}' created successfully.")
    return admin


def main():
    parser = argparse.ArgumentParser(description="Initialize the database and create an admin user.")
    parser.add_argument("--admin-email", default="admin@example.com", help="Admin email address")
    parser.add_argument("--admin-password", default="admin123456", help="Admin password")
    parser.add_argument("--admin-name", default="Administrator", help="Admin full name")
    args = parser.parse_args()

    print("Initializing database...")
    init_db()
    print("Database tables created.")

    db = SessionLocal()
    try:
        create_admin_user(db, args.admin_email, args.admin_password, args.admin_name)
    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    main()
