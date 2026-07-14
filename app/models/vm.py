"""
Virtual Machine model for VMware VM management.
"""

from datetime import datetime

# Import shared db instance from models package
from app.models import db


class VirtualMachine(db.Model):
    """
    Virtual Machine model representing a VMware Workstation VM.
    
    Attributes:
        id: Primary key
        name: Virtual machine name
        vm_path: File system path to the VM
        uuid: Unique identifier for the VM
        status: Current status (active, paused, stopped)
        memory_mb: Amount of RAM allocated (MB)
        cpu_cores: Number of CPU cores
        disk_size_gb: Total disk size (GB)
        description: VM description
        created_at: Timestamp of VM addition
        updated_at: Timestamp of last update
    """
    
    __tablename__ = 'virtual_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    vm_path = db.Column(db.String(500), nullable=False, unique=True)
    uuid = db.Column(db.String(36), unique=True, nullable=True)
    status = db.Column(db.String(32), default='active', nullable=False)
    memory_mb = db.Column(db.Integer, nullable=True)
    cpu_cores = db.Column(db.Integer, nullable=True)
    disk_size_gb = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    backups = db.relationship('Backup', backref='virtual_machine', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='virtual_machine', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_last_backup(self):
        """Get the most recent backup for this VM."""
        return self.backups.order_by(Backup.created_at.desc()).first()
    
    def is_active(self) -> bool:
        """Check if VM is in active status."""
        return self.status == 'active'
    
    def __repr__(self) -> str:
        return f'<VirtualMachine {self.name}>'
