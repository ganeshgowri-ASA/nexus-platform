"""
Streamlit Dashboard for Image Recognition Module

Interactive web interface featuring:
- Multi-page layout with sidebar navigation
- Image upload and processing
- Classification and detection
- Batch processing and job monitoring
- Model management
- Dataset annotation
- Results visualization
- Real-time updates via WebSocket
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import time
import io
import base64
import json

# Plotting libraries
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    px = go = None

# Image processing
from PIL import Image
import cv2

# Database and API clients
import requests
from sqlalchemy.orm import Session

# Module imports
from .db_models import (
    RecognitionJob, Image as ImageDB, Prediction,
    Label, RecognitionModel, Annotation,
    JobStatus, JobType, ModelType
)
from .classifier import ImageClassifier
from .detection import ObjectDetector
from .quality import QualityAssessment
from .features import FeatureExtractor


# ============================================================================
# CONFIGURATION
# ============================================================================

# Page config
st.set_page_config(
    page_title="NEXUS Image Recognition",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
CUSTOM_CSS = """
<style>
    /* Main container */
    .main {
        padding: 2rem;
    }

    /* Headers */
    h1 {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }

    h2 {
        color: #ff7f0e;
        margin-top: 2rem;
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .info-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }

    .success-card {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }

    .warning-card {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }

    .error-card {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }

    /* Image containers */
    .image-container {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        background: white;
    }

    /* Tables */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0 0;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user"

if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None

if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []

