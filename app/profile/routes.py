"""User profile routes and views."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def index():
    """Display the current user's profile page."""
    return render_template('profile/index.html', title='Profile', user=current_user)
