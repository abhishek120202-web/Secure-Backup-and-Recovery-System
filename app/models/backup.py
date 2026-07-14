"""
Backup model for backup records and metadata.
"""

from datetime import datetime

# Import shared db instance from models package
from app.models import db


class Backup(db.Model):
    """
    Backup model representing a backup of a virtual machine.
    
    Attributes:
        id: Primary key
        vm_id: Foreign key referencing VirtualMachine
        backup_name: Name/identifier for the backup
        backup_path: File system path to the backup file
        file_size_bytes: Size of the backup file in bytes
        compression_ratio: Compression ratio (original_size / compressed_size)
        status: Backup status (completed, in_progress, failed)
        encryption_algorithm: Algorithm used for encryption (AES-256)
        integrity_hash: SHA-256 hash for integrity verification
        backup_type: Type of backup (full, incremental, differential)
        created_at: Timestamp of backup creation
        completed_at: Timestamp of backup completion
        expires_at: Timestamp when backup expires (retention policy)
        notes: Additional notes about the backup
    """
    
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    vm_id = db.Column(db.Integer, db.ForeignKey('virtual_machines.id'), nullable=False, index=True)
    backup_name = db.Column(db.String(255), nullable=False)
    backup_path = db.Column(db.String(500), nullable=False, unique=True)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)
    compression_ratio = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(32), default='in_progress', nullable=False, index=True)
    encryption_algorithm = db.Column(db.String(64), default='AES-256', nullable=False)
    integrity_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash
    backup_type = db.Column(db.String(32), default='full', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='backup', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_complete(self) -> bool:
        """Check if backup is completed."""
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """Check if backup failed."""
        return self.status == 'failed'
    
    def is_expired(self) -> bool:
        """Check if backup has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_file_size_mb(self) -> float:
        """Get backup file size in MB."""
        if self.file_size_bytes is None:
            return 0.0
        return self.file_size_bytes / (1024 * 1024)
    
    def __repr__(self) -> str:
        return f'<Backup {self.backup_name}>'
