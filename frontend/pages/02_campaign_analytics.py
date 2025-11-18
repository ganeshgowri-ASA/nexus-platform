"""
Campaign Analytics Page with Gantt Charts and Performance Dashboards.

This page provides detailed analytics for individual campaigns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from frontend.utils import APIClient, require_auth
from frontend.config import config

# Require authentication
require_auth()

st.set_page_config(
    page_title=f"{config.APP_TITLE} - Campaign Analytics",
    page_icon="📈",
    layout=config.LAYOUT
)

st.title("📈 Campaign Analytics")

# Campaign selection
try:
    campaigns_data = APIClient.list_campaigns()
    campaigns = campaigns_data.get("campaigns", [])

    if not campaigns:
        st.warning("No campaigns available")
        st.stop()

    # Use session state campaign if set, otherwise select first
    default_idx = 0
    if "selected_campaign" in st.session_state:
        for idx, camp in enumerate(campaigns):
            if camp['id'] == st.session_state.selected_campaign:
                default_idx = idx
                break

    selected_campaign = st.selectbox(
        "Select Campaign",
        campaigns,
        format_func=lambda x: f"{x['name']} ({x['status']})",
        index=default_idx
    )

    campaign_id = selected_campaign['id']

    # Fetch detailed analytics
    analytics = APIClient.get_campaign_analytics(campaign_id)
    milestones = APIClient.list_milestones(campaign_id)
    channels = APIClient.list_channels(campaign_id)

    # Display campaign header
    st.header(f"📊 {selected_campaign['name']}")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Impressions", f"{analytics['total_impressions']:,}")

    with col2:
        st.metric("Total Clicks", f"{analytics['total_clicks']:,}")

    with col3:
        st.metric("Conversions", f"{analytics['total_conversions']:,}")

    with col4:
        st.metric("ROI", f"{analytics['overall_roi']:.1f}%")

    with col5:
        st.metric("CTR", f"{analytics['overall_ctr']:.2f}%")

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Performance Dashboard",
        "📅 Timeline & Milestones",
        "📡 Channel Performance",
        "🤖 AI Insights"
    ])

    with tab1:
        st.subheader("Performance Dashboard")

        # Performance over time
        if analytics.get('timeline_data'):
            st.write("**Performance Trend**")

            timeline_df = pd.DataFrame(analytics['timeline_data'])
            timeline_df['date'] = pd.to_datetime(timeline_df['date'])

            fig_timeline = go.Figure()

            fig_timeline.add_trace(go.Scatter(
                x=timeline_df['date'],
                y=timeline_df['impressions'],
                name='Impressions',
                mode='lines+markers'
            ))

            fig_timeline.add_trace(go.Scatter(
                x=timeline_df['date'],
                y=timeline_df['clicks'],
                name='Clicks',
                mode='lines+markers',
                yaxis='y2'
            ))

            fig_timeline.update_layout(
                title='Campaign Performance Over Time',
                xaxis=dict(title='Date'),
                yaxis=dict(title='Impressions'),
                yaxis2=dict(title='Clicks', overlaying='y', side='right'),
                hovermode='x unified'
            )

            st.plotly_chart(fig_timeline, use_container_width=True)

        # Financial metrics
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Financial Overview**")
            fig_finance = go.Figure(data=[
                go.Bar(
                    name='Budget',
                    x=['Total', 'Spent', 'Remaining'],
                    y=[
                        selected_campaign['total_budget'],
                        selected_campaign['spent_budget'],
                        selected_campaign['remaining_budget']
                    ]
                )
            ])
            fig_finance.update_layout(title='Budget Breakdown')
            st.plotly_chart(fig_finance, use_container_width=True)

        with col2:
            st.write("**Conversion Funnel**")
            funnel_data = {
                'Stage': ['Impressions', 'Clicks', 'Conversions'],
                'Count': [
                    analytics['total_impressions'],
                    analytics['total_clicks'],
                    analytics['total_conversions']
                ]
            }
            fig_funnel = px.funnel(
                funnel_data,
                x='Count',
                y='Stage'
            )
            st.plotly_chart(fig_funnel, use_container_width=True)

    with tab2:
        st.subheader("Timeline & Milestones")

        if milestones:
            # Create Gantt chart
            st.write("**Gantt Chart**")

            gantt_data = []
            for milestone in milestones:
                # Calculate start date (due date - 7 days as example)
                due_date = pd.to_datetime(milestone['due_date'])
                start_date = due_date - timedelta(days=7)

                status_color = {
                    'completed': '#00CC66',
                    'in_progress': '#3399FF',
                    'pending': '#CCCCCC',
                    'delayed': '#FF6666',
                    'cancelled': '#999999'
                }

                gantt_data.append({
                    'Task': milestone['title'],
                    'Start': start_date,
                    'Finish': due_date,
                    'Status': milestone['status'],
                    'Progress': milestone.get('progress_percentage', 0)
                })

            df_gantt = pd.DataFrame(gantt_data)

            fig_gantt = px.timeline(
                df_gantt,
                x_start='Start',
                x_end='Finish',
                y='Task',
                color='Status',
                title='Campaign Milestone Timeline'
            )
            fig_gantt.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig_gantt, use_container_width=True)

            # Milestone list
            st.write("**Milestone Details**")
            for milestone in milestones:
                status_emoji = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'pending': '⏳',
                    'delayed': '⚠️',
                    'cancelled': '❌'
                }

                with st.expander(
                    f"{status_emoji.get(milestone['status'], '📌')} {milestone['title']}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Status:** {milestone['status']}")
                        st.write(f"**Due Date:** {milestone['due_date']}")
                        st.write(f"**Progress:** {milestone['progress_percentage']}%")

                    with col2:
                        if milestone.get('description'):
                            st.write(f"**Description:** {milestone['description']}")
                        if milestone.get('is_overdue'):
                            st.error("⚠️ Overdue!")

                    st.progress(milestone['progress_percentage'] / 100)

        else:
            st.info("No milestones defined for this campaign")

            if st.button("➕ Add First Milestone"):
                st.info("Milestone creation form would go here")

    with tab3:
        st.subheader("Channel Performance")

        if channels:
            # Channel comparison
            channel_df = pd.DataFrame(analytics.get('channel_performance', []))

            if not channel_df.empty:
                # ROI by channel
                fig_roi = px.bar(
                    channel_df,
                    x='channel_name',
                    y='roi',
                    color='roi',
                    title='ROI by Channel (%)',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_roi, use_container_width=True)

                # Channel spend
                fig_spend = px.pie(
                    channel_df,
                    values='spent',
                    names='channel_name',
                    title='Budget Allocation by Channel'
                )
                st.plotly_chart(fig_spend, use_container_width=True)

                # Detailed channel table
                st.write("**Channel Details**")
                st.dataframe(
                    channel_df[['channel_name', 'channel_type', 'roi', 'conversions', 'spent']],
                    use_container_width=True
                )

        else:
            st.info("No channels configured for this campaign")

    with tab4:
        st.subheader("🤖 AI-Powered Insights")

        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("🔍 Generate Insights", use_container_width=True):
                with st.spinner("AI is analyzing your campaign..."):
                    try:
                        result = APIClient.optimize_campaign(campaign_id)
                        st.success("Optimization started! Check back in a few moments.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        # Display existing insights
        if selected_campaign.get('ai_insights'):
            st.write("**Latest AI Insights**")
            insights = selected_campaign['ai_insights']

            if insights.get('summary'):
                st.info(insights['summary'])

            col1, col2 = st.columns(2)

            with col1:
                if insights.get('strengths'):
                    st.write("**✅ Strengths**")
                    for strength in insights['strengths']:
                        st.write(f"- {strength}")

                if insights.get('opportunities'):
                    st.write("**💡 Opportunities**")
                    for opp in insights['opportunities']:
                        st.write(f"- {opp}")

            with col2:
                if insights.get('weaknesses'):
                    st.write("**⚠️ Areas for Improvement**")
                    for weakness in insights['weaknesses']:
                        st.write(f"- {weakness}")

                if insights.get('threats'):
                    st.write("**🚨 Risks**")
                    for threat in insights['threats']:
                        st.write(f"- {threat}")

        # Optimization suggestions
        if selected_campaign.get('optimization_suggestions'):
            st.write("**💡 Optimization Recommendations**")
            suggestions = selected_campaign['optimization_suggestions']

            if suggestions.get('reallocations'):
                st.write("**Budget Reallocation Suggestions:**")
                for realloc in suggestions['reallocations']:
                    with st.expander(f"📊 {realloc.get('channel_name', 'Channel')}"):
                        st.write(f"**Current:** ${realloc.get('current_allocation', 0):,.2f}")
                        st.write(f"**Recommended:** ${realloc.get('recommended_allocation', 0):,.2f}")
                        st.write(f"**Reason:** {realloc.get('reason', 'N/A')}")
                        st.write(f"**Expected Impact:** {realloc.get('expected_impact', 'N/A')}")

except Exception as e:
    st.error(f"Error loading analytics: {str(e)}")
    st.exception(e)
