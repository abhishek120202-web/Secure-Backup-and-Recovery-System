"""
Audit routes and views.

This module handles audit log viewing and filtering.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.audit_log import AuditLog
from datetime import datetime, timedelta

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')


@audit_bp.route('/')
@login_required
def list_logs():
    """
    List audit logs.
    
    Requires admin role.
    
    TODO: Implement log filtering by date range
    TODO: Implement log filtering by user
    TODO: Implement log filtering by action type
    TODO: Implement log export functionality
    """
    if not current_user.is_admin():
        return render_template('errors/403.html'), 403
    
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', None)
    user_id_filter = request.args.get('user_id', None)
    status_filter = request.args.get('status', None)
    
    query = AuditLog.query
    
    # Apply filters
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    if user_id_filter:
        try:
            query = query.filter_by(user_id=int(user_id_filter))
        except ValueError:
            pass
    
    if status_filter:
        query = query.filter_by(action_status=status_filter)
    
    # Order by creation date descending
    audit_logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    
    return render_template(
        'audit/list_logs.html',
        title='Audit Logs',
        audit_logs=audit_logs
    )


@audit_bp.route('/user/<int:user_id>')
@login_required
def user_logs(user_id: int):
    """
    View audit logs for a specific user.
    
    Args:
        user_id: ID of the user
    """
    from app.models.user import User
    
    if not current_user.is_admin() and current_user.id != user_id:
        return render_template('errors/403.html'), 403
    
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    
    audit_logs = AuditLog.query.filter_by(user_id=user_id).order_by(
        AuditLog.created_at.desc()
    ).paginate(page=page, per_page=50)
    
    return render_template(
        'audit/user_logs.html',
        title=f'Audit Logs for {user.username}',
        user=user,
        audit_logs=audit_logs
    )


@audit_bp.route('/vm/<int:vm_id>')
@login_required
def vm_logs(vm_id: int):
    """
    View audit logs for a specific VM.
    
    Args:
        vm_id: ID of the virtual machine
        
    Requires admin or operator role.
    """
    from app.models.vm import VirtualMachine
    
    if not current_user.is_operator():
        return render_template('errors/403.html'), 403
    
    vm = VirtualMachine.query.get_or_404(vm_id)
    page = request.args.get('page', 1, type=int)
    
    audit_logs = AuditLog.query.filter_by(vm_id=vm_id).order_by(
        AuditLog.created_at.desc()
    ).paginate(page=page, per_page=50)
    
    return render_template(
        'audit/vm_logs.html',
        title=f'Audit Logs for {vm.name}',
        vm=vm,
        audit_logs=audit_logs
    )


@audit_bp.route('/api/activity-stats')
@login_required
def activity_stats():
    """
    Get activity statistics.
    
    Returns:
        JSON response with activity statistics
    """
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Statistics for last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    total_actions = AuditLog.query.count()
    recent_actions = AuditLog.query.filter(
        AuditLog.created_at >= seven_days_ago
    ).count()
    
    successful_actions = AuditLog.query.filter_by(action_status='success').count()
    failed_actions = AuditLog.query.filter_by(action_status='failure').count()
    
    # Top actions
    from sqlalchemy import func
    top_actions = AuditLog.query.with_entities(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(5).all()
    
    return jsonify({
        'total_actions': total_actions,
        'recent_actions': recent_actions,
        'successful_actions': successful_actions,
        'failed_actions': failed_actions,
        'top_actions': [
            {'action': action, 'count': count}
            for action, count in top_actions
        ]
    })


@audit_bp.route('/api/user-activity/<int:user_id>')
@login_required
def user_activity(user_id: int):
    """
    Get activity for a specific user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        JSON response with user activity
    """
    if not current_user.is_admin() and current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from app.models.user import User
    
    user = User.query.get_or_404(user_id)
    
    # Last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_logs = AuditLog.query.filter_by(user_id=user_id).filter(
        AuditLog.created_at >= thirty_days_ago
    ).order_by(AuditLog.created_at.desc()).limit(20).all()
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        },
        'recent_activity': [
            {
                'action': log.action,
                'status': log.action_status,
                'created_at': log.created_at.isoformat(),
                'details': log.details
            }
            for log in recent_logs
        ]
    })
