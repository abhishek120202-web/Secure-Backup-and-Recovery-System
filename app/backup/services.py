"""
Backup services module.

This module contains business logic for backup operations.
"""

from __future__ import annotations

import base64
import hashlib
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import current_app

from app.models import db
from app.models.backup import Backup
from app.models.vm import VirtualMachine


class BackupService:
    """Service class for backup operations."""

    def __init__(self):
        """Initialize BackupService."""
        self.backup_folder = Path(current_app.config.get('BACKUP_FOLDER', 'backups/'))

    def create_backup(self, backup_id: int, backup_type: str = 'full', compression: str = 'standard', encryption_key: str = None) -> bool:
        """
        Create a real backup snapshot for a database backup record.

        Args:
            backup_id: ID of the backup record to update
            backup_type: Type of backup (full, incremental, differential)
            compression: Compression setting (none, standard, high)
            encryption_key: Optional passphrase-derived key

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

        target_dir = Path(backup.backup_path)
        if target_dir.suffix:
            target_dir = target_dir.with_suffix('')
        target_dir.mkdir(parents=True, exist_ok=True)

        source_path = Path(vm.vm_path)
        if not source_path.exists():
            backup.status = 'failed'
            backup.notes = f'VM source path does not exist: {source_path}'
            backup.completed_at = datetime.utcnow()
            db.session.commit()
            return False

        if source_path.is_file():
            copy_entries = [(source_path, False)]
        else:
            copy_entries = []
            for root, dirs, files in os.walk(source_path):
                dirs[:] = sorted([directory for directory in dirs if not directory.startswith('.')])
                files = sorted([file_name for file_name in files if not file_name.startswith('.')])
                root_path = Path(root)
                copy_entries.append((root_path, True))
                for file_name in files:
                    copy_entries.append((root_path / file_name, False))

        backup.status = 'in_progress'
        backup.progress = 5
        backup.notes = f'Queued for execution\nCreating {backup_type} backup for {vm.name}'
        backup.backup_type = backup_type
        db.session.commit()

        snapshot_dir = target_dir
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        if not copy_entries:
            backup.progress = 25
            backup.notes = f'{backup.notes}\nNo files found in VM source path {source_path}'
            db.session.commit()

        # Create a real snapshot copy of the VM directory contents or file-based VM definition.
        total_entries = len(copy_entries)
        for index, (src, is_dir) in enumerate(copy_entries, start=1):
            dst = snapshot_dir / src.relative_to(source_path)
            if is_dir:
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

            progress = 10 + int((index / max(total_entries, 1)) * 70)
            backup.progress = progress
            backup.notes = f'{backup.notes}\nCopied {index}/{total_entries} paths for {vm.name}'
            db.session.commit()

        # Persist a metadata file with VM information.
        metadata_path = snapshot_dir / 'backup_metadata.json'
        metadata_path.write_text(
            '{"vm_name": "%s", "vm_path": "%s", "created_at": "%s", "backup_type": "%s"}\n'
            % (vm.name, str(source_path), datetime.utcnow().isoformat(), backup_type),
            encoding='utf-8'
        )

        backup.progress = 90
        backup.notes = f'{backup.notes}\nFinalizing backup and calculating checksum'
        db.session.commit()

        final_path = snapshot_dir
        if compression != 'none' or bool(encryption_key):
            archive_path = self.compress_backup(snapshot_dir, compression)
            if archive_path is None:
                backup.status = 'failed'
                backup.notes = 'Failed to create backup archive.'
                db.session.commit()
                return False

            final_path = archive_path
            if encryption_key:
                encrypted_path = self.encrypt_backup(str(archive_path), encryption_key)
                if encrypted_path is None:
                    backup.status = 'failed'
                    backup.notes = 'Failed to encrypt backup archive.'
                    db.session.commit()
                    return False

                final_path = encrypted_path
                try:
                    archive_path.unlink(missing_ok=True)
                except Exception:
                    pass

            try:
                shutil.rmtree(snapshot_dir, ignore_errors=True)
            except Exception:
                pass

        backup.backup_path = str(final_path)
        backup.file_size_bytes = self._item_size(final_path)
        backup.status = 'completed'
        backup.progress = 100
        backup.completed_at = datetime.utcnow()
        backup.integrity_hash = self.generate_integrity_hash(str(final_path))
        backup.notes = f'{backup.notes}\nBackup completed successfully for {vm.name} ({compression} compression, {"encrypted" if encryption_key else "unencrypted"})'
        db.session.commit()
        return True

    def compress_backup(self, backup_path: Path, compression: str = 'standard') -> Optional[Path]:
        """Compress a backup directory into a .zip file."""
        if not backup_path.exists() or not backup_path.is_dir():
            return None

        archive_path = backup_path.with_suffix('.zip')
        compresslevel = 5
        if compression == 'high':
            compresslevel = 9
        elif compression == 'none':
            compresslevel = 0

        try:
            with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compresslevel) as archive:
                for file_path in sorted(backup_path.rglob('*')):
                    if file_path.is_file():
                        archive.write(file_path, file_path.relative_to(backup_path))
            return archive_path
        except Exception:
            return None

    def encrypt_backup(self, backup_path: str, encryption_key: str) -> Optional[Path]:
        """Encrypt a backup archive and write a .enc file."""
        path = Path(backup_path)
        if not path.exists() or not path.is_file():
            return None

        try:
            with path.open('rb') as handle:
                plaintext = handle.read()

            key = base64.b64decode(encryption_key)
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            encrypted_path = path.with_suffix('.enc')
            encrypted_path.write_bytes(nonce + ciphertext)
            return encrypted_path
        except Exception:
            return None

    def generate_integrity_hash(self, backup_path: str) -> str:
        """Generate SHA-256 hash for a file or directory tree."""
        digest = hashlib.sha256()
        path = Path(backup_path)
        if not path.exists():
            return ''

        if path.is_file():
            with path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(chunk)
            return digest.hexdigest()

        for file_path in sorted(path.rglob('*')):
            if file_path.is_file():
                digest.update(str(file_path.relative_to(path)).encode('utf-8'))
                with file_path.open('rb') as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                        digest.update(chunk)
        return digest.hexdigest()

    def delete_backup(self, backup_id: int) -> bool:
        """Delete a backup artifact from disk and remove the DB record."""
        backup = Backup.query.get(backup_id)
        if not backup:
            return False

        backup_path = Path(backup.backup_path)
        if backup_path.exists():
            if backup_path.is_dir():
                shutil.rmtree(backup_path, ignore_errors=True)
            else:
                backup_path.unlink(missing_ok=True)

        archive_path = backup_path.with_suffix('.zip')
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)

        encrypted_path = backup_path.with_suffix(backup_path.suffix + '.enc')
        if encrypted_path.exists():
            encrypted_path.unlink(missing_ok=True)

        db.session.delete(backup)
        db.session.commit()
        return True

    def _item_size(self, path: Path) -> int:
        """Return the total size of a file or directory tree in bytes."""
        if path.is_file():
            return path.stat().st_size

        total = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
