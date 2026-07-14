"""
Recovery module initialization.
"""

from app.recovery.routes import recovery_bp
from app.recovery.services import RecoveryService

__all__ = ['recovery_bp', 'RecoveryService']
