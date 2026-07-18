"""
Dashboard routes and views.
"""

from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.vm import VirtualMachine
from app.models.backup import Backup
from app.models.audit_log import AuditLog
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """
    Dashboard homepage.
    
    Displays system overview and key metrics.
    
    TODO: Implement real-time system statistics
    TODO: Implement dashboard widgets
    TODO: Implement backup status monitoring
    """
    
    # Get statistics
    total_vms = VirtualMachine.query.count()
    total_backups = Backup.query.count()
    total_users = User.query.count()
    completed_backups = Backup.query.filter_by(status='completed').count()
    
    # Get recent backups
    recent_backups = Backup.query.order_by(Backup.created_at.desc()).limit(5).all()
    
    # Get recent activity
    recent_activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    total_activities = AuditLog.query.count()
    
    # Calculate statistics
    stats = {
        'total_vms': total_vms,
        'total_backups': total_backups,
        'total_users': total_users,
        'completed_backups': completed_backups,
        'failed_backups': Backup.query.filter_by(status='failed').count(),
        'in_progress_backups': Backup.query.filter_by(status='in_progress').count(),
    }
    
    # Calculate backup success rate
    if total_backups > 0:
        stats['success_rate'] = (completed_backups / total_backups) * 100
    else:
        stats['success_rate'] = 0
    
    return render_template(
        'dashboard/index.html',
        title='Dashboard',
        stats=stats,
        recent_backups=recent_backups,
        recent_activity=recent_activity,
        total_activities=total_activities
    )


@dashboard_bp.route('/system-status')
@login_required
def system_status():
    """
    System status and health check page.
    
    TODO: Implement health check endpoints
    TODO: Implement system resource monitoring
    TODO: Implement backup destination status
    """
    
    system_info = {
        'database_connected': _check_database_connection(),
        'current_time': datetime.utcnow(),
        'application_version': '1.0.0',
        'python_version': _get_python_version(),
        'total_users': User.query.count(),
        'total_vms': VirtualMachine.query.count(),
    }
    
    return render_template(
        'dashboard/system_status.html',
        title='System Status',
        system_info=system_info
    )


def _check_database_connection() -> bool:
    """
    Check if database is connected.
    
    Returns:
        True if database is connected, False otherwise
    """
    try:
        User.query.first()
        return True
    except Exception:
        return False


def _get_python_version() -> str:
    """
    Get Python version.
    
    Returns:
        Python version string
    """
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
