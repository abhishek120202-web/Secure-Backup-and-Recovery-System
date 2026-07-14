"""
Authentication routes and views.
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models.user import db, User
from app.models.audit_log import AuditLog
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    
    TODO: Implement login rate limiting
    TODO: Implement two-factor authentication
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            # Log failed authentication attempt
            _log_audit(
                action='LOGIN_FAILED',
                action_status='failure',
                details=f'Failed login attempt for username: {form.username.data}'
            )
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been disabled.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Successful login
        user.update_last_login()
        login_user(user, remember=form.remember_me.data)
        
        # Log successful login
        _log_audit(
            user_id=user.id,
            action='LOGIN_SUCCESS',
            action_status='success',
            details=f'User {user.username} logged in'
        )
        
        next_page = request.args.get('next')
        if not next_page or url_has_allowed_host_and_scheme(next_page):
            next_page = url_for('dashboard.index')
        
        flash('You have been successfully logged in.', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form, title='Sign In')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    
    TODO: Implement email verification
    TODO: Implement CAPTCHA for registration
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role='operator'
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Log user registration
        _log_audit(
            user_id=user.id,
            action='USER_REGISTERED',
            action_status='success',
            details=f'New user registered: {user.username}'
        )
        
        flash('Congratulations! You are now registered. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form, title='Register')


@auth_bp.route('/logout')
def logout():
    """
    User logout route.
    
    Logs out the current user and clears the session.
    """
    _log_audit(
        user_id=current_user.id,
        action='LOGOUT',
        action_status='success',
        details=f'User {current_user.username} logged out'
    )
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """
    Change user password route.
    
    TODO: Implement password strength requirements
    """
    if not current_user.is_authenticated:
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        # Log password change
        _log_audit(
            user_id=current_user.id,
            action='PASSWORD_CHANGED',
            action_status='success',
            details=f'User {current_user.username} changed their password'
        )
        
        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/change_password.html', form=form, title='Change Password')


def url_has_allowed_host_and_scheme(url: str, allowed_hosts=None) -> bool:
    """
    Check if URL is safe to redirect to.
    
    Args:
        url: URL to check
        allowed_hosts: List of allowed hosts
        
    Returns:
        True if URL is safe, False otherwise
    """
    from urllib.parse import urlparse
    
    if allowed_hosts is None:
        allowed_hosts = ['localhost']
    
    parsed = urlparse(url)
    
    # Allow relative URLs
    if not parsed.scheme and not parsed.netloc:
        return True
    
    # Check if host is in allowed list
    return parsed.netloc in allowed_hosts


def _log_audit(action: str, action_status: str = 'success', 
               details: str = None, user_id: int = None, 
               vm_id: int = None, backup_id: int = None) -> None:
    """
    Log an audit event.
    
    Args:
        action: Action type
        action_status: Status of action (success, failure)
        details: Additional details
        user_id: User ID (uses current_user if not provided)
        vm_id: Virtual Machine ID (optional)
        backup_id: Backup ID (optional)
    """
    if user_id is None and hasattr(current_user, 'id'):
        user_id = current_user.id
    
    if user_id is None:
        return
    
    audit_log = AuditLog(
        user_id=user_id,
        vm_id=vm_id,
        backup_id=backup_id,
        action=action,
        action_status=action_status,
        details=details,
        ip_address=request.remote_addr if request else None,
        user_agent=request.user_agent.string if request else None
    )
    db.session.add(audit_log)
    db.session.commit()
