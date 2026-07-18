"""
Backup routes and views.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.models.vm import VirtualMachine
from typing import List, Dict
import os
from datetime import datetime
from app.models.backup import Backup
from app.models.user import db
from app.models.audit_log import AuditLog
from app.vm.detector import detect_local_vms

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')


@backup_bp.route('/', endpoint='index')
@login_required
def index():
    """Display the backup overview page."""
    page = request.args.get('page', 1, type=int)
    backups = Backup.query.order_by(Backup.created_at.desc()).paginate(page=page, per_page=20)

    return render_template(
        'backup/list_backups.html',
        title='Backups',
        backups=backups
    )


@backup_bp.route('/list', endpoint='list_backups')
@login_required
def list_backups():
    """
    List all backups.
    
    TODO: Implement backup filtering and search
    TODO: Implement backup sorting options
    TODO: Implement pagination
    """
    page = request.args.get('page', 1, type=int)
    backups = Backup.query.order_by(Backup.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template(
        'backup/list_backups.html',
        title='Backups',
        backups=backups
    )


@backup_bp.route('/vm/<int:vm_id>')
@login_required
def vm_backups(vm_id: int):
    """
    List backups for a specific VM.
    
    Args:
        vm_id: ID of the virtual machine
    """
    vm = VirtualMachine.query.get_or_404(vm_id)
    page = request.args.get('page', 1, type=int)
    backups = vm.backups.order_by(Backup.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template(
        'backup/vm_backups.html',
        title=f'Backups for {vm.name}',
        vm=vm,
        backups=backups
    )


@backup_bp.route('/create-step-1', methods=['GET', 'POST'])
@login_required
def create_step1():
    """Render the first step of the backup creation wizard and accept selection.

    On POST we persist the chosen VM ids into the session under `backup_job` and
    redirect to step 2.
    """
    if request.method == 'POST':
        # selected vm ids may be sent as 'vms' checkbox values; some may be
        # detected entries like 'detected:0' — handle both.
        selected = request.form.getlist('vms') or request.form.getlist('vm')
        detected_list = []
        try:
            detected_list = detect_local_vms()
        except Exception:
            detected_list = []

        db_selected_ids: List[int] = []
        detected_selected: List[Dict] = []
        for val in selected:
            if not val:
                continue
            if isinstance(val, str) and val.startswith('detected:'):
                try:
                    idx = int(val.split(':', 1)[1])
                    if 0 <= idx < len(detected_list):
                        detected_selected.append(detected_list[idx])
                except Exception:
                    continue
            else:
                try:
                    db_selected_ids.append(int(val))
                except Exception:
                    continue

        session.setdefault('backup_job', {})
        session['backup_job']['vm_ids'] = db_selected_ids
        # store detected VMs payload in session for later review (non-persistent)
        session['backup_job']['detected_vms'] = detected_selected
        flash(f'Selected {len(db_selected_ids) + len(detected_selected)} VM(s) for backup.', 'success')
        return redirect(url_for('backup.create_step2'))

    # GET: show page with DB VMs + best-effort detected local VMs
    vms = VirtualMachine.query.order_by(VirtualMachine.created_at.desc()).all()
    detected = []
    try:
        detected = detect_local_vms()
    except Exception:
        detected = []

    return render_template(
        'backup/create_step1.html',
        title='Create Backup',
        vms=vms,
        detected_vms=detected
    )


@backup_bp.route('/create-step-2', methods=['GET', 'POST'])
@login_required
def create_step2():
    """Render and handle the second step (location) of the backup wizard.

    On POST we persist the destination information into the session under
    `backup_job.destination` and redirect to step 3.
    """
    if request.method == 'POST':
        storage_type = request.form.get('storageType')
        server_address = request.form.get('server_address')
        username = request.form.get('username')
        # NOTE: storing passwords in session is not ideal for security; keep
        # this temporary for the wizard flow. Consider encrypting or skipping.
        password = request.form.get('password')

        session.setdefault('backup_job', {})
        session['backup_job']['destination'] = {
            'type': storage_type,
            'path': server_address,
            'username': username,
            # We intentionally do not echo password back into templates
        }
        # Do NOT store raw password unless explicitly required and secure.
        flash('Backup destination saved for this session.', 'success')
        return redirect(url_for('backup.create_step3'))

    # GET: render page and prefill from session if present
    return render_template(
        'backup/create_step2.html',
        title='Create Backup',
        destinations=[{'id': 1, 'name': 'Local NAS', 'path': 'C:/Backups/NAS'}]
    )


@backup_bp.route('/create-step-3', methods=['GET', 'POST'])
@login_required
def create_step3():
    """Render and handle the third step (compression) of the backup wizard.

    On POST we persist compression and deduplication choices into the session
    under `backup_job` then redirect to the next step.
    """
    if request.method == 'POST':
        compression = request.form.get('compression', 'standard')
        # checkbox present when checked
        dedup = 'deduplication' in request.form

        session.setdefault('backup_job', {})
        session['backup_job']['compression'] = compression
        session['backup_job']['deduplication'] = dedup

        flash('Compression settings saved for this session.', 'success')
        return redirect(url_for('backup.create_step4'))

    # GET
    return render_template(
        'backup/create_step3.html',
        title='Create Backup',
        compression_options=[{'id': 1, 'name': 'Zip', 'description': 'Standard compression'}]
    )


@backup_bp.route('/create-step-4')
@login_required
def create_step4():
    """Render and handle the fourth step (encryption) of the backup wizard.

    On POST we validate the passphrase (basic checks) and persist an encryption
    summary into the session under `backup_job.encryption`. We do NOT store
    the raw passphrase in the session for security; only a flag that it was
    provided.
    """
    if request.method == 'POST':
        passphrase = request.form.get('passphrase', '')
        confirm = request.form.get('confirm_passphrase', '')
        kms = 'kms_storage' in request.form

        # Basic validation: if passphrase provided, ensure minimum length and match
        if passphrase:
            if len(passphrase) < 12:
                flash('Passphrase must be at least 12 characters.', 'danger')
                return render_template('backup/create_step4.html', title='Create Backup')
            if passphrase != confirm:
                flash('Passphrase and confirmation do not match.', 'danger')
                return render_template('backup/create_step4.html', title='Create Backup')

        session.setdefault('backup_job', {})
        session['backup_job']['encryption'] = {
            'type': 'AES-256',
            'passphrase_set': bool(passphrase),
            'kms': bool(kms)
        }
        flash('Encryption settings saved for this session.', 'success')
        return redirect(url_for('backup.review'))

    return render_template(
        'backup/create_step4.html',
        title='Create Backup',
        encryption_options=[{'id': 1, 'name': 'AES-256', 'description': 'Strong encryption'}]
    )


@backup_bp.route('/review')
@login_required
def review():
    """Render the review and confirm screen for the backup wizard."""
    job = session.get('backup_job', {})
    vm_ids = job.get('vm_ids', [])
    detected = job.get('detected_vms', [])
    selected_count = len(vm_ids) + len(detected)
    destination = job.get('destination', {}).get('path') or 'Not set'
    compression = job.get('compression') or 'Not set'
    encryption = job.get('encryption', {}).get('type') if job.get('encryption') else None

    return render_template(
        'backup/review.html',
        title='Review Backup',
        selected_vms_count=selected_count,
        selected_destination=destination,
        selected_compression=(compression if compression else 'Not set'),
        selected_encryption=(encryption if encryption else 'Disabled')
    )


@backup_bp.route('/success')
@login_required
def success():
    """Render the backup success confirmation screen."""
    return render_template('backup/success.html', title='Backup Created')


@backup_bp.route('/start', methods=['POST'])
@login_required
def start_backup():
    """
    Persist backup records for the current `backup_job` in session and
    create AuditLog entries. Detected VMs will be optionally imported into
    the database as `VirtualMachine` records so they can be referenced.
    Returns JSON with created backup ids.
    """
    job = session.get('backup_job')
    if not job:
        return jsonify({'error': 'No backup job in session'}), 400

    vm_ids = job.get('vm_ids', [])[:]  # DB VM ids
    detected = job.get('detected_vms', [])[:]  # detected payloads
    destination = job.get('destination', {})

    created = []

    # Import detected VMs into DB if present
    for d in detected:
        name = d.get('name') or f"detected-{datetime.utcnow().strftime('%Y%m%d%H%M%S') }"
        vm_path = d.get('path') or d.get('vm_path') or ''
        uuid = d.get('uuid') or None
        # avoid duplicate by uuid or path
        existing = None
        if uuid:
            existing = VirtualMachine.query.filter_by(uuid=uuid).first()
        if not existing and vm_path:
            existing = VirtualMachine.query.filter_by(vm_path=vm_path).first()

        if existing:
            vm_ids.append(existing.id)
        else:
            new_vm = VirtualMachine(name=name, vm_path=vm_path, uuid=uuid)
            db.session.add(new_vm)
            db.session.flush()
            vm_ids.append(new_vm.id)

    # For each vm id, create a Backup record
    for vid in vm_ids:
        vm = VirtualMachine.query.get(vid)
        if not vm:
            continue

        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        safe_name = vm.name.replace(' ', '_')
        backup_name = f"{safe_name}-{timestamp}"

        dest_path = destination.get('path') if isinstance(destination, dict) else None
        if dest_path:
            backup_file = os.path.join(dest_path, f"{backup_name}.bak")
        else:
            backup_file = os.path.join('backups', f"{backup_name}.bak")

        backup = Backup(
            vm_id=vm.id,
            backup_name=backup_name,
            backup_path=backup_file,
            status='in_progress',
            encryption_algorithm=(job.get('encryption', {}).get('type') if job.get('encryption') else 'none'),
            backup_type='full'
        )
        db.session.add(backup)
        db.session.flush()

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            vm_id=vm.id,
            backup_id=backup.id,
            action='BACKUP_CREATED',
            action_status='success',
            details=f'Backup record created for VM {vm.name} -> {backup.backup_path}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit_log)

        created.append(backup.id)

    db.session.commit()

    # clear the wizard state
    try:
        session.pop('backup_job', None)
    except Exception:
        pass

    return jsonify({'created': created}), 201


@backup_bp.route('/create/<int:vm_id>', methods=['GET', 'POST'])
@login_required
def create_backup(vm_id: int):
    """
    Create a new backup for a VM.
    
    Args:
        vm_id: ID of the virtual machine
        
    TODO: Implement backup creation form
    TODO: Implement backup type selection (full, incremental, differential)
    TODO: Implement backup start
    """
    vm = VirtualMachine.query.get_or_404(vm_id)
    
    if request.method == 'POST':
        # TODO: Implement backup creation logic
        flash('Backup creation started. This is a placeholder.', 'info')
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_user.id,
            vm_id=vm.id,
            action='BACKUP_REQUESTED',
            action_status='success',
            details=f'Backup requested for VM: {vm.name}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return redirect(url_for('backup.vm_backups', vm_id=vm.id))
    
    return render_template(
        'backup/create_backup.html',
        title=f'Create Backup for {vm.name}',
        vm=vm
    )


@backup_bp.route('/<int:backup_id>')
@login_required
def backup_details(backup_id: int):
    """
    View backup details.
    
    Args:
        backup_id: ID of the backup
        
    TODO: Implement detailed backup information display
    TODO: Implement backup verification status
    """
    backup = Backup.query.get_or_404(backup_id)
    
    return render_template(
        'backup/backup_details.html',
        title=f'Backup Details: {backup.backup_name}',
        backup=backup
    )


@backup_bp.route('/<int:backup_id>/delete', methods=['POST'])
@login_required
def delete_backup(backup_id: int):
    """
    Delete a backup.
    
    Args:
        backup_id: ID of the backup
        
    TODO: Implement secure backup deletion
    TODO: Implement confirmation before deletion
    """
    backup = Backup.query.get_or_404(backup_id)
    
    if not current_user.is_admin():
        flash('You do not have permission to delete backups.', 'danger')
        return redirect(url_for('backup.backup_details', backup_id=backup.id))
    
    # TODO: Implement backup deletion
    flash('Backup deletion is not yet implemented.', 'warning')
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        backup_id=backup.id,
        vm_id=backup.vm_id,
        action='BACKUP_DELETION_REQUESTED',
        action_status='success',
        details=f'Deletion requested for backup: {backup.backup_name}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return redirect(url_for('backup.backup_details', backup_id=backup.id))


@backup_bp.route('/api/backup-stats')
@login_required
def backup_stats():
    """
    Get backup statistics as JSON.
    
    Returns:
        JSON response with backup statistics
    """
    total_backups = Backup.query.count()
    completed = Backup.query.filter_by(status='completed').count()
    failed = Backup.query.filter_by(status='failed').count()
    in_progress = Backup.query.filter_by(status='in_progress').count()
    
    return jsonify({
        'total_backups': total_backups,
        'completed': completed,
        'failed': failed,
        'in_progress': in_progress,
        'success_rate': (completed / total_backups * 100) if total_backups > 0 else 0
    })
