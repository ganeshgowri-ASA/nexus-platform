"""
Lead Generation UI module.
"""
import streamlit as st
import httpx
import pandas as pd
from datetime import datetime


API_BASE_URL = "http://localhost:8000/api/lead-generation"


def render_lead_generation():
    """Render lead generation module UI."""
    st.markdown('<p class="main-header">Lead Generation</p>', unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Leads", "Forms", "Landing Pages", "Chatbot", "Analytics"
    ])

    with tab1:
        render_leads_tab()

    with tab2:
        render_forms_tab()

    with tab3:
        render_landing_pages_tab()

    with tab4:
        render_chatbot_tab()

    with tab5:
        render_analytics_tab()


def render_leads_tab():
    """Render leads management tab."""
    st.subheader("Lead Management")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "New", "Contacted", "Qualified", "Unqualified", "Converted"]
        )

    with col2:
        source_filter = st.selectbox(
            "Source",
            ["All", "Form", "Landing Page", "Chatbot", "Manual"]
        )

    with col3:
        grade_filter = st.selectbox(
            "Grade",
            ["All", "A+", "A", "B+", "B", "C+", "C", "D", "F"]
        )

    with col4:
        qualified_filter = st.selectbox(
            "Qualified",
            ["All", "Yes", "No"]
        )

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ New Lead"):
            st.session_state.show_add_lead = True

    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Add lead form
    if st.session_state.get("show_add_lead", False):
        with st.form("add_lead_form"):
            st.subheader("Add New Lead")

            col1, col2 = st.columns(2)

            with col1:
                email = st.text_input("Email *", placeholder="john@example.com")
                first_name = st.text_input("First Name", placeholder="John")
                company = st.text_input("Company", placeholder="Acme Corp")

            with col2:
                phone = st.text_input("Phone", placeholder="+1234567890")
                last_name = st.text_input("Last Name", placeholder="Doe")
                job_title = st.text_input("Job Title", placeholder="CEO")

            source = st.selectbox("Source", ["form", "landing_page", "chatbot", "manual"])

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Lead")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if submit:
                if not email:
                    st.error("Email is required")
                else:
                    # Create lead via API
                    st.success(f"Lead created: {email}")
                    st.session_state.show_add_lead = False
                    st.rerun()

            if cancel:
                st.session_state.show_add_lead = False
                st.rerun()

    # Leads table
    st.markdown("### Leads")

    # Placeholder data
    leads_data = {
        "Email": ["john@example.com", "jane@example.com", "bob@example.com"],
        "Name": ["John Doe", "Jane Smith", "Bob Johnson"],
        "Company": ["Acme Corp", "TechCo", "StartupXYZ"],
        "Score": [85, 72, 90],
        "Grade": ["A", "B+", "A+"],
        "Status": ["Qualified", "New", "Converted"],
        "Created": ["2024-01-15", "2024-01-16", "2024-01-14"]
    }

    df = pd.DataFrame(leads_data)
    st.dataframe(df, use_container_width=True)


def render_forms_tab():
    """Render forms management tab."""
    st.subheader("Lead Capture Forms")

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("➕ New Form"):
            st.session_state.show_form_builder = True

    if st.session_state.get("show_form_builder", False):
        st.markdown("### Form Builder")

        with st.form("form_builder"):
            form_name = st.text_input("Form Name *", placeholder="Contact Form")
            form_type = st.selectbox("Form Type", ["Inline", "Popup", "Slide-in", "Embedded"])

            st.markdown("**Fields**")

            # Field builder
            num_fields = st.number_input("Number of Fields", min_value=1, max_value=20, value=3)

            fields = []
            for i in range(num_fields):
                col1, col2, col3 = st.columns(3)
                with col1:
                    field_name = st.text_input(f"Field {i+1} Name", key=f"field_name_{i}")
                with col2:
                    field_type = st.selectbox(
                        f"Type",
                        ["text", "email", "phone", "textarea", "select"],
                        key=f"field_type_{i}"
                    )
                with col3:
                    required = st.checkbox("Required", key=f"field_req_{i}")

            thank_you_message = st.text_area("Thank You Message")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Form")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if submit:
                st.success("Form created successfully!")
                st.session_state.show_form_builder = False
                st.rerun()

            if cancel:
                st.session_state.show_form_builder = False
                st.rerun()

    # Forms list
    st.markdown("### Your Forms")

    forms_data = {
        "Name": ["Contact Form", "Newsletter Signup", "Demo Request"],
        "Type": ["Inline", "Popup", "Embedded"],
        "Submissions": [45, 128, 67],
        "Conversion Rate": ["12.5%", "8.3%", "15.2%"],
        "Status": ["Active", "Active", "Paused"]
    }

    df = pd.DataFrame(forms_data)
    st.dataframe(df, use_container_width=True)


def render_landing_pages_tab():
    """Render landing pages tab."""
    st.subheader("Landing Pages")
    st.info("Landing page builder will be available here")


def render_chatbot_tab():
    """Render chatbot tab."""
    st.subheader("AI Chatbot Lead Capture")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Chat Conversation")

        # Chat messages
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "bot", "content": "Hi! Welcome to NEXUS. How can I help you today?"}
            ]

        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Bot:** {message['content']}")

        # Chat input
        user_input = st.text_input("Type your message...", key="chat_input")

        if st.button("Send") and user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            # Call chatbot API here
            bot_response = "Thank you for your message! How can I assist you further?"
            st.session_state.messages.append({"role": "bot", "content": bot_response})
            st.rerun()

    with col2:
        st.markdown("### Chatbot Settings")
        enable_chatbot = st.checkbox("Enable Chatbot", value=True)
        greeting_message = st.text_area("Greeting Message", value="Hi! Welcome to NEXUS.")
        ai_model = st.selectbox("AI Model", ["Claude 3.5 Sonnet", "GPT-4", "GPT-3.5"])

        if st.button("Save Settings"):
            st.success("Settings saved!")


def render_analytics_tab():
    """Render analytics tab."""
    st.subheader("Lead Generation Analytics")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Leads", "1,234", "+12%")

    with col2:
        st.metric("Qualified Leads", "456", "+18%")

    with col3:
        st.metric("Conversion Rate", "8.5%", "+1.2%")

    with col4:
        st.metric("Avg Lead Score", "72", "+5")

    st.markdown("---")

    # Charts placeholder
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Leads by Source")
        st.info("Chart will be displayed here")

    with col2:
        st.markdown("### Lead Quality Distribution")
        st.info("Chart will be displayed here")
