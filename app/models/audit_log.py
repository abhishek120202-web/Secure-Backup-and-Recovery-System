"""
Audit Log model for tracking system activities and security events.
"""

from datetime import datetime

# Import shared db instance from models package
from app.models import db


class AuditLog(db.Model):
    """
    Audit Log model for tracking user actions and system events.
    
    Attributes:
        id: Primary key
        user_id: Foreign key referencing User
        vm_id: Foreign key referencing VirtualMachine (optional)
        backup_id: Foreign key referencing Backup (optional)
        action: Type of action performed
        action_status: Status of action (success, failure)
        details: Detailed description of the action
        ip_address: IP address of the request origin
        user_agent: User agent string from the request
        created_at: Timestamp of the audit log entry
    """
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vm_id = db.Column(db.Integer, db.ForeignKey('virtual_machines.id'), nullable=True, index=True)
    backup_id = db.Column(db.Integer, db.ForeignKey('backups.id'), nullable=True, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    action_status = db.Column(db.String(32), default='success', nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def is_success(self) -> bool:
        """Check if action was successful."""
        return self.action_status == 'success'
    
    def is_failure(self) -> bool:
        """Check if action failed."""
        return self.action_status == 'failure'
    
    def __repr__(self) -> str:
        return f'<AuditLog {self.action} - {self.created_at}>'
