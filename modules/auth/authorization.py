"""
Authorization module for Role-Based Access Control (RBAC).
"""
from typing import List, Optional, Set
from sqlalchemy.orm import Session

from modules.database.models import User, Role, Permission


class AuthorizationError(Exception):
    """Base exception for authorization errors."""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions."""
    pass


class RoleNotFoundError(AuthorizationError):
    """Raised when role is not found."""
    pass


def check_permission(user: User, permission_name: str) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user: User to check
        permission_name: Permission name to check

    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user or not user.is_active:
        return False

    # Check if user has the permission through any of their roles
    for role in user.roles:
        for permission in role.permissions:
            if permission.name == permission_name:
                return True

    return False


def check_role(user: User, role_name: str) -> bool:
    """
    Check if user has a specific role.

    Args:
        user: User to check
        role_name: Role name to check

    Returns:
        bool: True if user has role, False otherwise
    """
    if not user or not user.is_active:
        return False

    return any(role.name == role_name for role in user.roles)


def check_any_role(user: User, role_names: List[str]) -> bool:
    """
    Check if user has any of the specified roles.

    Args:
        user: User to check
        role_names: List of role names to check

    Returns:
        bool: True if user has any of the roles, False otherwise
    """
    if not user or not user.is_active:
        return False

    user_roles = {role.name for role in user.roles}
    return bool(user_roles.intersection(set(role_names)))


def check_all_roles(user: User, role_names: List[str]) -> bool:
    """
    Check if user has all of the specified roles.

    Args:
        user: User to check
        role_names: List of role names to check

    Returns:
        bool: True if user has all roles, False otherwise
    """
    if not user or not user.is_active:
        return False

    user_roles = {role.name for role in user.roles}
    return set(role_names).issubset(user_roles)


def get_user_permissions(user: User) -> Set[str]:
    """
    Get all permissions for a user.

    Args:
        user: User to get permissions for

    Returns:
        Set[str]: Set of permission names
    """
    if not user or not user.is_active:
        return set()

    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.name)

    return permissions


def get_user_roles(user: User) -> Set[str]:
    """
    Get all roles for a user.

    Args:
        user: User to get roles for

    Returns:
        Set[str]: Set of role names
    """
    if not user or not user.is_active:
        return set()

    return {role.name for role in user.roles}


def is_admin(user: User) -> bool:
    """
    Check if user is an admin.

    Args:
        user: User to check

    Returns:
        bool: True if user is admin, False otherwise
    """
    return check_role(user, "admin")


def is_manager(user: User) -> bool:
    """
    Check if user is a manager or admin.

    Args:
        user: User to check

    Returns:
        bool: True if user is manager or admin, False otherwise
    """
    return check_any_role(user, ["admin", "manager"])


def assign_role(db: Session, user: User, role_name: str) -> bool:
    """
    Assign a role to a user.

    Args:
        db: Database session
        user: User to assign role to
        role_name: Role name to assign

    Returns:
        bool: True if role assigned successfully

    Raises:
        RoleNotFoundError: If role doesn't exist
    """
    # Check if role exists
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise RoleNotFoundError(f"Role '{role_name}' not found")

    # Check if user already has the role
    if role in user.roles:
        return True

    # Assign role
    user.roles.append(role)
    db.commit()
    db.refresh(user)

    return True


def remove_role(db: Session, user: User, role_name: str) -> bool:
    """
    Remove a role from a user.

    Args:
        db: Database session
        user: User to remove role from
        role_name: Role name to remove

    Returns:
        bool: True if role removed successfully

    Raises:
        RoleNotFoundError: If role doesn't exist or user doesn't have it
    """
    # Find the role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise RoleNotFoundError(f"Role '{role_name}' not found")

    # Check if user has the role
    if role not in user.roles:
        return True

    # Remove role
    user.roles.remove(role)
    db.commit()
    db.refresh(user)

    return True


def create_role(
    db: Session,
    name: str,
    description: Optional[str] = None,
    permissions: Optional[List[str]] = None
) -> Role:
    """
    Create a new role.

    Args:
        db: Database session
        name: Role name
        description: Role description
        permissions: List of permission names to assign to role

    Returns:
        Role: Created role

    Raises:
        ValueError: If role already exists
    """
    # Check if role already exists
    existing_role = db.query(Role).filter(Role.name == name).first()
    if existing_role:
        raise ValueError(f"Role '{name}' already exists")

    # Create role
    role = Role(name=name, description=description)

    # Assign permissions if provided
    if permissions:
        for perm_name in permissions:
            permission = db.query(Permission).filter(Permission.name == perm_name).first()
            if permission:
                role.permissions.append(permission)

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def create_permission(
    db: Session,
    name: str,
    description: Optional[str] = None,
    module: Optional[str] = None
) -> Permission:
    """
    Create a new permission.

    Args:
        db: Database session
        name: Permission name
        description: Permission description
        module: Module this permission applies to

    Returns:
        Permission: Created permission

    Raises:
        ValueError: If permission already exists
    """
    # Check if permission already exists
    existing_perm = db.query(Permission).filter(Permission.name == name).first()
    if existing_perm:
        raise ValueError(f"Permission '{name}' already exists")

    # Create permission
    permission = Permission(name=name, description=description, module=module)
    db.add(permission)
    db.commit()
    db.refresh(permission)

    return permission


def assign_permission_to_role(
    db: Session,
    role_name: str,
    permission_name: str
) -> bool:
    """
    Assign a permission to a role.

    Args:
        db: Database session
        role_name: Role name
        permission_name: Permission name

    Returns:
        bool: True if permission assigned successfully

    Raises:
        RoleNotFoundError: If role doesn't exist
        ValueError: If permission doesn't exist
    """
    # Get role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise RoleNotFoundError(f"Role '{role_name}' not found")

    # Get permission
    permission = db.query(Permission).filter(Permission.name == permission_name).first()
    if not permission:
        raise ValueError(f"Permission '{permission_name}' not found")

    # Check if role already has the permission
    if permission in role.permissions:
        return True

    # Assign permission
    role.permissions.append(permission)
    db.commit()

    return True


def remove_permission_from_role(
    db: Session,
    role_name: str,
    permission_name: str
) -> bool:
    """
    Remove a permission from a role.

    Args:
        db: Database session
        role_name: Role name
        permission_name: Permission name

    Returns:
        bool: True if permission removed successfully

    Raises:
        RoleNotFoundError: If role doesn't exist
        ValueError: If permission doesn't exist
    """
    # Get role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise RoleNotFoundError(f"Role '{role_name}' not found")

    # Get permission
    permission = db.query(Permission).filter(Permission.name == permission_name).first()
    if not permission:
        raise ValueError(f"Permission '{permission_name}' not found")

    # Check if role has the permission
    if permission not in role.permissions:
        return True

    # Remove permission
    role.permissions.remove(permission)
    db.commit()

    return True


def get_role_hierarchy_level(role_name: str) -> int:
    """
    Get hierarchy level of a role (higher = more privileged).

    Args:
        role_name: Role name

    Returns:
        int: Hierarchy level
    """
    hierarchy = {
        "guest": 0,
        "user": 1,
        "manager": 2,
        "admin": 3
    }
    return hierarchy.get(role_name, 0)


def can_manage_user(manager: User, target_user: User) -> bool:
    """
    Check if a manager can manage another user.
    Managers can only manage users with lower or equal hierarchy level.

    Args:
        manager: User attempting to manage
        target_user: User being managed

    Returns:
        bool: True if manager can manage target user
    """
    if not manager or not target_user:
        return False

    # Admins can manage anyone
    if is_admin(manager):
        return True

    # Get highest role level for both users
    manager_roles = get_user_roles(manager)
    target_roles = get_user_roles(target_user)

    manager_level = max(
        (get_role_hierarchy_level(role) for role in manager_roles),
        default=0
    )
    target_level = max(
        (get_role_hierarchy_level(role) for role in target_roles),
        default=0
    )

    # Manager must have higher level than target
    return manager_level > target_level


def require_permission_check(user: User, permission: str) -> None:
    """
    Check if user has permission, raise exception if not.

    Args:
        user: User to check
        permission: Permission required

    Raises:
        InsufficientPermissionsError: If user lacks permission
    """
    if not check_permission(user, permission):
        raise InsufficientPermissionsError(
            f"User does not have required permission: {permission}"
        )


def require_role_check(user: User, role: str) -> None:
    """
    Check if user has role, raise exception if not.

    Args:
        user: User to check
        role: Role required

    Raises:
        InsufficientPermissionsError: If user lacks role
    """
    if not check_role(user, role):
        raise InsufficientPermissionsError(
            f"User does not have required role: {role}"
        )


def require_any_role_check(user: User, roles: List[str]) -> None:
    """
    Check if user has any of the specified roles, raise exception if not.

    Args:
        user: User to check
        roles: List of acceptable roles

    Raises:
        InsufficientPermissionsError: If user lacks all roles
    """
    if not check_any_role(user, roles):
        raise InsufficientPermissionsError(
            f"User does not have any of the required roles: {', '.join(roles)}"
        )
