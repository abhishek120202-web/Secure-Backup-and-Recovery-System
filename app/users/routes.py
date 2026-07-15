"""User administration routes and views."""

from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import User

users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/')
@login_required
def index():
    """Display users list for administrators."""
    if not current_user.is_admin():
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template(
        'users/index.html',
        title='Users',
        users=users
    )
