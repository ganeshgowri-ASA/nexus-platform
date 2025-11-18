"""Streamlit UI for advertising module."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from config.database import get_db_context
from .models import Campaign, AdGroup, Ad, Creative
from .analytics import AdAnalytics
from .reporting import AdReporting
from .campaigns import CampaignManager
from .creatives import CreativeManager
from .budgets import BudgetManager


def main():
    """Main Streamlit UI for Advertising."""
    st.set_page_config(page_title="NEXUS Advertising Manager", layout="wide")
    
    st.title("📊 Advertising Manager Dashboard")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigate",
        ["Dashboard", "Campaigns", "Creatives", "Analytics", "Reports", "Budget Tracking"]
    )
    
    with get_db_context() as db:
        if page == "Dashboard":
            show_dashboard(db)
        elif page == "Campaigns":
            show_campaigns(db)
        elif page == "Creatives":
            show_creatives(db)
        elif page == "Analytics":
            show_analytics(db)
        elif page == "Reports":
            show_reports(db)
        elif page == "Budget Tracking":
            show_budget_tracking(db)


def show_dashboard(db: Session):
    """Show main advertising dashboard."""
    st.header("Advertising Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_campaigns = db.query(Campaign).count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == "active").count()
    total_spend = db.query(Campaign).with_entities(
        db.func.sum(Campaign.spend)
    ).scalar() or 0
    total_conversions = db.query(Campaign).with_entities(
        db.func.sum(Campaign.conversions)
    ).scalar() or 0
    
    with col1:
        st.metric("Total Campaigns", total_campaigns)
    with col2:
        st.metric("Active Campaigns", active_campaigns)
    with col3:
        st.metric("Total Spend", f"${total_spend:,.2f}")
    with col4:
        st.metric("Total Conversions", total_conversions)
    
    # Campaign performance table
    st.subheader("Campaign Performance")
    campaigns = db.query(Campaign).order_by(Campaign.spend.desc()).limit(10).all()
    
    if campaigns:
        campaign_data = []
        for campaign in campaigns:
            ctr = (campaign.clicks / campaign.impressions * 100) if campaign.impressions > 0 else 0
            cpc = (campaign.spend / campaign.clicks) if campaign.clicks > 0 else 0
            
            campaign_data.append({
                "Name": campaign.name,
                "Platform": campaign.platform,
                "Status": campaign.status,
                "Impressions": f"{campaign.impressions:,}",
                "Clicks": campaign.clicks,
                "CTR": f"{ctr:.2f}%",
                "CPC": f"${cpc:.2f}",
                "Spend": f"${campaign.spend:,.2f}",
                "Conversions": campaign.conversions,
            })
        
        st.dataframe(pd.DataFrame(campaign_data), use_container_width=True)


def show_campaigns(db: Session):
    """Show campaign management interface."""
    st.header("Campaign Management")
    
    # Create new campaign
    with st.expander("Create New Campaign"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Campaign Name")
            platform = st.selectbox("Platform", ["google_ads", "facebook", "linkedin", "twitter"])
            objective = st.selectbox("Objective", ["traffic", "conversions", "awareness", "engagement"])
        
        with col2:
            daily_budget = st.number_input("Daily Budget ($)", min_value=10.0, value=100.0)
            start_date = st.date_input("Start Date", datetime.utcnow())
            end_date = st.date_input("End Date", datetime.utcnow() + timedelta(days=30))
        
        if st.button("Create Campaign"):
            if name:
                from .ad_types import CampaignCreate, AdPlatform, CampaignStatus
                campaign_data = CampaignCreate(
                    name=name,
                    objective=objective,
                    platform=AdPlatform(platform),
                    daily_budget=daily_budget,
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.max.time()),
                    status=CampaignStatus.DRAFT,
                )
                manager = CampaignManager(db)
                import asyncio
                campaign = asyncio.run(manager.create_campaign(campaign_data))
                st.success(f"Campaign created: {campaign.name}")
    
    # List existing campaigns
    st.subheader("Existing Campaigns")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "draft", "active", "paused", "completed"])
    with col2:
        platform_filter = st.selectbox("Platform", ["All", "google_ads", "facebook", "linkedin"])
    with col3:
        sort_by = st.selectbox("Sort By", ["Spend", "Conversions", "Created Date"])
    
    # Query campaigns
    query = db.query(Campaign)
    if status_filter != "All":
        query = query.filter(Campaign.status == status_filter)
    if platform_filter != "All":
        query = query.filter(Campaign.platform == platform_filter)
    
    campaigns = query.order_by(Campaign.created_at.desc()).limit(50).all()
    
    if campaigns:
        campaign_data = []
        for campaign in campaigns:
            campaign_data.append({
                "ID": campaign.id,
                "Name": campaign.name,
                "Platform": campaign.platform,
                "Status": campaign.status,
                "Daily Budget": f"${campaign.daily_budget:.2f}",
                "Spend": f"${campaign.spend:.2f}",
                "Conversions": campaign.conversions,
                "Start Date": campaign.start_date.strftime("%Y-%m-%d"),
            })
        
        df = pd.DataFrame(campaign_data)
        st.dataframe(df, use_container_width=True)


def show_creatives(db: Session):
    """Show creative management interface."""
    st.header("Creative Library")
    
    creatives = db.query(Creative).all()
    
    if creatives:
        creative_data = []
        for creative in creatives:
            creative_data.append({
                "Name": creative.name,
                "Type": creative.type,
                "Asset URL": creative.asset_url or "-",
                "Created": creative.created_at.strftime("%Y-%m-%d"),
            })
        
        st.dataframe(pd.DataFrame(creative_data), use_container_width=True)
    else:
        st.info("No creatives found. Upload your first creative!")


def show_analytics(db: Session):
    """Show analytics dashboard."""
    st.header("Advertising Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.utcnow() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.utcnow())
    
    # Cross-platform metrics
    st.subheader("Cross-Platform Performance")
    
    analytics = AdAnalytics(db)
    import asyncio
    
    platform_metrics = asyncio.run(analytics.get_cross_platform_metrics())
    
    if platform_metrics:
        st.dataframe(pd.DataFrame(platform_metrics), use_container_width=True)
    
    # Campaign-specific metrics
    st.subheader("Campaign Metrics")
    
    campaigns = db.query(Campaign).all()
    campaign_names = {c.id: c.name for c in campaigns}
    
    selected_campaign = st.selectbox(
        "Select Campaign",
        options=list(campaign_names.keys()),
        format_func=lambda x: campaign_names[x]
    )
    
    if selected_campaign:
        metrics = asyncio.run(analytics.get_campaign_metrics(
            selected_campaign,
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        ))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Impressions", f"{metrics['impressions']:,}")
        with col2:
            st.metric("CTR", f"{metrics['ctr']:.2f}%")
        with col3:
            st.metric("CPC", f"${metrics['cpc']:.2f}")
        with col4:
            st.metric("ROAS", f"{metrics['roas']:.2f}x")


def show_reports(db: Session):
    """Show reporting interface."""
    st.header("Advertising Reports")
    
    report_type = st.selectbox(
        "Report Type",
        ["Performance Report", "ROI Report", "Platform Comparison"]
    )
    
    reporting = AdReporting(db)
    import asyncio
    
    if report_type == "ROI Report":
        roi = asyncio.run(reporting.generate_roi_report())
        
        st.subheader("ROI Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spend", f"${roi['total_spend']:.2f}")
        with col2:
            st.metric("Total Conversions", roi['total_conversions'])
        with col3:
            st.metric("Avg CPA", f"${roi['avg_cpa']:.2f}")


def show_budget_tracking(db: Session):
    """Show budget tracking interface."""
    st.header("Budget Tracking")
    
    from .models import BudgetTracking
    
    trackers = db.query(BudgetTracking).all()
    
    if trackers:
        budget_data = []
        for tracker in trackers:
            campaign = db.query(Campaign).filter(Campaign.id == tracker.campaign_id).first()
            
            budget_data.append({
                "Campaign": campaign.name if campaign else "Unknown",
                "Daily Budget": f"${tracker.daily_budget:.2f}",
                "Total Budget": f"${tracker.total_budget:.2f}" if tracker.total_budget else "Unlimited",
                "Spent Today": f"${tracker.spent_today:.2f}",
                "Spent Total": f"${tracker.spent_total:.2f}",
                "Remaining": f"${tracker.remaining:.2f}",
            })
        
        st.dataframe(pd.DataFrame(budget_data), use_container_width=True)


if __name__ == "__main__":
    main()
