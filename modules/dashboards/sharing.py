"""
NEXUS Dashboard Builder - Sharing and Embed Module
Dashboard sharing, public links, and embed functionality
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib


class SharePermission(Enum):
    """Share permission levels"""
    VIEW = "view"
    INTERACT = "interact"
    EDIT = "edit"


class ShareExpiry(Enum):
    """Share link expiry options"""
    NEVER = "never"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    CUSTOM = "custom"


@dataclass
class ShareLink:
    """Represents a dashboard share link"""
    share_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dashboard_id: str = ""
    token: str = field(default_factory=lambda: hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest())
    created_by: str = "admin"
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    permission: SharePermission = SharePermission.VIEW
    password_protected: bool = False
    password_hash: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    is_active: bool = True
    allowed_domains: List[str] = field(default_factory=list)
    max_access_count: Optional[int] = None

    def is_valid(self) -> bool:
        """Check if share link is valid"""
        if not self.is_active:
            return False

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        if self.max_access_count and self.access_count >= self.max_access_count:
            return False

        return True

    def record_access(self):
        """Record an access to this link"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def check_password(self, password: str) -> bool:
        """Check password"""
        if not self.password_protected:
            return True

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash

    def set_password(self, password: str):
        """Set password"""
        self.password_protected = True
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def get_url(self, base_url: str) -> str:
        """Get share URL"""
        return f"{base_url}/share/{self.token}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'share_id': self.share_id,
            'dashboard_id': self.dashboard_id,
            'token': self.token,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'permission': self.permission.value,
            'password_protected': self.password_protected,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'is_active': self.is_active,
            'allowed_domains': self.allowed_domains,
            'max_access_count': self.max_access_count
        }


@dataclass
class EmbedConfig:
    """Configuration for dashboard embedding"""
    embed_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dashboard_id: str = ""
    width: str = "100%"
    height: str = "800px"
    border: bool = False
    title_visible: bool = True
    filters_visible: bool = True
    toolbar_visible: bool = False
    auto_refresh: bool = True
    theme: str = "light"
    allowed_origins: List[str] = field(default_factory=list)

    def generate_iframe_code(self, share_token: str, base_url: str) -> str:
        """Generate iframe embed code"""
        url = f"{base_url}/embed/{self.dashboard_id}?token={share_token}"

        params = []
        if not self.title_visible:
            params.append("hide_title=1")
        if not self.filters_visible:
            params.append("hide_filters=1")
        if not self.toolbar_visible:
            params.append("hide_toolbar=1")
        if self.auto_refresh:
            params.append("auto_refresh=1")
        if self.theme:
            params.append(f"theme={self.theme}")

        if params:
            url += "&" + "&".join(params)

        border = "0" if not self.border else "1"

        return f'''<iframe
    src="{url}"
    width="{self.width}"
    height="{self.height}"
    frameborder="{border}"
    allowfullscreen
></iframe>'''

    def generate_script_embed(self, share_token: str, base_url: str) -> str:
        """Generate JavaScript embed code"""
        return f'''<div id="nexus-dashboard-{self.embed_id}"></div>
<script src="{base_url}/static/embed.js"></script>
<script>
  NexusDashboard.embed({{
    container: '#nexus-dashboard-{self.embed_id}',
    dashboardId: '{self.dashboard_id}',
    token: '{share_token}',
    width: '{self.width}',
    height: '{self.height}',
    theme: '{self.theme}',
    autoRefresh: {str(self.auto_refresh).lower()}
  }});
</script>'''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'embed_id': self.embed_id,
            'dashboard_id': self.dashboard_id,
            'width': self.width,
            'height': self.height,
            'border': self.border,
            'title_visible': self.title_visible,
            'filters_visible': self.filters_visible,
            'toolbar_visible': self.toolbar_visible,
            'auto_refresh': self.auto_refresh,
            'theme': self.theme,
            'allowed_origins': self.allowed_origins
        }


