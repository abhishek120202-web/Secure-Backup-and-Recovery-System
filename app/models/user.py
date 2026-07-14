"""
User model for authentication and user management.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Deferred import to avoid circular import at module load time
# db is created in models/__init__.py before this class is instantiated
from app.models import db


class User(UserMixin, db.Model):
    """
    User model representing a system user.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        password_hash: Hashed password using bcrypt
        full_name: User's full name
        is_active: Whether the user account is active
        role: User role (admin, operator, viewer)
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
        last_login: Timestamp of last login
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role = db.Column(db.String(32), default='operator', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password using PBKDF2-SHA256.
        
        Args:
            password: Plain text password
        """
        # Using pbkdf2:sha256 which is built-in and doesn't require external dependencies
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """
        Verify the provided password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def is_operator(self) -> bool:
        """Check if user is an operator."""
        return self.role in ['admin', 'operator']
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
