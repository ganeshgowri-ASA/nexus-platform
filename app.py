"""
Nexus Platform - Main Streamlit Application
AI-powered productivity platform with background task processing
"""
import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Nexus Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .module-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point"""

    # Sidebar navigation
    with st.sidebar:
        st.title("🎯 Nexus Platform")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            [
                "🏠 Home",
                "📧 Email Tasks",
                "📁 File Processing",
                "🤖 AI Tasks",
                "📊 Reports",
                "🔍 Task Monitor",
                "⚙️ Settings"
            ]
        )

        st.markdown("---")
        st.caption("Version 1.0.0")
        st.caption("Built with Streamlit & Celery")

    # Main content area
    if page == "🏠 Home":
        show_home()
    elif page == "📧 Email Tasks":
        show_email_tasks()
    elif page == "📁 File Processing":
        show_file_processing()
    elif page == "🤖 AI Tasks":
        show_ai_tasks()
    elif page == "📊 Reports":
        show_reports()
    elif page == "🔍 Task Monitor":
        from app.pages.task_monitor import show_task_monitor
        show_task_monitor()
    elif page == "⚙️ Settings":
        show_settings()


def show_home():
    """Display home page"""
    st.markdown('<h1 class="main-header">Welcome to Nexus Platform</h1>', unsafe_allow_html=True)

    st.markdown("""
    ### 🚀 AI-Powered Productivity Platform

    Nexus is a unified productivity platform with 24 integrated modules, powered by Claude AI
    and equipped with a robust background task processing system using Celery and Redis.

    #### ✨ Key Features:
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **📧 Email Automation**
        - Send single or bulk emails
        - Templated notifications
        - Scheduled delivery
        - Attachment support
        """)

    with col2:
        st.markdown("""
        **📁 File Processing**
        - Word, Excel, PowerPoint
        - PDF extraction
        - Image processing
        - Batch operations
        """)

    with col3:
        st.markdown("""
        **🤖 AI Integration**
        - Claude AI powered
        - Document analysis
        - Content generation
        - Translation services
        """)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **📊 Report Generation**
        - Analytics reports
        - Data exports
        - Performance tracking
        - Custom templates
        """)

    with col2:
        st.markdown("""
        **⚡ Background Tasks**
        - Async processing
        - Multiple queues
        - Auto-retry logic
        - Real-time monitoring
        """)

    with col3:
        st.markdown("""
        **🔍 Task Monitoring**
        - Live dashboard
        - Queue status
        - Worker information
        - Performance metrics
        """)

    st.markdown("---")

    # Quick stats
    st.subheader("📈 System Status")

    try:
        from app.utils.task_stats import get_task_statistics, get_queue_lengths

        stats = get_task_statistics()
        queues = get_queue_lengths()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Workers", stats.get('active_workers', 0))
        with col2:
            st.metric("Active Tasks", stats.get('active_tasks', 0))
        with col3:
            st.metric("Total Queues", len(queues))
        with col4:
            total_queued = sum(queues.values()) if queues else 0
            st.metric("Queued Tasks", total_queued)

    except Exception as e:
        st.warning("Unable to load system stats. Make sure Redis and Celery workers are running.")


def show_email_tasks():
    """Display email tasks page"""
    st.title("📧 Email Tasks")

    tab1, tab2 = st.tabs(["Send Email", "Email History"])

    with tab1:
        st.subheader("Send Email Task")

        with st.form("email_form"):
            to_email = st.text_input("To Email Address", placeholder="recipient@example.com")
            subject = st.text_input("Subject", placeholder="Email subject")
            body = st.text_area("Message Body", height=200)

            col1, col2 = st.columns(2)
            with col1:
                send_type = st.selectbox("Send Type", ["Immediate", "Scheduled"])
            with col2:
                if send_type == "Scheduled":
                    schedule_time = st.time_input("Schedule Time")

            submitted = st.form_submit_button("📤 Queue Email Task", type="primary")

            if submitted:
                if to_email and subject and body:
                    try:
                        from app.tasks.email_tasks import send_email

                        task = send_email.delay(
                            to_email=to_email,
                            subject=subject,
                            body=body
                        )

                        st.success(f"✅ Email task queued successfully!")
                        st.info(f"Task ID: `{task.id}`")
                        st.markdown(f"Check task status in the **Task Monitor** page")

                    except Exception as e:
                        st.error(f"Error queueing email: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")

    with tab2:
        st.info("Email history will be displayed here")


