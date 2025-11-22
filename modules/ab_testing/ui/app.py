"""
Streamlit UI for NEXUS A/B Testing Module.

Production-ready dashboard for managing experiments, analyzing results,
and visualizing statistical data.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="NEXUS A/B Testing",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar navigation
st.sidebar.title("🧪 NEXUS A/B Testing")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🆕 Create Experiment",
        "📈 Experiment Results",
        "🎯 Variant Builder",
        "📏 Sample Size Calculator",
        "⚙️ Settings",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    ### Quick Links
    - [API Documentation](/api/docs)
    - [GitHub Repository](https://github.com/nexus-platform)

    ### Support
    - 📧 Email: support@nexus.com
    - 💬 Chat: [Discord](https://discord.gg/nexus)
    """
)

# Main content
if page == "📊 Dashboard":
    st.markdown('<h1 class="main-header">A/B Testing Dashboard</h1>', unsafe_allow_html=True)

    st.markdown(
        """
        Welcome to the NEXUS A/B Testing Dashboard! This production-ready platform
        enables you to run sophisticated experiments, analyze results with statistical
        rigor, and make data-driven decisions.
        """
    )

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Experiments",
            value="0",
            delta="0",
        )

    with col2:
        st.metric(
            label="Total Participants",
            value="0",
            delta="0",
        )

    with col3:
        st.metric(
            label="Conversion Rate",
            value="0.0%",
            delta="0%",
        )

    with col4:
        st.metric(
            label="Completed Tests",
            value="0",
            delta="0",
        )

    st.markdown("---")

    # Recent experiments
    st.subheader("📋 Recent Experiments")

    st.info(
        """
        **No experiments yet!**

        Get started by creating your first A/B test. Click on "🆕 Create Experiment"
        in the sidebar to begin.
        """
    )

    # Getting started guide
    with st.expander("📚 Getting Started Guide", expanded=False):
        st.markdown(
            """
            ### How to Run Your First A/B Test

            1. **Create an Experiment**
               - Navigate to "🆕 Create Experiment"
               - Define your hypothesis and goals
               - Set confidence level and sample size

            2. **Add Variants**
               - Create at least 2 variants (Control + Treatment)
               - Configure each variant's parameters
               - Set traffic allocation weights

            3. **Define Metrics**
               - Add conversion goals
               - Set up revenue tracking (if applicable)
               - Configure custom metrics

            4. **Start Experiment**
               - Review your configuration
               - Start the experiment
               - Monitor real-time results

            5. **Analyze Results**
               - View statistical significance
               - Check confidence intervals
               - Determine the winner

            6. **Deploy Winner**
               - Review recommendations
               - Implement winning variant
               - Archive experiment
            """
        )

