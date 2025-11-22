"""
NEXUS Dashboard Builder - Templates Module
Pre-built dashboard templates for common use cases
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class DashboardCategory(Enum):
    """Dashboard template categories"""
    ANALYTICS = "analytics"
    BUSINESS = "business"
    OPERATIONS = "operations"
    MONITORING = "monitoring"
    SALES = "sales"
    MARKETING = "marketing"
    FINANCE = "finance"
    HR = "hr"
    CUSTOM = "custom"


@dataclass
class DashboardTemplate:
    """Dashboard template definition"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: DashboardCategory = DashboardCategory.CUSTOM
    thumbnail: str = ""
    author: str = "NEXUS"
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    is_public: bool = True
    usage_count: int = 0

    # Template structure
    layout: Dict[str, Any] = field(default_factory=dict)
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    filters: List[Dict[str, Any]] = field(default_factory=list)
    theme: str = "light"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'thumbnail': self.thumbnail,
            'author': self.author,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'is_public': self.is_public,
            'usage_count': self.usage_count,
            'layout': self.layout,
            'widgets': self.widgets,
            'filters': self.filters,
            'theme': self.theme
        }


class TemplateLibrary:
    """Manages dashboard templates"""

    def __init__(self):
        self.templates: Dict[str, DashboardTemplate] = {}
        self._load_built_in_templates()

    def _load_built_in_templates(self):
        """Load built-in templates"""

        # Executive Dashboard
        exec_template = DashboardTemplate(
            name="Executive Dashboard",
            description="High-level KPIs and metrics for executives",
            category=DashboardCategory.BUSINESS,
            tags=["executive", "kpi", "metrics", "overview"],
            layout={
                "columns": 12,
                "responsive": True
            },
            widgets=[
                {
                    "type": "kpi",
                    "title": "Revenue",
                    "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                    "config": {"format": "currency"}
                },
                {
                    "type": "kpi",
                    "title": "Profit Margin",
                    "position": {"x": 3, "y": 0, "w": 3, "h": 2},
                    "config": {"format": "percentage"}
                },
                {
                    "type": "kpi",
                    "title": "Customers",
                    "position": {"x": 6, "y": 0, "w": 3, "h": 2},
                    "config": {"format": "number"}
                },
                {
                    "type": "kpi",
                    "title": "Growth Rate",
                    "position": {"x": 9, "y": 0, "w": 3, "h": 2},
                    "config": {"format": "percentage"}
                },
                {
                    "type": "chart",
                    "title": "Revenue Trend",
                    "position": {"x": 0, "y": 2, "w": 6, "h": 4},
                    "config": {"chart_type": "line"}
                },
                {
                    "type": "chart",
                    "title": "Top Products",
                    "position": {"x": 6, "y": 2, "w": 6, "h": 4},
                    "config": {"chart_type": "bar"}
                }
            ]
        )
        self.templates[exec_template.template_id] = exec_template

        # Sales Dashboard
        sales_template = DashboardTemplate(
            name="Sales Dashboard",
            description="Track sales performance and pipeline",
            category=DashboardCategory.SALES,
            tags=["sales", "revenue", "pipeline", "conversion"],
            widgets=[
                {
                    "type": "kpi",
                    "title": "Monthly Sales",
                    "position": {"x": 0, "y": 0, "w": 4, "h": 2}
                },
                {
                    "type": "gauge",
                    "title": "Quota Achievement",
                    "position": {"x": 4, "y": 0, "w": 4, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Win Rate",
                    "position": {"x": 8, "y": 0, "w": 4, "h": 2}
                },
                {
                    "type": "chart",
                    "title": "Sales Funnel",
                    "position": {"x": 0, "y": 2, "w": 6, "h": 4},
                    "config": {"chart_type": "funnel"}
                },
                {
                    "type": "chart",
                    "title": "Sales by Region",
                    "position": {"x": 6, "y": 2, "w": 6, "h": 4},
                    "config": {"chart_type": "treemap"}
                },
                {
                    "type": "table",
                    "title": "Top Deals",
                    "position": {"x": 0, "y": 6, "w": 12, "h": 4}
                }
            ],
            filters=[
                {
                    "name": "date_range",
                    "type": "date",
                    "label": "Date Range"
                },
                {
                    "name": "region",
                    "type": "multiselect",
                    "label": "Region"
                }
            ]
        )
        self.templates[sales_template.template_id] = sales_template

        # Operations Dashboard
        ops_template = DashboardTemplate(
            name="Operations Dashboard",
            description="Monitor operations and system health",
            category=DashboardCategory.OPERATIONS,
            tags=["operations", "monitoring", "health", "performance"],
            theme="dark",
            widgets=[
                {
                    "type": "gauge",
                    "title": "System Health",
                    "position": {"x": 0, "y": 0, "w": 3, "h": 3}
                },
                {
                    "type": "stat",
                    "title": "Uptime",
                    "position": {"x": 3, "y": 0, "w": 3, "h": 3}
                },
                {
                    "type": "chart",
                    "title": "Response Time",
                    "position": {"x": 6, "y": 0, "w": 6, "h": 3},
                    "config": {"chart_type": "line"}
                },
                {
                    "type": "chart",
                    "title": "Error Rate",
                    "position": {"x": 0, "y": 3, "w": 6, "h": 3},
                    "config": {"chart_type": "area"}
                },
                {
                    "type": "chart",
                    "title": "Resource Utilization",
                    "position": {"x": 6, "y": 3, "w": 6, "h": 3},
                    "config": {"chart_type": "bar"}
                },
                {
                    "type": "table",
                    "title": "Active Alerts",
                    "position": {"x": 0, "y": 6, "w": 12, "h": 4}
                }
            ]
        )
        self.templates[ops_template.template_id] = ops_template

        # Marketing Dashboard
        marketing_template = DashboardTemplate(
            name="Marketing Dashboard",
            description="Track marketing campaigns and ROI",
            category=DashboardCategory.MARKETING,
            tags=["marketing", "campaigns", "roi", "engagement"],
            widgets=[
                {
                    "type": "kpi",
                    "title": "Campaign ROI",
                    "position": {"x": 0, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Impressions",
                    "position": {"x": 3, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Conversions",
                    "position": {"x": 6, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "CTR",
                    "position": {"x": 9, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "chart",
                    "title": "Engagement Trend",
                    "position": {"x": 0, "y": 2, "w": 8, "h": 4},
                    "config": {"chart_type": "line"}
                },
                {
                    "type": "chart",
                    "title": "Channel Performance",
                    "position": {"x": 8, "y": 2, "w": 4, "h": 4},
                    "config": {"chart_type": "pie"}
                },
                {
                    "type": "table",
                    "title": "Campaign Summary",
                    "position": {"x": 0, "y": 6, "w": 12, "h": 4}
                }
            ]
        )
        self.templates[marketing_template.template_id] = marketing_template

        # Analytics Dashboard
        analytics_template = DashboardTemplate(
            name="Web Analytics Dashboard",
            description="Website traffic and user behavior analytics",
            category=DashboardCategory.ANALYTICS,
            tags=["analytics", "web", "traffic", "users"],
            widgets=[
                {
                    "type": "kpi",
                    "title": "Total Visits",
                    "position": {"x": 0, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Unique Visitors",
                    "position": {"x": 3, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Bounce Rate",
                    "position": {"x": 6, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Avg. Session Duration",
                    "position": {"x": 9, "y": 0, "w": 3, "h": 2}
                },
                {
                    "type": "chart",
                    "title": "Traffic Over Time",
                    "position": {"x": 0, "y": 2, "w": 12, "h": 4},
                    "config": {"chart_type": "area"}
                },
                {
                    "type": "chart",
                    "title": "Traffic Sources",
                    "position": {"x": 0, "y": 6, "w": 6, "h": 4},
                    "config": {"chart_type": "pie"}
                },
                {
                    "type": "chart",
                    "title": "Top Pages",
                    "position": {"x": 6, "y": 6, "w": 6, "h": 4},
                    "config": {"chart_type": "bar"}
                }
            ]
        )
        self.templates[analytics_template.template_id] = analytics_template

        # Financial Dashboard
        financial_template = DashboardTemplate(
            name="Financial Dashboard",
            description="Financial metrics and performance tracking",
            category=DashboardCategory.FINANCE,
            tags=["finance", "revenue", "expenses", "profitability"],
            widgets=[
                {
                    "type": "kpi",
                    "title": "Total Revenue",
                    "position": {"x": 0, "y": 0, "w": 4, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Operating Expenses",
                    "position": {"x": 4, "y": 0, "w": 4, "h": 2}
                },
                {
                    "type": "kpi",
                    "title": "Net Profit",
                    "position": {"x": 8, "y": 0, "w": 4, "h": 2}
                },
                {
                    "type": "chart",
                    "title": "Revenue vs Expenses",
                    "position": {"x": 0, "y": 2, "w": 6, "h": 4},
                    "config": {"chart_type": "line"}
                },
                {
                    "type": "chart",
                    "title": "Expense Breakdown",
                    "position": {"x": 6, "y": 2, "w": 6, "h": 4},
                    "config": {"chart_type": "treemap"}
                },
                {
                    "type": "chart",
                    "title": "Cash Flow",
                    "position": {"x": 0, "y": 6, "w": 12, "h": 4},
                    "config": {"chart_type": "waterfall"}
                }
            ]
        )
        self.templates[financial_template.template_id] = financial_template

    def add_template(self, template: DashboardTemplate) -> str:
        """Add a template to the library"""
        self.templates[template.template_id] = template
        return template.template_id

    def get_template(self, template_id: str) -> Optional[DashboardTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)

    def list_templates(self, category: Optional[DashboardCategory] = None) -> List[DashboardTemplate]:
        """List templates with optional category filter"""
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    def search_templates(self, query: str) -> List[DashboardTemplate]:
        """Search templates by name or description"""
        query_lower = query.lower()
        results = []

        for template in self.templates.values():
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)

        return results

    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def clone_template(self, template_id: str, new_name: str) -> Optional[str]:
        """Clone an existing template"""
        template = self.get_template(template_id)
        if not template:
            return None

        cloned = DashboardTemplate(
            name=new_name,
            description=template.description,
            category=template.category,
            tags=template.tags.copy(),
            layout=template.layout.copy(),
            widgets=[w.copy() for w in template.widgets],
            filters=[f.copy() for f in template.filters],
            theme=template.theme
        )

        return self.add_template(cloned)

    def increment_usage(self, template_id: str):
        """Increment template usage count"""
        template = self.get_template(template_id)
        if template:
            template.usage_count += 1

    def get_popular_templates(self, limit: int = 10) -> List[DashboardTemplate]:
        """Get most popular templates"""
        templates = sorted(
            self.templates.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )
        return templates[:limit]

    def export_template(self, template_id: str) -> str:
        """Export template as JSON"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return json.dumps(template.to_dict(), indent=2)

    def import_template(self, json_str: str) -> str:
        """Import template from JSON"""
        data = json.loads(json_str)

        template = DashboardTemplate(
            template_id=data.get('template_id', str(uuid.uuid4())),
            name=data['name'],
            description=data.get('description', ''),
            category=DashboardCategory(data.get('category', 'custom')),
            tags=data.get('tags', []),
            layout=data.get('layout', {}),
            widgets=data.get('widgets', []),
            filters=data.get('filters', []),
            theme=data.get('theme', 'light')
        )

        return self.add_template(template)

    def to_dict(self) -> Dict[str, Any]:
        """Convert library to dictionary"""
        return {
            'templates': [t.to_dict() for t in self.templates.values()],
            'count': len(self.templates)
        }
