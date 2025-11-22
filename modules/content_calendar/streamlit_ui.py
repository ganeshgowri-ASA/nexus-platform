"""
Streamlit UI for Content Calendar Module.

This provides a comprehensive web interface for:
- Visual calendar view
- Content creation and editing
- Team collaboration
- Analytics dashboards
- Publishing management
"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

# Configure page
st.set_page_config(
    page_title="NEXUS Content Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state() -> None:
    """Initialize session state variables."""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now()
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "month"
    if "selected_content" not in st.session_state:
        st.session_state.selected_content = None
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "channels": [],
            "status": [],
            "campaign": None,
        }


def render_sidebar() -> None:
    """Render sidebar navigation."""
    with st.sidebar:
        st.title("📅 Content Calendar")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            [
                "Calendar View",
                "Content Library",
                "Create Content",
                "Analytics",
                "Campaigns",
                "Team & Workflow",
                "Settings",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Quick filters
        st.subheader("Filters")
        st.session_state.filters["channels"] = st.multiselect(
            "Channels",
            ["Twitter", "Facebook", "Instagram", "LinkedIn", "Blog", "Email"],
        )

        st.session_state.filters["status"] = st.multiselect(
            "Status",
            ["Draft", "In Review", "Approved", "Scheduled", "Published"],
        )

        st.markdown("---")

        # Quick stats
        st.subheader("Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Scheduled", "12")
            st.metric("Published", "45")
        with col2:
            st.metric("Drafts", "8")
            st.metric("In Review", "3")

        return page


def render_calendar_view() -> None:
    """Render calendar view page."""
    st.header("Content Calendar")

    # View mode selector
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        view_mode = st.radio(
            "View",
            ["Month", "Week", "Day", "List"],
            horizontal=True,
        )

    with col2:
        if st.button("◀ Previous"):
            if view_mode == "Month":
                st.session_state.selected_date -= timedelta(days=30)
            elif view_mode == "Week":
                st.session_state.selected_date -= timedelta(days=7)
            else:
                st.session_state.selected_date -= timedelta(days=1)

    with col3:
        if st.button("Today"):
            st.session_state.selected_date = datetime.now()

    with col4:
        if st.button("Next ▶"):
            if view_mode == "Month":
                st.session_state.selected_date += timedelta(days=30)
            elif view_mode == "Week":
                st.session_state.selected_date += timedelta(days=7)
            else:
                st.session_state.selected_date += timedelta(days=1)

    st.markdown("---")

    # Calendar grid
    if view_mode == "Month":
        render_month_view()
    elif view_mode == "Week":
        render_week_view()
    elif view_mode == "Day":
        render_day_view()
    else:
        render_list_view()


def render_month_view() -> None:
    """Render month calendar view."""
    st.subheader(st.session_state.selected_date.strftime("%B %Y"))

    # Sample calendar data
    calendar_data = []
    start_date = st.session_state.selected_date.replace(day=1)

    for day in range(1, 32):
        try:
            date = start_date.replace(day=day)
            calendar_data.append(
                {
                    "date": date,
                    "day": day,
                    "events": 2 if day % 3 == 0 else 0,
                }
            )
        except ValueError:
            break

    # Display calendar grid
    cols = st.columns(7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for idx, day in enumerate(days):
        cols[idx].markdown(f"**{day}**")

    for idx, day_data in enumerate(calendar_data):
        col_idx = idx % 7
        with cols[col_idx]:
            if day_data["events"] > 0:
                if st.button(
                    f"{day_data['day']}\n📝 {day_data['events']}",
                    key=f"day_{day_data['day']}",
                ):
                    st.session_state.selected_date = day_data["date"]
            else:
                st.button(str(day_data["day"]), key=f"day_{day_data['day']}")


def render_week_view() -> None:
    """Render week calendar view."""
    st.subheader(
        f"Week of {st.session_state.selected_date.strftime('%B %d, %Y')}"
    )

    # Create time slots
    hours = [f"{h:02d}:00" for h in range(9, 18)]

    # Sample events
    events = [
        {"day": 0, "hour": 10, "title": "Twitter Post", "color": "#1DA1F2"},
        {"day": 2, "hour": 14, "title": "Blog Article", "color": "#FF6B6B"},
        {"day": 4, "hour": 11, "title": "LinkedIn Update", "color": "#0077B5"},
    ]

    # Display week grid
    cols = st.columns(7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for idx, day in enumerate(days):
        with cols[idx]:
            st.markdown(f"**{day}**")
            for hour_idx, hour in enumerate(hours[:3]):  # Show first 3 hours
                day_events = [e for e in events if e["day"] == idx and e["hour"] == hour_idx + 9]
                if day_events:
                    for event in day_events:
                        st.markdown(
                            f'<div style="background-color: {event["color"]}; '
                            f'padding: 5px; border-radius: 3px; margin: 2px 0;">'
                            f'{hour}: {event["title"]}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.text(hour)


def render_day_view() -> None:
    """Render single day view."""
    st.subheader(st.session_state.selected_date.strftime("%A, %B %d, %Y"))

    # Sample events for the day
    events = [
        {
            "time": "09:00",
            "title": "Twitter Post: Product Launch",
            "channel": "Twitter",
            "status": "Scheduled",
        },
        {
            "time": "12:00",
            "title": "Instagram Story",
            "channel": "Instagram",
            "status": "Scheduled",
        },
        {
            "time": "15:00",
            "title": "Blog Post: Industry Trends",
            "channel": "Blog",
            "status": "Scheduled",
        },
    ]

    for event in events:
        with st.expander(f"⏰ {event['time']} - {event['title']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Channel:** {event['channel']}")
            with col2:
                st.write(f"**Status:** {event['status']}")
            with col3:
                if st.button("Edit", key=f"edit_{event['time']}"):
                    st.session_state.selected_content = event


def render_list_view() -> None:
    """Render list view of content."""
    st.subheader("Content List")

    # Sample data
    data = {
        "Date": ["2024-01-15", "2024-01-16", "2024-01-18"],
        "Title": ["Product Launch Tweet", "Instagram Campaign", "Blog Post"],
        "Channel": ["Twitter", "Instagram", "Blog"],
        "Status": ["Scheduled", "Draft", "Approved"],
        "Engagement": [1250, 890, 2340],
    }

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


def render_content_library() -> None:
    """Render content library page."""
    st.header("Content Library")

    # Search and filters
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        search = st.text_input("Search content", placeholder="Search by title or keywords...")

    with col2:
        sort_by = st.selectbox("Sort by", ["Date", "Engagement", "Title"])

    with col3:
        view_type = st.selectbox("View", ["Grid", "List"])

    st.markdown("---")

    # Sample content cards
    if view_type == "Grid":
        cols = st.columns(3)
        for idx in range(6):
            with cols[idx % 3]:
                with st.container():
                    st.image("https://via.placeholder.com/300x200", use_column_width=True)
                    st.subheader(f"Content Item {idx + 1}")
                    st.write("Published on Twitter • 1.2K views")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.button("Edit", key=f"edit_content_{idx}")
                    with col_b:
                        st.button("Analytics", key=f"analytics_{idx}")
                st.markdown("---")
    else:
        # List view
        data = {
            "Title": [f"Content Item {i}" for i in range(1, 7)],
            "Type": ["Social Post", "Blog", "Email", "Video", "Image", "Article"],
            "Status": ["Published", "Draft", "Scheduled", "Published", "Draft", "Published"],
            "Views": [1200, 340, 0, 2300, 0, 890],
            "Engagement": [4.5, 0, 0, 6.2, 0, 3.1],
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)


def render_create_content() -> None:
    """Render content creation page."""
    st.header("Create New Content")

    # Content type selector
    content_type = st.selectbox(
        "Content Type",
        ["Social Post", "Blog Article", "Email Campaign", "Video", "Story/Reel"],
    )

    # AI assistance toggle
    use_ai = st.toggle("Use AI Assistant", value=True)

    if use_ai:
        with st.expander("🤖 AI Content Generator", expanded=True):
            topic = st.text_input("Topic", placeholder="Enter your content topic...")
            tone = st.selectbox("Tone", ["Professional", "Casual", "Humorous", "Educational"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Generate Ideas"):
                    with st.spinner("Generating content ideas..."):
                        st.write("💡 **AI Generated Ideas:**")
                        st.write("1. Top 5 trends in your industry")
                        st.write("2. Behind-the-scenes look at...")
                        st.write("3. Customer success story")

            with col2:
                if st.button("Generate Draft"):
                    with st.spinner("Creating draft..."):
                        st.text_area(
                            "Generated Content",
                            value="Here's your AI-generated content draft...",
                            height=150,
                        )

    st.markdown("---")

    # Content form
    with st.form("content_form"):
        title = st.text_input("Title")
        content = st.text_area("Content", height=200)

        # Media upload
        st.subheader("Media")
        uploaded_files = st.file_uploader(
            "Upload images or videos",
            accept_multiple_files=True,
            type=["jpg", "png", "mp4", "mov"],
        )

        # Channels
        st.subheader("Publishing Channels")
        channels = st.multiselect(
            "Select channels",
            ["Twitter", "Facebook", "Instagram", "LinkedIn", "Blog", "Email"],
        )

        # Scheduling
        st.subheader("Schedule")
        col1, col2 = st.columns(2)

        with col1:
            schedule_date = st.date_input("Date")
            schedule_time = st.time_input("Time")

        with col2:
            auto_schedule = st.checkbox("Auto-schedule at optimal time")
            timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "CST"])

        # Tags and metadata
        st.subheader("Metadata")
        tags = st.text_input("Tags (comma-separated)")
        campaign = st.selectbox("Campaign", ["None", "Product Launch", "Holiday 2024"])

        # Submit buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            save_draft = st.form_submit_button("Save as Draft", type="secondary")

        with col2:
            submit_review = st.form_submit_button("Submit for Review", type="primary")

        with col3:
            schedule = st.form_submit_button("Schedule", type="primary")

        if save_draft or submit_review or schedule:
            st.success("Content saved successfully!")


def render_analytics() -> None:
    """Render analytics dashboard."""
    st.header("Analytics Dashboard")

    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        start_date = st.date_input("From", value=datetime.now() - timedelta(days=30))

    with col2:
        end_date = st.date_input("To", value=datetime.now())

    with col3:
        st.button("Refresh", type="primary")

    st.markdown("---")

    # Key metrics
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Views", "24.5K", "+12.5%")

    with col2:
        st.metric("Engagement Rate", "4.8%", "+0.3%")

    with col3:
        st.metric("Followers", "12.3K", "+234")

    with col4:
        st.metric("ROI", "245%", "+15%")

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Engagement Over Time")
        # Sample data
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        values = [1000 + i * 50 for i in range(len(dates))]

        fig = px.line(
            x=dates,
            y=values,
            labels={"x": "Date", "y": "Engagement"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Channel Performance")
        # Sample data
        channels = ["Twitter", "Facebook", "Instagram", "LinkedIn"]
        engagement = [4500, 3200, 5800, 2100]

        fig = px.bar(
            x=channels,
            y=engagement,
            labels={"x": "Channel", "y": "Engagement"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # Top performing content
    st.subheader("Top Performing Content")
    data = {
        "Title": ["Product Launch", "Tutorial Video", "Customer Story"],
        "Channel": ["Twitter", "YouTube", "Blog"],
        "Views": [5200, 8900, 3400],
        "Engagement": [6.2, 8.1, 4.5],
        "ROI": [250, 340, 180],
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)


def render_campaigns() -> None:
    """Render campaigns page."""
    st.header("Campaigns")

    if st.button("+ Create New Campaign"):
        st.session_state.show_campaign_form = True

    st.markdown("---")

    # Active campaigns
    st.subheader("Active Campaigns")

    campaigns = [
        {"name": "Product Launch 2024", "content": 12, "budget": 5000, "roi": 245},
        {"name": "Holiday Marketing", "content": 8, "budget": 3000, "roi": 180},
    ]

    for campaign in campaigns:
        with st.expander(f"📊 {campaign['name']}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Content Items", campaign["content"])

            with col2:
                st.metric("Budget", f"${campaign['budget']}")

            with col3:
                st.metric("ROI", f"{campaign['roi']}%")

            with col4:
                if st.button("View Details", key=f"view_{campaign['name']}"):
                    pass


def render_team_workflow() -> None:
    """Render team and workflow page."""
    st.header("Team & Workflow")

    tabs = st.tabs(["My Tasks", "Team", "Workflows", "Comments"])

    with tabs[0]:
        st.subheader("My Assignments")
        tasks = [
            {"title": "Review blog post", "due": "2024-01-15", "status": "Pending"},
            {"title": "Approve social campaign", "due": "2024-01-16", "status": "In Progress"},
        ]

        for task in tasks:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{task['title']}**")
                with col2:
                    st.write(f"Due: {task['due']}")
                with col3:
                    st.button("Start", key=f"start_{task['title']}")
                st.markdown("---")

    with tabs[1]:
        st.subheader("Team Members")
        members = [
            {"name": "John Doe", "role": "Content Manager", "tasks": 5},
            {"name": "Jane Smith", "role": "Social Media Manager", "tasks": 8},
        ]

        for member in members:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{member['name']}**")
            with col2:
                st.write(member["role"])
            with col3:
                st.write(f"{member['tasks']} tasks")

    with tabs[2]:
        st.subheader("Approval Workflows")
        st.info("Configure approval workflows for different content types")

    with tabs[3]:
        st.subheader("Recent Comments")
        comments = [
            {"author": "John Doe", "text": "Looks great! Just minor edits needed.", "time": "2 hours ago"},
            {"author": "Jane Smith", "text": "Can we change the image?", "time": "5 hours ago"},
        ]

        for comment in comments:
            with st.container():
                st.write(f"**{comment['author']}** - {comment['time']}")
                st.write(comment["text"])
                st.markdown("---")


def render_settings() -> None:
    """Render settings page."""
    st.header("Settings")

    tabs = st.tabs(["General", "Integrations", "Notifications", "Team"])

    with tabs[0]:
        st.subheader("General Settings")
        default_timezone = st.selectbox("Default Timezone", ["UTC", "EST", "PST", "CST"])
        auto_save = st.checkbox("Auto-save drafts", value=True)

        if st.button("Save Settings"):
            st.success("Settings saved successfully!")

    with tabs[1]:
        st.subheader("Social Media Integrations")

        platforms = ["Twitter", "Facebook", "Instagram", "LinkedIn"]
        for platform in platforms:
            with st.expander(f"{platform} Integration"):
                connected = st.checkbox(f"Connected", key=f"{platform}_connected")
                if connected:
                    st.text_input(f"Account", key=f"{platform}_account")
                    if st.button(f"Test Connection", key=f"{platform}_test"):
                        st.success("Connection successful!")

    with tabs[2]:
        st.subheader("Notification Preferences")
        st.checkbox("Email notifications")
        st.checkbox("Assignment notifications")
        st.checkbox("Deadline reminders")
        st.checkbox("Publishing notifications")

    with tabs[3]:
        st.subheader("Team Management")
        if st.button("+ Invite Team Member"):
            email = st.text_input("Email address")
            role = st.selectbox("Role", ["Viewer", "Editor", "Admin"])
            if st.button("Send Invitation"):
                st.success("Invitation sent!")


def main() -> None:
    """Main application entry point."""
    init_session_state()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "Calendar View":
        render_calendar_view()
    elif page == "Content Library":
        render_content_library()
    elif page == "Create Content":
        render_create_content()
    elif page == "Analytics":
        render_analytics()
    elif page == "Campaigns":
        render_campaigns()
    elif page == "Team & Workflow":
        render_team_workflow()
    elif page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
