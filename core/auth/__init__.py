"""Authentication module for NEXUS platform."""
from .models import User
from .service import AuthService
from .middleware import require_auth

__all__ = ['User', 'AuthService', 'require_auth']
