"""
Campaign Manager Page for NEXUS Platform.

This page provides comprehensive campaign management functionality.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, Any

from frontend.utils import APIClient, require_auth
from frontend.config import config

# Require authentication
require_auth()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - Campaign Manager",
    page_icon=config.APP_ICON,
    layout=config.LAYOUT
)

# Page title
st.title("📊 Campaign Manager")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📋 Campaigns", "➕ Create Campaign", "📈 Analytics"])

with tab1:
    st.subheader("Your Campaigns")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "draft", "planned", "active", "paused", "completed", "cancelled"]
        )

    with col2:
        search_term = st.text_input("Search campaigns")

    with col3:
        refresh_btn = st.button("🔄 Refresh", use_container_width=True)

    try:
        # Fetch campaigns
        campaigns_data = APIClient.list_campaigns(
            status=status_filter if status_filter != "All" else None
        )
        campaigns = campaigns_data.get("campaigns", [])

        if campaigns:
            # Display campaigns
            for campaign in campaigns:
                with st.expander(
                    f"📊 {campaign['name']} - {campaign['status'].upper()}",
                    expanded=False
                ):
                    # Campaign details
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Type:** {campaign['campaign_type']}")
                        st.write(f"**Status:** {campaign['status']}")
                        st.write(f"**Start:** {campaign.get('start_date', 'Not set')}")
                        st.write(f"**End:** {campaign.get('end_date', 'Not set')}")

                    with col2:
                        st.write(f"**Total Budget:** ${campaign['total_budget']:,.2f}")
                        st.write(f"**Spent:** ${campaign['spent_budget']:,.2f}")
                        st.write(f"**Remaining:** ${campaign['remaining_budget']:,.2f}")
                        st.progress(campaign['budget_utilization'] / 100)

                    with col3:
                        st.write(f"**ROI:** {campaign.get('roi', 0):.1f}%")
                        st.write(f"**Created:** {campaign['created_at'][:10]}")

                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✏️ Edit", key=f"edit_{campaign['id']}"):
                                st.session_state.editing_campaign = campaign['id']
                                st.rerun()

                        with btn_col2:
                            if st.button("📈 Analytics", key=f"analytics_{campaign['id']}"):
                                st.session_state.selected_campaign = campaign['id']
                                st.switch_page("pages/02_campaign_analytics.py")

                    # Status update
                    if campaign['status'] in ['draft', 'planned']:
                        if st.button(f"▶️ Start Campaign", key=f"start_{campaign['id']}"):
                            try:
                                APIClient.update_campaign_status(campaign['id'], 'active')
                                st.success("Campaign started!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

        else:
            st.info("No campaigns found. Create your first campaign!")

    except Exception as e:
        st.error(f"Error loading campaigns: {str(e)}")

with tab2:
    st.subheader("Create New Campaign")

    with st.form("create_campaign_form"):
        # Basic Information
        st.write("**Basic Information**")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Campaign Name *")
            campaign_type = st.selectbox(
                "Campaign Type *",
                [
                    "product_launch",
                    "brand_awareness",
                    "lead_generation",
                    "sales",
                    "event",
                    "content",
                    "social",
                    "email",
                    "custom"
                ]
            )

        with col2:
            total_budget = st.number_input(
                "Total Budget ($) *",
                min_value=0.0,
                value=10000.0,
                step=100.0
            )

        description = st.text_area("Description")

        # Timeline
        st.write("**Timeline**")
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.today()
            )

        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today() + timedelta(days=30)
            )

        # Goals
        st.write("**Campaign Goals**")
        col1, col2 = st.columns(2)

        with col1:
            target_reach = st.number_input("Target Reach", min_value=0, value=100000)
            target_conversions = st.number_input("Target Conversions", min_value=0, value=1000)

        with col2:
            target_roi = st.number_input("Target ROI (%)", min_value=0.0, value=150.0)

        # Submit
        submit = st.form_submit_button("Create Campaign", use_container_width=True)

        if submit:
            if not name:
                st.error("Campaign name is required")
            else:
                try:
                    campaign_data = {
                        "name": name,
                        "description": description,
                        "campaign_type": campaign_type,
                        "total_budget": total_budget,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "goals": {
                            "reach": target_reach,
                            "conversions": target_conversions,
                            "roi": target_roi
                        }
                    }

                    with st.spinner("Creating campaign..."):
                        new_campaign = APIClient.create_campaign(campaign_data)

                    st.success(f"Campaign '{name}' created successfully!")
                    st.balloons()

                except Exception as e:
                    st.error(f"Error creating campaign: {str(e)}")

with tab3:
    st.subheader("Campaign Analytics Overview")

    try:
        campaigns_data = APIClient.list_campaigns()
        campaigns = campaigns_data.get("campaigns", [])

        if campaigns:
            # Create DataFrame for visualization
            df = pd.DataFrame(campaigns)

            # Budget Overview
            st.write("**Budget Overview**")
            fig_budget = px.bar(
                df,
                x='name',
                y=['total_budget', 'spent_budget'],
                title='Budget vs Spent by Campaign',
                barmode='group'
            )
            st.plotly_chart(fig_budget, use_container_width=True)

            # Campaign Status Distribution
            st.write("**Campaign Status Distribution**")
            status_counts = df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title='Campaigns by Status'
            )
            st.plotly_chart(fig_status, use_container_width=True)

            # Budget Utilization
            st.write("**Budget Utilization**")
            fig_util = px.bar(
                df,
                x='name',
                y='budget_utilization',
                title='Budget Utilization (%)',
                color='budget_utilization',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_util, use_container_width=True)

        else:
            st.info("No campaign data available")

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
