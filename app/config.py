"""
Configuration classes for different environments.

This module provides configuration for Development, Testing, and Production environments.
Configuration values are loaded from environment variables or use defaults.
"""

import os
from datetime import timedelta
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
INSTANCE_PATH = PROJECT_ROOT / 'instance'


class Config:
    """
    Base configuration class with common settings.
    """
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = False
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login settings
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # Application settings
    BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', 'backups/')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB max file size
    
    # Logging settings
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', False)
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Security settings
    AES_KEY_LENGTH = 256  # AES-256
    HASH_ALGORITHM = 'sha256'
    
    # Retention policies (in days)
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 90))
    AUDIT_LOG_RETENTION_DAYS = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', 365))
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Mail settings (for future use)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')


class DevelopmentConfig(Config):
    """
    Development configuration.
    """
    
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Database - default to local SQLite unless DEV_DATABASE_URL is provided
    _dev_db_url = os.getenv('DEV_DATABASE_URL')
    if not _dev_db_url:
        db_file = INSTANCE_PATH / 'dev.db'
        _dev_db_url = f'sqlite:///{db_file}'

    if 'sqlite' in _dev_db_url:
        # For SQLite, construct proper absolute path
        db_file = INSTANCE_PATH / 'dev.db'
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_file}'
    else:
        SQLALCHEMY_DATABASE_URI = _dev_db_url
    
    SQLALCHEMY_ECHO = True
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True


class TestingConfig(Config):
    """
    Testing configuration.
    """
    
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    BACKUP_RETENTION_DAYS = 30
    AUDIT_LOG_RETENTION_DAYS = 90


class ProductionConfig(Config):
    """
    Production configuration.
    """
    
    DEBUG = False
    TESTING = False
    
    # Database - handle SQLite paths specially
    _prod_db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@localhost:3306/secure_backup_prod')
    if 'sqlite' in _prod_db_url:
        # For SQLite, construct proper absolute path
        db_file = INSTANCE_PATH / 'prod.db'
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_file}'
    else:
        SQLALCHEMY_DATABASE_URI = _prod_db_url
    
    SQLALCHEMY_ECHO = False
    
    # Security enforcements
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Logging
    LOG_LEVEL = 'WARNING'
    LOG_TO_STDOUT = True


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Config:
    """
    Get configuration class by name.
    
    Args:
        config_name: Name of the configuration (development, testing, production)
        
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, DevelopmentConfig)
