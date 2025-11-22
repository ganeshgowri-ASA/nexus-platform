"""
Database Admin Manager

User management, roles, permissions, and access control
for database administration.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import secrets
import logging


class PermissionType(Enum):
    """Permission types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    INDEX = "INDEX"
    GRANT = "GRANT"
    ALL = "ALL"


class ResourceType(Enum):
    """Resource types"""
    DATABASE = "DATABASE"
    TABLE = "TABLE"
    SCHEMA = "SCHEMA"
    VIEW = "VIEW"


@dataclass
class Permission:
    """Database permission"""
    permission_type: PermissionType
    resource_type: ResourceType
    resource_name: str
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "permission_type": self.permission_type.value,
            "resource_type": self.resource_type.value,
            "resource_name": self.resource_name,
            "granted_at": self.granted_at.isoformat(),
            "granted_by": self.granted_by
        }

    def to_sql(self, username: str) -> str:
        """Convert to SQL GRANT statement"""
        if self.permission_type == PermissionType.ALL:
            perm = "ALL PRIVILEGES"
        else:
            perm = self.permission_type.value

        if self.resource_type == ResourceType.TABLE:
            resource = f"TABLE {self.resource_name}"
        else:
            resource = self.resource_name

        return f"GRANT {perm} ON {resource} TO {username}"


