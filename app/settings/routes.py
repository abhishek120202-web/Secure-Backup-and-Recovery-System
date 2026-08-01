"""Application settings routes and views."""

import os
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


def _resolve_backup_folder(path_value: str | None) -> str:
    """Return an absolute backup folder path for the current app instance."""
    if path_value:
        candidate = Path(path_value).expanduser()
        if not candidate.is_absolute():
            candidate = Path(current_app.root_path).parent / candidate
        return str(candidate)

    fallback = current_app.config.get('BACKUP_FOLDER', str(Path(current_app.root_path).parent / 'backups'))
    candidate = Path(fallback).expanduser()
    if not candidate.is_absolute():
        candidate = Path(current_app.root_path).parent / candidate
    return str(candidate)


def _persist_setting(key: str, value: str) -> None:
    """Persist a setting in the project's .env file so it survives app restarts."""
    env_path = Path(current_app.root_path).parent / '.env'
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding='utf-8').splitlines()

    updated = []
    found = False
    for line in lines:
        if line.startswith(f'{key}='):
            updated.append(f'{key}={value}')
            found = True
        else:
            updated.append(line)

    if not found:
        updated.append(f'{key}={value}')

    env_path.write_text('\n'.join([line for line in updated if line.strip() != '']) + '\n', encoding='utf-8')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Display and update backup-related settings."""
    if request.method == 'POST':
        backup_folder = _resolve_backup_folder(request.form.get('backup_folder', '').strip())
        compression = request.form.get('compression', current_app.config.get('BACKUP_COMPRESSION_DEFAULT', 'standard'))
        encryption_enabled = 'encryption' in request.form

        os.makedirs(backup_folder, exist_ok=True)
        current_app.config['BACKUP_FOLDER'] = backup_folder
        current_app.config['BACKUP_COMPRESSION_DEFAULT'] = compression
        current_app.config['BACKUP_ENCRYPTION_DEFAULT'] = encryption_enabled

        _persist_setting('BACKUP_FOLDER', backup_folder)
        _persist_setting('BACKUP_COMPRESSION_DEFAULT', compression)
        _persist_setting('BACKUP_ENCRYPTION_DEFAULT', 'true' if encryption_enabled else 'false')

        flash('Backup settings updated successfully.', 'success')
        return redirect(url_for('settings.index'))

    return render_template(
        'settings/index.html',
        title='Settings',
        backup_folder=_resolve_backup_folder(current_app.config.get('BACKUP_FOLDER')),
        compression=current_app.config.get('BACKUP_COMPRESSION_DEFAULT', 'standard'),
        encryption_enabled=current_app.config.get('BACKUP_ENCRYPTION_DEFAULT', False),
    )