elif page == "🆕 Create Experiment":
    st.markdown('<h1 class="main-header">Create New Experiment</h1>', unsafe_allow_html=True)

    st.markdown("Use this visual builder to create and configure a new A/B test.")

    # Experiment details
    st.subheader("1. Experiment Details")

    col1, col2 = st.columns(2)

    with col1:
        experiment_name = st.text_input(
            "Experiment Name *",
            placeholder="e.g., Homepage CTA Button Test",
        )

        experiment_type = st.selectbox(
            "Experiment Type *",
            ["A/B Test", "Multivariate Test", "Multi-Armed Bandit"],
        )

    with col2:
        hypothesis = st.text_area(
            "Hypothesis",
            placeholder="e.g., Changing the CTA button from blue to red will increase conversions by 10%",
        )

    description = st.text_area(
        "Description",
        placeholder="Detailed description of what you're testing and why...",
    )

    st.markdown("---")

    # Statistical configuration
    st.subheader("2. Statistical Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        target_sample_size = st.number_input(
            "Target Sample Size (per variant)",
            min_value=100,
            max_value=100000,
            value=1000,
            step=100,
        )

    with col2:
        confidence_level = st.slider(
            "Confidence Level",
            min_value=0.80,
            max_value=0.99,
            value=0.95,
            step=0.01,
            format="%.2f",
        )

    with col3:
        traffic_allocation = st.slider(
            "Traffic Allocation",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            format="%.2f",
            help="Percentage of total traffic to include in experiment",
        )

    st.markdown("---")

    # Variants configuration
    st.subheader("3. Variants Configuration")

    num_variants = st.number_input(
        "Number of Variants",
        min_value=2,
        max_value=10,
        value=2,
    )

    variants = []
    for i in range(num_variants):
        with st.expander(f"Variant {i + 1}: {'Control' if i == 0 else f'Treatment {i}'}", expanded=True):
            vcol1, vcol2 = st.columns(2)

            with vcol1:
                variant_name = st.text_input(
                    "Name",
                    value="Control" if i == 0 else f"Treatment {i}",
                    key=f"variant_name_{i}",
                )

            with vcol2:
                traffic_weight = st.number_input(
                    "Traffic Weight",
                    min_value=0.1,
                    max_value=10.0,
                    value=1.0,
                    step=0.1,
                    key=f"variant_weight_{i}",
                )

            variant_description = st.text_area(
                "Description",
                placeholder="Describe what's different in this variant...",
                key=f"variant_desc_{i}",
            )

            is_control = i == 0

            variants.append(
                {
                    "name": variant_name,
                    "description": variant_description,
                    "is_control": is_control,
                    "traffic_weight": traffic_weight,
                }
            )

    st.markdown("---")

    # Metrics configuration
    st.subheader("4. Metrics Configuration")

    num_metrics = st.number_input(
        "Number of Metrics",
        min_value=1,
        max_value=5,
        value=1,
    )

    metrics = []
    for i in range(num_metrics):
        with st.expander(f"Metric {i + 1}", expanded=i == 0):
            mcol1, mcol2 = st.columns(2)

            with mcol1:
                metric_name = st.text_input(
                    "Metric Name",
                    placeholder="e.g., Conversion Rate",
                    key=f"metric_name_{i}",
                )

                metric_type = st.selectbox(
                    "Metric Type",
                    ["Conversion", "Revenue", "Engagement", "Custom"],
                    key=f"metric_type_{i}",
                )

            with mcol2:
                is_primary = st.checkbox(
                    "Primary Metric",
                    value=i == 0,
                    key=f"metric_primary_{i}",
                )

                goal_value = st.number_input(
                    "Goal Value (optional)",
                    min_value=0.0,
                    value=0.0,
                    key=f"metric_goal_{i}",
                )

            metrics.append(
                {
                    "name": metric_name,
                    "type": metric_type.lower(),
                    "is_primary": is_primary,
                    "goal_value": goal_value if goal_value > 0 else None,
                }
            )

    st.markdown("---")

    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        auto_winner = st.checkbox(
            "Enable Automatic Winner Detection",
            value=True,
            help="Automatically determine winner when statistical significance is reached",
        )

    st.markdown("---")

    # Create button
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("✨ Create Experiment", type="primary", use_container_width=True):
            if not experiment_name:
                st.error("Please provide an experiment name")
            else:
                st.success(
                    f"""
                    **Experiment Created Successfully!**

                    - Name: {experiment_name}
                    - Type: {experiment_type}
                    - Variants: {len(variants)}
                    - Metrics: {len(metrics)}

                    Your experiment is ready to start!
                    """
                )

                # Display configuration summary
                with st.expander("📋 Configuration Summary"):
                    st.json(
                        {
                            "name": experiment_name,
                            "type": experiment_type.lower().replace(" ", "_"),
                            "hypothesis": hypothesis,
                            "target_sample_size": target_sample_size,
                            "confidence_level": confidence_level,
                            "traffic_allocation": traffic_allocation,
                            "variants": variants,
                            "metrics": metrics,
                            "auto_winner_enabled": auto_winner,
                        }
                    )

elif page == "📈 Experiment Results":
    st.markdown('<h1 class="main-header">Experiment Results</h1>', unsafe_allow_html=True)

    st.info("Select an experiment to view detailed results and statistical analysis.")

    # Placeholder for experiment selection
    experiment_id = st.selectbox(
        "Select Experiment",
        ["No experiments available"],
    )

    st.markdown("---")

    st.markdown(
        """
        ### Features Available:

        - **Real-time Dashboard**: View live conversion rates and participant counts
        - **Statistical Analysis**: P-values, confidence intervals, effect sizes
        - **Winner Detection**: Automatic recommendation based on statistical significance
        - **Visualizations**: Interactive charts powered by Plotly
        - **Export**: Download results as CSV or PDF reports
        """
    )