@dataclass
class Role:
    """Database role"""
    name: str
    description: str = ""
    permissions: List[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def add_permission(self, permission: Permission) -> None:
        """Add permission to role"""
        self.permissions.append(permission)
        self.modified_at = datetime.now()

    def remove_permission(
        self,
        permission_type: PermissionType,
        resource_name: str
    ) -> None:
        """Remove permission from role"""
        self.permissions = [
            p for p in self.permissions
            if not (p.permission_type == permission_type and p.resource_name == resource_name)
        ]
        self.modified_at = datetime.now()

    def has_permission(
        self,
        permission_type: PermissionType,
        resource_name: str
    ) -> bool:
        """Check if role has specific permission"""
        return any(
            p.permission_type in (permission_type, PermissionType.ALL) and
            p.resource_name in (resource_name, "*")
            for p in self.permissions
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat()
        }


@dataclass
class User:
    """Database user"""
    username: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_password(self, password: str) -> None:
        """Set user password (hashed)"""
        salt = secrets.token_hex(16)
        self.password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex() + ":" + salt

    def verify_password(self, password: str) -> bool:
        """Verify password"""
        if not self.password_hash:
            return False

        try:
            hash_part, salt = self.password_hash.split(":")
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            return hash_part == new_hash
        except Exception:
            return False

    def add_role(self, role_name: str) -> None:
        """Add role to user"""
        if role_name not in self.roles:
            self.roles.append(role_name)

    def remove_role(self, role_name: str) -> None:
        """Remove role from user"""
        if role_name in self.roles:
            self.roles.remove(role_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding password)"""
        return {
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "metadata": self.metadata
        }


class AdminManager:
    """
    Database Admin Manager

    Manage database users, roles, permissions, and access control.
    """

    def __init__(self, connection=None):
        """
        Initialize admin manager

        Args:
            connection: DatabaseConnection instance (optional)
        """
        self.connection = connection
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.logger = logging.getLogger("database.admin")

        # Initialize default roles
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """Initialize default roles"""
        # Admin role
        admin_role = Role(
            name="admin",
            description="Full database access"
        )
        admin_role.add_permission(Permission(
            permission_type=PermissionType.ALL,
            resource_type=ResourceType.DATABASE,
            resource_name="*"
        ))
        self.roles["admin"] = admin_role

        # Read-only role
        readonly_role = Role(
            name="readonly",
            description="Read-only access"
        )
        readonly_role.add_permission(Permission(
            permission_type=PermissionType.SELECT,
            resource_type=ResourceType.TABLE,
            resource_name="*"
        ))
        self.roles["readonly"] = readonly_role

        # Developer role
        developer_role = Role(
            name="developer",
            description="Development access (CRUD operations)"
        )
        for perm_type in [PermissionType.SELECT, PermissionType.INSERT,
                         PermissionType.UPDATE, PermissionType.DELETE]:
            developer_role.add_permission(Permission(
                permission_type=perm_type,
                resource_type=ResourceType.TABLE,
                resource_name="*"
            ))
        self.roles["developer"] = developer_role

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        """
        Create a new user

        Args:
            username: Username
            password: Password
            email: Email address
            roles: List of role names

        Returns:
            Created User object
        """
        if username in self.users:
            raise ValueError(f"User '{username}' already exists")

        user = User(username=username, email=email)
        user.set_password(password)

        if roles:
            for role_name in roles:
                if role_name not in self.roles:
                    raise ValueError(f"Role '{role_name}' not found")
                user.add_role(role_name)

        self.users[username] = user
        self.logger.info(f"Created user: {username}")

        # Create database user if connection available
        if self.connection:
            self._create_db_user(username, password)

        return user

    def delete_user(self, username: str) -> None:
        """Delete a user"""
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")

        del self.users[username]
        self.logger.info(f"Deleted user: {username}")

        # Drop database user if connection available
        if self.connection:
            self._drop_db_user(username)

    def get_user(self, username: str) -> User:
        """Get user by username"""
        if username not in self.users:
            raise ValueError(f"User '{username}' not found")
        return self.users[username]

    def list_users(self, active_only: bool = False) -> List[User]:
        """List all users"""
        users = list(self.users.values())
        if active_only:
            users = [u for u in users if u.active]
        return users

    def update_user(
        self,
        username: str,
        email: Optional[str] = None,
        active: Optional[bool] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        """Update user information"""
        user = self.get_user(username)

        if email is not None:
            user.email = email
        if active is not None:
            user.active = active
        if roles is not None:
            user.roles = roles

        self.logger.info(f"Updated user: {username}")
        return user

    def change_password(self, username: str, new_password: str) -> None:
        """Change user password"""
        user = self.get_user(username)
        user.set_password(new_password)
        self.logger.info(f"Changed password for user: {username}")

        # Update database user if connection available
        if self.connection:
            self._update_db_user_password(username, new_password)

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user"""
        try:
            user = self.get_user(username)
            if not user.active:
                return False

            if user.verify_password(password):
                user.last_login = datetime.now()
                return True
            return False
        except ValueError:
            return False

    def create_role(self, name: str, description: str = "") -> Role:
        """Create a new role"""
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(name=name, description=description)
        self.roles[name] = role
        self.logger.info(f"Created role: {name}")

        return role

    def delete_role(self, name: str) -> None:
        """Delete a role"""
        if name not in self.roles:
            raise ValueError(f"Role '{name}' not found")

        # Remove role from all users
        for user in self.users.values():
            user.remove_role(name)

        del self.roles[name]
        self.logger.info(f"Deleted role: {name}")

    def get_role(self, name: str) -> Role:
        """Get role by name"""
        if name not in self.roles:
            raise ValueError(f"Role '{name}' not found")
        return self.roles[name]

    def list_roles(self) -> List[Role]:
        """List all roles"""
        return list(self.roles.values())

    def grant_permission(
        self,
        role_name: str,
        permission_type: PermissionType,
        resource_type: ResourceType,
        resource_name: str,
        granted_by: Optional[str] = None
    ) -> None:
        """Grant permission to role"""
        role = self.get_role(role_name)

        permission = Permission(
            permission_type=permission_type,
            resource_type=resource_type,
            resource_name=resource_name,
            granted_by=granted_by
        )

        role.add_permission(permission)
        self.logger.info(
            f"Granted {permission_type.value} on {resource_name} to role {role_name}"
        )

    def revoke_permission(
        self,
        role_name: str,
        permission_type: PermissionType,
        resource_name: str
    ) -> None:
        """Revoke permission from role"""
        role = self.get_role(role_name)
        role.remove_permission(permission_type, resource_name)
        self.logger.info(
            f"Revoked {permission_type.value} on {resource_name} from role {role_name}"
        )

    def check_permission(
        self,
        username: str,
        permission_type: PermissionType,
        resource_name: str
    ) -> bool:
        """Check if user has permission"""
        try:
            user = self.get_user(username)

            if not user.active:
                return False

            # Check all user's roles
            for role_name in user.roles:
                role = self.get_role(role_name)
                if role.has_permission(permission_type, resource_name):
                    return True

            return False

        except ValueError:
            return False

    def get_user_permissions(self, username: str) -> List[Permission]:
        """Get all permissions for a user"""
        user = self.get_user(username)
        permissions = []

        for role_name in user.roles:
            role = self.get_role(role_name)
            permissions.extend(role.permissions)

        return permissions

    def assign_role(self, username: str, role_name: str) -> None:
        """Assign role to user"""
        user = self.get_user(username)
        role = self.get_role(role_name)  # Verify role exists

        user.add_role(role_name)
        self.logger.info(f"Assigned role '{role_name}' to user '{username}'")

        # Grant role in database if connection available
        if self.connection:
            self._grant_db_role(username, role)

    def remove_role_from_user(self, username: str, role_name: str) -> None:
        """Remove role from user"""
        user = self.get_user(username)
        user.remove_role(role_name)
        self.logger.info(f"Removed role '{role_name}' from user '{username}'")

    def get_access_report(self) -> Dict[str, Any]:
        """
        Generate access control report

        Returns:
            Report dictionary
        """
        report = {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.active]),
            "total_roles": len(self.roles),
            "users_by_role": {},
            "permissions_by_role": {}
        }

        # Count users by role
        for role_name in self.roles:
            users_with_role = [
                u.username for u in self.users.values()
                if role_name in u.roles
            ]
            report["users_by_role"][role_name] = len(users_with_role)

        # Count permissions by role
        for role_name, role in self.roles.items():
            report["permissions_by_role"][role_name] = len(role.permissions)

        return report

    def export_config(self, filepath: str) -> None:
        """Export users and roles to JSON"""
        import json

        data = {
            "users": [u.to_dict() for u in self.users.values()],
            "roles": [r.to_dict() for r in self.roles.values()],
            "exported_at": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported config to {filepath}")

    def import_config(self, filepath: str) -> None:
        """Import users and roles from JSON"""
        import json

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Import roles first
        for role_data in data.get("roles", []):
            if role_data["name"] not in self.roles:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    created_at=datetime.fromisoformat(role_data["created_at"])
                )

                for perm_data in role_data.get("permissions", []):
                    permission = Permission(
                        permission_type=PermissionType(perm_data["permission_type"]),
                        resource_type=ResourceType(perm_data["resource_type"]),
                        resource_name=perm_data["resource_name"],
                        granted_at=datetime.fromisoformat(perm_data["granted_at"]),
                        granted_by=perm_data.get("granted_by")
                    )
                    role.add_permission(permission)

                self.roles[role.name] = role

        # Import users
        for user_data in data.get("users", []):
            if user_data["username"] not in self.users:
                user = User(
                    username=user_data["username"],
                    email=user_data.get("email"),
                    roles=user_data.get("roles", []),
                    active=user_data.get("active", True),
                    created_at=datetime.fromisoformat(user_data["created_at"]),
                    metadata=user_data.get("metadata", {})
                )

                if user_data.get("last_login"):
                    user.last_login = datetime.fromisoformat(user_data["last_login"])

                self.users[user.username] = user

        self.logger.info(f"Imported config from {filepath}")

    def _create_db_user(self, username: str, password: str) -> None:
        """Create user in database"""
        try:
            # PostgreSQL style
            create_sql = f"CREATE USER {username} WITH PASSWORD '{password}'"
            self.connection.execute_command(create_sql)
        except Exception as e:
            self.logger.warning(f"Could not create database user: {e}")

    def _drop_db_user(self, username: str) -> None:
        """Drop user from database"""
        try:
            drop_sql = f"DROP USER IF EXISTS {username}"
            self.connection.execute_command(drop_sql)
        except Exception as e:
            self.logger.warning(f"Could not drop database user: {e}")

    def _update_db_user_password(self, username: str, password: str) -> None:
        """Update database user password"""
        try:
            # PostgreSQL style
            alter_sql = f"ALTER USER {username} WITH PASSWORD '{password}'"
            self.connection.execute_command(alter_sql)
        except Exception as e:
            self.logger.warning(f"Could not update database user password: {e}")

    def _grant_db_role(self, username: str, role: Role) -> None:
        """Grant role permissions in database"""
        try:
            for permission in role.permissions:
                grant_sql = permission.to_sql(username)
                self.connection.execute_command(grant_sql)
        except Exception as e:
            self.logger.warning(f"Could not grant database permissions: {e}")
