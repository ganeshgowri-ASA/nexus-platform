"""
Hosting Manager - Custom domains, SSL certificates, CDN, and backups
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import json


class DomainStatus(Enum):
    """Domain status"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    ERROR = "error"


class SSLStatus(Enum):
    """SSL certificate status"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    RENEWING = "renewing"
    ERROR = "error"


class CDNProvider(Enum):
    """CDN providers"""
    CLOUDFLARE = "cloudflare"
    CLOUDFRONT = "cloudfront"
    FASTLY = "fastly"
    AKAMAI = "akamai"


@dataclass
class DomainConfig:
    """Domain configuration"""
    domain_id: str
    domain_name: str
    is_primary: bool = False
    status: DomainStatus = DomainStatus.PENDING
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    dns_records: List[Dict[str, str]] = field(default_factory=list)
    nameservers: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = datetime.now() + timedelta(days=365)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "domain_id": self.domain_id,
            "domain_name": self.domain_name,
            "is_primary": self.is_primary,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "dns_records": self.dns_records,
            "nameservers": self.nameservers,
        }


@dataclass
class SSLCertificate:
    """SSL certificate"""
    cert_id: str
    domain_name: str
    issuer: str = "Let's Encrypt"
    status: SSLStatus = SSLStatus.PENDING
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renew: bool = True

    def __post_init__(self):
        if self.issued_at is None:
            self.issued_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = datetime.now() + timedelta(days=90)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cert_id": self.cert_id,
            "domain_name": self.domain_name,
            "issuer": self.issuer,
            "status": self.status.value,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_renew": self.auto_renew,
        }


@dataclass
class CDNConfig:
    """CDN configuration"""
    cdn_id: str
    provider: CDNProvider
    enabled: bool = False
    cache_ttl: int = 3600  # seconds
    compress_assets: bool = True
    minify_html: bool = True
    minify_css: bool = True
    minify_js: bool = True
    image_optimization: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cdn_id": self.cdn_id,
            "provider": self.provider.value,
            "enabled": self.enabled,
            "cache_ttl": self.cache_ttl,
            "compress_assets": self.compress_assets,
            "minify_html": self.minify_html,
            "minify_css": self.minify_css,
            "minify_js": self.minify_js,
            "image_optimization": self.image_optimization,
            "custom_headers": self.custom_headers,
        }


@dataclass
class Backup:
    """Website backup"""
    backup_id: str
    backup_type: str  # full, incremental
    created_at: datetime
    size_bytes: int
    status: str  # pending, completed, failed
    file_path: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "status": self.status,
            "file_path": self.file_path,
            "description": self.description,
        }


class HostingManager:
    """Manager for website hosting"""

    def __init__(self):
        self.domains: Dict[str, DomainConfig] = {}
        self.ssl_certificates: Dict[str, SSLCertificate] = {}
        self.cdn_configs: Dict[str, CDNConfig] = {}
        self.backups: Dict[str, Backup] = {}

    # Domain Management

    def add_domain(self, domain_name: str, is_primary: bool = False) -> DomainConfig:
        """Add a custom domain"""
        # Validate domain name
        if not self._is_valid_domain(domain_name):
            raise ValueError(f"Invalid domain name: {domain_name}")

        # Check if domain already exists
        for domain in self.domains.values():
            if domain.domain_name == domain_name:
                raise ValueError(f"Domain {domain_name} already exists")

        domain_id = self._generate_id(domain_name)

        # If this is primary, unset other primary domains
        if is_primary:
            for domain in self.domains.values():
                domain.is_primary = False

        domain = DomainConfig(
            domain_id=domain_id,
            domain_name=domain_name,
            is_primary=is_primary,
            status=DomainStatus.PENDING,
        )

        self.domains[domain_id] = domain
        return domain

    def remove_domain(self, domain_id: str) -> bool:
        """Remove a domain"""
        if domain_id not in self.domains:
            return False

        # Remove associated SSL certificate
        domain = self.domains[domain_id]
        for cert_id, cert in list(self.ssl_certificates.items()):
            if cert.domain_name == domain.domain_name:
                del self.ssl_certificates[cert_id]

        del self.domains[domain_id]
        return True

    def verify_domain(self, domain_id: str) -> bool:
        """Verify domain ownership"""
        domain = self.domains.get(domain_id)
        if not domain:
            return False

        # In a real implementation, this would check DNS records
        # For now, we'll simulate verification
        domain.status = DomainStatus.ACTIVE
        return True

    def add_dns_record(
        self,
        domain_id: str,
        record_type: str,
        name: str,
        value: str,
        ttl: int = 3600,
    ) -> bool:
        """Add DNS record to domain"""
        domain = self.domains.get(domain_id)
        if not domain:
            return False

        record = {
            "type": record_type,
            "name": name,
            "value": value,
            "ttl": ttl,
        }

        domain.dns_records.append(record)
        return True

    def get_domain_info(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Get domain information"""
        domain = self.domains.get(domain_id)
        if not domain:
            return None

        return domain.to_dict()

    def get_all_domains(self) -> List[DomainConfig]:
        """Get all domains"""
        return list(self.domains.values())

    def get_primary_domain(self) -> Optional[DomainConfig]:
        """Get primary domain"""
        for domain in self.domains.values():
            if domain.is_primary:
                return domain
        return None

    def set_primary_domain(self, domain_id: str) -> bool:
        """Set a domain as primary"""
        domain = self.domains.get(domain_id)
        if not domain:
            return False

        # Unset other primary domains
        for d in self.domains.values():
            d.is_primary = False

        domain.is_primary = True
        return True

    # SSL Certificate Management

    def request_ssl_certificate(self, domain_name: str) -> SSLCertificate:
        """Request SSL certificate for domain"""
        cert_id = self._generate_id(f"ssl_{domain_name}")

        # Check if certificate already exists
        for cert in self.ssl_certificates.values():
            if cert.domain_name == domain_name:
                return cert

        cert = SSLCertificate(
            cert_id=cert_id,
            domain_name=domain_name,
            status=SSLStatus.PENDING,
        )

        self.ssl_certificates[cert_id] = cert

        # Auto-activate (in real implementation, this would involve ACME protocol)
        cert.status = SSLStatus.ACTIVE
        cert.issued_at = datetime.now()

        return cert

    def renew_ssl_certificate(self, cert_id: str) -> bool:
        """Renew SSL certificate"""
        cert = self.ssl_certificates.get(cert_id)
        if not cert:
            return False

        cert.status = SSLStatus.RENEWING
        # Simulate renewal
        cert.status = SSLStatus.ACTIVE
        cert.issued_at = datetime.now()
        cert.expires_at = datetime.now() + timedelta(days=90)

        return True

    def get_ssl_certificate(self, domain_name: str) -> Optional[SSLCertificate]:
        """Get SSL certificate for domain"""
        for cert in self.ssl_certificates.values():
            if cert.domain_name == domain_name:
                return cert
        return None

    def check_ssl_expiry(self) -> List[SSLCertificate]:
        """Check for expiring SSL certificates"""
        expiring = []
        now = datetime.now()
        warning_period = timedelta(days=30)

        for cert in self.ssl_certificates.values():
            if cert.expires_at and cert.expires_at - now < warning_period:
                expiring.append(cert)

        return expiring

    def auto_renew_ssl_certificates(self) -> int:
        """Auto-renew SSL certificates that are about to expire"""
        renewed_count = 0
        expiring = self.check_ssl_expiry()

        for cert in expiring:
            if cert.auto_renew:
                if self.renew_ssl_certificate(cert.cert_id):
                    renewed_count += 1

        return renewed_count

    # CDN Management

    def setup_cdn(self, provider: CDNProvider) -> CDNConfig:
        """Setup CDN for website"""
        cdn_id = self._generate_id(f"cdn_{provider.value}")

        cdn = CDNConfig(
            cdn_id=cdn_id,
            provider=provider,
            enabled=True,
        )

        self.cdn_configs[cdn_id] = cdn
        return cdn

    def enable_cdn(self, cdn_id: str) -> bool:
        """Enable CDN"""
        cdn = self.cdn_configs.get(cdn_id)
        if not cdn:
            return False

        cdn.enabled = True
        return True

    def disable_cdn(self, cdn_id: str) -> bool:
        """Disable CDN"""
        cdn = self.cdn_configs.get(cdn_id)
        if not cdn:
            return False

        cdn.enabled = False
        return True

    def purge_cdn_cache(self, cdn_id: str) -> bool:
        """Purge CDN cache"""
        cdn = self.cdn_configs.get(cdn_id)
        if not cdn or not cdn.enabled:
            return False

        # In real implementation, this would call CDN API
        return True

    def configure_cdn(
        self,
        cdn_id: str,
        cache_ttl: Optional[int] = None,
        minify_html: Optional[bool] = None,
        minify_css: Optional[bool] = None,
        minify_js: Optional[bool] = None,
        image_optimization: Optional[bool] = None,
    ) -> bool:
        """Configure CDN settings"""
        cdn = self.cdn_configs.get(cdn_id)
        if not cdn:
            return False

        if cache_ttl is not None:
            cdn.cache_ttl = cache_ttl
        if minify_html is not None:
            cdn.minify_html = minify_html
        if minify_css is not None:
            cdn.minify_css = minify_css
        if minify_js is not None:
            cdn.minify_js = minify_js
        if image_optimization is not None:
            cdn.image_optimization = image_optimization

        return True

    # Backup Management

    def create_backup(
        self,
        backup_type: str = "full",
        description: str = "",
    ) -> Backup:
        """Create website backup"""
        backup_id = self._generate_id(f"backup_{datetime.now().isoformat()}")

        backup = Backup(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=datetime.now(),
            size_bytes=0,  # Would be calculated in real implementation
            status="pending",
            file_path=f"/backups/{backup_id}.zip",
            description=description,
        )

        self.backups[backup_id] = backup

        # Simulate backup completion
        backup.status = "completed"
        backup.size_bytes = 1024 * 1024 * 100  # 100 MB

        return backup

    def restore_backup(self, backup_id: str) -> bool:
        """Restore from backup"""
        backup = self.backups.get(backup_id)
        if not backup or backup.status != "completed":
            return False

        # In real implementation, this would restore files and database
        return True

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        if backup_id not in self.backups:
            return False

        del self.backups[backup_id]
        return True

    def get_all_backups(self) -> List[Backup]:
        """Get all backups"""
        return sorted(
            self.backups.values(),
            key=lambda b: b.created_at,
            reverse=True
        )

    def schedule_automatic_backups(
        self,
        frequency: str = "daily",
        retention_days: int = 30,
    ) -> Dict[str, Any]:
        """Schedule automatic backups"""
        schedule = {
            "frequency": frequency,
            "retention_days": retention_days,
            "enabled": True,
            "last_backup": None,
            "next_backup": datetime.now() + timedelta(days=1),
        }

        return schedule

    # Deployment Management

    def deploy_website(
        self,
        version: str,
        environment: str = "production",
    ) -> Dict[str, Any]:
        """Deploy website"""
        deployment = {
            "deployment_id": self._generate_id(f"deploy_{version}"),
            "version": version,
            "environment": environment,
            "status": "deploying",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
        }

        # Simulate deployment
        deployment["status"] = "completed"
        deployment["completed_at"] = datetime.now().isoformat()

        return deployment

    def rollback_deployment(self, version: str) -> bool:
        """Rollback to previous version"""
        # In real implementation, this would restore previous version
        return True

    # Analytics & Monitoring

    def get_hosting_stats(self) -> Dict[str, Any]:
        """Get hosting statistics"""
        return {
            "domains": len(self.domains),
            "active_domains": len([d for d in self.domains.values() if d.status == DomainStatus.ACTIVE]),
            "ssl_certificates": len(self.ssl_certificates),
            "active_ssl": len([c for c in self.ssl_certificates.values() if c.status == SSLStatus.ACTIVE]),
            "cdn_enabled": any(cdn.enabled for cdn in self.cdn_configs.values()),
            "total_backups": len(self.backups),
            "backup_size_mb": sum(b.size_bytes for b in self.backups.values()) / (1024 * 1024),
        }

    def get_uptime_stats(self) -> Dict[str, Any]:
        """Get uptime statistics"""
        return {
            "uptime_percentage": 99.9,
            "total_downtime_minutes": 43,
            "last_incident": None,
            "average_response_time_ms": 150,
        }

    def get_bandwidth_usage(self, period: str = "month") -> Dict[str, Any]:
        """Get bandwidth usage"""
        return {
            "period": period,
            "total_bandwidth_gb": 150.5,
            "cached_bandwidth_gb": 120.2,
            "origin_bandwidth_gb": 30.3,
            "requests_count": 1500000,
        }

    # Helper Methods

    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain name format"""
        import re
        pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        return bool(re.match(pattern, domain))

    def _generate_id(self, data: str) -> str:
        """Generate unique ID"""
        return hashlib.md5(data.encode()).hexdigest()[:16]
