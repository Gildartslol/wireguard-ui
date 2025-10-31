#!/usr/bin/env python3
"""
Script to create an admin user for WireGuard UI
"""

from app import create_app
from models import db, User
import getpass
import sys


def create_admin_user():
    """Create admin user interactively"""
    print("=" * 60)
    print("WireGuard UI - Create Admin User")
    print("=" * 60)
    print()

    # Get username
    while True:
        username = input("Enter admin username: ").strip()
        if username:
            break
        print("Username cannot be empty!")

    # Check if user already exists
    app = create_app()
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"\nError: User '{username}' already exists!")
            sys.exit(1)

    # Get email (optional)
    email = input("Enter admin email (optional): ").strip()
    if not email:
        email = None

    # Get password
    while True:
        password = getpass.getpass("Enter admin password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters!")
            continue

        password_confirm = getpass.getpass("Confirm admin password: ")
        if password != password_confirm:
            print("Passwords do not match!")
            continue

        break

    # Create user
    print("\nCreating admin user...")

    with app.app_context():
        admin_user = User(
            username=username,
            email=email,
            is_admin=True,
            is_active=True
        )
        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"  ID: {admin_user.id}")
        print(f"  Email: {admin_user.email or 'Not set'}")
        print(f"  Admin: {admin_user.is_admin}")
        print()


if __name__ == '__main__':
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