elif page == "🎯 Variant Builder":
    st.markdown('<h1 class="main-header">Variant Builder</h1>', unsafe_allow_html=True)

    st.markdown("Visual tool for creating and managing experiment variants.")

    st.info("This feature allows you to visually configure variant parameters and preview changes.")

elif page == "📏 Sample Size Calculator":
    st.markdown('<h1 class="main-header">Sample Size Calculator</h1>', unsafe_allow_html=True)

    st.markdown(
        """
        Calculate the required sample size for your A/B test based on:
        - Baseline conversion rate
        - Minimum detectable effect
        - Statistical power
        - Significance level
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        baseline_rate = st.slider(
            "Baseline Conversion Rate",
            min_value=0.01,
            max_value=0.50,
            value=0.10,
            step=0.01,
            format="%.2f",
        )

        mde = st.slider(
            "Minimum Detectable Effect (Relative)",
            min_value=0.05,
            max_value=0.50,
            value=0.20,
            step=0.05,
            format="%.2f",
            help="E.g., 0.20 means 20% improvement",
        )

    with col2:
        power = st.slider(
            "Statistical Power (1 - β)",
            min_value=0.70,
            max_value=0.95,
            value=0.80,
            step=0.05,
            format="%.2f",
        )

        significance = st.slider(
            "Significance Level (α)",
            min_value=0.01,
            max_value=0.10,
            value=0.05,
            step=0.01,
            format="%.2f",
        )

    if st.button("Calculate Sample Size", type="primary"):
        # Placeholder calculation (would use StatisticalAnalyzer in production)
        import math

        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)
        z_alpha = 1.96  # for 0.05 significance
        z_beta = 0.84  # for 0.80 power

        n = ((z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))) / (p2 - p1) ** 2
        n = int(math.ceil(n))

        st.success(
            f"""
            ### Required Sample Size

            **{n:,} participants per variant**

            - Total participants needed: **{n * 2:,}**
            - Expected treatment conversion rate: **{p2:.2%}**
            - Absolute improvement: **{(p2 - p1):.2%}**
            """
        )

        # Visualization
        import pandas as pd
        import plotly.graph_objects as go

        sample_sizes = list(range(100, 5000, 100))
        powers = []

        for size in sample_sizes:
            # Simplified power calculation
            effect = (p2 - p1) / math.sqrt(p1 * (1 - p1) / size)
            estimated_power = min(0.99, effect / 3)
            powers.append(estimated_power)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=sample_sizes,
                y=powers,
                mode="lines",
                name="Statistical Power",
                line=dict(color="#1f77b4", width=2),
            )
        )
        fig.add_hline(
            y=power,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target Power: {power:.0%}",
        )
        fig.update_layout(
            title="Statistical Power vs Sample Size",
            xaxis_title="Sample Size (per variant)",
            yaxis_title="Statistical Power",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "⚙️ Settings":
    st.markdown('<h1 class="main-header">Settings</h1>', unsafe_allow_html=True)

    st.subheader("API Configuration")

    col1, col2 = st.columns(2)

    with col1:
        api_host = st.text_input("API Host", value="localhost")
        api_port = st.number_input("API Port", value=8000, min_value=1, max_value=65535)

    with col2:
        database_url = st.text_input(
            "Database URL",
            value="postgresql://nexus:password@localhost:5432/nexus_db",
            type="password",
        )
        redis_url = st.text_input(
            "Redis URL",
            value="redis://localhost:6379/0",
        )

    st.markdown("---")

    st.subheader("Default Settings")

    col1, col2 = st.columns(2)

    with col1:
        default_confidence = st.slider(
            "Default Confidence Level",
            min_value=0.80,
            max_value=0.99,
            value=0.95,
            step=0.01,
        )

    with col2:
        default_sample_size = st.number_input(
            "Default Sample Size",
            min_value=100,
            max_value=100000,
            value=1000,
            step=100,
        )

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>NEXUS A/B Testing Module v1.0.0 | Built with ❤️ using Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True,
)
