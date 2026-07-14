"""
Models package for the Secure VMware Backup and Recovery System.

This package contains all SQLAlchemy models for the application.
"""

from flask_sqlalchemy import SQLAlchemy

# Shared database instance - all models use this
db = SQLAlchemy()

# Import models AFTER db is created to avoid circular imports
from app.models.user import User
from app.models.vm import VirtualMachine
from app.models.backup import Backup
from app.models.audit_log import AuditLog

__all__ = ['db', 'User', 'VirtualMachine', 'Backup', 'AuditLog']
