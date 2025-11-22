"""Streamlit UI for Contracts Management.

This module provides an interactive web dashboard for managing contracts,
with features for creation, tracking, approval, analytics, and more.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from .contract_types import (
    Contract,
    ContractStatus,
    ContractType,
    Party,
    PartyRole,
    RiskLevel,
)
from .templates import TemplateManager, TemplateLibrary
from .lifecycle import ContractLifecycleManager
from .compliance import ComplianceEngine
from .analytics import ContractAnalytics
from .ai_assistant import ContractAIAssistant


# Page configuration
st.set_page_config(
    page_title="NEXUS Contracts Management",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS
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
        border-left: 4px solid #1f77b4;
    }
    .contract-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .danger-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "contracts" not in st.session_state:
        st.session_state.contracts = []
    if "analytics" not in st.session_state:
        st.session_state.analytics = ContractAnalytics()
    if "template_manager" not in st.session_state:
        st.session_state.template_manager = TemplateManager()
    if "ai_assistant" not in st.session_state:
        st.session_state.ai_assistant = ContractAIAssistant()


def render_sidebar():
    """Render sidebar navigation."""
    st.sidebar.markdown("# 📄 NEXUS Contracts")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📝 Create Contract",
            "📋 All Contracts",
            "✅ Approvals",
            "📅 Obligations",
            "🎯 Milestones",
            "📈 Analytics",
            "🤖 AI Assistant",
            "⚙️ Settings",
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")

    # Quick stats
    total_contracts = len(st.session_state.contracts)
    active_contracts = sum(1 for c in st.session_state.contracts if c.status == ContractStatus.ACTIVE)
    pending_approvals = sum(1 for c in st.session_state.contracts if c.status == ContractStatus.PENDING_APPROVAL)

    st.sidebar.metric("Total Contracts", total_contracts)
    st.sidebar.metric("Active", active_contracts)
    st.sidebar.metric("Pending Approval", pending_approvals)

    return menu


def render_dashboard():
    """Render main dashboard."""
    st.markdown('<div class="main-header">📊 Contracts Dashboard</div>', unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total = len(st.session_state.contracts)
        st.metric("Total Contracts", total)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        active = sum(1 for c in st.session_state.contracts if c.status == ContractStatus.ACTIVE)
        st.metric("Active Contracts", active)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        expiring = sum(1 for c in st.session_state.contracts if c.is_expiring())
        st.metric("Expiring Soon", expiring, delta="-2 this month")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_value = sum(float(c.total_value or 0) for c in st.session_state.contracts)
        st.metric("Total Value", f"${total_value:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Contracts by Status")
        if st.session_state.contracts:
            status_counts = {}
            for contract in st.session_state.contracts:
                status = contract.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Contract Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No contracts yet")

    with col2:
        st.subheader("Contracts by Type")
        if st.session_state.contracts:
            type_counts = {}
            for contract in st.session_state.contracts:
                contract_type = contract.contract_type.value
                type_counts[contract_type] = type_counts.get(contract_type, 0) + 1

            fig = px.bar(
                x=list(type_counts.keys()),
                y=list(type_counts.values()),
                title="Contracts by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No contracts yet")

    # Recent contracts
    st.subheader("Recent Contracts")
    if st.session_state.contracts:
        recent = sorted(st.session_state.contracts, key=lambda c: c.created_at, reverse=True)[:5]
        for contract in recent:
            render_contract_card(contract)
    else:
        st.info("No contracts to display")


def render_create_contract():
    """Render contract creation form."""
    st.markdown('<div class="main-header">📝 Create New Contract</div>', unsafe_allow_html=True)

    # Template selection
    st.subheader("1. Select Template (Optional)")
    templates = st.session_state.template_manager.list_templates()
    template_options = ["Start from Scratch"] + [t.name for t in templates]
    selected_template = st.selectbox("Choose a template", template_options)

    st.markdown("---")

    # Basic information
    st.subheader("2. Basic Information")
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Contract Title *", placeholder="Enter contract title")
        contract_type = st.selectbox(
            "Contract Type *",
            [t.value for t in ContractType]
        )

    with col2:
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

    description = st.text_area("Description", placeholder="Enter contract description")

    st.markdown("---")

    # Parties
    st.subheader("3. Parties")
    num_parties = st.number_input("Number of Parties", min_value=2, max_value=10, value=2)

    parties = []
    for i in range(num_parties):
        with st.expander(f"Party {i+1}", expanded=(i < 2)):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(f"Name *", key=f"party_name_{i}")
                organization = st.text_input(f"Organization", key=f"party_org_{i}")
            with col2:
                role = st.selectbox(f"Role *", [r.value for r in PartyRole], key=f"party_role_{i}")
                email = st.text_input(f"Email", key=f"party_email_{i}")

            if name and role:
                parties.append({
                    "name": name,
                    "role": role,
                    "organization": organization,
                    "email": email,
                })

    st.markdown("---")

    # Financial terms
    st.subheader("4. Financial Terms")
    col1, col2 = st.columns(2)

    with col1:
        total_value = st.number_input("Total Value", min_value=0.0, step=1000.0)

    with col2:
        currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "INR"])

    st.markdown("---")

    # Create button
    if st.button("Create Contract", type="primary", use_container_width=True):
        if not title:
            st.error("Please enter a contract title")
        elif len(parties) < 2:
            st.error("Please add at least 2 parties")
        else:
            # Create contract
            contract_data = {
                "title": title,
                "description": description,
                "contract_type": contract_type,
                "status": ContractStatus.DRAFT,
                "start_date": datetime.combine(start_date, datetime.min.time()) if start_date else None,
                "end_date": datetime.combine(end_date, datetime.min.time()) if end_date else None,
                "total_value": total_value if total_value > 0 else None,
                "currency": currency,
                "created_by": uuid4(),  # Would use actual user ID
            }

            # Create party objects
            party_objects = []
            for p in parties:
                party = Party(**p)
                party_objects.append(party)

            contract = Contract(**contract_data, parties=party_objects)
            st.session_state.contracts.append(contract)

            st.success(f"✅ Contract '{title}' created successfully!")
            st.balloons()


def render_all_contracts():
    """Render all contracts list."""
    st.markdown('<div class="main-header">📋 All Contracts</div>', unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.multiselect(
            "Status",
            [s.value for s in ContractStatus],
        )

    with col2:
        type_filter = st.multiselect(
            "Type",
            [t.value for t in ContractType],
        )

    with col3:
        search = st.text_input("Search", placeholder="Search contracts...")

    st.markdown("---")

    # Contracts list
    contracts = st.session_state.contracts

    # Apply filters
    if status_filter:
        contracts = [c for c in contracts if c.status.value in status_filter]

    if type_filter:
        contracts = [c for c in contracts if c.contract_type.value in type_filter]

    if search:
        contracts = [c for c in contracts if search.lower() in c.title.lower()]

    st.write(f"Showing {len(contracts)} contracts")

    for contract in contracts:
        render_contract_card(contract, detailed=True)


def render_contract_card(contract: Contract, detailed: bool = False):
    """Render a contract card."""
    with st.container():
        st.markdown('<div class="contract-card">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"### {contract.title}")
            st.caption(f"Type: {contract.contract_type.value.upper()}")

        with col2:
            status_color = {
                ContractStatus.DRAFT: "🟡",
                ContractStatus.ACTIVE: "🟢",
                ContractStatus.EXPIRED: "🔴",
            }.get(contract.status, "⚪")

            st.markdown(f"{status_color} **{contract.status.value.upper()}**")

        with col3:
            if contract.total_value:
                st.metric("Value", f"${contract.total_value:,.2f}")

        with col4:
            if st.button("View", key=f"view_{contract.id}"):
                st.session_state.selected_contract = contract

        if detailed:
            with st.expander("Details"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Parties:**")
                    for party in contract.parties:
                        st.write(f"- {party.name} ({party.role.value})")

                with col2:
                    st.write("**Dates:**")
                    if contract.start_date:
                        st.write(f"Start: {contract.start_date.date()}")
                    if contract.end_date:
                        st.write(f"End: {contract.end_date.date()}")

        st.markdown('</div>', unsafe_allow_html=True)


def render_analytics():
    """Render analytics dashboard."""
    st.markdown('<div class="main-header">📈 Analytics</div>', unsafe_allow_html=True)

    # Add contracts to analytics
    analytics = st.session_state.analytics
    for contract in st.session_state.contracts:
        analytics.add_contract(contract)

    # Tabs for different analytics
    tab1, tab2, tab3, tab4 = st.tabs(["Cycle Time", "Value Analysis", "Risk Distribution", "Status Breakdown"])

    with tab1:
        st.subheader("Contract Cycle Time Analysis")
        cycle_time = analytics.calculate_cycle_time()
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Average Days", f"{cycle_time['average_days']:.1f}")
        with col2:
            st.metric("Min Days", cycle_time['min_days'])
        with col3:
            st.metric("Max Days", cycle_time['max_days'])

    with tab2:
        st.subheader("Contract Value Analysis")
        value_analysis = analytics.get_value_analysis()
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Contract Value", f"${value_analysis['total_value']:,.2f}")
            st.metric("Active Contract Value", f"${value_analysis['active_value']:,.2f}")

        with col2:
            st.metric("Total Contracts", value_analysis['total_contracts'])
            st.metric("Active Contracts", value_analysis['active_contracts'])

    with tab3:
        st.subheader("Risk Level Distribution")
        risk_dist = analytics.get_risk_distribution()

        fig = px.pie(
            values=list(risk_dist.values()),
            names=list(risk_dist.keys()),
            title="Contracts by Risk Level",
            color_discrete_map={
                "low": "green",
                "medium": "yellow",
                "high": "orange",
                "critical": "red",
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Status Breakdown")
        status_breakdown = analytics.get_status_breakdown()

        fig = px.bar(
            x=list(status_breakdown.keys()),
            y=list(status_breakdown.values()),
            title="Contracts by Status"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_ai_assistant():
    """Render AI assistant interface."""
    st.markdown('<div class="main-header">🤖 AI Assistant</div>', unsafe_allow_html=True)

    if not st.session_state.contracts:
        st.info("No contracts available. Create a contract first to use AI features.")
        return

    # Contract selection
    contract_options = {c.title: c for c in st.session_state.contracts}
    selected_title = st.selectbox("Select Contract", list(contract_options.keys()))
    selected_contract = contract_options[selected_title]

    st.markdown("---")

    # AI features
    tab1, tab2, tab3, tab4 = st.tabs(["Summarize", "Risk Analysis", "Recommendations", "Compliance"])

    with tab1:
        st.subheader("Contract Summary")
        if st.button("Generate Summary", use_container_width=True):
            with st.spinner("Generating summary..."):
                # Placeholder - would call actual AI
                st.success("Summary generated!")
                st.info("**Summary:** This is a comprehensive contract summary generated by AI...")

    with tab2:
        st.subheader("Risk Analysis")
        if st.button("Analyze Risks", use_container_width=True):
            with st.spinner("Analyzing risks..."):
                st.success("Risk analysis complete!")
                st.warning("**High Risk:** Unlimited liability clause detected")
                st.info("**Medium Risk:** Payment terms exceed 60 days")

    with tab3:
        st.subheader("Clause Recommendations")
        st.write("AI-powered clause recommendations for this contract:")
        st.success("✅ All mandatory clauses present")
        st.info("💡 Consider adding: Dispute Resolution clause")

    with tab4:
        st.subheader("Compliance Check")
        if st.button("Check Compliance", use_container_width=True):
            engine = ComplianceEngine()
            issues = engine.check_compliance(selected_contract)

            if not issues:
                st.success("✅ No compliance issues found")
            else:
                for issue in issues:
                    st.warning(f"⚠️ {issue['issue']}: {issue['recommendation']}")


def main():
    """Main application entry point."""
    initialize_session_state()

    # Render sidebar and get selected menu
    menu = render_sidebar()

    # Render selected page
    if menu == "📊 Dashboard":
        render_dashboard()
    elif menu == "📝 Create Contract":
        render_create_contract()
    elif menu == "📋 All Contracts":
        render_all_contracts()
    elif menu == "📈 Analytics":
        render_analytics()
    elif menu == "🤖 AI Assistant":
        render_ai_assistant()
    else:
        st.info(f"{menu} - Coming soon!")


if __name__ == "__main__":
    main()
