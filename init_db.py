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
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print("ℹ Admin user already exists")
            print(f"  Username: admin")
            print(f"  Email: {admin_user.email}")
        else:
            # Create default admin user
            print("Creating default admin user...")
            try:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    full_name='System Administrator',
                    role='admin',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✓ Admin user created successfully")
                print()
                print("Default Admin Credentials:")
                print("  Username: admin")
                print("  Password: admin123")
                print("  Email: admin@example.com")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error creating admin user: {e}")
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