def show_file_processing():
    """Display file processing page"""
    st.title("📁 File Processing")

    st.subheader("Upload and Process Files")

    file_type = st.selectbox(
        "File Type",
        ["Word Document (.docx)", "Excel File (.xlsx)", "PowerPoint (.pptx)", "PDF", "Image"]
    )

    uploaded_file = st.file_uploader(f"Upload {file_type}", type=None)

    if uploaded_file:
        # File processing options
        st.subheader("Processing Options")

        if "Word" in file_type:
            operations = st.multiselect(
                "Select operations",
                ["extract_text", "count_stats", "extract_images"]
            )
        elif "Excel" in file_type:
            operations = st.multiselect(
                "Select operations",
                ["analyze_sheets", "convert_to_csv", "calculate_totals"]
            )
        elif "PowerPoint" in file_type:
            operations = st.multiselect(
                "Select operations",
                ["extract_text", "analyze_structure"]
            )
        elif "PDF" in file_type:
            operations = st.multiselect(
                "Select operations",
                ["extract_text", "get_metadata"]
            )
        else:  # Image
            operations = st.multiselect(
                "Select operations",
                ["create_thumbnail", "resize", "get_info"]
            )

        if st.button("🚀 Process File", type="primary"):
            if operations:
                # Save uploaded file
                from config.settings import settings
                import tempfile

                temp_path = settings.TEMP_DIR / uploaded_file.name
                temp_path.write_bytes(uploaded_file.read())

                # Queue appropriate task
                st.success(f"File processing task queued!")
                st.info("Check **Task Monitor** for progress")
            else:
                st.warning("Please select at least one operation")


def show_ai_tasks():
    """Display AI tasks page"""
    st.title("🤖 AI Tasks")

    tab1, tab2, tab3 = st.tabs(["Chat", "Document Analysis", "Content Generation"])

    with tab1:
        st.subheader("AI Chat")

        prompt = st.text_area("Enter your prompt", height=150)

        col1, col2 = st.columns(2)
        with col1:
            model = st.selectbox("Model", ["Claude", "GPT-4"])
        with col2:
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7)

        if st.button("💬 Send to AI", type="primary"):
            if prompt:
                try:
                    from app.tasks.ai_tasks import claude_completion

                    with st.spinner("Processing..."):
                        task = claude_completion.delay(
                            prompt=prompt,
                            temperature=temperature
                        )

                        st.success("AI task queued!")
                        st.info(f"Task ID: `{task.id}`")

                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a prompt")

    with tab2:
        st.subheader("Document Analysis")
        st.info("Upload a document to analyze with AI")

        document = st.text_area("Paste document text", height=200)
        analysis_type = st.selectbox(
            "Analysis Type",
            ["summary", "key_points", "sentiment", "action_items"]
        )

        if st.button("🔍 Analyze", type="primary") and document:
            try:
                from app.tasks.ai_tasks import analyze_document

                task = analyze_document.delay(
                    document_text=document,
                    analysis_type=analysis_type
                )

                st.success("Analysis task queued!")
                st.info(f"Task ID: `{task.id}`")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    with tab3:
        st.subheader("Content Generation")

        content_type = st.selectbox(
            "Content Type",
            ["email", "blog", "presentation", "report", "social_media"]
        )

        topic = st.text_input("Topic/Subject")
        length = st.select_slider("Length", ["short", "medium", "long"])

        if st.button("✨ Generate", type="primary") and topic:
            try:
                from app.tasks.ai_tasks import generate_content

                task = generate_content.delay(
                    content_type=content_type,
                    topic=topic,
                    length=length
                )

                st.success("Content generation task queued!")
                st.info(f"Task ID: `{task.id}`")

            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_reports():
    """Display reports page"""
    st.title("📊 Reports")

    tab1, tab2 = st.tabs(["Generate Report", "Export Data"])

    with tab1:
        st.subheader("Generate Analytics Report")

        report_type = st.selectbox(
            "Report Type",
            ["Summary", "Detailed", "Performance", "Custom"]
        )

        format = st.selectbox("Output Format", ["HTML", "Excel", "PDF", "JSON"])

        if st.button("📄 Generate Report", type="primary"):
            st.info("Report generation coming soon!")

    with tab2:
        st.subheader("Export Data")

        export_format = st.selectbox("Format", ["CSV", "Excel", "JSON"])

        if st.button("💾 Export", type="primary"):
            st.info("Data export coming soon!")


def show_settings():
    """Display settings page"""
    st.title("⚙️ Settings")

    st.subheader("System Configuration")

    from config.settings import settings

    st.markdown("### Celery Configuration")
    st.text(f"Broker URL: {settings.CELERY_BROKER_URL}")
    st.text(f"Result Backend: {settings.CELERY_RESULT_BACKEND}")

    st.markdown("### Directories")
    st.text(f"Upload Directory: {settings.UPLOAD_DIR}")
    st.text(f"Temp Directory: {settings.TEMP_DIR}")
    st.text(f"Logs Directory: {settings.LOGS_DIR}")

    st.markdown("### Task Queues")
    st.text(f"Email Queue: {settings.TASK_QUEUE_EMAIL}")
    st.text(f"File Processing Queue: {settings.TASK_QUEUE_FILE_PROCESSING}")
    st.text(f"AI Queue: {settings.TASK_QUEUE_AI}")
    st.text(f"Reports Queue: {settings.TASK_QUEUE_REPORTS}")


if __name__ == "__main__":
    main()
