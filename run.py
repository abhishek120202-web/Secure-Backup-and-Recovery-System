#!/usr/bin/env python
"""
Application Entry Point

Run the Secure VMware Backup and Recovery System Flask application.
"""

import os
from dotenv import load_dotenv
from app import create_app, db

# Load environment variables from .env file
load_dotenv()

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make database objects available in shell."""
    from app.models.user import User
    from app.models.vm import VirtualMachine
    from app.models.backup import Backup
    from app.models.audit_log import AuditLog
    
    return {
        'db': db,
        'User': User,
        'VirtualMachine': VirtualMachine,
        'Backup': Backup,
        'AuditLog': AuditLog
    }


if __name__ == '__main__':
    # Run development server
    debug = os.getenv('FLASK_DEBUG', True)
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=debug,
        use_reloader=True
    )
