"""
Backup services module.

This module contains business logic for backup operations.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import current_app

from app.models import db
from app.models.backup import Backup
from app.models.vm import VirtualMachine


class BackupService:
    """Service class for backup operations."""

    def __init__(self):
        """Initialize BackupService."""
        self.backup_folder = Path(current_app.config.get('BACKUP_FOLDER', 'backups/'))

    def create_backup(self, backup_id: int, backup_type: str = 'full') -> bool:
        """
        Create a real backup snapshot for a database backup record.

        Args:
            backup_id: ID of the backup record to update
            backup_type: Type of backup (full, incremental, differential)

        Returns:
            True if backup created successfully, False otherwise
        """
        backup = Backup.query.get(backup_id)
        if not backup:
            return False

        vm = VirtualMachine.query.get(backup.vm_id)
        if not vm:
            backup.status = 'failed'
            backup.notes = 'Referenced VM could not be found.'
            db.session.commit()
            return False

        self.backup_folder.mkdir(parents=True, exist_ok=True)

        source_path = Path(vm.vm_path)
        if not source_path.exists():
            backup.status = 'failed'
            backup.notes = f'VM source path does not exist: {source_path}'
            backup.completed_at = datetime.utcnow()
            db.session.commit()
            return False

        backup.status = 'in_progress'
        backup.progress = 5
        backup.notes = f'Creating {backup_type} backup for {vm.name}'
        backup.backup_type = backup_type
        db.session.commit()

        snapshot_dir = self.backup_folder / f"{backup.backup_name}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        items = list(source_path.iterdir())
        if not items:
            backup.progress = 25
            backup.notes = f'No files found in VM source path {source_path}'
            db.session.commit()

        # Create a real snapshot copy of the VM directory contents.
        for index, item in enumerate(items, start=1):
            src = item
            dst = snapshot_dir / item.name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            progress = 10 + int((index / max(len(items), 1)) * 70)
            backup.progress = progress
            backup.notes = f'Copied {index}/{len(items)} items for {vm.name}'
            db.session.commit()

        # Persist a metadata file with VM information.
        metadata_path = snapshot_dir / 'backup_metadata.json'
        metadata_path.write_text(
            '{"vm_name": "%s", "vm_path": "%s", "created_at": "%s", "backup_type": "%s"}\n'
            % (vm.name, str(source_path), datetime.utcnow().isoformat(), backup_type),
            encoding='utf-8'
        )

        backup.progress = 90
        backup.notes = 'Finalizing backup and calculating checksum'
        db.session.commit()

        backup.backup_path = str(snapshot_dir)
        backup.file_size_bytes = self._directory_size(snapshot_dir)
        backup.status = 'completed'
        backup.progress = 100
        backup.completed_at = datetime.utcnow()
        backup.integrity_hash = self.generate_integrity_hash(str(snapshot_dir))
        backup.notes = f'Backup completed successfully for {vm.name}'
        db.session.commit()
        return True

    def compress_backup(self, backup_path: str) -> bool:
        """Compress a backup directory into a .zip file."""
        path = Path(backup_path)
        if not path.exists():
            return False
        archive_path = path.with_suffix('.zip')
        shutil.make_archive(str(path), 'zip', str(path.parent), path.name)
        return archive_path.exists()

    def encrypt_backup(self, backup_path: str, encryption_key: str) -> bool:
        """Placeholder encryption routine for backup files."""
        return True

    def generate_integrity_hash(self, backup_path: str) -> str:
        """Generate SHA-256 hash for a directory tree."""
        digest = hashlib.sha256()
        path = Path(backup_path)
        if not path.exists():
            return ''

        for file_path in sorted(path.rglob('*')):
            if file_path.is_file():
                digest.update(str(file_path.relative_to(path)).encode('utf-8'))
                with file_path.open('rb') as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                        digest.update(chunk)
        return digest.hexdigest()

    def delete_backup(self, backup_id: int) -> bool:
        """Delete a backup directory from disk and database."""
        backup = Backup.query.get(backup_id)
        if not backup:
            return False

        backup_path = Path(backup.backup_path)
        if backup_path.exists():
            shutil.rmtree(backup_path, ignore_errors=True)
        db.session.delete(backup)
        db.session.commit()
        return True

    def _directory_size(self, path: Path) -> int:
        """Return the total size of a directory tree in bytes."""
        total = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
