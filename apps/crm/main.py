"""CRM Application with Contacts, Deals, Pipeline, Email Integration"""
import streamlit as st
from datetime import datetime, timedelta

# Lazy imports - will be imported inside main()
px = None
pd = None
SessionLocal = None
CRMContact = None
CRMDeal = None
CRMActivity = None
ClaudeClient = None
settings = None
CRM_DEAL_STAGES = None
CRM_CONTACT_TYPES = None


def _lazy_imports():
    """Import all dependencies lazily to avoid circular imports"""
    global px, pd, SessionLocal, CRMContact, CRMDeal, CRMActivity
    global ClaudeClient, settings, CRM_DEAL_STAGES, CRM_CONTACT_TYPES
    global format_currency, format_date, format_percentage

    import plotly.express as _px
    import pandas as _pd
    from database import init_database, get_session
    from database.models import CRMContact as _CRMContact, CRMDeal as _CRMDeal, CRMActivity as _CRMActivity
    from config.settings import settings as _settings
    from config.constants import CRM_DEAL_STAGES as _CRM_DEAL_STAGES, CRM_CONTACT_TYPES as _CRM_CONTACT_TYPES
    from utils.formatters import format_currency as _format_currency, format_date as _format_date, format_percentage as _format_percentage

    px = _px
    pd = _pd
    SessionLocal = get_session
    CRMContact = _CRMContact
    CRMDeal = _CRMDeal
    CRMActivity = _CRMActivity
    settings = _settings
    CRM_DEAL_STAGES = _CRM_DEAL_STAGES
    CRM_CONTACT_TYPES = _CRM_CONTACT_TYPES
    format_currency = _format_currency
    format_date = _format_date
    format_percentage = _format_percentage

    init_database()
    return get_session

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_contact' not in st.session_state:
        st.session_state.current_contact = None
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'contacts'

def render_sidebar():
    """Render sidebar with navigation"""
    st.sidebar.title("💼 CRM")

    # View selector
    st.sidebar.subheader("Views")
    views = {
        "Contacts": "contacts",
        "Deals": "deals",
        "Pipeline": "pipeline",
        "Activities": "activities"
    }

    for label, mode in views.items():
        if st.sidebar.button(label, key=f"view_{mode}", use_container_width=True):
            st.session_state.view_mode = mode
            st.rerun()

    st.sidebar.divider()

    # Quick stats
    st.sidebar.subheader("Quick Stats")

    db = SessionLocal()

    total_contacts = db.query(CRMContact).count()
    total_deals = db.query(CRMDeal).count()
    total_value = db.query(CRMDeal).filter(CRMDeal.stage.in_(['Proposal', 'Negotiation'])).with_entities(
        db.func.sum(CRMDeal.value)
    ).scalar() or 0

    st.sidebar.metric("Total Contacts", total_contacts)
    st.sidebar.metric("Active Deals", total_deals)
    st.sidebar.metric("Pipeline Value", format_currency(total_value))

    db.close()

    st.sidebar.divider()

    # Quick actions
    st.sidebar.subheader("Quick Actions")
    if st.sidebar.button("➕ New Contact", use_container_width=True):
        st.session_state.current_contact = None
        st.session_state.view_mode = 'contact_edit'
        st.rerun()

    if st.sidebar.button("➕ New Deal", use_container_width=True):
        st.session_state.view_mode = 'deal_edit'
        st.rerun()

