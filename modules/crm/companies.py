"""
CRM Companies Module - Organization profiles, hierarchies, and relationships.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum


class CompanyType(Enum):
    """Company type classification."""
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    PARTNER = "partner"
    VENDOR = "vendor"
    COMPETITOR = "competitor"
    INACTIVE = "inactive"


class Industry(Enum):
    """Industry classifications."""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    CONSULTING = "consulting"
    MEDIA = "media"
    TELECOMMUNICATIONS = "telecommunications"
    ENERGY = "energy"
    TRANSPORTATION = "transportation"
    HOSPITALITY = "hospitality"
    OTHER = "other"


class CompanySize(Enum):
    """Company size ranges."""
    STARTUP = "1-10"
    SMALL = "11-50"
    MEDIUM = "51-200"
    LARGE = "201-1000"
    ENTERPRISE = "1000+"


@dataclass
class CompanyAddress:
    """Company address information."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CompanyFinancials:
    """Company financial information."""
    annual_revenue: Optional[float] = None
    currency: str = "USD"
    fiscal_year_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Company:
    """Company entity with full organization profile."""
    id: str
    name: str
    company_type: CompanyType = CompanyType.PROSPECT
    industry: Optional[Industry] = None

    # Contact information
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    # Address
    address: Optional[CompanyAddress] = None

    # Company details
    description: Optional[str] = None
    employee_count: Optional[int] = None
    company_size: Optional[CompanySize] = None
    founded_year: Optional[int] = None

    # Financial information
    financials: Optional[CompanyFinancials] = None

    # Hierarchy
    parent_company_id: Optional[str] = None
    subsidiary_ids: List[str] = field(default_factory=list)

    # Social and external IDs
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None

    # CRM metadata
    owner_id: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # Health and engagement
    health_score: int = 0  # 0-100
    relationship_strength: int = 0  # 0-100

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_interaction: Optional[datetime] = None

    # Metrics
    total_revenue: float = 0.0
    open_deals_count: int = 0
    won_deals_count: int = 0
    lost_deals_count: int = 0
    contacts_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'company_type': self.company_type.value,
            'industry': self.industry.value if self.industry else None,
            'website': self.website,
            'phone': self.phone,
            'email': self.email,
            'address': self.address.to_dict() if self.address else None,
            'description': self.description,
            'employee_count': self.employee_count,
            'company_size': self.company_size.value if self.company_size else None,
            'founded_year': self.founded_year,
            'financials': self.financials.to_dict() if self.financials else None,
            'parent_company_id': self.parent_company_id,
            'subsidiary_ids': self.subsidiary_ids,
            'linkedin_url': self.linkedin_url,
            'twitter_handle': self.twitter_handle,
            'owner_id': self.owner_id,
            'tags': list(self.tags),
            'custom_fields': self.custom_fields,
            'health_score': self.health_score,
            'relationship_strength': self.relationship_strength,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None,
            'total_revenue': self.total_revenue,
            'open_deals_count': self.open_deals_count,
            'won_deals_count': self.won_deals_count,
            'lost_deals_count': self.lost_deals_count,
            'contacts_count': self.contacts_count,
        }


