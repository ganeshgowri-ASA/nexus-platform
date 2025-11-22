"""
NEXUS Reports Builder - Templates Module
Pre-built report templates for common use cases
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class TemplateCategory(Enum):
    """Categories of report templates"""
    FINANCIAL = "financial"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    HR = "hr"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class TemplateType(Enum):
    """Types of templates"""
    STANDARD = "standard"
    DASHBOARD = "dashboard"
    DETAILED = "detailed"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    TREND = "trend"


@dataclass
class ReportTemplate:
    """Report template definition"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    template_type: TemplateType = TemplateType.STANDARD
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
    data_sources: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    filters: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'template_type': self.template_type.value,
            'thumbnail': self.thumbnail,
            'author': self.author,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'is_public': self.is_public,
            'usage_count': self.usage_count,
            'layout': self.layout,
            'data_sources': self.data_sources,
            'charts': self.charts,
            'tables': self.tables,
            'filters': self.filters,
            'parameters': self.parameters
        }


class TemplateLibrary:
    """Manages report templates"""

    def __init__(self):
        self.templates: Dict[str, ReportTemplate] = {}
        self._load_built_in_templates()

    def _load_built_in_templates(self):
        """Load built-in templates"""
        # Sales Report Template
        sales_template = ReportTemplate(
            name="Monthly Sales Report",
            description="Comprehensive monthly sales analysis with trends and comparisons",
            category=TemplateCategory.SALES,
            template_type=TemplateType.STANDARD,
            tags=["sales", "revenue", "monthly", "trends"],
            layout={
                "orientation": "portrait",
                "sections": ["summary", "charts", "details"]
            },
            charts=[
                {
                    "type": "line",
                    "title": "Sales Trend",
                    "x_axis": "date",
                    "y_axis": "revenue"
                },
                {
                    "type": "bar",
                    "title": "Sales by Product",
                    "x_axis": "product",
                    "y_axis": "revenue"
                },
                {
                    "type": "pie",
                    "title": "Revenue Distribution",
                    "names": "category",
                    "values": "revenue"
                }
            ],
            tables=[
                {
                    "title": "Top Performing Products",
                    "columns": ["product", "revenue", "units_sold", "growth"]
                }
            ],
            parameters=[
                {
                    "name": "month",
                    "type": "date",
                    "label": "Report Month",
                    "required": True
                },
                {
                    "name": "region",
                    "type": "list",
                    "label": "Region",
                    "options": ["North", "South", "East", "West", "All"]
                }
            ]
        )
        self.templates[sales_template.template_id] = sales_template

        # Financial Report Template
        financial_template = ReportTemplate(
            name="Financial Statement",
            description="Standard financial statement with P&L, balance sheet, and cash flow",
            category=TemplateCategory.FINANCIAL,
            template_type=TemplateType.DETAILED,
            tags=["financial", "p&l", "balance sheet", "cash flow"],
            layout={
                "orientation": "portrait",
                "sections": ["summary", "income_statement", "balance_sheet", "cash_flow"]
            },
            charts=[
                {
                    "type": "waterfall",
                    "title": "Revenue Breakdown",
                    "x_axis": "category",
                    "y_axis": "amount"
                },
                {
                    "type": "bar",
                    "title": "Expense Analysis",
                    "x_axis": "expense_type",
                    "y_axis": "amount"
                }
            ],
            tables=[
                {
                    "title": "Income Statement",
                    "columns": ["account", "current_period", "previous_period", "variance"]
                },
                {
                    "title": "Balance Sheet",
                    "columns": ["account", "assets", "liabilities", "equity"]
                }
            ],
            parameters=[
                {
                    "name": "period",
                    "type": "date",
                    "label": "Reporting Period",
                    "required": True
                },
                {
                    "name": "comparison",
                    "type": "boolean",
                    "label": "Include Period Comparison",
                    "default": True
                }
            ]
        )
        self.templates[financial_template.template_id] = financial_template

        # Marketing Campaign Report
        marketing_template = ReportTemplate(
            name="Marketing Campaign Report",
            description="Campaign performance analysis with ROI and engagement metrics",
            category=TemplateCategory.MARKETING,
            template_type=TemplateType.DASHBOARD,
            tags=["marketing", "campaign", "roi", "engagement"],
            layout={
                "orientation": "landscape",
                "sections": ["kpis", "performance", "channels", "audience"]
            },
            charts=[
                {
                    "type": "gauge",
                    "title": "ROI",
                    "value": "roi_percentage"
                },
                {
                    "type": "funnel",
                    "title": "Conversion Funnel",
                    "x_axis": "stage",
                    "y_axis": "count"
                },
                {
                    "type": "line",
                    "title": "Engagement Over Time",
                    "x_axis": "date",
                    "y_axis": "engagement"
                },
                {
                    "type": "treemap",
                    "title": "Spend by Channel",
                    "path": ["channel", "campaign"],
                    "values": "spend"
                }
            ],
            tables=[
                {
                    "title": "Campaign Summary",
                    "columns": ["campaign", "impressions", "clicks", "conversions", "cost", "roi"]
                }
            ],
            parameters=[
                {
                    "name": "campaign_id",
                    "type": "string",
                    "label": "Campaign ID",
                    "required": True
                },
                {
                    "name": "date_range",
                    "type": "date",
                    "label": "Date Range",
                    "required": True
                }
            ]
        )
        self.templates[marketing_template.template_id] = marketing_template

        # Operations Dashboard
        ops_template = ReportTemplate(
            name="Operations Dashboard",
            description="Real-time operations monitoring with KPIs and alerts",
            category=TemplateCategory.OPERATIONS,
            template_type=TemplateType.DASHBOARD,
            tags=["operations", "monitoring", "kpi", "realtime"],
            layout={
                "orientation": "landscape",
                "sections": ["kpis", "status", "trends", "alerts"]
            },
            charts=[
                {
                    "type": "gauge",
                    "title": "System Health",
                    "value": "health_score"
                },
                {
                    "type": "line",
                    "title": "Throughput",
                    "x_axis": "timestamp",
                    "y_axis": "throughput"
                },
                {
                    "type": "heatmap",
                    "title": "Activity Heatmap",
                    "x_axis": "hour",
                    "y_axis": "day"
                }
            ],
            tables=[
                {
                    "title": "Active Alerts",
                    "columns": ["severity", "message", "timestamp", "status"]
                },
                {
                    "title": "Resource Utilization",
                    "columns": ["resource", "current", "average", "max"]
                }
            ]
        )
        self.templates[ops_template.template_id] = ops_template

        # HR Analytics Report
        hr_template = ReportTemplate(
            name="HR Analytics Report",
            description="Workforce analytics with headcount, turnover, and performance metrics",
            category=TemplateCategory.HR,
            template_type=TemplateType.STANDARD,
            tags=["hr", "workforce", "analytics", "turnover"],
            layout={
                "orientation": "portrait",
                "sections": ["summary", "demographics", "performance", "retention"]
            },
            charts=[
                {
                    "type": "bar",
                    "title": "Headcount by Department",
                    "x_axis": "department",
                    "y_axis": "headcount"
                },
                {
                    "type": "line",
                    "title": "Turnover Trend",
                    "x_axis": "month",
                    "y_axis": "turnover_rate"
                },
                {
                    "type": "sunburst",
                    "title": "Organization Structure",
                    "path": ["division", "department", "team"],
                    "values": "headcount"
                }
            ],
            tables=[
                {
                    "title": "Department Summary",
                    "columns": ["department", "headcount", "new_hires", "terminations", "turnover_rate"]
                }
            ],
            parameters=[
                {
                    "name": "quarter",
                    "type": "string",
                    "label": "Quarter",
                    "required": True
                }
            ]
        )
        self.templates[hr_template.template_id] = hr_template

    def add_template(self, template: ReportTemplate) -> str:
        """Add a template to the library"""
        self.templates[template.template_id] = template
        return template.template_id

    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)

    def list_templates(self, category: Optional[TemplateCategory] = None,
                      template_type: Optional[TemplateType] = None,
                      tags: Optional[List[str]] = None) -> List[ReportTemplate]:
        """List templates with optional filters"""
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if template_type:
            templates = [t for t in templates if t.template_type == template_type]

        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]

        return templates

    def search_templates(self, query: str) -> List[ReportTemplate]:
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

        cloned = ReportTemplate(
            name=new_name,
            description=template.description,
            category=template.category,
            template_type=template.template_type,
            tags=template.tags.copy(),
            layout=template.layout.copy(),
            data_sources=template.data_sources.copy(),
            charts=template.charts.copy(),
            tables=template.tables.copy(),
            filters=template.filters.copy(),
            parameters=template.parameters.copy()
        )

        return self.add_template(cloned)

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update a template"""
        template = self.get_template(template_id)
        if not template:
            return False

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now()
        return True

    def increment_usage(self, template_id: str):
        """Increment template usage count"""
        template = self.get_template(template_id)
        if template:
            template.usage_count += 1

    def get_popular_templates(self, limit: int = 10) -> List[ReportTemplate]:
        """Get most popular templates by usage"""
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

        template = ReportTemplate(
            template_id=data.get('template_id', str(uuid.uuid4())),
            name=data['name'],
            description=data.get('description', ''),
            category=TemplateCategory(data.get('category', 'custom')),
            template_type=TemplateType(data.get('template_type', 'standard')),
            tags=data.get('tags', []),
            layout=data.get('layout', {}),
            data_sources=data.get('data_sources', []),
            charts=data.get('charts', []),
            tables=data.get('tables', []),
            filters=data.get('filters', []),
            parameters=data.get('parameters', [])
        )

        return self.add_template(template)

    def to_dict(self) -> Dict[str, Any]:
        """Convert library to dictionary"""
        return {
            'templates': [t.to_dict() for t in self.templates.values()],
            'count': len(self.templates)
        }