def render_contacts_view(db):
    """Render contacts list view"""
    st.subheader("👥 Contacts")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        search_query = st.text_input("🔍 Search", placeholder="Name, email, company...")

    with col2:
        contact_type_filter = st.selectbox("Type", ["All"] + CRM_CONTACT_TYPES)

    with col3:
        sort_by = st.selectbox("Sort by", ["Name", "Company", "Recent"])

    # Build query
    query = db.query(CRMContact)

    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            (CRMContact.first_name.like(search_term)) |
            (CRMContact.last_name.like(search_term)) |
            (CRMContact.email.like(search_term)) |
            (CRMContact.company.like(search_term))
        )

    if contact_type_filter != "All":
        query = query.filter(CRMContact.contact_type == contact_type_filter)

    # Apply sorting
    if sort_by == "Name":
        query = query.order_by(CRMContact.first_name)
    elif sort_by == "Company":
        query = query.order_by(CRMContact.company)
    else:
        query = query.order_by(CRMContact.updated_at.desc())

    contacts = query.all()

    # Display contacts
    if contacts:
        for contact in contacts:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    full_name = f"{contact.first_name} {contact.last_name}"
                    if st.button(f"👤 {full_name}", key=f"contact_{contact.id}",
                               use_container_width=True):
                        st.session_state.current_contact = contact.id
                        st.session_state.view_mode = 'contact_view'
                        st.rerun()

                    if contact.job_title or contact.company:
                        st.caption(f"{contact.job_title or ''} @ {contact.company or ''}")

                with col2:
                    if contact.email:
                        st.caption(f"📧 {contact.email}")
                    if contact.phone:
                        st.caption(f"📞 {contact.phone}")

                with col3:
                    st.caption(f"🏷️ {contact.contact_type}")

                with col4:
                    if st.button("✉️", key=f"email_{contact.id}"):
                        st.info(f"Email to {contact.email}")

                    if st.button("🗑️", key=f"del_contact_{contact.id}"):
                        db.query(CRMDeal).filter(CRMDeal.contact_id == contact.id).delete()
                        db.query(CRMActivity).filter(CRMActivity.contact_id == contact.id).delete()
                        db.delete(contact)
                        db.commit()
                        st.rerun()

                st.divider()

        # Export button
        if st.button("📊 Export to Excel"):
            contacts_data = [
                {
                    'Name': f"{c.first_name} {c.last_name}",
                    'Email': c.email,
                    'Phone': c.phone,
                    'Company': c.company,
                    'Job Title': c.job_title,
                    'Type': c.contact_type,
                    'Owner': c.owner
                }
                for c in contacts
            ]

            output_path = settings.EXPORTS_DIR / f"contacts_{datetime.now().strftime('%Y%m%d')}.xlsx"
            export_to_xlsx(contacts_data, str(output_path), "Contacts")

            with open(output_path, 'rb') as f:
                st.download_button(
                    "⬇️ Download Excel",
                    f,
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    else:
        st.info("No contacts found")

def render_contact_detail(db, contact_id):
    """Render contact detail view"""
    contact = db.query(CRMContact).filter(CRMContact.id == contact_id).first()

    if not contact:
        st.error("Contact not found")
        return

    # Back button
    if st.button("← Back to Contacts"):
        st.session_state.current_contact = None
        st.session_state.view_mode = 'contacts'
        st.rerun()

    # Contact header
    st.title(f"👤 {contact.first_name} {contact.last_name}")

    # Contact info
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Contact Information")
        contact.first_name = st.text_input("First Name", value=contact.first_name)
        contact.last_name = st.text_input("Last Name", value=contact.last_name)
        contact.email = st.text_input("Email", value=contact.email or "")
        contact.phone = st.text_input("Phone", value=contact.phone or "")

    with col2:
        st.subheader("Professional Information")
        contact.company = st.text_input("Company", value=contact.company or "")
        contact.job_title = st.text_input("Job Title", value=contact.job_title or "")
        contact.contact_type = st.selectbox("Type", CRM_CONTACT_TYPES,
                                           index=CRM_CONTACT_TYPES.index(contact.contact_type) if contact.contact_type in CRM_CONTACT_TYPES else 0)
        contact.owner = st.text_input("Owner", value=contact.owner or "")

    # Additional info
    contact.address = st.text_area("Address", value=contact.address or "", height=80)
    contact.notes = st.text_area("Notes", value=contact.notes or "", height=100)

    # Social links
    col1, col2, col3 = st.columns(3)
    with col1:
        contact.linkedin_url = st.text_input("LinkedIn", value=contact.linkedin_url or "")
    with col2:
        contact.twitter_url = st.text_input("Twitter", value=contact.twitter_url or "")
    with col3:
        contact.website = st.text_input("Website", value=contact.website or "")

    # Tags
    tags_input = st.text_input("Tags (comma-separated)",
                              value=", ".join(contact.tags) if contact.tags else "")
    contact.tags = [t.strip() for t in tags_input.split(',') if t.strip()]

    # Save button
    if st.button("💾 Save Changes", type="primary"):
        db.commit()
        st.success("Contact updated!")

    st.divider()

    # Deals
    st.subheader("💰 Deals")
    deals = db.query(CRMDeal).filter(CRMDeal.contact_id == contact_id).all()

    if deals:
        for deal in deals:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"**{deal.title}**")

            with col2:
                st.write(format_currency(deal.value or 0))

            with col3:
                st.write(deal.stage)

            with col4:
                st.write(format_percentage(deal.probability or 0))

    else:
        st.info("No deals associated with this contact")

    if st.button("➕ Add Deal"):
        st.session_state.new_deal_contact = contact_id
        st.session_state.view_mode = 'deal_edit'
        st.rerun()

    st.divider()

    # Activities
    st.subheader("📋 Activities")
    activities = db.query(CRMActivity).filter(CRMActivity.contact_id == contact_id).order_by(
        CRMActivity.created_at.desc()
    ).limit(10).all()

    if activities:
        for activity in activities:
            icon = {'Email': '📧', 'Call': '📞', 'Meeting': '👥', 'Note': '📝'}.get(activity.activity_type, '📋')
            status = "✅" if activity.is_completed else "⬜"

            st.write(f"{status} {icon} {activity.subject} - {format_date(activity.created_at)}")

    # AI Suggestions
    if settings.ENABLE_AI_FEATURES:
        with st.expander("🤖 AI Suggestions"):
            if st.button("Get Next Steps", type="primary"):
                try:
                    with st.spinner("Analyzing..."):
                        ai_client = ClaudeClient()
                        contact_info = f"{contact.first_name} {contact.last_name}, {contact.job_title} at {contact.company}"
                        deal_stage = deals[0].stage if deals else "Lead"
                        suggestions = ai_client.suggest_crm_next_steps(contact_info, deal_stage)

                        st.write("**Suggested Next Steps:**")
                        for suggestion in suggestions:
                            st.write(f"• {suggestion}")
                except Exception as e:
                    st.error(f"Error: {e}")

