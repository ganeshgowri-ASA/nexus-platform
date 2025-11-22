"""
NEXUS Platform - Unified AI-Powered Productivity Platform
A comprehensive enterprise platform with 73+ integrated modules.
"""

import streamlit as st
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="NEXUS Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ganeshgowri-ASA/nexus-platform',
        'Report a bug': 'https://github.com/ganeshgowri-ASA/nexus-platform/issues',
        'About': 'NEXUS Platform - Enterprise Productivity Suite v1.0.0'
    }
)

# Module categories and their modules
MODULE_CATEGORIES: Dict[str, List[Dict]] = {
    "Productivity Suite": [
        {"name": "Word Processor", "icon": "📝", "module": "modules.word", "desc": "Document editing with AI"},
        {"name": "Excel Editor", "icon": "📊", "module": "modules.excel", "desc": "Spreadsheet analysis"},
        {"name": "Presentation", "icon": "📽️", "module": "modules.presentation", "desc": "Create presentations"},
        {"name": "Notes", "icon": "📒", "module": "modules.notes", "desc": "Note-taking"},
        {"name": "Email Client", "icon": "📧", "module": "modules.email_client", "desc": "Email management"},
    ],
    "Communication": [
        {"name": "Chat & Messaging", "icon": "💬", "module": "modules.chat", "desc": "Team messaging"},
        {"name": "Video Conferencing", "icon": "🎥", "module": "modules.video", "desc": "HD video meetings"},
        {"name": "Voice Assistant", "icon": "🎤", "module": "modules.voice", "desc": "Voice commands"},
    ],
    "Content & Knowledge": [
        {"name": "Wiki System", "icon": "📚", "module": "modules.wiki", "desc": "Knowledge base"},
        {"name": "Knowledge Base", "icon": "🧠", "module": "modules.knowledge_base", "desc": "AI knowledge mgmt"},
        {"name": "Document Management", "icon": "📁", "module": "modules.documents", "desc": "Enterprise DMS"},
        {"name": "File Manager", "icon": "📂", "module": "modules.files", "desc": "File storage"},
    ],
    "Project & Workflow": [
        {"name": "Project Management", "icon": "📋", "module": "modules.projects", "desc": "Kanban, Gantt"},
        {"name": "CRM", "icon": "🤝", "module": "modules.crm", "desc": "Customer management"},
        {"name": "Workflow Automation", "icon": "⚡", "module": "modules.workflows", "desc": "Business automation"},
        {"name": "Calendar", "icon": "📅", "module": "modules.calendar", "desc": "Scheduling"},
        {"name": "Contracts", "icon": "📄", "module": "modules.contracts", "desc": "Contract management"},
    ],
    "Analytics & Reports": [
        {"name": "Analytics Dashboard", "icon": "📈", "module": "modules.analytics", "desc": "Business intelligence"},
        {"name": "Report Builder", "icon": "📊", "module": "modules.reports", "desc": "Custom reports"},
        {"name": "Dashboard Builder", "icon": "🎛️", "module": "modules.dashboards", "desc": "Visual dashboards"},
        {"name": "Attribution", "icon": "🎯", "module": "modules.attribution", "desc": "Marketing attribution"},
        {"name": "A/B Testing", "icon": "🔬", "module": "modules.ab_testing", "desc": "Experiment optimization"},
    ],
    "Marketing Suite": [
        {"name": "Social Media Manager", "icon": "📱", "module": "modules.social_media", "desc": "Social management"},
        {"name": "SEO Tools", "icon": "🔍", "module": "modules.seo", "desc": "Search optimization"},
        {"name": "Content Calendar", "icon": "🗓️", "module": "modules.content_calendar", "desc": "Content planning"},
        {"name": "Marketing Automation", "icon": "🤖", "module": "modules.marketing", "desc": "Auto campaigns"},
        {"name": "Campaign Manager", "icon": "📣", "module": "modules.campaigns", "desc": "Campaign management"},
        {"name": "Lead Generation", "icon": "🎣", "module": "modules.lead_generation", "desc": "Lead capture"},
        {"name": "Advertising", "icon": "📺", "module": "modules.advertising", "desc": "Ad campaigns"},
    ],
    "AI & Automation": [
        {"name": "AI Orchestrator", "icon": "🧠", "module": "modules.ai", "desc": "AI workflow orchestration"},
        {"name": "AI Automation", "icon": "⚙️", "module": "modules.ai_automation", "desc": "AI-powered automation"},
        {"name": "Translation", "icon": "🌐", "module": "modules.translation", "desc": "Multi-language"},
        {"name": "OCR", "icon": "👁️", "module": "modules.ocr", "desc": "Character recognition"},
        {"name": "Speech to Text", "icon": "🎙️", "module": "modules.speech_to_text", "desc": "Transcription"},
        {"name": "Image Recognition", "icon": "🖼️", "module": "modules.image_recognition", "desc": "Image analysis"},
    ],
    "Integration & ETL": [
        {"name": "ETL Pipeline", "icon": "🔄", "module": "modules.etl", "desc": "Data transformation"},
        {"name": "Integration Hub", "icon": "🔌", "module": "modules.integration_hub", "desc": "Third-party integrations"},
        {"name": "Webhooks", "icon": "🪝", "module": "modules.webhooks", "desc": "Webhook management"},
        {"name": "API Gateway", "icon": "🚪", "module": "modules.api_gateway", "desc": "API management"},
        {"name": "API Builder", "icon": "🛠️", "module": "modules.api_builder", "desc": "Build custom APIs"},
    ],
    "Process Automation": [
        {"name": "RPA", "icon": "🤖", "module": "modules.rpa", "desc": "Robotic automation"},
        {"name": "Browser Automation", "icon": "🌐", "module": "modules.browser_automation", "desc": "Web automation"},
        {"name": "Scheduler", "icon": "⏰", "module": "modules.scheduler", "desc": "Task scheduling"},
        {"name": "Orchestration", "icon": "🎭", "module": "modules.orchestration", "desc": "Workflow orchestration"},
        {"name": "Batch Processing", "icon": "📦", "module": "modules.batch_processing", "desc": "Batch jobs"},
        {"name": "Pipeline", "icon": "🔗", "module": "modules.pipeline", "desc": "Data pipelines"},
    ],
    "Business Management": [
        {"name": "Accounting", "icon": "💰", "module": "modules.accounting", "desc": "Financial management"},
        {"name": "HR Management", "icon": "👥", "module": "modules.hr", "desc": "Human resources"},
        {"name": "Payroll", "icon": "💵", "module": "modules.payroll", "desc": "Payroll processing"},
        {"name": "Inventory", "icon": "📦", "module": "modules.inventory", "desc": "Inventory management"},
        {"name": "E-Commerce", "icon": "🛒", "module": "modules.ecommerce", "desc": "Online store"},
        {"name": "LMS", "icon": "🎓", "module": "modules.lms", "desc": "Learning management"},
    ],
    "Web & Forms": [
        {"name": "Website Builder", "icon": "🌐", "module": "modules.website", "desc": "Build websites"},
        {"name": "Forms & Surveys", "icon": "📝", "module": "modules.forms", "desc": "Forms and surveys"},
        {"name": "Database Manager", "icon": "🗄️", "module": "modules.database", "desc": "Database management"},
    ],
    "Visualization": [
        {"name": "Flowcharts", "icon": "📐", "module": "modules.flowchart", "desc": "Create flowcharts"},
        {"name": "Mind Maps", "icon": "🧩", "module": "modules.mindmap", "desc": "Brainstorming"},
        {"name": "Infographics", "icon": "📊", "module": "modules.infographics", "desc": "Design infographics"},
    ],
    "Testing & Quality": [
        {"name": "Testing & QA", "icon": "✅", "module": "modules.testing_qa", "desc": "Automated testing"},
        {"name": "Logging", "icon": "📋", "module": "modules.logging", "desc": "Centralized logging"},
        {"name": "Notifications", "icon": "🔔", "module": "modules.notifications", "desc": "Multi-channel alerts"},
    ],
}

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.module-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
    border-left: 4px solid #667eea;
}
.stat-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 8px;
    color: white;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("# 🚀 NEXUS Platform")
    st.markdown("---")

    # Search
    search = st.text_input("🔍 Search modules...", "")

    st.markdown("---")

    # Category selection
    selected_cat = st.selectbox(
        "📂 Select Category",
        ["🏠 Home"] + list(MODULE_CATEGORIES.keys())
    )

    st.markdown("---")

    # Stats
    total = sum(len(m) for m in MODULE_CATEGORIES.values())
    st.markdown(f"**📦 Modules:** {total}")
    st.markdown(f"**📂 Categories:** {len(MODULE_CATEGORIES)}")
    st.markdown("**🎯 Version:** 1.0.0")

