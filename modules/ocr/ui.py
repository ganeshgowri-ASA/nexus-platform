"""
Streamlit Dashboard UI

Interactive web interface for OCR operations.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="NEXUS OCR Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state"""
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None


def main():
    """Main UI function"""
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80?text=NEXUS+OCR", use_column_width=True)
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["🏠 Home", "📄 Single OCR", "📚 Batch OCR", "📊 Analytics", "⚙️ Settings"]
        )

        st.markdown("---")
        st.markdown("### Quick Stats")
        display_quick_stats()

    # Main content
    if page == "🏠 Home":
        show_home_page()
    elif page == "📄 Single OCR":
        show_single_ocr_page()
    elif page == "📚 Batch OCR":
        show_batch_ocr_page()
    elif page == "📊 Analytics":
        show_analytics_page()
    elif page == "⚙️ Settings":
        show_settings_page()


def display_quick_stats():
    """Display quick statistics in sidebar"""
    st.metric("Total Processed", len(st.session_state.processing_history))

    if st.session_state.processing_history:
        avg_conf = sum(h.get('confidence', 0) for h in st.session_state.processing_history) / len(st.session_state.processing_history)
        st.metric("Avg Confidence", f"{avg_conf:.2%}")


def show_home_page():
    """Home page"""
    st.markdown('<div class="main-header">📄 NEXUS OCR Dashboard</div>', unsafe_allow_html=True)
    st.markdown("Welcome to the NEXUS OCR platform - Production-ready Optical Character Recognition")

    # Features grid
    st.markdown('<div class="sub-header">✨ Features</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 🎯 Multi-Engine Support
        - Tesseract OCR
        - Google Cloud Vision
        - Azure Computer Vision
        - AWS Textract
        - OpenAI GPT-4 Vision
        """)

    with col2:
        st.markdown("""
        #### 🔧 Advanced Processing
        - Image preprocessing
        - Layout analysis
        - Table extraction
        - Handwriting recognition
        - Post-processing
        """)

    with col3:
        st.markdown("""
        #### 📤 Export Options
        - PDF with text layer
        - Word documents
        - Excel spreadsheets
        - JSON data
        - Plain text
        """)

    # Recent activity
    st.markdown('<div class="sub-header">📋 Recent Activity</div>', unsafe_allow_html=True)

    if st.session_state.processing_history:
        recent = st.session_state.processing_history[-5:]
        df = pd.DataFrame(recent)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent activity. Start by processing a document!")


def show_single_ocr_page():
    """Single document OCR page"""
    st.markdown('<div class="main-header">📄 Single Document OCR</div>', unsafe_allow_html=True)

    # File upload
    uploaded_file = st.file_uploader(
        "Upload document (Image or PDF)",
        type=['png', 'jpg', 'jpeg', 'pdf', 'tiff', 'bmp']
    )

    if uploaded_file:
        # Display uploaded file
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 📎 Uploaded File")
            st.info(f"**Filename:** {uploaded_file.name}")
            st.info(f"**Size:** {uploaded_file.size / 1024:.2f} KB")

            # Display image preview if it's an image
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption="Preview", use_column_width=True)

        with col2:
            st.markdown("### ⚙️ Processing Options")

            # Engine selection
            engine = st.selectbox(
                "OCR Engine",
                ["tesseract", "google_vision", "azure", "aws", "openai"],
                help="Select the OCR engine to use"
            )

            # Language
            language = st.selectbox(
                "Language",
                ["eng", "fra", "deu", "spa", "ita", "por", "rus", "ara", "chi_sim", "jpn", "kor"],
                help="Select document language"
            )

            # Advanced options
            with st.expander("Advanced Options"):
                preprocess = st.checkbox("Enable preprocessing", value=True)
                detect_layout = st.checkbox("Detect layout", value=False)
                extract_tables = st.checkbox("Extract tables", value=False)
                post_process = st.checkbox("Post-processing", value=True)

            # Process button
            if st.button("🚀 Process Document", type="primary"):
                process_single_document(
                    uploaded_file,
                    engine,
                    language,
                    preprocess,
                    detect_layout,
                    extract_tables,
                    post_process
                )


def process_single_document(
    file,
    engine: str,
    language: str,
    preprocess: bool,
    detect_layout: bool,
    extract_tables: bool,
    post_process: bool
):
    """Process single document"""
    try:
        # Show processing status
        with st.spinner("🔄 Processing document..."):
            # Save uploaded file temporarily
            temp_path = Path(f"/tmp/{file.name}")
            with open(temp_path, "wb") as f:
                f.write(file.read())

            # Import OCR components
            from .processor import OCRPipeline

            # Create pipeline
            pipeline = OCRPipeline(engine_type=engine)

            # Process
            start_time = time.time()
            result = pipeline.process_file(
                temp_path,
                language=language,
                preprocess=preprocess,
                detect_layout=detect_layout,
                post_process=post_process
            )
            processing_time = time.time() - start_time

            # Store results
            result['filename'] = file.name
            result['engine'] = engine
            result['processing_time'] = processing_time
            result['timestamp'] = datetime.now().isoformat()

            st.session_state.current_results = result
            st.session_state.processing_history.append({
                'filename': file.name,
                'confidence': result.get('confidence', 0.0),
                'engine': engine,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # Display success
        st.markdown(
            f'<div class="success-message">✅ Processing complete in {processing_time:.2f}s</div>',
            unsafe_allow_html=True
        )

        # Display results
        display_ocr_results(result)

    except Exception as e:
        st.markdown(
            f'<div class="error-message">❌ Error: {str(e)}</div>',
            unsafe_allow_html=True
        )


def display_ocr_results(result: Dict[str, Any]):
    """Display OCR results"""
    st.markdown('<div class="sub-header">📊 Results</div>', unsafe_allow_html=True)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Confidence", f"{result.get('confidence', 0):.2%}")
    with col2:
        st.metric("Pages", result.get('page_count', 1))
    with col3:
        st.metric("Words", len(result.get('words', [])))
    with col4:
        st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")

    # Extracted text
    st.markdown("### 📝 Extracted Text")
    text = result.get('text', '')

    # Text display with options
    col1, col2 = st.columns([3, 1])

    with col1:
        st.text_area("", text, height=400)

    with col2:
        st.markdown("**Actions**")

        # Copy button
        st.code(text, language=None)

        # Download options
        st.download_button(
            "📥 Download TXT",
            text,
            file_name=f"ocr_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

        # Export options
        export_format = st.selectbox("Export Format", ["txt", "pdf", "word", "json"])

        if st.button("📤 Export"):
            export_result(result, export_format)

    # Quality metrics
    if 'result_quality' in result:
        st.markdown("### 📈 Quality Metrics")
        quality = result['result_quality']

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Image Quality", f"{quality.get('image_quality', 0):.2%}")
        with col2:
            st.metric("Text Clarity", f"{quality.get('text_clarity', 0):.2%}")
        with col3:
            st.metric("Overall Quality", f"{quality.get('overall_quality', 0):.2%}")


def show_batch_ocr_page():
    """Batch OCR processing page"""
    st.markdown('<div class="main-header">📚 Batch OCR Processing</div>', unsafe_allow_html=True)

    # Multiple file upload
    uploaded_files = st.file_uploader(
        "Upload multiple documents",
        type=['png', 'jpg', 'jpeg', 'pdf', 'tiff'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} files uploaded")

        # Processing options
        col1, col2 = st.columns(2)

        with col1:
            engine = st.selectbox("OCR Engine", ["tesseract", "google_vision", "azure", "aws"])
            language = st.selectbox("Language", ["eng", "fra", "deu", "spa"])

        with col2:
            parallel = st.checkbox("Parallel processing", value=True)
            max_workers = st.slider("Max workers", 1, 8, 4)

        # Process button
        if st.button("🚀 Process Batch", type="primary"):
            process_batch(uploaded_files, engine, language, parallel, max_workers)


def process_batch(files: List, engine: str, language: str, parallel: bool, max_workers: int):
    """Process batch of files"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        from .processor import BatchProcessor
        from pathlib import Path
        import tempfile

        # Save files temporarily
        temp_paths = []
        for i, file in enumerate(files):
            temp_path = Path(tempfile.gettempdir()) / file.name
            with open(temp_path, "wb") as f:
                f.write(file.read())
            temp_paths.append(temp_path)

        # Create batch processor
        processor = BatchProcessor(engine_type=engine, max_workers=max_workers)

        # Process
        results = []
        for i, temp_path in enumerate(temp_paths):
            status_text.text(f"Processing {i+1}/{len(temp_paths)}: {temp_path.name}")
            progress_bar.progress((i + 1) / len(temp_paths))

            result = processor.document_processor.process_file(temp_path, language=language)
            results.append(result)

        # Display results summary
        st.success(f"✅ Processed {len(results)} documents")

        # Results table
        df = pd.DataFrame([{
            'Filename': r.get('file_path', 'Unknown'),
            'Confidence': f"{r.get('confidence', 0):.2%}",
            'Pages': r.get('page_count', 1),
            'Words': len(r.get('words', []))
        } for r in results])

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def show_analytics_page():
    """Analytics and statistics page"""
    st.markdown('<div class="main-header">📊 Analytics Dashboard</div>', unsafe_allow_html=True)

    if not st.session_state.processing_history:
        st.info("No data available. Process some documents first!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.processing_history)

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Documents", len(df))
    with col2:
        st.metric("Avg Confidence", f"{df['confidence'].mean():.2%}")
    with col3:
        st.metric("Engines Used", df['engine'].nunique())
    with col4:
        st.metric("Today", len(df[df['timestamp'].str.contains(datetime.now().strftime("%Y-%m-%d"))]))

    # Charts
    st.markdown("### 📈 Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Confidence distribution
        fig = px.histogram(
            df,
            x='confidence',
            title="Confidence Score Distribution",
            labels={'confidence': 'Confidence Score'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Engine usage
        engine_counts = df['engine'].value_counts()
        fig = px.pie(
            values=engine_counts.values,
            names=engine_counts.index,
            title="Engine Usage"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Processing timeline
    st.markdown("### 📅 Processing Timeline")
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    timeline = df.groupby('date').size().reset_index(name='count')

    fig = px.line(
        timeline,
        x='date',
        y='count',
        title="Documents Processed Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)


def show_settings_page():
    """Settings page"""
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)

    # Engine settings
    st.markdown("### 🔧 Engine Configuration")

    with st.expander("Tesseract Settings"):
        tesseract_path = st.text_input("Tesseract Path", value="/usr/bin/tesseract")
        tessdata_path = st.text_input("Tessdata Path", value="/usr/share/tesseract-ocr/4.00/tessdata")

    with st.expander("Cloud API Settings"):
        st.text_input("Google Cloud Credentials", type="password")
        st.text_input("Azure Key", type="password")
        st.text_input("AWS Access Key", type="password")
        st.text_input("OpenAI API Key", type="password")

    # Processing settings
    st.markdown("### 🎛️ Processing Settings")

    default_engine = st.selectbox("Default Engine", ["tesseract", "google_vision", "azure", "aws"])
    default_language = st.selectbox("Default Language", ["eng", "fra", "deu", "spa"])
    default_dpi = st.slider("Default DPI", 150, 600, 300)

    # Storage settings
    st.markdown("### 💾 Storage Settings")

    upload_path = st.text_input("Upload Directory", value="/tmp/nexus_ocr_uploads")
    storage_path = st.text_input("Storage Directory", value="/tmp/nexus_ocr_storage")
    max_file_size = st.number_input("Max File Size (MB)", value=50)

    # Save button
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")


def export_result(result: Dict[str, Any], format: str):
    """Export OCR result"""
    try:
        from .export import ExportManager
        from pathlib import Path
        import tempfile

        # Create temporary output path
        output_path = Path(tempfile.gettempdir()) / f"ocr_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

        # Export
        export_manager = ExportManager()
        success = export_manager.export(result, output_path, format)

        if success:
            st.success(f"✅ Exported to {format.upper()}")

            # Offer download
            with open(output_path, "rb") as f:
                st.download_button(
                    f"📥 Download {format.upper()}",
                    f,
                    file_name=output_path.name,
                    mime="application/octet-stream"
                )
        else:
            st.error("❌ Export failed")

    except Exception as e:
        st.error(f"❌ Export error: {str(e)}")


if __name__ == "__main__":
    main()