def render_pipeline_view(db):
    """Render pipeline/deals view"""
    st.subheader("💰 Sales Pipeline")

    deals = db.query(CRMDeal).all()

    if not deals:
        st.info("No deals in pipeline")
        return

    # Pipeline visualization
    stage_counts = {}
    stage_values = {}

    for deal in deals:
        stage = deal.stage
        if stage not in stage_counts:
            stage_counts[stage] = 0
            stage_values[stage] = 0
        stage_counts[stage] += 1
        stage_values[stage] += deal.value or 0

    # Create columns for each stage
    stages = CRM_DEAL_STAGES
    cols = st.columns(len(stages))

    for idx, stage in enumerate(stages):
        with cols[idx]:
            st.markdown(f"### {stage}")
            count = stage_counts.get(stage, 0)
            value = stage_values.get(stage, 0)

            st.metric("Deals", count)
            st.metric("Value", format_currency(value))

            st.markdown("---")

            # Show deals in this stage
            stage_deals = [d for d in deals if d.stage == stage]
            for deal in stage_deals[:3]:  # Show max 3
                if st.button(f"{deal.title}\n{format_currency(deal.value or 0)}",
                           key=f"pipeline_deal_{deal.id}",
                           use_container_width=True):
                    st.info(f"Deal: {deal.title}")

            if len(stage_deals) > 3:
                st.caption(f"+ {len(stage_deals) - 3} more")

    st.divider()

    # Pipeline chart
    if deals:
        df = pd.DataFrame([
            {
                'Stage': deal.stage,
                'Value': deal.value or 0,
                'Deal': deal.title
            }
            for deal in deals
        ])

        fig = px.funnel(df, x='Value', y='Stage', color='Stage')
        st.plotly_chart(fig, use_container_width=True)

def render_deals_list(db):
    """Render deals list"""
    st.subheader("💰 All Deals")

    deals = db.query(CRMDeal).order_by(CRMDeal.created_at.desc()).all()

    if deals:
        for deal in deals:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

                with col1:
                    st.write(f"**{deal.title}**")
                    if deal.description:
                        st.caption(deal.description[:50] + "..." if len(deal.description) > 50 else deal.description)

                with col2:
                    contact = db.query(CRMContact).filter(CRMContact.id == deal.contact_id).first()
                    if contact:
                        st.caption(f"👤 {contact.first_name} {contact.last_name}")

                with col3:
                    st.write(format_currency(deal.value or 0))

                with col4:
                    st.write(deal.stage)

                with col5:
                    st.write(format_percentage(deal.probability or 0))

                st.divider()
    else:
        st.info("No deals found")

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="CRM - NEXUS",
        page_icon="💼",
        layout="wide"
    )

    try:
        # Lazy import all dependencies
        get_session = _lazy_imports()

        # Initialize session state
        initialize_session_state()

        # Render sidebar
        render_sidebar()

        # Render main content
        st.title("💼 Customer Relationship Management")

        db = get_session()

        if st.session_state.view_mode == 'contacts':
            render_contacts_view(db)
        elif st.session_state.view_mode == 'contact_view' and st.session_state.current_contact:
            render_contact_detail(db, st.session_state.current_contact)
        elif st.session_state.view_mode == 'pipeline':
            render_pipeline_view(db)
        elif st.session_state.view_mode == 'deals':
            render_deals_list(db)
        elif st.session_state.view_mode == 'contact_edit':
            # New contact form
            st.subheader("➕ Add New Contact")

            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name*")
                last_name = st.text_input("Last Name*")
                email = st.text_input("Email")
                phone = st.text_input("Phone")

            with col2:
                company = st.text_input("Company")
                job_title = st.text_input("Job Title")
                contact_type = st.selectbox("Type", CRM_CONTACT_TYPES)
                owner = st.text_input("Owner")

            if st.button("Add Contact", type="primary"):
                if first_name and last_name:
                    contact = CRMContact(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        company=company,
                        job_title=job_title,
                        contact_type=contact_type,
                        owner=owner
                    )
                    db.add(contact)
                    db.commit()
                    st.success("Contact added!")
                    st.session_state.view_mode = 'contacts'
                    st.rerun()
                else:
                    st.error("Please fill in required fields")

        db.close()

    except Exception as e:
        st.error(f"Error in CRM module: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
