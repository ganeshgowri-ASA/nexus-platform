"""
Versioning Module

Handles API versioning (v1, v2), deprecation warnings, and migration guides.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import json


class VersionStatus(Enum):
    """API version status."""
    DEVELOPMENT = "development"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class VersioningStrategy(Enum):
    """API versioning strategies."""
    URL_PATH = "url_path"  # /v1/resource
    QUERY_PARAM = "query_param"  # /resource?version=1
    HEADER = "header"  # Accept: application/vnd.api+json; version=1
    CONTENT_TYPE = "content_type"  # Content-Type: application/vnd.api.v1+json


@dataclass
class DeprecationWarning:
    """Represents a deprecation warning."""
    message: str
    sunset_date: Optional[datetime] = None  # When the version will be retired
    alternative: Optional[str] = None  # Recommended alternative
    migration_guide_url: Optional[str] = None
    breaking_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "alternative": self.alternative,
            "migration_guide_url": self.migration_guide_url,
            "breaking_changes": self.breaking_changes,
        }

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers."""
        headers = {
            "Deprecation": "true",
            "X-API-Deprecated": "true",
        }

        if self.sunset_date:
            headers["Sunset"] = self.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

        if self.alternative:
            headers["X-API-Alternative"] = self.alternative

        if self.migration_guide_url:
            headers["Link"] = f'<{self.migration_guide_url}>; rel="deprecation"'

        return headers


@dataclass
class ChangelogEntry:
    """Represents a changelog entry."""
    version: str
    date: datetime
    type: str  # "added", "changed", "deprecated", "removed", "fixed", "security"
    description: str
    breaking: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "date": self.date.isoformat(),
            "type": self.type,
            "description": self.description,
            "breaking": self.breaking,
        }


@dataclass
class APIVersion:
    """Represents an API version."""
    version: str  # e.g., "1.0.0", "2.0.0"
    status: VersionStatus
    release_date: datetime = field(default_factory=datetime.now)
    sunset_date: Optional[datetime] = None
    description: str = ""
    changelog: List[ChangelogEntry] = field(default_factory=list)
    deprecation_warning: Optional[DeprecationWarning] = None
    endpoints: List[str] = field(default_factory=list)  # Endpoint IDs in this version
    base_path: str = ""  # e.g., "/v1" or "/api/v2"

    def is_active(self) -> bool:
        """Check if version is active (not retired)."""
        return self.status != VersionStatus.RETIRED

    def is_supported(self) -> bool:
        """Check if version is still supported."""
        if self.status == VersionStatus.RETIRED:
            return False

        if self.sunset_date and datetime.now() > self.sunset_date:
            return False

        return True

    def days_until_sunset(self) -> Optional[int]:
        """Get number of days until sunset."""
        if not self.sunset_date:
            return None

        delta = self.sunset_date - datetime.now()
        return max(0, delta.days)

    def add_changelog_entry(
        self,
        type: str,
        description: str,
        breaking: bool = False,
    ) -> None:
        """Add a changelog entry."""
        entry = ChangelogEntry(
            version=self.version,
            date=datetime.now(),
            type=type,
            description=description,
            breaking=breaking,
        )
        self.changelog.append(entry)

    def mark_deprecated(
        self,
        message: str,
        sunset_days: int = 90,
        alternative: Optional[str] = None,
        migration_guide_url: Optional[str] = None,
    ) -> None:
        """Mark version as deprecated."""
        self.status = VersionStatus.DEPRECATED
        self.sunset_date = datetime.now() + timedelta(days=sunset_days)

        self.deprecation_warning = DeprecationWarning(
            message=message,
            sunset_date=self.sunset_date,
            alternative=alternative,
            migration_guide_url=migration_guide_url,
        )

    def retire(self) -> None:
        """Retire this version."""
        self.status = VersionStatus.RETIRED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "status": self.status.value,
            "release_date": self.release_date.isoformat(),
            "sunset_date": self.sunset_date.isoformat() if self.sunset_date else None,
            "description": self.description,
            "changelog": [e.to_dict() for e in self.changelog],
            "deprecation_warning": self.deprecation_warning.to_dict() if self.deprecation_warning else None,
            "endpoints": self.endpoints,
            "base_path": self.base_path,
        }


