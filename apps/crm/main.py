"""CRM Application with Contacts, Deals, Pipeline"""


def main():
    import streamlit as st

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="CRM - NEXUS",
            page_icon="💼",
            layout="wide"
        )

        st.title("💼 Customer Relationship Management")

        # Session state
        if 'contacts' not in st.session_state:
            st.session_state.contacts = []
        if 'deals' not in st.session_state:
            st.session_state.deals = []
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'contacts'

        # Sidebar
        st.sidebar.title("💼 CRM")
        st.sidebar.subheader("Views")

        for label, mode in [("👥 Contacts", "contacts"), ("💰 Deals", "deals"), ("📊 Pipeline", "pipeline")]:
            if st.sidebar.button(label, key=f"view_{mode}", use_container_width=True):
                st.session_state.view_mode = mode
                st.rerun()

        st.sidebar.divider()
        st.sidebar.metric("Total Contacts", len(st.session_state.contacts))
        st.sidebar.metric("Active Deals", len(st.session_state.deals))

        # Main content
        if st.session_state.view_mode == 'contacts':
            st.subheader("👥 Contacts")

            with st.expander("➕ Add New Contact"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name")
                    last_name = st.text_input("Last Name")
                    email = st.text_input("Email")
                with col2:
                    company = st.text_input("Company")
                    phone = st.text_input("Phone")
                    job_title = st.text_input("Job Title")

                if st.button("Add Contact", type="primary"):
                    if first_name and last_name:
                        st.session_state.contacts.append({'first_name': first_name, 'last_name': last_name, 'email': email, 'company': company, 'phone': phone, 'job_title': job_title})
                        st.success("Contact added!")
                        st.rerun()

            for idx, contact in enumerate(st.session_state.contacts):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{contact['first_name']} {contact['last_name']}**")
                    st.caption(f"{contact.get('job_title', '')} @ {contact.get('company', '')}")
                with col2:
                    st.caption(f"📧 {contact.get('email', '')}")
                with col3:
                    if st.button("🗑️", key=f"del_contact_{idx}"):
                        st.session_state.contacts.pop(idx)
                        st.rerun()
                st.divider()

            if not st.session_state.contacts:
                st.info("No contacts yet. Add your first contact!")

        elif st.session_state.view_mode == 'deals':
            st.subheader("💰 Deals")

            with st.expander("➕ Add New Deal"):
                title = st.text_input("Deal Title")
                value = st.number_input("Value ($)", min_value=0)
                stage = st.selectbox("Stage", ["Lead", "Qualified", "Proposal", "Negotiation", "Won", "Lost"])

                if st.button("Add Deal", type="primary"):
                    if title:
                        st.session_state.deals.append({'title': title, 'value': value, 'stage': stage})
                        st.success("Deal added!")
                        st.rerun()

            for idx, deal in enumerate(st.session_state.deals):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{deal['title']}**")
                with col2:
                    st.write(f"${deal['value']:,.0f}")
                with col3:
                    st.caption(deal['stage'])
                st.divider()

            if not st.session_state.deals:
                st.info("No deals yet. Add your first deal!")

        elif st.session_state.view_mode == 'pipeline':
            st.subheader("📊 Sales Pipeline")
            stages = ["Lead", "Qualified", "Proposal", "Negotiation", "Won"]
            cols = st.columns(len(stages))

            for idx, stage in enumerate(stages):
                with cols[idx]:
                    st.markdown(f"### {stage}")
                    stage_deals = [d for d in st.session_state.deals if d['stage'] == stage]
                    st.metric("Deals", len(stage_deals))
                    st.metric("Value", f"${sum(d['value'] for d in stage_deals):,.0f}")

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
