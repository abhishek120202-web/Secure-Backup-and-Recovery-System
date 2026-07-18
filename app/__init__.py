"""
Secure VMware Backup and Recovery System - Flask Application Factory

This module initializes the Flask application with all necessary extensions
and blueprints for managing secure backups and recovery of VMware VMs.
"""

# Load environment variables from .env file at module import time
from dotenv import load_dotenv
load_dotenv()

import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_login import LoginManager

try:
    from flask_migrate import Migrate
except Exception:
    Migrate = None

from app.config import get_config
from app.models import db


def initialize_development_database(app: Flask) -> None:
    """Create development database tables and seed a default admin user if needed."""
    try:
        with app.app_context():
            db.create_all()

            from app.models.user import User

            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    full_name='System Administrator',
                    role='admin',
                    is_active=True,
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
    except Exception as exc:
        app.logger.warning(f'Development database initialization skipped: {exc}')


def create_app(config_name: str = None) -> Flask:
    """
    Application factory function.
    
    Creates and configures the Flask application with all extensions,
    blueprints, and settings.
    
    Args:
        config_name: Configuration environment (development, testing, production)
        
    Returns:
        Configured Flask application instance
    """
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Create necessary directories
    os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initialize Flask extensions
    db.init_app(app)

    # Automatically create development database tables if needed
    if app.config['DEBUG'] and not app.config['TESTING']:
        initialize_development_database(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Load user for Flask-Login
    @login_manager.user_loader
    def load_user(user_id: int):
        """Load user by ID for Flask-Login."""
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Initialize Flask-Migrate when available
    if Migrate is not None:
        try:
            Migrate(app, db)
        except Exception as exc:
            app.logger.warning(f'Flask-Migrate initialization skipped: {exc}')
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables (only for testing/development with manual setup)
    # In production, use Flask-Migrate: flask db upgrade
    # with app.app_context():
    #     db.create_all()
    
    # Setup logging
    setup_logging(app)
    
    # Register shell context for flask shell
    register_shell_context(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    return app


def register_blueprints(app: Flask) -> None:
    """
    Register all application blueprints.
    
    Args:
        app: Flask application instance
    """
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.backup.routes import backup_bp
    from app.recovery.routes import recovery_bp
    from app.audit.routes import audit_bp
    from app.vm.routes import vm_bp
    from app.users.routes import users_bp
    from app.settings.routes import settings_bp
    from app.profile.routes import profile_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(recovery_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(vm_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(profile_bp)


def setup_logging(app: Flask) -> None:
    """
    Configure application logging.
    
    Args:
        app: Flask application instance
    """
    if app.config['LOG_TO_STDOUT']:
        # Log to stdout
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
    else:
        # Log to file
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        handler = RotatingFileHandler(
            'logs/secure_backup_recovery.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
    
    handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    app.logger.info('Secure VMware Backup and Recovery System startup')


def register_shell_context(app: Flask) -> None:
    """
    Register objects for flask shell.
    
    Args:
        app: Flask application instance
    """
    @app.shell_context_processor
    def make_shell_context():
        """Make database objects available in shell."""
        from app.models.user import User
        from app.models.vm import VirtualMachine
        from app.models.backup import Backup
        from app.models.audit_log import AuditLog
        
        return {
            'db': db,
            'User': User,
            'VirtualMachine': VirtualMachine,
            'Backup': Backup,
            'AuditLog': AuditLog
        }


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers.
    
    Args:
        app: Flask application instance
    """
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        app.logger.warning(f'404 error: {error}')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f'500 error: {error}')
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        app.logger.warning(f'403 error: {error}')
        return render_template('errors/403.html'), 403


def register_template_filters(app: Flask) -> None:
    """
    Register custom Jinja2 filters.
    
    Args:
        app: Flask application instance
    """
    
    @app.template_filter('file_size')
    def format_file_size(size_bytes: int) -> str:
        """Format bytes to human-readable file size."""
        if size_bytes == 0:
            return "0B"
        
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = int((len(str(int(size_bytes))) - 1) // 3)
        p = pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    @app.template_filter('datetime_format')
    def format_datetime(dt, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format datetime object."""
        if dt is None:
            return ''
        return dt.strftime(format_str)
