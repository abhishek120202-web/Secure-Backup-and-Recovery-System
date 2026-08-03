#!/usr/bin/env python
"""
Database Initialization Script

Creates all database tables from SQLAlchemy models and optionally creates
a default admin user for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_db():
    """Initialize the database with tables and seed data."""
    from app import create_app, db
    from app.models import User, VirtualMachine, Backup, AuditLog
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("DATABASE INITIALIZATION".center(70))
        print("=" * 70)
        print()
        
        # Create all tables
        print("Creating database tables from models...")
        try:
            db.create_all()
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return False
        
        print()
        
        seed_accounts = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'full_name': 'System Administrator',
                'role': 'admin',
                'password': 'admin123',
                'label': 'Admin'
            },
            {
                'username': 'general',
                'email': 'general@example.com',
                'full_name': 'General User',
                'role': 'operator',
                'password': 'general123',
                'label': 'General'
            }
        ]

        for account in seed_accounts:
            existing_user = User.query.filter_by(username=account['username']).first()
            if existing_user:
                print(f"ℹ {account['label']} user already exists")
                print(f"  Username: {account['username']}")
                print(f"  Email: {existing_user.email}")
                print(f"  Role: {existing_user.role}")
            else:
                print(f"Creating default {account['label'].lower()} user...")
                try:
                    user = User(
                        username=account['username'],
                        email=account['email'],
                        full_name=account['full_name'],
                        role=account['role'],
                        is_active=True
                    )
                    user.set_password(account['password'])
                    db.session.add(user)
                    db.session.commit()
                    print(f"✓ {account['label']} user created successfully")
                    print()
                    print(f"Default {account['label']} Credentials:")
                    print(f"  Username: {account['username']}")
                    print(f"  Password: {account['password']}")
                    print(f"  Email: {account['email']}")
                except Exception as e:
                    db.session.rollback()
                    print(f"✗ Error creating {account['label'].lower()} user: {e}")
                    return False
            print()
        
        print("=" * 70)
        print("DATABASE INITIALIZATION COMPLETE!".center(70))
        print("=" * 70)
        print()
        print("Database Information:")
        print(f"  Type: SQLite")
        print(f"  Path: instance/dev.db")
        print()
        print("Next Steps:")
        print("  1. Run: python run.py")
        print("  2. Open: http://localhost:5000")
        print("  3. Login with admin credentials above")
        print()
        
        return True


if __name__ == '__main__':
    success = init_db()
    exit(0 if success else 1)
