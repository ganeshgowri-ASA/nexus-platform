"""NEXUS Platform - Streamlit Frontend"""
import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("# 🚀 NEXUS Platform")
    st.markdown("### AI-Powered Productivity Suite")
    st.markdown("---")

    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "OCR", "Translation", "Settings"],
        icons=["house", "file-text", "translate", "gear"],
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("---")
    st.markdown("### About")
    st.info("NEXUS Platform v0.1.0\n\n24 Integrated Modules for Enhanced Productivity")

# Main content
if selected == "Home":
    # Home page
    st.markdown('<p class="main-header">Welcome to NEXUS Platform 🚀</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Productivity Suite with 24 Integrated Modules</p>', unsafe_allow_html=True)

    # Feature cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 OCR Module")
        st.markdown("""
        <div class="feature-box">
        <h4>Text Extraction Made Easy</h4>
        <ul>
            <li>Extract text from images and PDFs</li>
            <li>Handwriting recognition</li>
            <li>Table detection and extraction</li>
            <li>100+ languages supported</li>
            <li>Layout analysis</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🌐 Translation Module")
        st.markdown("""
        <div class="feature-box">
        <h4>Professional Translation Services</h4>
        <ul>
            <li>Translate text to 100+ languages</li>
            <li>Custom glossaries</li>
            <li>Batch translation</li>
            <li>Quality scoring</li>
            <li>Context-aware translation</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Quick stats
    st.markdown("---")
    st.markdown("### 📊 Platform Capabilities")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="stat-card">
            <h2>100+</h2>
            <p>Languages Supported</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stat-card">
            <h2>24</h2>
            <p>Integrated Modules</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-card">
            <h2>3</h2>
            <p>OCR Engines</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="stat-card">
            <h2>∞</h2>
            <p>Possibilities</p>
        </div>
        """, unsafe_allow_html=True)

    # Getting started
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")

    with st.expander("📖 Quick Start Guide"):
        st.markdown("""
        1. **OCR Module**: Navigate to the OCR page to extract text from images and PDFs
        2. **Translation Module**: Go to Translation page to translate text between languages
        3. **Settings**: Configure API keys and preferences
        4. **API Documentation**: Visit `/api/v1/docs` for full API documentation
        """)

    with st.expander("🔑 API Keys Configuration"):
        st.markdown("""
        To use all features, configure the following API keys in Settings or `.env` file:

        - **Google Cloud API Key**: For Google Vision OCR and Translation
        - **AWS Credentials**: For AWS Textract OCR
        - **Anthropic API Key**: For Claude-powered translation

        Note: Tesseract OCR works without any API keys!
        """)

elif selected == "OCR":
    # Import OCR page
    from pages import ocr_page
    ocr_page.show()

elif selected == "Translation":
    # Import Translation page
    from pages import translation_page
    translation_page.show()

elif selected == "Settings":
    st.markdown("# ⚙️ Settings")
    st.markdown("### Configure your NEXUS Platform")

    with st.expander("🔑 API Keys", expanded=True):
        google_api_key = st.text_input("Google Cloud API Key", type="password")
        aws_access_key = st.text_input("AWS Access Key ID", type="password")
        aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
        anthropic_api_key = st.text_input("Anthropic API Key", type="password")

        if st.button("Save API Keys"):
            st.success("API keys saved successfully!")
            st.info("Note: In production, these should be saved securely in environment variables or a secrets manager.")

    with st.expander("⚙️ OCR Settings"):
        ocr_engine = st.selectbox(
            "Default OCR Engine",
            ["tesseract", "google_vision", "aws_textract"]
        )
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1
        )

        if st.button("Save OCR Settings"):
            st.success("OCR settings saved!")

    with st.expander("🌐 Translation Settings"):
        translation_service = st.selectbox(
            "Default Translation Service",
            ["google", "anthropic", "deepl"]
        )
        default_target_lang = st.selectbox(
            "Default Target Language",
            ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        )

        if st.button("Save Translation Settings"):
            st.success("Translation settings saved!")

    with st.expander("ℹ️ System Information"):
        st.markdown(f"""
        **Version:** 0.1.0
        **Backend API:** http://localhost:8000
        **API Docs:** http://localhost:8000/api/v1/docs
        **Environment:** {os.getenv('APP_ENV', 'development')}
        """)
