"""
Authentication and Authorization module for NEXUS Platform.
"""

# Password utilities
from .password_utils import (
    hash_password,
    verify_password,
    validate_password,
    validate_passwords_match,
    check_password_strength,
    generate_password_requirements_text,
    PasswordStrength
)

# Authentication
from .authentication import (
    register_user,
    login_user,
    logout_user,
    verify_email,
    request_password_reset,
    reset_password,
    change_password,
    get_user_by_token,
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_email,
    validate_username,
    AuthenticationError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountNotVerifiedError,
    UserAlreadyExistsError
)

# Authorization
from .authorization import (
    check_permission,
    check_role,
    check_any_role,
    check_all_roles,
    get_user_permissions,
    get_user_roles,
    is_admin,
    is_manager,
    assign_role,
    remove_role,
    create_role,
    create_permission,
    assign_permission_to_role,
    remove_permission_from_role,
    can_manage_user,
    require_permission_check,
    require_role_check,
    require_any_role_check,
    AuthorizationError,
    InsufficientPermissionsError,
    RoleNotFoundError
)

# Session Manager
from .session_manager import StreamlitSessionManager

# OAuth
from .oauth import (
    GoogleOAuth,
    MicrosoftOAuth,
    authenticate_with_oauth,
    handle_google_oauth,
    handle_microsoft_oauth,
    is_oauth_configured,
    OAuthProvider,
    OAuthError,
    OAuthConfigurationError,
    OAuthAuthenticationError
)

# Middleware
from .middleware import (
    require_auth,
    require_role,
    require_any_role,
    require_admin,
    require_manager,
    optional_auth,
    rate_limit,
    show_for_roles,
    hide_for_roles,
    with_session_state,
    track_activity,
    csrf_protect
)

__all__ = [
    # Password utilities
    'hash_password',
    'verify_password',
    'validate_password',
    'validate_passwords_match',
    'check_password_strength',
    'generate_password_requirements_text',
    'PasswordStrength',

    # Authentication
    'register_user',
    'login_user',
    'logout_user',
    'verify_email',
    'request_password_reset',
    'reset_password',
    'change_password',
    'get_user_by_token',
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'validate_email',
    'validate_username',
    'AuthenticationError',
    'InvalidCredentialsError',
    'AccountLockedError',
    'AccountNotVerifiedError',
    'UserAlreadyExistsError',

    # Authorization
    'check_permission',
    'check_role',
    'check_any_role',
    'check_all_roles',
    'get_user_permissions',
    'get_user_roles',
    'is_admin',
    'is_manager',
    'assign_role',
    'remove_role',
    'create_role',
    'create_permission',
    'assign_permission_to_role',
    'remove_permission_from_role',
    'can_manage_user',
    'require_permission_check',
    'require_role_check',
    'require_any_role_check',
    'AuthorizationError',
    'InsufficientPermissionsError',
    'RoleNotFoundError',

    # Session Manager
    'StreamlitSessionManager',

    # OAuth
    'GoogleOAuth',
    'MicrosoftOAuth',
    'authenticate_with_oauth',
    'handle_google_oauth',
    'handle_microsoft_oauth',
    'is_oauth_configured',
    'OAuthProvider',
    'OAuthError',
    'OAuthConfigurationError',
    'OAuthAuthenticationError',

    # Middleware
    'require_auth',
    'require_role',
    'require_any_role',
    'require_admin',
    'require_manager',
    'optional_auth',
    'rate_limit',
    'show_for_roles',
    'hide_for_roles',
    'with_session_state',
    'track_activity',
    'csrf_protect',
]
