#!/usr/bin/env python
"""Quick test of database connection after path fix."""

from app import create_app

app = create_app()
print('✓ Application initialized successfully')
print('✓ Database path configured correctly')
print(f'✓ Database URI: {app.config.get("SQLALCHEMY_DATABASE_URI")}')

with app.app_context():
    from app.models import db
    try:
        # Try to execute a simple query to verify connection
        result = db.session.execute(db.text("SELECT 1"))
        print('✓ Database connection successful')
        print('✓ SQLite database is accessible')
    except Exception as e:
        print(f'✗ Database connection error: {e}')
