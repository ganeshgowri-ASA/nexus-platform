"""
Streamlit UI for Knowledge Base System

Modern, responsive UI for KB portal, article viewer, search, and admin dashboard.
"""

import streamlit as st
from datetime import datetime
from typing import Optional
from uuid import UUID

# Configure page
st.set_page_config(
    page_title="NEXUS Knowledge Base",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


class KnowledgeBaseUI:
    """Main UI controller for KB system."""

    def __init__(self):
        """Initialize the UI."""
        if "page" not in st.session_state:
            st.session_state.page = "home"
        if "search_query" not in st.session_state:
            st.session_state.search_query = ""

    def run(self):
        """Run the main application."""
        # Sidebar navigation
        self.render_sidebar()

        # Main content area
        if st.session_state.page == "home":
            self.render_home()
        elif st.session_state.page == "search":
            self.render_search()
        elif st.session_state.page == "article":
            self.render_article_viewer()
        elif st.session_state.page == "browse":
            self.render_browse()
        elif st.session_state.page == "faqs":
            self.render_faqs()
        elif st.session_state.page == "tutorials":
            self.render_tutorials()
        elif st.session_state.page == "videos":
            self.render_videos()
        elif st.session_state.page == "glossary":
            self.render_glossary()
        elif st.session_state.page == "chatbot":
            self.render_chatbot()
        elif st.session_state.page == "admin":
            self.render_admin_dashboard()

    def render_sidebar(self):
        """Render sidebar navigation."""
        with st.sidebar:
            st.title("📚 NEXUS KB")

            # Search box
            query = st.text_input(
                "🔍 Search",
                value=st.session_state.search_query,
                placeholder="Search knowledge base...",
            )

            if query:
                st.session_state.search_query = query
                st.session_state.page = "search"
                st.rerun()

            st.divider()

            # Navigation menu
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()

            if st.button("📖 Browse Articles", use_container_width=True):
                st.session_state.page = "browse"
                st.rerun()

            if st.button("❓ FAQs", use_container_width=True):
                st.session_state.page = "faqs"
                st.rerun()

            if st.button("🎓 Tutorials", use_container_width=True):
                st.session_state.page = "tutorials"
                st.rerun()

            if st.button("🎥 Videos", use_container_width=True):
                st.session_state.page = "videos"
                st.rerun()

            if st.button("📝 Glossary", use_container_width=True):
                st.session_state.page = "glossary"
                st.rerun()

            if st.button("💬 Chat Assistant", use_container_width=True):
                st.session_state.page = "chatbot"
                st.rerun()

            st.divider()

            # Admin section
            with st.expander("⚙️ Admin"):
                if st.button("Dashboard", use_container_width=True):
                    st.session_state.page = "admin"
                    st.rerun()

    def render_home(self):
        """Render home page."""
        st.title("📚 Welcome to NEXUS Knowledge Base")
        st.markdown("*Your comprehensive resource for product documentation and support*")

        # Hero search
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            search_query = st.text_input(
                "",
                placeholder="What can we help you with?",
                key="hero_search",
                label_visibility="collapsed",
            )
            if search_query:
                st.session_state.search_query = search_query
                st.session_state.page = "search"
                st.rerun()

        st.divider()

        # Quick links
        st.subheader("🚀 Quick Access")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container(border=True):
                st.markdown("### 📖 Articles")
                st.markdown("Browse our comprehensive guides")
                if st.button("View Articles", key="quick_articles"):
                    st.session_state.page = "browse"
                    st.rerun()

        with col2:
            with st.container(border=True):
                st.markdown("### ❓ FAQs")
                st.markdown("Frequently asked questions")
                if st.button("View FAQs", key="quick_faqs"):
                    st.session_state.page = "faqs"
                    st.rerun()

        with col3:
            with st.container(border=True):
                st.markdown("### 🎓 Tutorials")
                st.markdown("Step-by-step guides")
                if st.button("View Tutorials", key="quick_tutorials"):
                    st.session_state.page = "tutorials"
                    st.rerun()

        with col4:
            with st.container(border=True):
                st.markdown("### 💬 Chat")
                st.markdown("Get instant answers")
                if st.button("Start Chat", key="quick_chat"):
                    st.session_state.page = "chatbot"
                    st.rerun()

        # Popular articles
        st.divider()
        st.subheader("🔥 Popular Articles")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.markdown("**Getting Started Guide**")
                st.caption("⭐ 4.8 | 👁️ 1,234 views")
                st.markdown("Learn the basics and get up and running quickly...")
                st.button("Read More", key="popular_1")

        with col2:
            with st.container(border=True):
                st.markdown("**Advanced Features**")
                st.caption("⭐ 4.9 | 👁️ 987 views")
                st.markdown("Unlock the full potential of the platform...")
                st.button("Read More", key="popular_2")

        # Recent updates
        st.divider()
        st.subheader("📰 Recent Updates")

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**New Video Tutorial: API Integration**")
                st.caption("2 days ago")
            with col2:
                st.button("Watch", key="update_1")

    def render_search(self):
        """Render search results page."""
        st.title("🔍 Search Results")

        query = st.session_state.search_query

        if not query:
            st.info("Enter a search query to find articles")
            return

        st.markdown(f"Showing results for: **{query}**")

        # Filters
        with st.expander("🎛️ Filters"):
            col1, col2, col3 = st.columns(3)

            with col1:
                content_type = st.multiselect(
                    "Content Type",
                    ["Articles", "FAQs", "Tutorials", "Videos"],
                )

            with col2:
                language = st.selectbox(
                    "Language",
                    ["All", "English", "Spanish", "French"],
                )

            with col3:
                sort_by = st.selectbox(
                    "Sort By",
                    ["Relevance", "Newest", "Popular", "Rating"],
                )

        # Search results (demo data)
        st.divider()

        for i in range(5):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"### Result {i+1}: Sample Article Title")
                    st.caption("📖 Article | Updated 3 days ago | ⭐ 4.7")
                    st.markdown(
                        "This is a snippet of the article content showing relevant "
                        "information that matches the search query..."
                    )

                    # Tags
                    st.markdown("🏷️ `getting-started` `tutorial` `api`")

                with col2:
                    if st.button("View", key=f"result_{i}"):
                        st.session_state.page = "article"
                        st.rerun()

    def render_article_viewer(self):
        """Render article viewer."""
        st.title("Getting Started with NEXUS")

        # Article metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Views", "1,234")
        with col2:
            st.metric("Rating", "4.8 ⭐")
        with col3:
            st.metric("Helpful", "95%")
        with col4:
            st.button("📥 Export PDF")

        st.divider()

        # Article content
        st.markdown("""
        ## Overview

        Welcome to the NEXUS platform! This guide will help you get started
        with all the essential features and capabilities.

        ## Prerequisites

        - Basic understanding of web applications
        - An active NEXUS account
        - Modern web browser

        ## Step 1: Initial Setup

        First, configure your workspace...

        ```python
        import nexus

        # Initialize your workspace
        workspace = nexus.create_workspace("My Workspace")
        ```

        ## Step 2: Create Your First Project

        Now let's create a project...
        """)

        st.divider()

        # Feedback section
        st.subheader("💭 Was this helpful?")

        col1, col2 = st.columns(2)
        with col1:
            st.button("👍 Yes, this helped!", use_container_width=True)
        with col2:
            st.button("👎 Not really", use_container_width=True)

        # Rating
        st.markdown("**Rate this article:**")
        rating = st.slider("", 1, 5, 4, label_visibility="collapsed")

        # Comments
        comment = st.text_area("Leave a comment (optional)")

        if st.button("Submit Feedback"):
            st.success("Thank you for your feedback!")

        st.divider()

        # Related articles
        st.subheader("📚 Related Articles")

        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container(border=True):
                st.markdown("**Advanced Configuration**")
                st.caption("⭐ 4.6")
                st.button("Read", key="related_1")

        with col2:
            with st.container(border=True):
                st.markdown("**API Reference**")
                st.caption("⭐ 4.9")
                st.button("Read", key="related_2")

        with col3:
            with st.container(border=True):
                st.markdown("**Troubleshooting**")
                st.caption("⭐ 4.7")
                st.button("Read", key="related_3")

    def render_browse(self):
        """Render browse articles page."""
        st.title("📖 Browse Articles")

        # Categories
        col1, col2 = st.columns([1, 3])

        with col1:
            st.subheader("Categories")
            categories = [
                "Getting Started",
                "API Documentation",
                "Integrations",
                "Best Practices",
                "Troubleshooting",
                "Advanced Topics",
            ]

            for cat in categories:
                if st.button(f"📁 {cat}", use_container_width=True):
                    st.session_state.selected_category = cat

        with col2:
            st.subheader("All Articles")

            # Sort and filter
            sort_col, filter_col = st.columns(2)
            with sort_col:
                sort = st.selectbox("Sort by", ["Newest", "Popular", "Rating"])
            with filter_col:
                filter_lang = st.selectbox("Language", ["All", "English"])

            # Article list
            for i in range(10):
                with st.container(border=True):
                    col_title, col_meta = st.columns([3, 1])

                    with col_title:
                        st.markdown(f"### Sample Article Title {i+1}")
                        st.markdown("Brief description of the article content...")

                    with col_meta:
                        st.caption("📅 2024-01-15")
                        st.caption("⭐ 4.7")
                        st.button("View", key=f"article_{i}")

    def render_faqs(self):
        """Render FAQs page."""
        st.title("❓ Frequently Asked Questions")

        # Categories
        faq_categories = st.tabs([
            "General",
            "Account",
            "Billing",
            "Technical",
            "Security",
        ])

        with faq_categories[0]:
            faqs = [
                {
                    "q": "What is NEXUS?",
                    "a": "NEXUS is a comprehensive AI-powered productivity platform...",
                },
                {
                    "q": "How do I get started?",
                    "a": "Getting started is easy! First, create an account...",
                },
            ]

            for i, faq in enumerate(faqs):
                with st.expander(f"**{faq['q']}**"):
                    st.markdown(faq["a"])

                    col1, col2 = st.columns(2)
                    with col1:
                        st.button("👍 Helpful", key=f"faq_helpful_{i}")
                    with col2:
                        st.button("👎 Not helpful", key=f"faq_not_helpful_{i}")

    def render_tutorials(self):
        """Render tutorials page."""
        st.title("🎓 Interactive Tutorials")

        # Tutorial list
        tutorials = [
            {
                "title": "Getting Started with NEXUS",
                "difficulty": "Beginner",
                "duration": "15 min",
                "steps": 5,
                "completion": 0,
            },
            {
                "title": "API Integration Guide",
                "difficulty": "Intermediate",
                "duration": "30 min",
                "steps": 8,
                "completion": 50,
            },
        ]

        for tutorial in tutorials:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {tutorial['title']}")
                    st.caption(
                        f"🎯 {tutorial['difficulty']} | "
                        f"⏱️ {tutorial['duration']} | "
                        f"📝 {tutorial['steps']} steps"
                    )

                    if tutorial["completion"] > 0:
                        st.progress(tutorial["completion"] / 100)
                        st.caption(f"{tutorial['completion']}% complete")

                with col2:
                    button_label = "Continue" if tutorial["completion"] > 0 else "Start"
                    st.button(button_label, use_container_width=True)

    def render_videos(self):
        """Render videos page."""
        st.title("🎥 Video Library")

        # Video grid
        col1, col2, col3 = st.columns(3)

        videos = [
            {"title": "Platform Overview", "duration": "10:30"},
            {"title": "API Basics", "duration": "15:45"},
            {"title": "Advanced Features", "duration": "22:10"},
        ]

        for i, video in enumerate(videos):
            col = [col1, col2, col3][i % 3]

            with col:
                with st.container(border=True):
                    # Video thumbnail placeholder
                    st.markdown("🎬 **Video Thumbnail**")
                    st.markdown(f"**{video['title']}**")
                    st.caption(f"⏱️ {video['duration']}")
                    st.button("▶️ Watch", key=f"video_{i}")

    def render_glossary(self):
        """Render glossary page."""
        st.title("📝 Glossary")

        # Search glossary
        term_search = st.text_input("Search terms", placeholder="Enter a term...")

        # Alphabet navigation
        alphabet = st.columns(26)
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            with alphabet[i]:
                st.button(letter, key=f"letter_{letter}", use_container_width=True)

        st.divider()

        # Terms list
        terms = [
            {
                "term": "API",
                "definition": "Application Programming Interface - A set of protocols...",
            },
            {
                "term": "Authentication",
                "definition": "The process of verifying the identity of a user...",
            },
        ]

        for term in terms:
            with st.expander(f"**{term['term']}**"):
                st.markdown(term["definition"])
                st.caption("📚 Related articles: Getting Started, API Guide")

    def render_chatbot(self):
        """Render AI chatbot interface."""
        st.title("💬 KB Chat Assistant")
        st.markdown("*Ask me anything about the knowledge base!*")

        # Chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Hi! How can I help you today?"}
            ]

        # Display chat messages
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your question..."):
            # Add user message
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt}
            )

            # Simulate assistant response
            response = f"I found some relevant information about '{prompt}'. Here are the top articles..."

            st.session_state.chat_history.append(
                {"role": "assistant", "content": response}
            )

            st.rerun()

    def render_admin_dashboard(self):
        """Render admin dashboard."""
        st.title("⚙️ Admin Dashboard")

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Articles", "1,234", "+12")
        with col2:
            st.metric("Views (30d)", "45,678", "+15%")
        with col3:
            st.metric("Avg Rating", "4.7", "+0.2")
        with col4:
            st.metric("Active Users", "892", "+5%")

        st.divider()

        # Tabs for different admin sections
        admin_tabs = st.tabs([
            "📊 Analytics",
            "✍️ Content",
            "👥 Users",
            "⚙️ Settings",
        ])

        with admin_tabs[0]:  # Analytics
            st.subheader("Analytics Overview")

            # Charts placeholder
            st.line_chart({"views": [100, 150, 120, 180, 200, 190, 220]})

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Top Articles")
                for i in range(5):
                    st.markdown(f"{i+1}. Sample Article {i+1}")
                    st.progress((5-i) / 5)

            with col2:
                st.subheader("Popular Searches")
                for i in range(5):
                    st.markdown(f"{i+1}. search query {i+1}")

        with admin_tabs[1]:  # Content
            st.subheader("Content Management")

            if st.button("➕ Create New Article", type="primary"):
                st.info("Article creation form would appear here")

            st.divider()

            st.markdown("**Recent Articles**")
            for i in range(5):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"Article {i+1}")
                with col2:
                    st.caption("Published")
                with col3:
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        st.button("✏️", key=f"edit_{i}")
                    with col_delete:
                        st.button("🗑️", key=f"delete_{i}")


def main():
    """Main entry point."""
    app = KnowledgeBaseUI()
    app.run()


if __name__ == "__main__":
    main()