class CompanyManager:
    """Manage companies with hierarchies and relationships."""

    def __init__(self):
        """Initialize company manager."""
        self.companies: Dict[str, Company] = {}
        self._name_index: Dict[str, str] = {}  # company_name_lower -> company_id
        self._parent_index: Dict[str, List[str]] = {}  # parent_id -> [subsidiary_ids]
        self._industry_index: Dict[str, Set[str]] = {}  # industry -> {company_ids}
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> {company_ids}

    def create_company(self, company: Company) -> Company:
        """Create a new company."""
        # Check for duplicates
        name_key = company.name.lower()
        if name_key in self._name_index:
            raise ValueError(f"Company with name '{company.name}' already exists")

        self.companies[company.id] = company
        self._name_index[name_key] = company.id

        # Update indexes
        if company.industry:
            if company.industry not in self._industry_index:
                self._industry_index[company.industry] = set()
            self._industry_index[company.industry].add(company.id)

        for tag in company.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(company.id)

        # Handle parent-subsidiary relationship
        if company.parent_company_id:
            if company.parent_company_id not in self._parent_index:
                self._parent_index[company.parent_company_id] = []
            self._parent_index[company.parent_company_id].append(company.id)

        return company

    def get_company(self, company_id: str) -> Optional[Company]:
        """Get a company by ID."""
        return self.companies.get(company_id)

    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get a company by name."""
        company_id = self._name_index.get(name.lower())
        return self.companies.get(company_id) if company_id else None

    def update_company(self, company_id: str, updates: Dict[str, Any]) -> Optional[Company]:
        """Update a company."""
        company = self.companies.get(company_id)
        if not company:
            return None

        # Handle name update
        if 'name' in updates and updates['name'] != company.name:
            name_key = updates['name'].lower()
            if name_key in self._name_index:
                raise ValueError(f"Company with name '{updates['name']}' already exists")
            del self._name_index[company.name.lower()]
            self._name_index[name_key] = company_id

        # Handle industry update
        if 'industry' in updates:
            if company.industry and company.industry in self._industry_index:
                self._industry_index[company.industry].discard(company_id)
            if updates['industry']:
                industry = updates['industry'] if isinstance(updates['industry'], Industry) else Industry(updates['industry'])
                if industry not in self._industry_index:
                    self._industry_index[industry] = set()
                self._industry_index[industry].add(company_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(company, key):
                # Handle enum conversions
                if key == 'company_type' and isinstance(value, str):
                    value = CompanyType(value)
                elif key == 'industry' and isinstance(value, str):
                    value = Industry(value)
                elif key == 'company_size' and isinstance(value, str):
                    value = CompanySize(value)
                setattr(company, key, value)

        company.updated_at = datetime.now()
        return company

    def delete_company(self, company_id: str) -> bool:
        """Delete a company."""
        company = self.companies.get(company_id)
        if not company:
            return False

        # Remove from indexes
        del self._name_index[company.name.lower()]

        if company.industry and company.industry in self._industry_index:
            self._industry_index[company.industry].discard(company_id)

        for tag in company.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(company_id)

        # Handle parent-subsidiary relationships
        if company.parent_company_id and company.parent_company_id in self._parent_index:
            self._parent_index[company.parent_company_id].remove(company_id)

        # Remove subsidiaries references
        if company_id in self._parent_index:
            del self._parent_index[company_id]

        del self.companies[company_id]
        return True

    def list_companies(
        self,
        company_type: Optional[CompanyType] = None,
        industry: Optional[Industry] = None,
        tags: Optional[List[str]] = None,
        owner_id: Optional[str] = None,
        min_employees: Optional[int] = None,
        max_employees: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Company]:
        """List companies with filtering."""
        results = list(self.companies.values())

        # Apply filters
        if company_type:
            results = [c for c in results if c.company_type == company_type]

        if industry:
            results = [c for c in results if c.industry == industry]

        if tags:
            results = [c for c in results if any(tag in c.tags for tag in tags)]

        if owner_id:
            results = [c for c in results if c.owner_id == owner_id]

        if min_employees is not None:
            results = [c for c in results if c.employee_count and c.employee_count >= min_employees]

        if max_employees is not None:
            results = [c for c in results if c.employee_count and c.employee_count <= max_employees]

        # Sort by updated_at descending
        results.sort(key=lambda c: c.updated_at, reverse=True)

        # Apply pagination
        if limit:
            results = results[offset:offset + limit]
        else:
            results = results[offset:]

        return results

    def search_companies(self, query: str) -> List[Company]:
        """Search companies by name or description."""
        query_lower = query.lower()
        results = []

        for company in self.companies.values():
            if (query_lower in company.name.lower() or
                (company.description and query_lower in company.description.lower()) or
                (company.website and query_lower in company.website.lower())):
                results.append(company)

        return results

    def get_subsidiaries(self, parent_id: str) -> List[Company]:
        """Get all subsidiary companies of a parent."""
        subsidiary_ids = self._parent_index.get(parent_id, [])
        return [self.companies[sid] for sid in subsidiary_ids if sid in self.companies]

    def get_parent_company(self, company_id: str) -> Optional[Company]:
        """Get the parent company of a subsidiary."""
        company = self.companies.get(company_id)
        if not company or not company.parent_company_id:
            return None
        return self.companies.get(company.parent_company_id)

    def get_company_hierarchy(self, company_id: str) -> Dict[str, Any]:
        """Get the full hierarchy for a company (parent and all subsidiaries)."""
        company = self.companies.get(company_id)
        if not company:
            return {}

        hierarchy = {
            'company': company.to_dict(),
            'parent': None,
            'subsidiaries': []
        }

        # Get parent
        if company.parent_company_id:
            parent = self.get_parent_company(company_id)
            if parent:
                hierarchy['parent'] = parent.to_dict()

        # Get subsidiaries
        subsidiaries = self.get_subsidiaries(company_id)
        hierarchy['subsidiaries'] = [s.to_dict() for s in subsidiaries]

        return hierarchy

    def set_parent_company(self, company_id: str, parent_id: Optional[str]) -> Optional[Company]:
        """Set or update the parent company for a subsidiary."""
        company = self.companies.get(company_id)
        if not company:
            return None

        # Validate parent exists
        if parent_id and parent_id not in self.companies:
            raise ValueError(f"Parent company {parent_id} does not exist")

        # Prevent circular references
        if parent_id == company_id:
            raise ValueError("Company cannot be its own parent")

        # Remove from old parent
        if company.parent_company_id and company.parent_company_id in self._parent_index:
            self._parent_index[company.parent_company_id].remove(company_id)

        # Add to new parent
        if parent_id:
            if parent_id not in self._parent_index:
                self._parent_index[parent_id] = []
            self._parent_index[parent_id].append(company_id)

            # Update parent's subsidiary list
            parent = self.companies[parent_id]
            if company_id not in parent.subsidiary_ids:
                parent.subsidiary_ids.append(company_id)

        company.parent_company_id = parent_id
        company.updated_at = datetime.now()
        return company

    def add_tags(self, company_id: str, tags: List[str]) -> Optional[Company]:
        """Add tags to a company."""
        company = self.companies.get(company_id)
        if not company:
            return None

        for tag in tags:
            company.tags.add(tag)
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(company_id)

        company.updated_at = datetime.now()
        return company

    def remove_tags(self, company_id: str, tags: List[str]) -> Optional[Company]:
        """Remove tags from a company."""
        company = self.companies.get(company_id)
        if not company:
            return None

        for tag in tags:
            company.tags.discard(tag)
            if tag in self._tag_index:
                self._tag_index[tag].discard(company_id)

        company.updated_at = datetime.now()
        return company

    def get_companies_by_tag(self, tag: str) -> List[Company]:
        """Get all companies with a specific tag."""
        company_ids = self._tag_index.get(tag, set())
        return [self.companies[cid] for cid in company_ids if cid in self.companies]

    def get_companies_by_industry(self, industry: Industry) -> List[Company]:
        """Get all companies in a specific industry."""
        company_ids = self._industry_index.get(industry, set())
        return [self.companies[cid] for cid in company_ids if cid in self.companies]

    def update_metrics(
        self,
        company_id: str,
        total_revenue: Optional[float] = None,
        open_deals: Optional[int] = None,
        won_deals: Optional[int] = None,
        lost_deals: Optional[int] = None,
        contacts: Optional[int] = None
    ) -> Optional[Company]:
        """Update company metrics."""
        company = self.companies.get(company_id)
        if not company:
            return None

        if total_revenue is not None:
            company.total_revenue = total_revenue
        if open_deals is not None:
            company.open_deals_count = open_deals
        if won_deals is not None:
            company.won_deals_count = won_deals
        if lost_deals is not None:
            company.lost_deals_count = lost_deals
        if contacts is not None:
            company.contacts_count = contacts

        company.updated_at = datetime.now()
        return company

    def calculate_health_score(self, company_id: str) -> int:
        """Calculate company health score based on various factors."""
        company = self.companies.get(company_id)
        if not company:
            return 0

        score = 0

        # Recent interaction (20 points)
        if company.last_interaction:
            days_since = (datetime.now() - company.last_interaction).days
            if days_since < 7:
                score += 20
            elif days_since < 30:
                score += 15
            elif days_since < 90:
                score += 10

        # Open deals (20 points)
        if company.open_deals_count > 0:
            score += min(20, company.open_deals_count * 5)

        # Win rate (30 points)
        total_closed = company.won_deals_count + company.lost_deals_count
        if total_closed > 0:
            win_rate = company.won_deals_count / total_closed
            score += int(win_rate * 30)

        # Revenue (20 points)
        if company.total_revenue > 100000:
            score += 20
        elif company.total_revenue > 50000:
            score += 15
        elif company.total_revenue > 10000:
            score += 10

        # Contacts (10 points)
        if company.contacts_count > 5:
            score += 10
        elif company.contacts_count > 2:
            score += 7
        elif company.contacts_count > 0:
            score += 5

        company.health_score = min(100, score)
        return company.health_score

    def get_statistics(self) -> Dict[str, Any]:
        """Get company statistics."""
        total = len(self.companies)
        by_type = {}
        by_industry = {}
        by_size = {}

        total_revenue = 0.0
        total_employees = 0

        for company in self.companies.values():
            # Count by type
            type_key = company.company_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by industry
            if company.industry:
                industry_key = company.industry.value
                by_industry[industry_key] = by_industry.get(industry_key, 0) + 1

            # Count by size
            if company.company_size:
                size_key = company.company_size.value
                by_size[size_key] = by_size.get(size_key, 0) + 1

            # Sum revenue and employees
            total_revenue += company.total_revenue
            if company.employee_count:
                total_employees += company.employee_count

        return {
            'total_companies': total,
            'by_type': by_type,
            'by_industry': by_industry,
            'by_size': by_size,
            'total_revenue': total_revenue,
            'total_employees': total_employees,
            'total_tags': len(self._tag_index),
            'companies_with_parent': sum(1 for c in self.companies.values() if c.parent_company_id),
        }

    def _generate_id(self) -> str:
        """Generate a unique company ID."""
        import uuid
        return f"company_{uuid.uuid4().hex[:12]}"
