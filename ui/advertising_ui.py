"""
Advertising UI module.
"""
import streamlit as st
import pandas as pd


def render_advertising():
    """Render advertising module UI."""
    st.markdown('<p class="main-header">Advertising Manager</p>', unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Campaigns", "Ads", "Creatives", "Performance", "Automation"
    ])

    with tab1:
        render_campaigns_tab()

    with tab2:
        render_ads_tab()

    with tab3:
        render_creatives_tab()

    with tab4:
        render_performance_tab()

    with tab5:
        render_automation_tab()


def render_campaigns_tab():
    """Render campaigns tab."""
    st.subheader("Campaign Management")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ New Campaign"):
            st.session_state.show_create_campaign = True

    with col2:
        if st.button("🔄 Sync All"):
            st.info("Syncing campaign metrics...")

    # Create campaign form
    if st.session_state.get("show_create_campaign", False):
        with st.form("create_campaign_form"):
            st.subheader("Create New Campaign")

            col1, col2 = st.columns(2)

            with col1:
                campaign_name = st.text_input("Campaign Name *")
                platform = st.selectbox("Platform", ["Google Ads", "Facebook Ads", "LinkedIn Ads"])
                objective = st.selectbox(
                    "Objective",
                    ["Awareness", "Consideration", "Conversion", "Lead Generation", "Sales"]
                )

            with col2:
                budget_type = st.selectbox("Budget Type", ["Daily", "Lifetime"])
                budget_amount = st.number_input("Budget Amount ($)", min_value=1.0, value=100.0)
                bid_strategy = st.selectbox(
                    "Bid Strategy",
                    ["Manual CPC", "Automated", "Target CPA", "Target ROAS", "Maximize Conversions"]
                )

            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Campaign")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if submit:
                if not campaign_name:
                    st.error("Campaign name is required")
                else:
                    st.success(f"Campaign '{campaign_name}' created successfully!")
                    st.session_state.show_create_campaign = False
                    st.rerun()

            if cancel:
                st.session_state.show_create_campaign = False
                st.rerun()

    # Campaigns table
    st.markdown("### Active Campaigns")

    campaigns_data = {
        "Campaign": ["Brand Awareness Q1", "Lead Gen - Tech", "Product Launch"],
        "Platform": ["Google Ads", "LinkedIn Ads", "Facebook Ads"],
        "Status": ["Active", "Active", "Paused"],
        "Budget": ["$500/day", "$200/day", "$1,000 lifetime"],
        "Spent": ["$3,245", "$1,890", "$750"],
        "Impressions": ["45.2K", "12.8K", "8.5K"],
        "Clicks": ["1,234", "456", "289"],
        "CTR": ["2.73%", "3.56%", "3.40%"],
        "Conversions": ["45", "28", "12"],
        "ROAS": ["4.2x", "5.1x", "3.8x"]
    }

    df = pd.DataFrame(campaigns_data)
    st.dataframe(df, use_container_width=True)

    # Campaign actions
    st.markdown("### Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Pause All"):
            st.info("Pausing all campaigns...")

    with col2:
        if st.button("Resume All"):
            st.info("Resuming all campaigns...")

    with col3:
        if st.button("Optimize Budgets"):
            st.info("Optimizing campaign budgets...")

    with col4:
        if st.button("Generate Report"):
            st.info("Generating performance report...")


def render_ads_tab():
    """Render ads tab."""
    st.subheader("Ad Management")
    st.info("Ad creation and management will be available here")


def render_creatives_tab():
    """Render creatives tab."""
    st.subheader("Creative Management")

    if st.button("➕ Upload Creative"):
        st.session_state.show_upload_creative = True

    if st.session_state.get("show_upload_creative", False):
        with st.form("upload_creative_form"):
            st.subheader("Upload New Creative")

            creative_name = st.text_input("Creative Name *")
            creative_type = st.selectbox("Type", ["Image", "Video", "Carousel"])

            if creative_type == "Image":
                uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png"])
            elif creative_type == "Video":
                uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov"])

            title = st.text_input("Title")
            body = st.text_area("Body Text")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Upload")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if submit:
                st.success("Creative uploaded successfully!")
                st.session_state.show_upload_creative = False
                st.rerun()

            if cancel:
                st.session_state.show_upload_creative = False
                st.rerun()

    # Creatives gallery
    st.markdown("### Creative Library")
    st.info("Creative gallery will be displayed here")


def render_performance_tab():
    """Render performance analytics tab."""
    st.subheader("Performance Analytics")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")

    # KPIs
    st.markdown("### Key Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Spend", "$12,450", "-5%")

    with col2:
        st.metric("Impressions", "125.4K", "+12%")

    with col3:
        st.metric("Clicks", "3,456", "+8%")

    with col4:
        st.metric("Conversions", "189", "+15%")

    with col5:
        st.metric("ROAS", "4.2x", "+0.3x")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Spend vs Revenue")
        st.info("Chart will be displayed here")

    with col2:
        st.markdown("### Conversion Funnel")
        st.info("Chart will be displayed here")


def render_automation_tab():
    """Render automation tab."""
    st.subheader("Automated Rules & Optimization")

    if st.button("➕ Create Rule"):
        st.session_state.show_create_rule = True

    if st.session_state.get("show_create_rule", False):
        with st.form("create_rule_form"):
            st.subheader("Create Automated Rule")

            rule_name = st.text_input("Rule Name *")
            target_type = st.selectbox("Apply To", ["Campaign", "Ad Set", "Ad"])

            st.markdown("**Conditions**")
            condition_metric = st.selectbox("When", ["CPA", "ROAS", "CTR", "Spend"])
            condition_operator = st.selectbox("Is", ["Greater than", "Less than", "Equal to"])
            condition_value = st.number_input("Value", min_value=0.0)

            st.markdown("**Actions**")
            action_type = st.selectbox("Then", ["Pause", "Adjust Budget", "Send Alert"])

            if action_type == "Adjust Budget":
                adjustment = st.number_input("Adjustment (%)", min_value=-100, max_value=100)

            schedule = st.selectbox("Run", ["Hourly", "Daily", "Weekly"])

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Rule")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if submit:
                st.success("Automated rule created successfully!")
                st.session_state.show_create_rule = False
                st.rerun()

            if cancel:
                st.session_state.show_create_rule = False
                st.rerun()

    # Rules list
    st.markdown("### Active Rules")

    rules_data = {
        "Rule": ["Pause High CPA Campaigns", "Increase Budget for Top Performers", "Alert Low CTR"],
        "Target": ["Campaign", "Campaign", "Ad"],
        "Condition": ["CPA > $50", "ROAS > 5.0", "CTR < 1%"],
        "Action": ["Pause", "Increase Budget 20%", "Send Alert"],
        "Status": ["Active", "Active", "Active"],
        "Last Run": ["2 hours ago", "1 day ago", "3 hours ago"]
    }

    df = pd.DataFrame(rules_data)
    st.dataframe(df, use_container_width=True)
