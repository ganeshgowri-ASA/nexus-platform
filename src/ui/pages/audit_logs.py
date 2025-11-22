"""
Audit logs page
"""
import streamlit as st

API_URL = "http://localhost:8000"


def show():
    """Display audit logs page"""
    st.markdown('<p class="main-header">📝 Audit Logs</p>', unsafe_allow_html=True)

    st.info(
        "Audit logging system is in place. Direct API endpoints are available at `/api/v1/rpa/statistics/audit`"
    )

    st.markdown("### Audit Log Features")

    features = [
        "✅ All automation actions are logged",
        "✅ User activity tracking",
        "✅ Execution audit trails",
        "✅ Entity history tracking",
        "✅ Configurable retention policies",
    ]

    for feature in features:
        st.markdown(feature)

    st.markdown("---")

    st.markdown("### API Endpoints")

    st.code(
        """
# Get audit statistics
GET /api/v1/rpa/statistics/audit

# View logs via database models:
- AuditLog table contains all audit entries
- Filterable by: entity_type, entity_id, user_id, action, date range
    """,
        language="http",
    )

    st.markdown("---")

    st.markdown("### Recent Activity Summary")

    st.markdown(
        """
    Audit logs are being collected in the background. You can query them via:
    - Database directly
    - API endpoints
    - Custom reporting tools
    """
    )