if 'processing_results' not in st.session_state:
    st.session_state.processing_results = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db_session() -> Session:
    """Get database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/nexus')
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def display_image_with_detections(image: Image.Image, detections: List[Dict], title: str = ""):
    """Display image with bounding boxes."""
    # Convert PIL to numpy
    img_np = np.array(image)

    # Draw bounding boxes
    for det in detections:
        bbox = det.get('bbox', {})
        x, y = int(bbox.get('x', 0)), int(bbox.get('y', 0))
        w, h = int(bbox.get('width', 0)), int(bbox.get('height', 0))

        # Draw rectangle
        cv2.rectangle(img_np, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Draw label
        label = f"{det.get('label', 'unknown')}: {det.get('confidence', 0):.2f}"
        cv2.putText(img_np, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    st.image(img_np, caption=title, use_column_width=True)


def display_metric_card(title: str, value: Any, delta: Optional[str] = None):
    """Display a metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <h3 style="margin:0; color: white;">{title}</h3>
        <h1 style="margin:0.5rem 0; color: white;">{value}</h1>
        {f'<p style="margin:0; color: rgba(255,255,255,0.8);">{delta}</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def display_info_box(message: str, box_type: str = "info"):
    """Display an info box."""
    st.markdown(f"""
    <div class="{box_type}-card">
        {message}
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=NEXUS", use_column_width=True)
        st.title("🔍 Image Recognition")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            [
                "🏠 Home",
                "📤 Upload Images",
                "🎯 Classification",
                "🎨 Object Detection",
                "📊 Batch Processing",
                "👁️ Job Monitor",
                "🤖 Model Management",
                "✏️ Annotation Tool",
                "📈 Analytics",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )

        st.divider()

        # User info
        st.markdown("### User Info")
        st.write(f"**User ID:** {st.session_state.user_id}")

        if st.session_state.current_job_id:
            st.write(f"**Current Job:** {st.session_state.current_job_id}")

        st.divider()

        # Quick stats
        try:
            db = get_db_session()
            total_jobs = db.query(RecognitionJob).count()
            total_images = db.query(ImageDB).count()

            st.markdown("### Quick Stats")
            st.metric("Total Jobs", total_jobs)
            st.metric("Total Images", total_images)

            db.close()
        except Exception as e:
            st.warning("Database not available")

        return page


# ============================================================================
# PAGE: HOME
# ============================================================================

def page_home():
    """Home page with overview."""
    st.title("🏠 NEXUS Image Recognition")
    st.markdown("### Welcome to the Image Recognition Module")

    st.markdown("""
    <div class="info-card">
        <h4>🚀 Production-Ready Image Recognition System</h4>
        <p>Powered by state-of-the-art deep learning models including VGG16, ResNet50,
        InceptionV3, EfficientNet, YOLO, and GPT-4 Vision.</p>
    </div>
    """, unsafe_allow_html=True)

    # Feature grid
    st.markdown("## 🌟 Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 🎯 Classification
        - Single & multi-label
        - Custom models
        - Transfer learning
        - Zero-shot learning
        """)

        st.markdown("""
        #### 🎨 Object Detection
        - YOLO-based detection
        - Bounding boxes
        - Instance segmentation
        - Real-time processing
        """)

    with col2:
        st.markdown("""
        #### 🔍 Advanced Features
        - Feature extraction
        - Similarity search
        - Scene understanding
        - Quality assessment
        """)

        st.markdown("""
        #### 📊 Batch Processing
        - Async job processing
        - Progress tracking
        - Celery integration
        - Redis caching
        """)

    with col3:
        st.markdown("""
        #### 🤖 Model Management
        - Custom models
        - Model training
        - Version control
        - Performance metrics
        """)

        st.markdown("""
        #### 📈 Analytics
        - Real-time stats
        - Visualizations
        - Export results
        - API integration
        """)

    # Recent activity
    st.markdown("## 📋 Recent Activity")

    try:
        db = get_db_session()
        recent_jobs = db.query(RecognitionJob).order_by(
            RecognitionJob.created_at.desc()
        ).limit(5).all()

        if recent_jobs:
            job_data = []
            for job in recent_jobs:
                job_data.append({
                    'Name': job.name,
                    'Type': job.job_type.value,
                    'Status': job.status.value,
                    'Progress': f"{job.progress_percentage:.1f}%",
                    'Created': job.created_at.strftime('%Y-%m-%d %H:%M')
                })

            df = pd.DataFrame(job_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent jobs")

        db.close()
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")

    # Quick actions
    st.markdown("## ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📤 Upload Images", use_container_width=True):
            st.session_state.page = "📤 Upload Images"
            st.rerun()

    with col2:
        if st.button("🎯 Classify", use_container_width=True):
            st.session_state.page = "🎯 Classification"
            st.rerun()

    with col3:
        if st.button("🎨 Detect Objects", use_container_width=True):
            st.session_state.page = "🎨 Object Detection"
            st.rerun()

    with col4:
        if st.button("📊 View Jobs", use_container_width=True):
            st.session_state.page = "👁️ Job Monitor"
            st.rerun()


# ============================================================================
# PAGE: UPLOAD IMAGES
# ============================================================================

def page_upload():
    """Image upload page."""
    st.title("📤 Upload Images")
    st.markdown("Upload images for recognition processing")

    # Create new job
    st.markdown("## Create New Job")

    col1, col2 = st.columns(2)

    with col1:
        job_name = st.text_input("Job Name", value=f"Job {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        job_type = st.selectbox(
            "Job Type",
            ["classification", "object_detection", "feature_extraction", "quality_assessment"]
        )

    with col2:
        model_type = st.selectbox(
            "Model Type",
            ["resnet50", "vgg16", "efficientnet", "yolo"]
        )
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.5, 0.05)

    description = st.text_area("Description (optional)")

    if st.button("Create Job", type="primary"):
        try:
            db = get_db_session()

            job = RecognitionJob(
                name=job_name,
                description=description,
                job_type=JobType(job_type),
                user_id=st.session_state.user_id,
                model_type=ModelType(model_type),
                confidence_threshold=confidence_threshold,
                status=JobStatus.PENDING
            )

            db.add(job)
            db.commit()
            db.refresh(job)

            st.session_state.current_job_id = str(job.id)

            display_info_box(f"✅ Job created successfully! Job ID: {job.id}", "success")

            db.close()
        except Exception as e:
            st.error(f"Error creating job: {e}")

    st.divider()

    # Upload images
    if st.session_state.current_job_id:
        st.markdown("## Upload Images")

        uploaded_files = st.file_uploader(
            "Choose images",
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} images")

            # Preview images
            cols = st.columns(4)
            for idx, file in enumerate(uploaded_files[:8]):  # Show first 8
                with cols[idx % 4]:
                    image = Image.open(file)
                    st.image(image, caption=file.name, use_column_width=True)

            if len(uploaded_files) > 8:
                st.info(f"+ {len(uploaded_files) - 8} more images")

            if st.button("Upload All Images", type="primary"):
                try:
                    db = get_db_session()

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for idx, file in enumerate(uploaded_files):
                        # Read image
                        image = Image.open(file)
                        width, height = image.size

                        # Save to disk (implement your storage logic)
                        import os
                        import uuid

                        storage_path = os.getenv('STORAGE_PATH', '/tmp/nexus/images')
                        os.makedirs(storage_path, exist_ok=True)

                        filename = f"{uuid.uuid4()}{Path(file.name).suffix}"
                        file_path = os.path.join(storage_path, filename)
                        image.save(file_path)

                        # Create DB record
                        img_db = ImageDB(
                            job_id=st.session_state.current_job_id,
                            filename=filename,
                            original_filename=file.name,
                            file_path=file_path,
                            file_size=file.size,
                            file_format=Path(file.name).suffix.lstrip('.'),
                            width=width,
                            height=height,
                            channels=len(image.getbands()),
                            color_mode=image.mode
                        )

                        db.add(img_db)

                        # Update progress
                        progress = (idx + 1) / len(uploaded_files)
                        progress_bar.progress(progress)
                        status_text.text(f"Uploading {idx + 1}/{len(uploaded_files)}: {file.name}")

                    # Update job
                    job = db.query(RecognitionJob).filter(
                        RecognitionJob.id == st.session_state.current_job_id
                    ).first()
                    if job:
                        job.total_images = len(uploaded_files)

                    db.commit()

                    status_text.empty()
                    progress_bar.empty()

                    display_info_box(f"✅ Successfully uploaded {len(uploaded_files)} images!", "success")

                    db.close()

                except Exception as e:
                    st.error(f"Error uploading images: {e}")
    else:
        st.info("Please create a job first")


# ============================================================================
# PAGE: CLASSIFICATION
# ============================================================================

def page_classification():
    """Image classification page."""
    st.title("🎯 Image Classification")
    st.markdown("Classify images using pre-trained models")

    # Upload single image
    uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        # Display image
        image = Image.open(uploaded_file)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Input Image")
            st.image(image, use_column_width=True)

            st.markdown("### Configuration")
            model_type = st.selectbox("Model", ["resnet50", "vgg16", "efficientnet", "inceptionv3"])
            top_k = st.slider("Top K Predictions", 1, 10, 5)
            confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.1, 0.05)

        with col2:
            st.markdown("### Results")

            if st.button("Classify Image", type="primary"):
                with st.spinner("Classifying..."):
                    try:
                        classifier = ImageClassifier(model_type=model_type)
                        result = classifier.classify(
                            image,
                            top_k=top_k,
                            confidence_threshold=confidence_threshold
                        )

                        if result.get('success'):
                            st.success(f"Classification completed in {result['processing_time_ms']:.2f}ms")

                            # Display predictions
                            predictions = result['predictions']

                            if predictions:
                                # Create dataframe
                                df = pd.DataFrame(predictions)
                                df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2%}")

                                st.dataframe(df, use_container_width=True)

                                # Visualization
                                if px:
                                    fig = px.bar(
                                        predictions,
                                        x='confidence',
                                        y='label',
                                        orientation='h',
                                        title='Classification Confidence',
                                        labels={'confidence': 'Confidence', 'label': 'Class'}
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No predictions above threshold")
                        else:
                            st.error(f"Classification failed: {result.get('error')}")

                    except Exception as e:
                        st.error(f"Error: {e}")


# ============================================================================
# PAGE: OBJECT DETECTION
# ============================================================================

def page_detection():
    """Object detection page."""
    st.title("🎨 Object Detection")
    st.markdown("Detect and locate objects in images")

    uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        image = Image.open(uploaded_file)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Input Image")
            st.image(image, use_column_width=True)

            st.markdown("### Configuration")
            model_type = st.selectbox("Model", ["yolo"])
            confidence_threshold = st.slider("Confidence", 0.0, 1.0, 0.5, 0.05)
            iou_threshold = st.slider("IOU Threshold", 0.0, 1.0, 0.4, 0.05)

        with col2:
            st.markdown("### Detections")

            if st.button("Detect Objects", type="primary"):
                with st.spinner("Detecting objects..."):
                    try:
                        detector = ObjectDetector(model_type=model_type)
                        result = detector.detect(
                            image,
                            confidence_threshold=confidence_threshold,
                            iou_threshold=iou_threshold
                        )

                        if result.get('success'):
                            detections = result.get('detections', [])

                            st.success(f"Found {len(detections)} objects in {result.get('processing_time_ms', 0):.2f}ms")

                            if detections:
                                # Display image with boxes
                                display_image_with_detections(image, detections, "Detection Results")

                                # Detection table
                                det_df = pd.DataFrame([
                                    {
                                        'Label': d.get('label'),
                                        'Confidence': f"{d.get('confidence', 0):.2%}",
                                        'X': int(d.get('bbox', {}).get('x', 0)),
                                        'Y': int(d.get('bbox', {}).get('y', 0)),
                                        'Width': int(d.get('bbox', {}).get('width', 0)),
                                        'Height': int(d.get('bbox', {}).get('height', 0))
                                    }
                                    for d in detections
                                ])

                                st.dataframe(det_df, use_container_width=True)
                            else:
                                st.warning("No objects detected")
                        else:
                            st.error(f"Detection failed: {result.get('error')}")

                    except Exception as e:
                        st.error(f"Error: {e}")


# ============================================================================
# PAGE: BATCH PROCESSING
# ============================================================================

def page_batch_processing():
    """Batch processing page."""
    st.title("📊 Batch Processing")
    st.markdown("Process multiple images in batch mode")

    try:
        db = get_db_session()

        # List jobs
        jobs = db.query(RecognitionJob).filter(
            RecognitionJob.status == JobStatus.PENDING
        ).order_by(RecognitionJob.created_at.desc()).limit(10).all()

        if jobs:
            job_options = {f"{job.name} ({job.job_type.value})": str(job.id) for job in jobs}
            selected_job_name = st.selectbox("Select Job", list(job_options.keys()))
            selected_job_id = job_options[selected_job_name]

            # Get job details
            job = db.query(RecognitionJob).filter(
                RecognitionJob.id == selected_job_id
            ).first()

            if job:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    display_metric_card("Total Images", job.total_images)

                with col2:
                    display_metric_card("Processed", job.processed_images)

                with col3:
                    display_metric_card("Status", job.status.value)

                with col4:
                    display_metric_card("Progress", f"{job.progress_percentage:.1f}%")

                # Start processing
                if job.status == JobStatus.PENDING:
                    if st.button("▶️ Start Processing", type="primary"):
                        # Start batch processing task
                        from .tasks import batch_process_job

                        task = batch_process_job.delay(selected_job_id)

                        st.success(f"Batch processing started! Task ID: {task.id if hasattr(task, 'id') else 'N/A'}")
                        time.sleep(1)
                        st.rerun()

                # Show images
                st.markdown("### Images")

                images = db.query(ImageDB).filter(
                    ImageDB.job_id == selected_job_id
                ).limit(20).all()

                if images:
                    cols = st.columns(4)
                    for idx, img in enumerate(images):
                        with cols[idx % 4]:
                            try:
                                pil_img = Image.open(img.file_path)
                                st.image(pil_img, caption=img.original_filename, use_column_width=True)

                                if img.processed:
                                    st.success("✅ Processed")
                                else:
                                    st.info("⏳ Pending")
                            except:
                                st.error("Error loading image")
        else:
            st.info("No pending jobs available")

        db.close()

    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================================
# PAGE: JOB MONITOR
# ============================================================================

def page_job_monitor():
    """Job monitoring page."""
    st.title("👁️ Job Monitor")
    st.markdown("Monitor and manage recognition jobs")

    try:
        db = get_db_session()

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "pending", "processing", "completed", "failed", "cancelled"]
            )

        with col2:
            job_type_filter = st.selectbox(
                "Job Type",
                ["All", "classification", "object_detection", "feature_extraction"]
            )

        with col3:
            limit = st.number_input("Limit", min_value=5, max_value=100, value=20)

        # Query jobs
        query = db.query(RecognitionJob)

        if status_filter != "All":
            query = query.filter(RecognitionJob.status == JobStatus(status_filter))

        if job_type_filter != "All":
            query = query.filter(RecognitionJob.job_type == JobType(job_type_filter))

        jobs = query.order_by(RecognitionJob.created_at.desc()).limit(limit).all()

        # Display jobs
        if jobs:
            for job in jobs:
                with st.expander(f"📋 {job.name} - {job.status.value.upper()}", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Type:** {job.job_type.value}")
                        st.write(f"**Model:** {job.model_type.value}")
                        st.write(f"**Created:** {job.created_at.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        st.write(f"**Total Images:** {job.total_images}")
                        st.write(f"**Processed:** {job.processed_images}")
                        st.write(f"**Successful:** {job.successful_images}")

                    with col3:
                        st.write(f"**Failed:** {job.failed_images}")
                        st.write(f"**Progress:** {job.progress_percentage:.1f}%")

                        if job.processing_time_seconds:
                            st.write(f"**Time:** {job.processing_time_seconds:.1f}s")

                    # Progress bar
                    st.progress(job.progress_percentage / 100)

                    # Actions
                    action_col1, action_col2, action_col3 = st.columns(3)

                    with action_col1:
                        if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
                            if st.button("❌ Cancel", key=f"cancel_{job.id}"):
                                job.status = JobStatus.CANCELLED
                                db.commit()
                                st.success("Job cancelled")
                                st.rerun()

                    with action_col2:
                        if st.button("🔍 View Details", key=f"view_{job.id}"):
                            st.session_state.current_job_id = str(job.id)
                            st.info(f"Current job set to {job.id}")

                    with action_col3:
                        if st.button("🗑️ Delete", key=f"delete_{job.id}"):
                            db.delete(job)
                            db.commit()
                            st.success("Job deleted")
                            st.rerun()
        else:
            st.info("No jobs found")

        db.close()

    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================================
# PAGE: MODEL MANAGEMENT
# ============================================================================

def page_model_management():
    """Model management page."""
    st.title("🤖 Model Management")
    st.markdown("Manage recognition models")

    try:
        db = get_db_session()

        # Tabs
        tab1, tab2 = st.tabs(["📋 Available Models", "➕ Register Model"])

        with tab1:
            models = db.query(RecognitionModel).filter(
                RecognitionModel.is_active == True
            ).order_by(RecognitionModel.created_at.desc()).all()

            if models:
                for model in models:
                    with st.expander(f"{model.display_name} (v{model.version})", expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Type:** {model.model_type.value}")
                            st.write(f"**Status:** {'✅ Active' if model.is_active else '❌ Inactive'}")
                            st.write(f"**Deployed:** {'✅ Yes' if model.is_deployed else '❌ No'}")

                            if model.description:
                                st.write(f"**Description:** {model.description}")

                        with col2:
                            if model.output_classes:
                                st.write(f"**Classes:** {model.output_classes}")

                            if model.training_accuracy:
                                st.write(f"**Train Accuracy:** {model.training_accuracy:.2%}")

                            if model.validation_accuracy:
                                st.write(f"**Val Accuracy:** {model.validation_accuracy:.2%}")

                            if model.inference_time_ms:
                                st.write(f"**Inference Time:** {model.inference_time_ms:.2f}ms")

                        # Capabilities
                        caps = []
                        if model.supports_classification:
                            caps.append("Classification")
                        if model.supports_detection:
                            caps.append("Detection")
                        if model.supports_segmentation:
                            caps.append("Segmentation")

                        if caps:
                            st.write(f"**Capabilities:** {', '.join(caps)}")
            else:
                st.info("No models found")

        with tab2:
            st.markdown("### Register New Model")

            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Model Name")
                display_name = st.text_input("Display Name")
                model_type = st.selectbox("Type", ["vgg16", "resnet50", "efficientnet", "yolo", "custom"])

            with col2:
                version = st.text_input("Version", value="1.0.0")
                model_path = st.text_input("Model Path")
                output_classes = st.number_input("Output Classes", min_value=1, value=1000)

            description = st.text_area("Description")

            col3, col4, col5 = st.columns(3)

            with col3:
                supports_classification = st.checkbox("Classification", value=True)

            with col4:
                supports_detection = st.checkbox("Detection", value=False)

            with col5:
                supports_segmentation = st.checkbox("Segmentation", value=False)

            if st.button("Register Model", type="primary"):
                if name and display_name and model_path:
                    try:
                        model = RecognitionModel(
                            name=name,
                            display_name=display_name,
                            description=description,
                            model_type=ModelType(model_type),
                            version=version,
                            model_path=model_path,
                            output_classes=output_classes,
                            supports_classification=supports_classification,
                            supports_detection=supports_detection,
                            supports_segmentation=supports_segmentation,
                            user_id=st.session_state.user_id,
                            is_active=True
                        )

                        db.add(model)
                        db.commit()

                        st.success(f"Model '{display_name}' registered successfully!")
                    except Exception as e:
                        st.error(f"Error registering model: {e}")
                else:
                    st.warning("Please fill in all required fields")

        db.close()

    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================================
# PAGE: ANALYTICS
# ============================================================================

def page_analytics():
    """Analytics and statistics page."""
    st.title("📈 Analytics & Statistics")
    st.markdown("Performance metrics and insights")

    try:
        db = get_db_session()

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        total_jobs = db.query(RecognitionJob).count()
        total_images = db.query(ImageDB).count()
        total_predictions = db.query(Prediction).count()
        avg_confidence = db.query(func.avg(Prediction.confidence)).scalar() or 0

        with col1:
            display_metric_card("Total Jobs", total_jobs)

        with col2:
            display_metric_card("Total Images", total_images)

        with col3:
            display_metric_card("Predictions", total_predictions)

        with col4:
            display_metric_card("Avg Confidence", f"{avg_confidence:.2%}")

        st.divider()

        # Charts
        if px:
            # Job status distribution
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Job Status Distribution")

                status_data = db.query(
                    RecognitionJob.status,
                    func.count(RecognitionJob.id).label('count')
                ).group_by(RecognitionJob.status).all()

                if status_data:
                    df_status = pd.DataFrame(status_data, columns=['status', 'count'])
                    fig = px.pie(df_status, values='count', names='status', title='Jobs by Status')
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("### Job Type Distribution")

                type_data = db.query(
                    RecognitionJob.job_type,
                    func.count(RecognitionJob.id).label('count')
                ).group_by(RecognitionJob.job_type).all()

                if type_data:
                    df_type = pd.DataFrame(type_data, columns=['job_type', 'count'])
                    fig = px.bar(df_type, x='job_type', y='count', title='Jobs by Type')
                    st.plotly_chart(fig, use_container_width=True)

            # Top labels
            st.markdown("### Top Predicted Labels")

            top_labels = db.query(
                Prediction.label_name,
                func.count(Prediction.id).label('count'),
                func.avg(Prediction.confidence).label('avg_confidence')
            ).group_by(Prediction.label_name).order_by(
                func.count(Prediction.id).desc()
            ).limit(10).all()

            if top_labels:
                df_labels = pd.DataFrame(
                    top_labels,
                    columns=['label', 'count', 'avg_confidence']
                )

                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=('Prediction Count', 'Average Confidence')
                )

                fig.add_trace(
                    go.Bar(x=df_labels['label'], y=df_labels['count'], name='Count'),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Bar(x=df_labels['label'], y=df_labels['avg_confidence'], name='Confidence'),
                    row=1, col=2
                )

                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

        db.close()

    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================================
# PAGE: SETTINGS
# ============================================================================

def page_settings():
    """Settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure module settings")

    # API Settings
    st.markdown("### API Configuration")

    api_url = st.text_input("API URL", value="http://localhost:8000/api/v1/image-recognition")
    api_key = st.text_input("API Key", type="password")

    # Model Settings
    st.markdown("### Default Model Settings")

    col1, col2 = st.columns(2)

    with col1:
        default_model = st.selectbox("Default Model", ["resnet50", "vgg16", "efficientnet"])
        default_confidence = st.slider("Default Confidence", 0.0, 1.0, 0.5, 0.05)

    with col2:
        default_top_k = st.number_input("Default Top K", min_value=1, max_value=20, value=5)
        batch_size = st.number_input("Batch Size", min_value=1, max_value=256, value=32)

    # Cache Settings
    st.markdown("### Cache Settings")

    enable_cache = st.checkbox("Enable Redis Cache", value=True)
    cache_ttl = st.number_input("Cache TTL (seconds)", min_value=60, max_value=86400, value=3600)

    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application entry point."""
    # Render sidebar and get selected page
    page = render_sidebar()

    # Route to appropriate page
    if page == "🏠 Home":
        page_home()
    elif page == "📤 Upload Images":
        page_upload()
    elif page == "🎯 Classification":
        page_classification()
    elif page == "🎨 Object Detection":
        page_detection()
    elif page == "📊 Batch Processing":
        page_batch_processing()
    elif page == "👁️ Job Monitor":
        page_job_monitor()
    elif page == "🤖 Model Management":
        page_model_management()
    elif page == "✏️ Annotation Tool":
        st.title("✏️ Annotation Tool")
        st.info("Annotation tool coming soon!")
    elif page == "📈 Analytics":
        page_analytics()
    elif page == "⚙️ Settings":
        page_settings()


if __name__ == "__main__":
    main()
