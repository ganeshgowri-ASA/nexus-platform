"""
CRM Streamlit UI - Professional interface with contact list, deal board, and analytics dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List

# Import CRM modules
from .contacts import ContactManager, Contact, ContactStatus, LeadSource
from .companies import CompanyManager, Company, CompanyType, Industry
from .deals import DealManager, Deal, DealStage, DealPriority
from .pipeline import PipelineManager
from .activities import ActivityManager, ActivityType
from .tasks import TaskManager, TaskStatus, TaskPriority
from .email_integration import EmailIntegrationManager
from .analytics import CRMAnalytics, MetricPeriod
from .automation import AutomationEngine
from .ai_insights import AIInsightsEngine


class CRMUI:
    """Streamlit-based CRM UI."""

    def __init__(self):
        """Initialize CRM UI."""
        self._initialize_managers()
        self._setup_page_config()

    def _initialize_managers(self):
        """Initialize all CRM managers."""
        if 'contact_manager' not in st.session_state:
            st.session_state.contact_manager = ContactManager()
        if 'company_manager' not in st.session_state:
            st.session_state.company_manager = CompanyManager()
        if 'deal_manager' not in st.session_state:
            st.session_state.deal_manager = DealManager()
        if 'pipeline_manager' not in st.session_state:
            st.session_state.pipeline_manager = PipelineManager()
            # Create default pipeline
            st.session_state.pipeline_manager.create_default_pipeline()
        if 'activity_manager' not in st.session_state:
            st.session_state.activity_manager = ActivityManager()
        if 'task_manager' not in st.session_state:
            st.session_state.task_manager = TaskManager()
        if 'email_manager' not in st.session_state:
            st.session_state.email_manager = EmailIntegrationManager()
        if 'automation_engine' not in st.session_state:
            st.session_state.automation_engine = AutomationEngine()
        if 'ai_insights' not in st.session_state:
            st.session_state.ai_insights = AIInsightsEngine(
                contact_manager=st.session_state.contact_manager,
                company_manager=st.session_state.company_manager,
                deal_manager=st.session_state.deal_manager,
                activity_manager=st.session_state.activity_manager,
                task_manager=st.session_state.task_manager,
            )
        if 'analytics' not in st.session_state:
            st.session_state.analytics = CRMAnalytics(
                contact_manager=st.session_state.contact_manager,
                company_manager=st.session_state.company_manager,
                deal_manager=st.session_state.deal_manager,
                activity_manager=st.session_state.activity_manager,
                task_manager=st.session_state.task_manager,
                email_manager=st.session_state.email_manager,
            )

    def _setup_page_config(self):
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title="Nexus CRM",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def run(self):
        """Run the CRM UI."""
        # Sidebar navigation
        with st.sidebar:
            st.title("📊 Nexus CRM")
            st.markdown("---")

            page = st.radio(
                "Navigation",
                [
                    "🏠 Dashboard",
                    "👥 Contacts",
                    "🏢 Companies",
                    "💼 Deals",
                    "📋 Pipeline",
                    "✅ Tasks",
                    "📧 Email",
                    "📊 Analytics",
                    "🤖 AI Insights",
                    "⚙️ Automation",
                ],
                key="navigation"
            )

        # Route to appropriate page
        if page == "🏠 Dashboard":
            self.show_dashboard()
        elif page == "👥 Contacts":
            self.show_contacts()
        elif page == "🏢 Companies":
            self.show_companies()
        elif page == "💼 Deals":
            self.show_deals()
        elif page == "📋 Pipeline":
            self.show_pipeline()
        elif page == "✅ Tasks":
            self.show_tasks()
        elif page == "📧 Email":
            self.show_email()
        elif page == "📊 Analytics":
            self.show_analytics()
        elif page == "🤖 AI Insights":
            self.show_ai_insights()
        elif page == "⚙️ Automation":
            self.show_automation()

    # Dashboard

    def show_dashboard(self):
        """Show main dashboard with key metrics."""
        st.title("🏠 Dashboard")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        contact_stats = st.session_state.contact_manager.get_statistics()
        deal_stats = st.session_state.deal_manager.get_statistics()

        with col1:
            st.metric("Total Contacts", contact_stats['total_contacts'])
            st.metric("New This Month", contact_stats.get('new_this_month', 0))

        with col2:
            st.metric("Active Deals", deal_stats['open_deals'])
            st.metric("Total Pipeline", f"${deal_stats['total_pipeline_value']:,.0f}")

        with col3:
            st.metric("Won Deals", deal_stats['won_deals'])
            st.metric("Total Revenue", f"${deal_stats['total_won_value']:,.0f}")

        with col4:
            conversion = st.session_state.deal_manager.get_conversion_rates()
            st.metric("Win Rate", f"{conversion['win_rate']}%")
            st.metric("Avg Deal Size", f"${conversion['average_deal_size']:,.0f}")

        st.markdown("---")

        # Two column layout
        col1, col2 = st.columns(2)

        with col1:
            # Recent activities
            st.subheader("Recent Activities")
            activities = st.session_state.activity_manager.list_activities(limit=5)
            if activities:
                for activity in activities:
                    with st.container():
                        st.write(f"**{activity.activity_type.value.title()}**: {activity.subject}")
                        st.caption(f"{activity.created_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.info("No recent activities")

        with col2:
            # Upcoming tasks
            st.subheader("Upcoming Tasks")
            tasks = st.session_state.task_manager.get_tasks_due_soon(days=7)
            if tasks:
                for task in tasks[:5]:
                    with st.container():
                        priority_emoji = "🔴" if task.priority.value == "urgent" else "🟡" if task.priority.value == "high" else "🟢"
                        st.write(f"{priority_emoji} **{task.title}**")
                        st.caption(f"Due: {task.due_date.strftime('%Y-%m-%d')}" if task.due_date else "No due date")
            else:
                st.info("No upcoming tasks")

        # Charts
        st.markdown("---")
        st.subheader("Pipeline by Stage")

        # Pipeline chart
        if deal_stats['by_stage']:
            stages = list(deal_stats['by_stage'].keys())
            counts = [deal_stats['by_stage'][s]['count'] for s in stages]
            values = [deal_stats['by_stage'][s]['value'] for s in stages]

            fig = go.Figure()
            fig.add_trace(go.Bar(name='Count', x=stages, y=counts))
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Contacts

    def show_contacts(self):
        """Show contacts page."""
        st.title("👥 Contacts")

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("➕ New Contact"):
                st.session_state.show_contact_form = True
        with col2:
            if st.button("📥 Import"):
                st.session_state.show_import = True

        # Filters
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            status_filter = st.selectbox("Status", ["All"] + [s.value for s in ContactStatus])
        with col2:
            search = st.text_input("Search", placeholder="Name, email, or company")
        with col3:
            sort_by = st.selectbox("Sort by", ["Updated (Newest)", "Name", "Lead Score"])

        # Get contacts
        contacts = st.session_state.contact_manager.list_contacts()

        # Apply filters
        if status_filter != "All":
            contacts = [c for c in contacts if c.status.value == status_filter]

        if search:
            search_lower = search.lower()
            contacts = [
                c for c in contacts
                if search_lower in c.first_name.lower()
                or search_lower in c.last_name.lower()
                or search_lower in c.email.lower()
                or (c.company_name and search_lower in c.company_name.lower())
            ]

        # Display contacts
        st.markdown(f"**{len(contacts)} contacts**")

        if contacts:
            for contact in contacts:
                with st.expander(f"{contact.full_name} - {contact.email}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Company:** {contact.company_name or 'N/A'}")
                        st.write(f"**Title:** {contact.title or 'N/A'}")
                        st.write(f"**Phone:** {contact.phone or 'N/A'}")
                    with col2:
                        st.write(f"**Status:** {contact.status.value.title()}")
                        st.write(f"**Lead Score:** {contact.lead_score}")
                        st.write(f"**Tags:** {', '.join(contact.tags) if contact.tags else 'None'}")

                    if st.button("View Details", key=f"contact_{contact.id}"):
                        st.session_state.selected_contact = contact.id
        else:
            st.info("No contacts found")

        # Contact form
        if st.session_state.get('show_contact_form'):
            self.show_contact_form()

    def show_contact_form(self):
        """Show contact creation form."""
        st.markdown("---")
        st.subheader("New Contact")

        with st.form("contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")
            with col2:
                last_name = st.text_input("Last Name*")
                company_name = st.text_input("Company")
                title = st.text_input("Title")

            status = st.selectbox("Status", [s.value for s in ContactStatus])

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Create Contact"):
                    if first_name and last_name and email:
                        contact = Contact(
                            id=st.session_state.contact_manager._generate_id(),
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=phone,
                            company_name=company_name,
                            title=title,
                            status=ContactStatus(status),
                        )
                        st.session_state.contact_manager.create_contact(contact)
                        st.success("Contact created!")
                        st.session_state.show_contact_form = False
                        st.rerun()
                    else:
                        st.error("Please fill required fields")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_contact_form = False
                    st.rerun()

    # Companies

    def show_companies(self):
        """Show companies page."""
        st.title("🏢 Companies")

        # Action button
        if st.button("➕ New Company"):
            st.session_state.show_company_form = True

        # Get companies
        companies = st.session_state.company_manager.list_companies()

        st.markdown(f"**{len(companies)} companies**")

        if companies:
            for company in companies:
                with st.expander(f"{company.name} - {company.company_type.value.title()}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Industry:** {company.industry.value.title() if company.industry else 'N/A'}")
                        st.write(f"**Size:** {company.company_size.value if company.company_size else 'N/A'}")
                        st.write(f"**Revenue:** ${company.total_revenue:,.0f}")
                    with col2:
                        st.write(f"**Website:** {company.website or 'N/A'}")
                        st.write(f"**Phone:** {company.phone or 'N/A'}")
                        st.write(f"**Health Score:** {company.health_score}/100")
        else:
            st.info("No companies found")

    # Deals

    def show_deals(self):
        """Show deals page."""
        st.title("💼 Deals")

        # Action button
        if st.button("➕ New Deal"):
            st.session_state.show_deal_form = True

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            stage_filter = st.selectbox("Stage", ["All"] + [s.value for s in DealStage])
        with col2:
            status_filter = st.selectbox("Status", ["All", "Open", "Closed"])

        # Get deals
        deals = st.session_state.deal_manager.list_deals()

        # Apply filters
        if stage_filter != "All":
            deals = [d for d in deals if d.stage.value == stage_filter]
        if status_filter == "Open":
            deals = [d for d in deals if not d.is_closed]
        elif status_filter == "Closed":
            deals = [d for d in deals if d.is_closed]

        st.markdown(f"**{len(deals)} deals**")

        if deals:
            for deal in deals:
                status_emoji = "✅" if deal.is_won else "❌" if deal.is_closed else "🔄"
                with st.expander(f"{status_emoji} {deal.name} - ${deal.amount:,.0f}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Stage:** {deal.stage.value.replace('_', ' ').title()}")
                        st.write(f"**Company:** {deal.company_name or 'N/A'}")
                    with col2:
                        st.write(f"**Probability:** {deal.probability}%")
                        st.write(f"**Weighted Value:** ${deal.weighted_value:,.0f}")
                    with col3:
                        st.write(f"**Expected Close:** {deal.expected_close_date or 'N/A'}")
                        st.write(f"**Priority:** {deal.priority.value.title()}")
        else:
            st.info("No deals found")

    # Pipeline

    def show_pipeline(self):
        """Show pipeline Kanban board."""
        st.title("📋 Pipeline")

        # Get default pipeline
        pipeline = st.session_state.pipeline_manager.get_default_pipeline()
        if not pipeline:
            st.error("No pipeline configured")
            return

        # Get deals data
        deals_dict = {d.id: d.to_dict() for d in st.session_state.deal_manager.deals.values()}

        # Get Kanban view
        kanban = st.session_state.pipeline_manager.get_kanban_view(pipeline.id, deals_dict)

        # Display stages in columns
        stages = kanban.get('stages', [])
        if stages:
            cols = st.columns(len(stages))

            for i, stage in enumerate(stages):
                with cols[i]:
                    st.subheader(stage['name'])
                    st.caption(f"{stage['deals_count']} deals | ${stage['total_value']:,.0f}")

                    # Display deals in this stage
                    for deal in stage.get('deals', []):
                        with st.container():
                            st.markdown(f"**{deal['name']}**")
                            st.write(f"${deal['amount']:,.0f}")
                            st.caption(f"{deal['probability']}% probability")
                            st.markdown("---")
        else:
            st.info("No pipeline stages configured")

    # Tasks

    def show_tasks(self):
        """Show tasks page."""
        st.title("✅ Tasks")

        # Action button
        if st.button("➕ New Task"):
            st.session_state.show_task_form = True

        # Tabs
        tab1, tab2, tab3 = st.tabs(["My Tasks", "All Tasks", "Overdue"])

        with tab1:
            # Mock user ID
            user_id = "user_1"
            my_tasks = st.session_state.task_manager.get_my_tasks(user_id)

            for category, tasks in my_tasks.items():
                if tasks:
                    st.subheader(category.replace('_', ' ').title())
                    for task in tasks:
                        self._render_task(task)

        with tab2:
            all_tasks = st.session_state.task_manager.list_tasks(limit=50)
            for task in all_tasks:
                self._render_task(task)

        with tab3:
            overdue = st.session_state.task_manager.get_overdue_tasks()
            if overdue:
                for task in overdue:
                    self._render_task(task, highlight_overdue=True)
            else:
                st.success("No overdue tasks!")

    def _render_task(self, task, highlight_overdue=False):
        """Render a task item."""
        priority_colors = {
            "urgent": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }
        priority_emoji = priority_colors.get(task.priority.value, "⚪")

        if highlight_overdue:
            st.error(f"{priority_emoji} **{task.title}** - Overdue!")
        else:
            st.write(f"{priority_emoji} **{task.title}**")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.caption(f"Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'}")
        with col2:
            st.caption(f"Status: {task.status.value.replace('_', ' ').title()}")
        with col3:
            if st.button("✓", key=f"complete_{task.id}"):
                st.session_state.task_manager.complete_task(task.id)
                st.rerun()

        st.markdown("---")

    # Email

    def show_email(self):
        """Show email management page."""
        st.title("📧 Email")

        tab1, tab2, tab3 = st.tabs(["Templates", "Campaigns", "Performance"])

        with tab1:
            st.subheader("Email Templates")
            templates = st.session_state.email_manager.list_templates()

            if templates:
                for template in templates:
                    with st.expander(f"{template.name}"):
                        st.write(f"**Type:** {template.template_type.value.replace('_', ' ').title()}")
                        st.write(f"**Subject:** {template.subject}")
                        st.write(f"**Used:** {template.times_used} times")
                        st.write(f"**Open Rate:** {template.open_rate:.1f}%")
                        st.write(f"**Click Rate:** {template.click_rate:.1f}%")
            else:
                st.info("No email templates found")

        with tab2:
            st.subheader("Campaigns")
            campaigns = list(st.session_state.email_manager.campaigns.values())
            if campaigns:
                for campaign in campaigns:
                    with st.expander(f"{campaign.name} - {campaign.status.value}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Recipients:** {campaign.total_recipients}")
                            st.write(f"**Sent:** {campaign.total_sent}")
                        with col2:
                            st.write(f"**Open Rate:** {campaign.open_rate:.1f}%")
                            st.write(f"**Click Rate:** {campaign.click_rate:.1f}%")
            else:
                st.info("No campaigns found")

        with tab3:
            st.subheader("Email Performance")
            stats = st.session_state.email_manager.get_engagement_stats()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sent", stats['total_sent'])
            with col2:
                st.metric("Open Rate", f"{stats['open_rate']}%")
            with col3:
                st.metric("Click Rate", f"{stats['click_rate']}%")
            with col4:
                st.metric("Reply Rate", f"{stats['reply_rate']}%")

    # Analytics

    def show_analytics(self):
        """Show analytics dashboard."""
        st.title("📊 Analytics")

        # Period selector
        period = st.selectbox("Period", ["Month", "Quarter", "Year", "All Time"])
        period_map = {
            "Month": MetricPeriod.MONTH,
            "Quarter": MetricPeriod.QUARTER,
            "Year": MetricPeriod.YEAR,
            "All Time": MetricPeriod.ALL_TIME,
        }

        # Key metrics
        metrics = st.session_state.analytics.get_key_metrics(period_map[period])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            self._render_metric_card("Total Revenue", metrics['total_revenue'])
        with col2:
            self._render_metric_card("New Deals", metrics['new_deals'])
        with col3:
            self._render_metric_card("Win Rate", metrics['win_rate'])
        with col4:
            self._render_metric_card("Avg Deal Size", metrics['avg_deal_size'])

        st.markdown("---")

        # Charts
        tab1, tab2, tab3 = st.tabs(["Sales Performance", "Pipeline", "Conversion Funnel"])

        with tab1:
            sales_perf = st.session_state.analytics.get_sales_performance()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Revenue", f"${sales_perf['total_revenue']:,.0f}")
                st.metric("Pipeline Value", f"${sales_perf['pipeline_value']:,.0f}")
            with col2:
                st.metric("Win Rate", f"{sales_perf['win_rate']}%")
                st.metric("Avg Sales Cycle", f"{sales_perf['avg_sales_cycle_days']} days")

        with tab2:
            pipeline_analysis = st.session_state.analytics.get_pipeline_analysis()
            st.write(f"**Total Pipeline Value:** ${pipeline_analysis['total_pipeline_value']:,.0f}")

        with tab3:
            funnel = st.session_state.analytics.get_conversion_funnel()
            if funnel:
                stages = [f['stage_name'] for f in funnel]
                counts = [f['count'] for f in funnel]

                fig = go.Figure(go.Funnel(
                    y=stages,
                    x=counts,
                ))
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    def _render_metric_card(self, title: str, metric_data: Dict[str, Any]):
        """Render a metric card with comparison."""
        current = metric_data['current']
        change = metric_data.get('change_percent')
        trend = metric_data.get('trend', 'neutral')

        st.metric(
            title,
            f"{current:,.0f}" if isinstance(current, (int, float)) else str(current),
            delta=f"{change:+.1f}%" if change is not None else None,
            delta_color="normal" if trend == "up" else "inverse" if trend == "down" else "off"
        )

    # AI Insights

    def show_ai_insights(self):
        """Show AI insights page."""
        st.title("🤖 AI Insights")

        tab1, tab2, tab3, tab4 = st.tabs(["Lead Prioritization", "Deal Insights", "Churn Prediction", "Upsell Opportunities"])

        with tab1:
            st.subheader("High-Priority Leads")
            leads = st.session_state.ai_insights.prioritize_leads(limit=10)

            if leads:
                for lead in leads:
                    with st.container():
                        score_color = "🔴" if lead['priority_score'] > 80 else "🟡" if lead['priority_score'] > 60 else "🟢"
                        st.write(f"{score_color} **{lead['contact_name']}** - {lead['company_name'] or 'No company'}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"Priority Score: {lead['priority_score']:.0f}/100")
                        with col2:
                            st.caption(f"Lead Score: {lead['lead_score']}")
                        st.markdown("---")
            else:
                st.info("No leads to prioritize")

        with tab2:
            st.subheader("Deals at Risk")
            deals = st.session_state.deal_manager.get_deals_at_risk()

            if deals:
                for deal in deals:
                    risk = st.session_state.ai_insights.analyze_deal_risk(deal.id)
                    with st.expander(f"{deal.name} - {risk['risk_level'].upper()} Risk"):
                        st.write(f"**Risk Score:** {risk['risk_score']}/100")
                        st.write(f"**Risk Factors:**")
                        for factor in risk['risk_factors']:
                            st.write(f"- {factor}")
                        st.write(f"**Recommendations:**")
                        for rec in risk['recommendations']:
                            st.write(f"- {rec}")
            else:
                st.success("No deals at risk!")

        with tab3:
            st.subheader("Churn Risk Analysis")
            st.info("Analyze customer churn risk for proactive retention")

        with tab4:
            st.subheader("Upsell Opportunities")
            opportunities = st.session_state.ai_insights.identify_upsell_opportunities(limit=10)

            if opportunities:
                for opp in opportunities:
                    with st.container():
                        st.write(f"**{opp['company_name']}**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"Score: {opp['upsell_score']:.0f}/100")
                        with col2:
                            st.caption(f"Current: ${opp['current_revenue']:,.0f}")
                        with col3:
                            st.caption(f"Health: {opp['health_score']}/100")
                        st.markdown("---")
            else:
                st.info("No upsell opportunities identified")

    # Automation

    def show_automation(self):
        """Show automation page."""
        st.title("⚙️ Automation")

        tab1, tab2 = st.tabs(["Workflows", "Lead Scoring"])

        with tab1:
            st.subheader("Workflows")
            workflows = st.session_state.automation_engine.list_workflows()

            if workflows:
                for workflow in workflows:
                    status_emoji = "✅" if workflow.status.value == "active" else "⏸️"
                    with st.expander(f"{status_emoji} {workflow.name}"):
                        st.write(f"**Status:** {workflow.status.value.title()}")
                        st.write(f"**Trigger:** {workflow.trigger_type.value.replace('_', ' ').title()}")
                        st.write(f"**Actions:** {len(workflow.actions)}")
                        st.write(f"**Triggered:** {workflow.times_triggered} times")
            else:
                st.info("No workflows configured")

        with tab2:
            st.subheader("Lead Scoring Rules")
            rules = st.session_state.automation_engine.list_scoring_rules()

            if rules:
                for rule in rules:
                    st.write(f"**{rule.name}** ({rule.score_change:+d} points)")
                    st.caption(f"{rule.field} {rule.operator.value} {rule.value}")
                    st.markdown("---")
            else:
                st.info("No scoring rules configured")


def main():
    """Main entry point for the CRM UI."""
    ui = CRMUI()
    ui.run()


if __name__ == "__main__":
    main()