# Main content
if search:
    st.markdown(f"## 🔍 Search: '{search}'")
    results = []
    for cat, mods in MODULE_CATEGORIES.items():
        for m in mods:
            if search.lower() in m['name'].lower() or search.lower() in m['desc'].lower():
                results.append({**m, 'cat': cat})

    if results:
        for r in results:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{r['icon']} {r['name']}** ({r['cat']}) - {r['desc']}")
            with col2:
                st.button("Open", key=f"s_{r['name']}")
    else:
        st.warning("No modules found")

elif selected_cat == "🏠 Home":
    st.markdown("""
    <div class="main-header">
        <h1>🚀 NEXUS Platform</h1>
        <p>Unified AI-Powered Enterprise Productivity Suite</p>
        <p>73+ Integrated Modules | All-in-One Business Platform</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Modules", sum(len(m) for m in MODULE_CATEGORIES.values()))
    with col2:
        st.metric("Categories", len(MODULE_CATEGORIES))
    with col3:
        st.metric("AI-Powered", "Yes")
    with col4:
        st.metric("Enterprise Ready", "Yes")

    st.markdown("---")
    st.markdown("## 📂 All Modules by Category")

    for cat, mods in MODULE_CATEGORIES.items():
        with st.expander(f"**{cat}** ({len(mods)} modules)"):
            cols = st.columns(3)
            for i, m in enumerate(mods):
                with cols[i % 3]:
                    st.markdown(f"**{m['icon']} {m['name']}**")
                    st.caption(m['desc'])

    st.markdown("---")
    st.markdown("## 🚀 Quick Start")
    st.info("Select a category from the sidebar to explore modules, or use the search to find specific features.")

else:
    st.markdown(f"## 📂 {selected_cat}")
    st.markdown("---")

    mods = MODULE_CATEGORIES[selected_cat]
    cols = st.columns(3)

    for i, m in enumerate(mods):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="module-card">
                <h3>{m['icon']} {m['name']}</h3>
                <p>{m['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.button(f"Open {m['name']}", key=f"btn_{m['name']}", use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    NEXUS Platform v1.0.0 | 73+ Integrated Modules | Powered by AI | Built with Streamlit
</div>
""", unsafe_allow_html=True)
