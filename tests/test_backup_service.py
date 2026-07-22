import os
import tempfile
import shutil

from app import create_app
from app.models import db
from app.models.backup import Backup
from app.models.vm import VirtualMachine
from app.models.user import User
from app.backup.services import BackupService


def test_create_backup_service_produces_real_snapshot(tmp_path):
    app = create_app('testing')
    app.config['BACKUP_FOLDER'] = str(tmp_path / 'backups')
    app.config['TESTING'] = True

    with app.app_context():
        db.drop_all()
        db.create_all()

        source_dir = tmp_path / 'source-vm'
        source_dir.mkdir(parents=True)
        (source_dir / 'disk.vmdk').write_text('fake-vm-disk-data', encoding='utf-8')

        vm = VirtualMachine(name='Test VM', vm_path=str(source_dir), uuid='vm-123')
        db.session.add(vm)
        db.session.flush()

        backup = Backup(vm_id=vm.id, backup_name='test-backup', backup_path='pending')
        db.session.add(backup)
        db.session.commit()

        service = BackupService()
        result = service.create_backup(backup.id)

        assert result is True
        backup = Backup.query.get(backup.id)
        assert backup.status == 'completed'
        assert backup.file_size_bytes is not None and backup.file_size_bytes > 0
        assert backup.integrity_hash
        assert os.path.exists(backup.backup_path)

        shutil.rmtree(tmp_path, ignore_errors=True)


def test_start_backup_route_creates_backup_records(tmp_path):
    app = create_app('testing')
    app.config['BACKUP_FOLDER'] = str(tmp_path / 'backups')
    app.config['TESTING'] = True

    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(username='tester', email='tester@example.com', full_name='Tester', role='admin', is_active=True)
        user.set_password('secret123')
        db.session.add(user)

        vm = VirtualMachine(name='Demo VM', vm_path=str(tmp_path / 'sample-vm'), uuid='demo-vm')
        db.session.add(vm)
        db.session.commit()
        user_id = user.id
        vm_id = vm.id

    with app.test_client() as client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['backup_job'] = {
                'vm_ids': [vm_id],
                'detected_vms': [],
                'destination': {'path': str(tmp_path / 'dest')},
                'compression': 'standard',
                'deduplication': True,
                'encryption': {'type': 'AES-256', 'passphrase_set': False, 'kms': False},
            }

        response = client.post('/backup/start', data={})
        assert response.status_code == 201

        with app.app_context():
            assert Backup.query.count() == 1