class VersionManager:
    """Manages API versions."""

    def __init__(self, strategy: VersioningStrategy = VersioningStrategy.URL_PATH):
        self.versions: Dict[str, APIVersion] = {}
        self.strategy = strategy
        self.current_version: Optional[str] = None
        self.default_version: Optional[str] = None

    def add_version(self, version: APIVersion) -> None:
        """Add a new API version."""
        self.versions[version.version] = version

        # Set as current if it's stable and we don't have a current version
        if version.status == VersionStatus.STABLE and not self.current_version:
            self.current_version = version.version

        # Set as default if we don't have one
        if not self.default_version:
            self.default_version = version.version

    def remove_version(self, version: str) -> bool:
        """Remove a version."""
        if version in self.versions:
            del self.versions[version]
            if self.current_version == version:
                self.current_version = None
            if self.default_version == version:
                self.default_version = None
            return True
        return False

    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get a specific version."""
        return self.versions.get(version)

    def get_latest_version(self) -> Optional[APIVersion]:
        """Get the latest stable version."""
        stable_versions = [
            v for v in self.versions.values()
            if v.status == VersionStatus.STABLE
        ]

        if not stable_versions:
            return None

        # Sort by version string (assumes semantic versioning)
        sorted_versions = sorted(
            stable_versions,
            key=lambda v: [int(x) for x in v.version.split('.')],
            reverse=True
        )

        return sorted_versions[0]

    def get_active_versions(self) -> List[APIVersion]:
        """Get all active (non-retired) versions."""
        return [v for v in self.versions.values() if v.is_active()]

    def get_supported_versions(self) -> List[APIVersion]:
        """Get all supported versions."""
        return [v for v in self.versions.values() if v.is_supported()]

    def get_deprecated_versions(self) -> List[APIVersion]:
        """Get all deprecated versions."""
        return [
            v for v in self.versions.values()
            if v.status == VersionStatus.DEPRECATED
        ]

    def extract_version_from_request(
        self,
        path: str,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Extract version from request based on strategy."""
        if self.strategy == VersioningStrategy.URL_PATH:
            # Extract from path like /v1/resource or /api/v2/resource
            parts = path.strip('/').split('/')
            for part in parts:
                if part.startswith('v') and part[1:].replace('.', '').isdigit():
                    version_num = part[1:]
                    # Convert "1" to "1.0.0" if needed
                    if version_num.isdigit():
                        version_num = f"{version_num}.0.0"
                    return version_num

        elif self.strategy == VersioningStrategy.QUERY_PARAM:
            # Extract from query parameter
            if query_params:
                return query_params.get('version') or query_params.get('api-version')

        elif self.strategy == VersioningStrategy.HEADER:
            # Extract from custom header
            if headers:
                return headers.get('X-API-Version') or headers.get('API-Version')

        elif self.strategy == VersioningStrategy.CONTENT_TYPE:
            # Extract from Accept or Content-Type header
            if headers:
                accept = headers.get('Accept', '')
                # Parse version from content type like "application/vnd.api.v1+json"
                if 'vnd.api.v' in accept:
                    version_part = accept.split('vnd.api.v')[1].split('+')[0]
                    return version_part

        # Return default version if no version specified
        return self.default_version

    def get_version_path(self, version: str, resource_path: str) -> str:
        """Get the full path for a resource in a specific version."""
        api_version = self.versions.get(version)
        if not api_version:
            return resource_path

        if self.strategy == VersioningStrategy.URL_PATH:
            base_path = api_version.base_path or f"/v{version.split('.')[0]}"
            return f"{base_path}{resource_path}"

        return resource_path

    def check_compatibility(
        self,
        from_version: str,
        to_version: str,
    ) -> tuple[bool, List[str]]:
        """Check compatibility between versions."""
        from_ver = self.versions.get(from_version)
        to_ver = self.versions.get(to_version)

        if not from_ver or not to_ver:
            return False, ["One or both versions not found"]

        breaking_changes = []

        # Check changelog for breaking changes
        for entry in to_ver.changelog:
            if entry.breaking and entry.version > from_version:
                breaking_changes.append(entry.description)

        # Check deprecation warnings
        if from_ver.deprecation_warning:
            breaking_changes.extend(from_ver.deprecation_warning.breaking_changes)

        is_compatible = len(breaking_changes) == 0

        return is_compatible, breaking_changes

    def generate_migration_guide(
        self,
        from_version: str,
        to_version: str,
    ) -> Dict[str, Any]:
        """Generate a migration guide between versions."""
        from_ver = self.versions.get(from_version)
        to_ver = self.versions.get(to_version)

        if not from_ver or not to_ver:
            return {"error": "Version not found"}

        is_compatible, breaking_changes = self.check_compatibility(
            from_version, to_version
        )

        # Collect all changes between versions
        changes = {
            "added": [],
            "changed": [],
            "deprecated": [],
            "removed": [],
            "fixed": [],
            "security": [],
        }

        for entry in to_ver.changelog:
            if entry.version > from_version:
                if entry.type in changes:
                    changes[entry.type].append(entry.description)

        guide = {
            "from_version": from_version,
            "to_version": to_version,
            "compatible": is_compatible,
            "breaking_changes": breaking_changes,
            "changes": changes,
            "steps": [],
        }

        # Add migration steps
        if breaking_changes:
            guide["steps"].append({
                "step": 1,
                "title": "Review Breaking Changes",
                "description": "Carefully review all breaking changes before migrating.",
                "items": breaking_changes,
            })

        if changes["deprecated"]:
            guide["steps"].append({
                "step": len(guide["steps"]) + 1,
                "title": "Update Deprecated Features",
                "description": "Replace deprecated features with recommended alternatives.",
                "items": changes["deprecated"],
            })

        if changes["changed"]:
            guide["steps"].append({
                "step": len(guide["steps"]) + 1,
                "title": "Adapt to Changes",
                "description": "Update your code to work with changed features.",
                "items": changes["changed"],
            })

        if changes["added"]:
            guide["steps"].append({
                "step": len(guide["steps"]) + 1,
                "title": "Consider New Features",
                "description": "Explore new features that may benefit your application.",
                "items": changes["added"],
            })

        guide["steps"].append({
            "step": len(guide["steps"]) + 1,
            "title": "Test Thoroughly",
            "description": "Run comprehensive tests to ensure compatibility.",
        })

        return guide

    def get_version_info(self, version: str) -> Dict[str, Any]:
        """Get comprehensive version information."""
        api_version = self.versions.get(version)
        if not api_version:
            return {"error": "Version not found"}

        info = api_version.to_dict()
        info["is_active"] = api_version.is_active()
        info["is_supported"] = api_version.is_supported()
        info["days_until_sunset"] = api_version.days_until_sunset()

        return info

    def export_versions(self) -> str:
        """Export all versions to JSON."""
        data = {
            "strategy": self.strategy.value,
            "current_version": self.current_version,
            "default_version": self.default_version,
            "versions": [v.to_dict() for v in self.versions.values()],
        }
        return json.dumps(data, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get version statistics."""
        by_status = {}
        for version in self.versions.values():
            status = version.status.value
            by_status[status] = by_status.get(status, 0) + 1

        deprecated = self.get_deprecated_versions()
        sunset_warnings = []

        for version in deprecated:
            days_left = version.days_until_sunset()
            if days_left is not None and days_left <= 30:
                sunset_warnings.append({
                    "version": version.version,
                    "days_left": days_left,
                })

        return {
            "total_versions": len(self.versions),
            "current_version": self.current_version,
            "default_version": self.default_version,
            "by_status": by_status,
            "sunset_warnings": sunset_warnings,
        }


# Utility functions

def create_version(
    version: str,
    status: VersionStatus = VersionStatus.DEVELOPMENT,
    description: str = "",
) -> APIVersion:
    """Create a new API version."""
    return APIVersion(
        version=version,
        status=status,
        description=description,
        base_path=f"/v{version.split('.')[0]}",
    )


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse semantic version string."""
    parts = version.split('.')
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return major, minor, patch


def compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2."""
    major1, minor1, patch1 = parse_semver(v1)
    major2, minor2, patch2 = parse_semver(v2)

    if (major1, minor1, patch1) < (major2, minor2, patch2):
        return -1
    elif (major1, minor1, patch1) > (major2, minor2, patch2):
        return 1
    else:
        return 0
