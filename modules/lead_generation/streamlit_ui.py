"""Streamlit UI for lead generation module."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from config.database import get_db_context
from .models import Lead as LeadModel, Form, LandingPage, Popup
from .analytics import LeadAnalytics
from .reports import LeadReports
from .forms import FormBuilder
from .landing_pages import LandingPageManager
from .popups import PopupManager
from .scoring import LeadScoring
from .qualification import LeadQualification


def main():
    """Main Streamlit UI for Lead Generation."""
    st.set_page_config(page_title="NEXUS Lead Generation", layout="wide")
    
    st.title("🎯 Lead Generation Dashboard")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigate",
        ["Dashboard", "Leads", "Forms", "Landing Pages", "Popups", "Analytics", "Reports"]
    )
    
    with get_db_context() as db:
        if page == "Dashboard":
            show_dashboard(db)
        elif page == "Leads":
            show_leads(db)
        elif page == "Forms":
            show_forms(db)
        elif page == "Landing Pages":
            show_landing_pages(db)
        elif page == "Popups":
            show_popups(db)
        elif page == "Analytics":
            show_analytics(db)
        elif page == "Reports":
            show_reports(db)


def show_dashboard(db: Session):
    """Show main dashboard with key metrics."""
    st.header("Lead Generation Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_leads = db.query(LeadModel).count()
    qualified_leads = db.query(LeadModel).filter(LeadModel.status == "qualified").count()
    converted_leads = db.query(LeadModel).filter(LeadModel.status == "converted").count()
    avg_score = db.query(LeadModel).with_entities(
        db.func.avg(LeadModel.score)
    ).scalar() or 0
    
    with col1:
        st.metric("Total Leads", total_leads)
    with col2:
        st.metric("Qualified Leads", qualified_leads)
    with col3:
        st.metric("Converted Leads", converted_leads)
    with col4:
        st.metric("Avg Score", f"{avg_score:.1f}")
    
    # Recent leads
    st.subheader("Recent Leads")
    recent_leads = db.query(LeadModel).order_by(LeadModel.created_at.desc()).limit(10).all()
    
    if recent_leads:
        leads_data = []
        for lead in recent_leads:
            leads_data.append({
                "Email": lead.email,
                "Name": f"{lead.first_name or ''} {lead.last_name or ''}",
                "Company": lead.company or "-",
                "Score": lead.score,
                "Status": lead.status,
                "Created": lead.created_at.strftime("%Y-%m-%d %H:%M"),
            })
        st.dataframe(pd.DataFrame(leads_data), use_container_width=True)


def show_leads(db: Session):
    """Show and manage leads."""
    st.header("Lead Management")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "new", "contacted", "qualified", "converted"])
    with col2:
        score_filter = st.slider("Min Score", 0, 100, 0)
    with col3:
        search = st.text_input("Search (email/company)")
    
    # Query leads
    query = db.query(LeadModel)
    if status_filter != "All":
        query = query.filter(LeadModel.status == status_filter)
    if score_filter > 0:
        query = query.filter(LeadModel.score >= score_filter)
    if search:
        query = query.filter(
            (LeadModel.email.contains(search)) | (LeadModel.company.contains(search))
        )
    
    leads = query.order_by(LeadModel.created_at.desc()).limit(50).all()
    
    if leads:
        leads_data = []
        for lead in leads:
            leads_data.append({
                "ID": lead.id,
                "Email": lead.email,
                "Name": f"{lead.first_name or ''} {lead.last_name or ''}",
                "Company": lead.company or "-",
                "Score": lead.score,
                "Status": lead.status,
                "Created": lead.created_at.strftime("%Y-%m-%d"),
            })
        
        df = pd.DataFrame(leads_data)
        st.dataframe(df, use_container_width=True)
        
        # Lead actions
        selected_id = st.selectbox("Select lead for actions", df["ID"].tolist())
        if selected_id:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Calculate Score"):
                    scorer = LeadScoring(db)
                    import asyncio
                    score = asyncio.run(scorer.calculate_score(selected_id))
                    st.success(f"Score calculated: {score}")
            with col2:
                if st.button("Qualify Lead"):
                    qualifier = LeadQualification(db)
                    import asyncio
                    result = asyncio.run(qualifier.qualify_lead(selected_id))
                    st.success(f"Qualification: {result['qualified']}")


def show_forms(db: Session):
    """Show and manage forms."""
    st.header("Form Builder")
    
    # Create new form
    with st.expander("Create New Form"):
        form_name = st.text_input("Form Name")
        form_title = st.text_input("Form Title")
        
        if st.button("Create Form"):
            if form_name and form_title:
                from .lead_types import FormCreate, FormField
                form_data = FormCreate(
                    name=form_name,
                    title=form_title,
                    fields=[
                        FormField(
                            name="email",
                            type="email",
                            label="Email Address",
                            required=True
                        ),
                        FormField(
                            name="first_name",
                            type="text",
                            label="First Name",
                            required=True
                        ),
                    ]
                )
                builder = FormBuilder(db)
                import asyncio
                form = asyncio.run(builder.create_form(form_data))
                st.success(f"Form created: {form.name}")
    
    # List existing forms
    st.subheader("Existing Forms")
    forms = db.query(Form).all()
    
    if forms:
        forms_data = []
        for form in forms:
            forms_data.append({
                "Name": form.name,
                "Title": form.title,
                "Submissions": form.submissions_count,
                "Conversion Rate": f"{form.conversion_rate:.2f}%",
                "Active": "✓" if form.is_active else "✗",
            })
        st.dataframe(pd.DataFrame(forms_data), use_container_width=True)


def show_landing_pages(db: Session):
    """Show and manage landing pages."""
    st.header("Landing Pages")
    
    pages = db.query(LandingPage).all()
    
    if pages:
        pages_data = []
        for page in pages:
            pages_data.append({
                "Name": page.name,
                "Slug": page.slug,
                "Views": page.views,
                "Submissions": page.submissions,
                "Conversion Rate": f"{page.conversion_rate:.2f}%",
                "Active": "✓" if page.is_active else "✗",
            })
        st.dataframe(pd.DataFrame(pages_data), use_container_width=True)


def show_popups(db: Session):
    """Show and manage popups."""
    st.header("Popups")
    
    popups = db.query(Popup).all()
    
    if popups:
        popups_data = []
        for popup in popups:
            popups_data.append({
                "Name": popup.name,
                "Trigger": popup.trigger_type,
                "Views": popup.views,
                "Submissions": popup.submissions,
                "Conversion Rate": f"{popup.conversion_rate:.2f}%",
                "Active": "✓" if popup.is_active else "✗",
            })
        st.dataframe(pd.DataFrame(popups_data), use_container_width=True)


def show_analytics(db: Session):
    """Show analytics dashboard."""
    st.header("Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.utcnow() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.utcnow())
    
    analytics = LeadAnalytics(db)
    import asyncio
    
    # Conversion metrics
    metrics = asyncio.run(analytics.get_conversion_metrics(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    ))
    
    st.subheader("Conversion Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Leads", metrics["total_leads"])
    with col2:
        st.metric("Converted", metrics["converted_leads"])
    with col3:
        st.metric("Conversion Rate", f"{metrics['conversion_rate']:.2f}%")
    
    # Source performance
    st.subheader("Source Performance")
    sources = asyncio.run(analytics.get_source_performance(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    ))
    
    if sources:
        st.dataframe(pd.DataFrame(sources), use_container_width=True)


def show_reports(db: Session):
    """Show reports."""
    st.header("Reports")
    
    report_type = st.selectbox("Report Type", ["Funnel Report", "Source Report", "Quality Report"])
    
    reports = LeadReports(db)
    import asyncio
    
    if report_type == "Funnel Report":
        funnel = asyncio.run(reports.generate_funnel_report())
        
        st.subheader("Lead Funnel")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", funnel["total"])
        with col2:
            st.metric("Contacted", funnel["contacted"], f"{funnel['contact_rate']:.1f}%")
        with col3:
            st.metric("Qualified", funnel["qualified"], f"{funnel['qualification_rate']:.1f}%")
        with col4:
            st.metric("Converted", funnel["converted"], f"{funnel['conversion_rate']:.1f}%")


if __name__ == "__main__":
    main()
