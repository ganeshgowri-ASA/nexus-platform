"""
NEXUS Platform - Main Application
Unified AI-powered productivity platform with integrated modules
Sessions 36-45: Advanced Features Batch
"""
import streamlit as st
import sys
import os

# Add modules to path
sys.path.append(os.path.dirname(__file__))

# Import all session modules
from modules import (
    session36_flowchart,
    session37_mindmap,
    session38_infographics,
    session39_whiteboard,
    session40_gantt,
    session41_database,
    session42_api_tester,
    session43_code_editor,
    session44_website_builder,
    session45_blog
)


def main():
    """Main application entry point"""

    # Page configuration
    st.set_page_config(
        page_title="NEXUS Platform",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 1rem 0;
        }
        .sub-header {
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
        }
        .module-card {
            padding: 1.5rem;
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            margin: 1rem 0;
            transition: all 0.3s;
        }
        .module-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/667eea/ffffff?text=NEXUS+Platform", use_container_width=True)
        st.markdown("---")

        st.markdown("### 🚀 Sessions 36-45")
        st.caption("Advanced AI-Powered Features")

        module = st.radio(
            "Select Module",
            [
                "🏠 Home",
                "🔄 Flowchart Editor (36)",
                "🧠 Mind Maps (37)",
                "📊 Infographics (38)",
                "🎨 Whiteboard (39)",
                "📊 Gantt Advanced (40)",
                "🗄️ Database Manager (41)",
                "🔌 API Tester (42)",
                "💻 Code Editor (43)",
                "🌐 Website Builder (44)",
                "✍️ Blog Platform (45)"
            ],
            key="module_selector"
        )

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        **NEXUS Platform**

        AI-powered productivity suite with 10 advanced modules.

        Sessions 36-45 Batch

        Built with Streamlit & Claude AI
        """)

        # API Key configuration
        with st.expander("⚙️ Settings"):
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Enter your Anthropic API key for AI features"
            )
            if api_key:
                os.environ['ANTHROPIC_API_KEY'] = api_key
                st.success("API Key configured!")

    # Main content area
    if module == "🏠 Home":
        show_home()
    elif module == "🔄 Flowchart Editor (36)":
        session36_flowchart.main()
    elif module == "🧠 Mind Maps (37)":
        session37_mindmap.main()
    elif module == "📊 Infographics (38)":
        session38_infographics.main()
    elif module == "🎨 Whiteboard (39)":
        session39_whiteboard.main()
    elif module == "📊 Gantt Advanced (40)":
        session40_gantt.main()
    elif module == "🗄️ Database Manager (41)":
        session41_database.main()
    elif module == "🔌 API Tester (42)":
        session42_api_tester.main()
    elif module == "💻 Code Editor (43)":
        session43_code_editor.main()
    elif module == "🌐 Website Builder (44)":
        session44_website_builder.main()
    elif module == "✍️ Blog Platform (45)":
        session45_blog.main()


def show_home():
    """Display home page"""

    st.markdown('<h1 class="main-header">🚀 NEXUS Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Unified AI-Powered Productivity Suite - Sessions 36-45</p>', unsafe_allow_html=True)

    st.markdown("---")

    # Overview stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Modules", "10", "+10 new")
    with col2:
        st.metric("AI Features", "45+", "100%")
    with col3:
        st.metric("Integration", "Full", "✓")
    with col4:
        st.metric("Sessions", "36-45", "Batch 4")

    st.markdown("---")

    # Module grid
    st.markdown("## 📦 Available Modules")

    col1, col2 = st.columns(2)

    modules_info = [
        {
            "icon": "🔄",
            "name": "Flowchart Editor",
            "session": "36",
            "description": "Create flowcharts with drag-drop shapes and Mermaid support. AI-powered diagram generation.",
            "features": ["Drag-drop interface", "Mermaid syntax", "AI generation", "Multiple exports"]
        },
        {
            "icon": "🧠",
            "name": "Mind Maps",
            "session": "37",
            "description": "Organize ideas with hierarchical mind maps. AI-powered brainstorming and expansion.",
            "features": ["Unlimited branches", "AI expansion", "Export formats", "Visual rendering"]
        },
        {
            "icon": "📊",
            "name": "Infographics Designer",
            "session": "38",
            "description": "Design stunning infographics with templates, charts, and icons. AI layout suggestions.",
            "features": ["Professional templates", "Chart integration", "Icon library", "AI design help"]
        },
        {
            "icon": "🎨",
            "name": "Whiteboard",
            "session": "39",
            "description": "Infinite canvas for brainstorming and collaboration. Real-time AI assistance.",
            "features": ["Infinite canvas", "Drawing tools", "Collaboration", "AI ideas"]
        },
        {
            "icon": "📊",
            "name": "Gantt Advanced",
            "session": "40",
            "description": "Advanced project management with critical path analysis and resource leveling.",
            "features": ["Critical path", "Resource leveling", "Dependencies", "AI optimization"]
        },
        {
            "icon": "🗄️",
            "name": "Database Manager",
            "session": "41",
            "description": "Visual database designer with query builder. Natural language SQL generation.",
            "features": ["Visual designer", "Query builder", "AI SQL generation", "Schema management"]
        },
        {
            "icon": "🔌",
            "name": "API Tester",
            "session": "42",
            "description": "Postman-like API testing with collections. AI-powered test generation.",
            "features": ["Request collections", "Test scripts", "Environment vars", "AI test gen"]
        },
        {
            "icon": "💻",
            "name": "Code Editor",
            "session": "43",
            "description": "Professional code editor with syntax highlighting, Git, and terminal.",
            "features": ["Syntax highlighting", "Git integration", "Terminal", "AI assistance"]
        },
        {
            "icon": "🌐",
            "name": "Website Builder",
            "session": "44",
            "description": "Build responsive websites with drag-drop. SEO optimization and AI content.",
            "features": ["Drag-drop", "Responsive", "SEO tools", "AI content"]
        },
        {
            "icon": "✍️",
            "name": "Blog Platform",
            "session": "45",
            "description": "Full-featured blogging platform. AI content generation and SEO optimization.",
            "features": ["Post management", "Categories/Tags", "Themes", "AI writer"]
        }
    ]

    for idx, module in enumerate(modules_info):
        with col1 if idx % 2 == 0 else col2:
            with st.container():
                st.markdown(f"""
                <div class="module-card">
                    <h3>{module['icon']} {module['name']}</h3>
                    <p><strong>Session {module['session']}</strong></p>
                    <p>{module['description']}</p>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Features"):
                    for feature in module['features']:
                        st.markdown(f"✓ {feature}")

    st.markdown("---")

    # Getting started
    st.markdown("## 🚀 Getting Started")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 1️⃣ Configure API
        - Add your Anthropic API key in settings
        - Enable AI features across all modules
        - Unlock advanced capabilities
        """)

    with col2:
        st.markdown("""
        ### 2️⃣ Choose Module
        - Select from 10 advanced modules
        - Each with unique features
        - Seamlessly integrated
        """)

    with col3:
        st.markdown("""
        ### 3️⃣ Create & Build
        - Start creating immediately
        - Use AI assistance
        - Export and share
        """)

    st.markdown("---")

    # Features highlight
    st.markdown("## ✨ Key Features")

    feature_cols = st.columns(5)

    features = [
        ("🤖", "AI-Powered", "Claude AI integration in all modules"),
        ("🎨", "Beautiful UI", "Modern, intuitive interface"),
        ("💾", "Auto-Save", "Never lose your work"),
        ("📤", "Export", "Multiple format support"),
        ("🔄", "Real-time", "Instant updates and previews")
    ]

    for idx, (icon, title, desc) in enumerate(features):
        with feature_cols[idx]:
            st.markdown(f"### {icon}")
            st.markdown(f"**{title}**")
            st.caption(desc)

    st.markdown("---")

    # Call to action
    st.success("""
    👈 **Select a module from the sidebar to get started!**

    Each module is fully featured with AI assistance, beautiful UI, and powerful capabilities.
    """)

    # Footer
    st.markdown("---")
    st.caption("NEXUS Platform - Sessions 36-45 | Built with ❤️ using Streamlit & Claude AI")


if __name__ == "__main__":
    main()