class SharingManager:
    """Manages dashboard sharing and embedding"""

    def __init__(self):
        self.share_links: Dict[str, ShareLink] = {}
        self.embed_configs: Dict[str, EmbedConfig] = {}
        self.token_to_share: Dict[str, str] = {}

    def create_share_link(self, dashboard_id: str, expiry: ShareExpiry = ShareExpiry.NEVER,
                         permission: SharePermission = SharePermission.VIEW,
                         password: Optional[str] = None,
                         created_by: str = "admin") -> ShareLink:
        """Create a new share link"""
        share = ShareLink(
            dashboard_id=dashboard_id,
            created_by=created_by,
            permission=permission
        )

        # Set expiry
        if expiry == ShareExpiry.ONE_HOUR:
            share.expires_at = datetime.now() + timedelta(hours=1)
        elif expiry == ShareExpiry.ONE_DAY:
            share.expires_at = datetime.now() + timedelta(days=1)
        elif expiry == ShareExpiry.ONE_WEEK:
            share.expires_at = datetime.now() + timedelta(weeks=1)
        elif expiry == ShareExpiry.ONE_MONTH:
            share.expires_at = datetime.now() + timedelta(days=30)

        # Set password
        if password:
            share.set_password(password)

        # Store share
        self.share_links[share.share_id] = share
        self.token_to_share[share.token] = share.share_id

        return share

    def get_share_link(self, share_id: str) -> Optional[ShareLink]:
        """Get share link by ID"""
        return self.share_links.get(share_id)

    def get_share_by_token(self, token: str) -> Optional[ShareLink]:
        """Get share link by token"""
        share_id = self.token_to_share.get(token)
        if share_id:
            return self.share_links.get(share_id)
        return None

    def revoke_share_link(self, share_id: str) -> bool:
        """Revoke a share link"""
        share = self.get_share_link(share_id)
        if share:
            share.is_active = False
            return True
        return False

    def delete_share_link(self, share_id: str) -> bool:
        """Delete a share link"""
        if share_id in self.share_links:
            share = self.share_links[share_id]
            del self.token_to_share[share.token]
            del self.share_links[share_id]
            return True
        return False

    def list_share_links(self, dashboard_id: Optional[str] = None) -> List[ShareLink]:
        """List share links"""
        links = list(self.share_links.values())

        if dashboard_id:
            links = [link for link in links if link.dashboard_id == dashboard_id]

        return links

    def create_embed_config(self, dashboard_id: str, **kwargs) -> EmbedConfig:
        """Create embed configuration"""
        config = EmbedConfig(dashboard_id=dashboard_id, **kwargs)
        self.embed_configs[config.embed_id] = config
        return config

    def get_embed_config(self, embed_id: str) -> Optional[EmbedConfig]:
        """Get embed configuration"""
        return self.embed_configs.get(embed_id)

    def update_embed_config(self, embed_id: str, updates: Dict[str, Any]) -> bool:
        """Update embed configuration"""
        config = self.get_embed_config(embed_id)
        if config:
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            return True
        return False

    def delete_embed_config(self, embed_id: str) -> bool:
        """Delete embed configuration"""
        if embed_id in self.embed_configs:
            del self.embed_configs[embed_id]
            return True
        return False

    def verify_access(self, token: str, password: Optional[str] = None) -> Optional[ShareLink]:
        """Verify access to a share link"""
        share = self.get_share_by_token(token)

        if not share:
            return None

        if not share.is_valid():
            return None

        if share.password_protected and not share.check_password(password or ""):
            return None

        share.record_access()
        return share

    def get_stats(self) -> Dict[str, Any]:
        """Get sharing statistics"""
        total_shares = len(self.share_links)
        active_shares = sum(1 for s in self.share_links.values() if s.is_active)
        total_accesses = sum(s.access_count for s in self.share_links.values())

        return {
            'total_shares': total_shares,
            'active_shares': active_shares,
            'total_accesses': total_accesses,
            'total_embeds': len(self.embed_configs)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'share_links': [s.to_dict() for s in self.share_links.values()],
            'embed_configs': [e.to_dict() for e in self.embed_configs.values()],
            'stats': self.get_stats()
        }
