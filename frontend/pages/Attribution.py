"""
NEXUS Platform - Attribution Module UI
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_client import AttributionClient


# Page configuration
st.set_page_config(
    page_title="Attribution Analysis - NEXUS Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize API client
@st.cache_resource
def get_api_client():
    return AttributionClient()

api = get_api_client()


# Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 0.25rem;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)


# Header
st.markdown('<div class="main-header">📊 Attribution Analysis</div>', unsafe_allow_html=True)
st.markdown("**Multi-touch attribution, journey mapping, and channel ROI analysis**")

# Sidebar navigation
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "Select View",
    [
        "Dashboard",
        "Journey Visualization",
        "Model Comparison",
        "Channel ROI",
        "Conversion Paths",
        "AI Insights",
        "Settings",
    ],
)


# ============================================================================
# Dashboard Page
# ============================================================================

if page == "Dashboard":
    st.header("📈 Attribution Dashboard")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
        )
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())

    try:
        # Fetch metrics
        with st.spinner("Loading dashboard metrics..."):
            metrics = api.get_journey_metrics(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

        # Display key metrics
        st.subheader("Key Performance Indicators")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Journeys",
                f"{metrics.get('total_journeys', 0):,}",
            )

        with col2:
            st.metric(
                "Conversions",
                f"{metrics.get('total_conversions', 0):,}",
                delta=f"{metrics.get('conversion_rate', 0):.1%} rate",
            )

        with col3:
            st.metric(
                "Total Revenue",
                f"${metrics.get('total_revenue', 0):,.2f}",
            )

        with col4:
            st.metric(
                "Avg Touchpoints",
                f"{metrics.get('avg_touchpoints', 0):.1f}",
            )

        # Channel performance
        st.subheader("Channel Performance")

        try:
            channels = api.list_channels(active_only=True)
            if channels:
                channel_ids = [ch["id"] for ch in channels[:10]]  # Top 10 channels

                roi_data = api.calculate_channel_roi({
                    "channel_ids": channel_ids,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "attribution_model_id": None,
                })

                if roi_data:
                    df = pd.DataFrame(roi_data)

                    # ROI Chart
                    fig = px.bar(
                        df,
                        x="channel_name",
                        y="roi",
                        color="roi",
                        title="Channel ROI (%)",
                        labels={"roi": "ROI (%)", "channel_name": "Channel"},
                        color_continuous_scale="RdYlGn",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Revenue vs Cost
                    col1, col2 = st.columns(2)

                    with col1:
                        fig = px.pie(
                            df,
                            values="total_revenue",
                            names="channel_name",
                            title="Revenue Distribution",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        fig = px.bar(
                            df,
                            x="channel_name",
                            y=["total_revenue", "total_cost"],
                            title="Revenue vs Cost",
                            barmode="group",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # Detailed table
                    st.subheader("Detailed Channel Metrics")
                    st.dataframe(
                        df[[
                            "channel_name",
                            "total_touchpoints",
                            "total_conversions",
                            "total_revenue",
                            "total_cost",
                            "roi",
                            "roas",
                        ]],
                        use_container_width=True,
                    )

        except Exception as e:
            st.warning(f"Could not load channel performance: {str(e)}")

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")


# ============================================================================
# Journey Visualization Page
# ============================================================================

elif page == "Journey Visualization":
    st.header("🗺️ Customer Journey Visualization")

    journey_id = st.number_input("Journey ID", min_value=1, value=1, step=1)

    # Model selector
    try:
        models = api.list_models(active_only=True)
        model_options = {m["name"]: m["id"] for m in models}
        model_options["No Attribution"] = None

        selected_model = st.selectbox("Attribution Model", list(model_options.keys()))
        model_id = model_options[selected_model]
    except Exception:
        model_id = None

    if st.button("Load Journey", type="primary"):
        try:
            with st.spinner("Loading journey data..."):
                journey_data = api.get_journey_visualization(journey_id, model_id)

            # Journey summary
            st.subheader("Journey Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("User ID", journey_data["user_id"])

            with col2:
                st.metric("Touchpoints", journey_data["total_touchpoints"])

            with col3:
                st.metric(
                    "Conversion Value",
                    f"${journey_data['conversion_value']:.2f}",
                )

            with col4:
                st.metric(
                    "Duration",
                    f"{journey_data.get('journey_duration_minutes', 0)} min",
                )

            # Journey timeline
            st.subheader("Journey Timeline")

            touchpoints = journey_data["touchpoints"]
            if touchpoints:
                df = pd.DataFrame(touchpoints)

                # Create timeline visualization
                fig = go.Figure()

                for idx, tp in enumerate(touchpoints):
                    fig.add_trace(go.Scatter(
                        x=[tp["timestamp"]],
                        y=[idx + 1],
                        mode="markers+text",
                        marker=dict(
                            size=20 + (tp["engagement_score"] * 30),
                            color=tp["attribution_credit"] if tp["attribution_credit"] else 0.5,
                            colorscale="Viridis",
                            showscale=True,
                        ),
                        text=tp["channel_name"],
                        textposition="top center",
                        name=tp["channel_name"],
                        hovertemplate=(
                            f"<b>{tp['channel_name']}</b><br>"
                            f"Type: {tp['touchpoint_type']}<br>"
                            f"Engagement: {tp['engagement_score']:.2f}<br>"
                            f"Time Spent: {tp['time_spent_seconds']}s<br>"
                            f"Cost: ${tp['cost']:.2f}<br>"
                            + (f"Attribution: {tp['attribution_credit']:.2%}" if tp['attribution_credit'] else "")
                            + "<extra></extra>"
                        ),
                    ))

                fig.update_layout(
                    title="Journey Touchpoints Timeline",
                    xaxis_title="Time",
                    yaxis_title="Touchpoint Position",
                    showlegend=False,
                    height=400,
                )

                st.plotly_chart(fig, use_container_width=True)

                # Detailed touchpoint table
                st.subheader("Touchpoint Details")

                display_df = df[[
                    "position",
                    "channel_name",
                    "touchpoint_type",
                    "engagement_score",
                    "time_spent_seconds",
                    "cost",
                ]]

                if model_id and "attribution_credit" in df.columns:
                    display_df["attribution_credit"] = df["attribution_credit"]

                st.dataframe(display_df, use_container_width=True)

            # Conversions
            if journey_data.get("conversions"):
                st.subheader("Conversions")
                conversions_df = pd.DataFrame(journey_data["conversions"])
                st.dataframe(conversions_df, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading journey: {str(e)}")


# ============================================================================
# Model Comparison Page
# ============================================================================

elif page == "Model Comparison":
    st.header("🔬 Attribution Model Comparison")

    st.markdown("""
    Compare different attribution models to understand how credit is distributed
    across marketing channels using various methodologies.
    """)

    # Select journeys
    st.subheader("Select Journeys")

    journey_input = st.text_area(
        "Enter Journey IDs (comma-separated)",
        value="1,2,3,4,5",
        help="Enter journey IDs separated by commas",
    )

    try:
        journey_ids = [int(j.strip()) for j in journey_input.split(",")]
    except ValueError:
        st.error("Please enter valid journey IDs")
        journey_ids = []

    # Select models
    try:
        models = api.list_models(active_only=True)
        selected_models = st.multiselect(
            "Select Attribution Models",
            options=[m["name"] for m in models],
            default=[m["name"] for m in models[:3]],
        )

        model_ids = [m["id"] for m in models if m["name"] in selected_models]
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        model_ids = []

    if st.button("Compare Models", type="primary") and journey_ids and model_ids:
        try:
            with st.spinner("Calculating attribution with multiple models..."):
                comparison = api.compare_models_ai(journey_ids, model_ids)

            # Display model summaries
            st.subheader("Model Comparison")

            summaries = comparison.get("model_summaries", {})

            # Create comparison table
            comparison_data = []
            for model_name, data in summaries.items():
                comparison_data.append({
                    "Model": model_name,
                    "Type": data["model_type"],
                    "Total Revenue": data["total_revenue"],
                    "Channels": data["channel_count"],
                })

            comp_df = pd.DataFrame(comparison_data)
            st.dataframe(comp_df, use_container_width=True)

            # Revenue distribution by model
            fig = px.bar(
                comp_df,
                x="Model",
                y="Total Revenue",
                title="Total Attributed Revenue by Model",
                color="Model",
            )
            st.plotly_chart(fig, use_container_width=True)

            # AI Analysis
            if "ai_comparison" in comparison:
                st.subheader("AI Analysis & Recommendations")
                st.markdown(comparison["ai_comparison"])

        except Exception as e:
            st.error(f"Error comparing models: {str(e)}")


# ============================================================================
# Channel ROI Page
# ============================================================================

elif page == "Channel ROI":
    st.header("💰 Channel ROI Analysis")

    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            key="roi_start",
        )
    with col2:
        end_date = st.date_input("End Date", value=datetime.now(), key="roi_end")

    # Channel selector
    try:
        channels = api.list_channels(active_only=True)
        channel_options = {ch["name"]: ch["id"] for ch in channels}

        selected_channels = st.multiselect(
            "Select Channels",
            options=list(channel_options.keys()),
            default=list(channel_options.keys())[:5],
        )

        channel_ids = [channel_options[name] for name in selected_channels]
    except Exception as e:
        st.error(f"Error loading channels: {str(e)}")
        channel_ids = []

    # Model selector
    try:
        models = api.list_models(active_only=True)
        model_options = {"Raw Data (No Attribution)": None}
        model_options.update({m["name"]: m["id"] for m in models})

        selected_model = st.selectbox("Attribution Model", list(model_options.keys()))
        model_id = model_options[selected_model]
    except Exception:
        model_id = None

    if st.button("Calculate ROI", type="primary") and channel_ids:
        try:
            with st.spinner("Calculating channel ROI..."):
                roi_data = api.calculate_channel_roi({
                    "channel_ids": channel_ids,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "attribution_model_id": model_id,
                })

            if roi_data:
                df = pd.DataFrame(roi_data)

                # ROI Metrics
                st.subheader("ROI Metrics")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Avg ROI", f"{df['roi'].mean():.1f}%")

                with col2:
                    st.metric("Avg ROAS", f"{df['roas'].mean():.2f}x")

                with col3:
                    st.metric("Total Revenue", f"${df['total_revenue'].sum():,.2f}")

                # ROI Comparison Chart
                fig = px.bar(
                    df.sort_values("roi", ascending=False),
                    x="channel_name",
                    y="roi",
                    color="roi",
                    title="Channel ROI Comparison",
                    labels={"roi": "ROI (%)", "channel_name": "Channel"},
                    color_continuous_scale="RdYlGn",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Scatter: Cost vs Revenue
                fig = px.scatter(
                    df,
                    x="total_cost",
                    y="total_revenue",
                    size="total_conversions",
                    color="channel_name",
                    title="Cost vs Revenue (bubble size = conversions)",
                    labels={
                        "total_cost": "Total Cost ($)",
                        "total_revenue": "Total Revenue ($)",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)

                # Detailed table
                st.subheader("Detailed ROI Data")
                st.dataframe(df, use_container_width=True)

                # Export data
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download ROI Data (CSV)",
                    data=csv,
                    file_name=f"channel_roi_{start_date}_{end_date}.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Error calculating ROI: {str(e)}")


# ============================================================================
# Conversion Paths Page
# ============================================================================

elif page == "Conversion Paths":
    st.header("🛤️ Conversion Path Analysis")

    st.markdown("""
    Analyze common conversion paths and understand the typical customer journey
    from first touch to conversion.
    """)

    limit = st.slider("Number of paths to show", min_value=10, max_value=500, value=100)

    if st.button("Load Conversion Paths", type="primary"):
        try:
            with st.spinner("Loading conversion paths..."):
                paths = api.get_conversion_paths(limit=limit, converted_only=True)

            if paths:
                st.success(f"Loaded {len(paths)} conversion paths")

                # Path length distribution
                df = pd.DataFrame(paths)

                fig = px.histogram(
                    df,
                    x="touchpoint_count",
                    title="Distribution of Conversion Path Lengths",
                    labels={"touchpoint_count": "Number of Touchpoints"},
                )
                st.plotly_chart(fig, use_container_width=True)

                # Top paths
                st.subheader("Top Conversion Paths")

                path_counts = df["path"].value_counts().head(10)

                fig = px.bar(
                    x=path_counts.values,
                    y=path_counts.index,
                    orientation="h",
                    title="Most Common Conversion Paths",
                    labels={"x": "Frequency", "y": "Path"},
                )
                st.plotly_chart(fig, use_container_width=True)

                # Detailed paths
                st.subheader("All Conversion Paths")
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Error loading conversion paths: {str(e)}")


# ============================================================================
# AI Insights Page
# ============================================================================

elif page == "AI Insights":
    st.header("🤖 AI-Powered Attribution Insights")

    st.markdown("""
    Get AI-powered insights and recommendations for your attribution data
    using Claude AI.
    """)

    # Journey selection
    journey_input = st.text_area(
        "Enter Journey IDs (comma-separated)",
        value="1,2,3,4,5,6,7,8,9,10",
        help="Enter journey IDs separated by commas",
    )

    try:
        journey_ids = [int(j.strip()) for j in journey_input.split(",")]
    except ValueError:
        st.error("Please enter valid journey IDs")
        journey_ids = []

    # Analysis type
    analysis_type = st.selectbox(
        "Analysis Type",
        ["performance", "optimization", "trends"],
    )

    if st.button("Generate AI Insights", type="primary") and journey_ids:
        try:
            with st.spinner("Generating AI insights... This may take a moment."):
                insights = api.get_ai_insights(journey_ids, analysis_type)

            st.success("AI insights generated successfully!")

            # Display insights
            st.subheader("AI Analysis")
            st.markdown(insights["insights"])

            # Metadata
            with st.expander("Analysis Details"):
                st.write(f"Journey Count: {insights['journey_count']}")
                st.write(f"Analysis Type: {insights['analysis_type']}")
                st.write(f"Generated At: {insights['generated_at']}")

        except Exception as e:
            st.error(f"Error generating insights: {str(e)}")


# ============================================================================
# Settings Page
# ============================================================================

elif page == "Settings":
    st.header("⚙️ Attribution Settings")

    tab1, tab2, tab3 = st.tabs(["Channels", "Models", "Cache"])

    # Channels Tab
    with tab1:
        st.subheader("Manage Channels")

        # Create channel
        with st.expander("Create New Channel"):
            channel_name = st.text_input("Channel Name")
            channel_type = st.selectbox(
                "Channel Type",
                [
                    "direct",
                    "organic_search",
                    "paid_search",
                    "social_organic",
                    "social_paid",
                    "email",
                    "referral",
                    "display",
                    "affiliate",
                    "video",
                    "other",
                ],
            )
            cost_per_click = st.number_input("Cost Per Click", min_value=0.0, value=0.0)
            monthly_budget = st.number_input("Monthly Budget", min_value=0.0, value=0.0)

            if st.button("Create Channel"):
                try:
                    result = api.create_channel({
                        "name": channel_name,
                        "channel_type": channel_type,
                        "cost_per_click": cost_per_click,
                        "monthly_budget": monthly_budget,
                        "is_active": True,
                    })
                    st.success(f"Channel '{channel_name}' created successfully!")
                except Exception as e:
                    st.error(f"Error creating channel: {str(e)}")

        # List channels
        try:
            channels = api.list_channels(active_only=False)
            if channels:
                st.subheader("Existing Channels")
                df = pd.DataFrame(channels)
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading channels: {str(e)}")

    # Models Tab
    with tab2:
        st.subheader("Manage Attribution Models")

        # Create model
        with st.expander("Create New Model"):
            model_name = st.text_input("Model Name")
            model_type = st.selectbox(
                "Model Type",
                [
                    "first_touch",
                    "last_touch",
                    "linear",
                    "time_decay",
                    "position_based",
                    "data_driven",
                ],
            )

            # Model-specific parameters
            if model_type == "time_decay":
                halflife = st.number_input(
                    "Half-life (days)",
                    min_value=1.0,
                    value=7.0,
                )
            elif model_type == "position_based":
                first_weight = st.slider("First Touch Weight", 0.0, 1.0, 0.4)
                last_weight = st.slider("Last Touch Weight", 0.0, 1.0, 0.4)
                middle_weight = 1.0 - first_weight - last_weight
                st.write(f"Middle Weight: {middle_weight:.2f}")

            if st.button("Create Model"):
                try:
                    model_data = {
                        "name": model_name,
                        "model_type": model_type,
                        "is_active": True,
                    }

                    if model_type == "time_decay":
                        model_data["time_decay_halflife_days"] = halflife
                    elif model_type == "position_based":
                        model_data["position_weights"] = {
                            "first": first_weight,
                            "middle": middle_weight,
                            "last": last_weight,
                        }

                    result = api.create_model(model_data)
                    st.success(f"Model '{model_name}' created successfully!")
                except Exception as e:
                    st.error(f"Error creating model: {str(e)}")

        # List models
        try:
            models = api.list_models(active_only=False)
            if models:
                st.subheader("Existing Models")
                df = pd.DataFrame(models)
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")

    # Cache Tab
    with tab3:
        st.subheader("Cache Management")

        st.markdown("""
        Clear cached attribution data to force recalculation.
        Use this when data has been updated.
        """)

        pattern = st.text_input("Cache Pattern", value="attribution:*")

        if st.button("Clear Cache", type="primary"):
            st.warning("Cache clearing is disabled in this demo")


# Footer
st.markdown("---")
st.markdown(
    "**NEXUS Platform** | Attribution Module | Powered by Claude AI"
)
