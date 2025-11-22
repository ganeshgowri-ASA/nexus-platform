"""
Streamlit UI for Image Recognition Module
"""
import streamlit as st
import requests
from PIL import Image
import io
<<<<<<< HEAD
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration
API_BASE_URL = "http://localhost:8001"

st.set_page_config(
    page_title="NEXUS Image Recognition",
    page_icon="🔍",
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-header">🔍 NEXUS Image Recognition</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1E88E5/FFFFFF?text=NEXUS", use_column_width=True)
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["🏠 Home", "📸 Analyze Image", "📊 Analytics", "🤖 Custom Models", "📋 History"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Settings")
        user_id = st.number_input("User ID", min_value=1, value=1)
        provider = st.selectbox("Vision Provider", ["aws", "google"])

    # Page routing
    if page == "🏠 Home":
        show_home()
    elif page == "📸 Analyze Image":
        show_analyze(user_id, provider)
    elif page == "📊 Analytics":
        show_analytics(user_id)
    elif page == "🤖 Custom Models":
        show_models(user_id)
    elif page == "📋 History":
        show_history(user_id)


def show_home():
    """Home page"""
    st.markdown("### Welcome to NEXUS Image Recognition")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🎯 Object Detection</h4>
            <p>Detect and classify objects in images with bounding boxes</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🏷️ Classification</h4>
            <p>Classify images into categories with confidence scores</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>👤 Face Detection</h4>
            <p>Detect faces with age, gender, and emotion analysis</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>🌆 Scene Recognition</h4>
            <p>Identify scenes and environments in images</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick stats
    try:
        response = requests.get(f"{API_BASE_URL}/analytics?days=7")
        if response.status_code == 200:
            data = response.json()

            st.markdown("### 📊 Last 7 Days Statistics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Analyses", data['total_analyses'])

            with col2:
                st.metric("Objects Detected", data['total_objects_detected'])

            with col3:
                st.metric("Faces Detected", data['total_faces_detected'])

            with col4:
                avg_time = data.get('average_processing_time_ms')
                if avg_time:
                    st.metric("Avg Processing Time", f"{avg_time:.0f}ms")
                else:
                    st.metric("Avg Processing Time", "N/A")

    except Exception as e:
        st.info("Start the API server to see statistics")


def show_analyze(user_id, provider):
    """Image analysis page"""
    st.markdown("### 📸 Analyze Image")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Upload Image")

        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)

            analysis_type = st.selectbox(
                "Analysis Type",
                ["object_detection", "image_classification", "face_detection", "scene_recognition"]
            )

            if st.button("🚀 Analyze Image", type="primary"):
                with st.spinner("Analyzing image..."):
                    try:
                        # Reset file pointer
                        uploaded_file.seek(0)

                        # Upload to API
                        files = {'file': uploaded_file}
                        params = {
                            'analysis_type': analysis_type,
                            'user_id': user_id,
                            'provider': provider
                        }

                        response = requests.post(
                            f"{API_BASE_URL}/analyze",
                            files=files,
                            params=params
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Analysis started successfully!")

                            # Store in session state
                            st.session_state['last_analysis'] = result

                            # Display initial result
                            st.json(result)

                            st.info("Processing... Check the History tab for results.")

                        else:
                            st.error(f"Error: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with col2:
        st.markdown("#### Analysis Results")

        if 'last_analysis' in st.session_state:
            analysis_id = st.session_state['last_analysis']['id']

            if st.button("🔄 Refresh Results"):
                try:
                    response = requests.get(f"{API_BASE_URL}/analyses/{analysis_id}")

                    if response.status_code == 200:
                        result = response.json()

                        st.markdown(f"**Status:** {result['status']}")

                        if result['status'] == 'completed':
                            st.success("✅ Analysis completed!")

                            # Display results based on type
                            if result.get('results'):
                                display_results(result, image)

                        elif result['status'] == 'failed':
                            st.error(f"❌ Analysis failed: {result.get('error_message', 'Unknown error')}")

                        else:
                            st.info(f"⏳ Status: {result['status']}")

                    else:
                        st.error("Failed to fetch results")

                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.info("Upload and analyze an image to see results here")


def display_results(result, image):
    """Display analysis results"""
    results = result.get('results', {})

    if 'objects' in results:
        st.markdown("#### 🎯 Detected Objects")
        objects_df = pd.DataFrame(results['objects'])
        if not objects_df.empty:
            st.dataframe(objects_df[['label', 'confidence']].head(10))

            # Visualize top objects
            fig = px.bar(
                objects_df.head(10),
                x='confidence',
                y='label',
                orientation='h',
                title='Top 10 Objects by Confidence'
            )
            st.plotly_chart(fig, use_container_width=True)

    elif 'labels' in results:
        st.markdown("#### 🏷️ Image Labels")
        labels_df = pd.DataFrame(results['labels'])
        if not labels_df.empty:
            st.dataframe(labels_df[['label', 'confidence']].head(10))

            # Visualize confidence
            fig = px.bar(
                labels_df.head(10),
                x='confidence',
                y='label',
                orientation='h',
                title='Classification Confidence'
            )
            st.plotly_chart(fig, use_container_width=True)

    elif 'faces' in results:
        st.markdown("#### 👤 Detected Faces")
        st.write(f"Found {len(results['faces'])} face(s)")

        for i, face in enumerate(results['faces']):
            with st.expander(f"Face {i+1}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Confidence:** {face['confidence']:.2f}")
                    if 'age_range' in face and face['age_range']:
                        st.write(f"**Age Range:** {face['age_range']['low']}-{face['age_range']['high']}")
                    if 'gender' in face and face['gender']:
                        st.write(f"**Gender:** {face['gender']}")

                with col2:
                    if 'emotions' in face and face['emotions']:
                        emotions_df = pd.DataFrame(list(face['emotions'].items()), columns=['Emotion', 'Score'])
                        fig = px.bar(emotions_df, x='Score', y='Emotion', orientation='h', title='Emotions')
                        st.plotly_chart(fig, use_container_width=True)

    elif 'scenes' in results:
        st.markdown("#### 🌆 Scene Recognition")
        if isinstance(results['scenes'], list):
            scenes_df = pd.DataFrame(results['scenes'])
            if not scenes_df.empty:
                st.dataframe(scenes_df.head(10))


def show_analytics(user_id):
    """Analytics page"""
    st.markdown("### 📊 Analytics Dashboard")

    days = st.slider("Time Range (days)", 1, 90, 30)

    try:
        response = requests.get(f"{API_BASE_URL}/analytics?user_id={user_id}&days={days}")
=======
import pandas as pd
from datetime import datetime
import time
import os

# API configuration
API_BASE_URL = os.getenv("IMAGE_API_URL", "http://localhost:8000")


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="NEXUS Image Recognition",
        page_icon="🖼️",
        layout="wide"
    )

    # Sidebar navigation
    st.sidebar.title("🖼️ NEXUS Image Recognition")
    page = st.sidebar.radio(
        "Navigation",
        ["Image Analysis", "Batch Processing", "Analytics", "Custom Models", "History"]
    )

    if page == "Image Analysis":
        image_analysis_page()
    elif page == "Batch Processing":
        batch_processing_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Custom Models":
        custom_models_page()
    elif page == "History":
        history_page()


def image_analysis_page():
    """Image analysis page"""
    st.title("🔍 Image Analysis")
    st.write("Upload an image or provide a URL for analysis")

    # Analysis configuration
    col1, col2 = st.columns([2, 1])

    with col1:
        # Image input method
        input_method = st.radio(
            "Select Input Method",
            ["Upload Image", "Image URL"]
        )

        image = None
        image_url = None

        if input_method == "Upload Image":
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=["jpg", "jpeg", "png", "gif", "bmp", "webp"]
            )
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_container_width=True)

        else:
            image_url = st.text_input("Enter image URL")
            if image_url:
                try:
                    response = requests.get(image_url, timeout=10)
                    image = Image.open(io.BytesIO(response.content))
                    st.image(image, caption="Image from URL", use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to load image: {str(e)}")

    with col2:
        st.subheader("Analysis Settings")

        analysis_type = st.selectbox(
            "Analysis Type",
            [
                "object_detection",
                "image_classification",
                "face_detection",
                "scene_recognition"
            ],
            format_func=lambda x: x.replace("_", " ").title()
        )

        provider = st.selectbox(
            "Provider",
            ["google_vision", "aws_rekognition"],
            format_func=lambda x: x.replace("_", " ").title()
        )

        analyze_button = st.button("🚀 Analyze Image", type="primary", use_container_width=True)

    # Perform analysis
    if analyze_button:
        if not image and not image_url:
            st.error("Please provide an image (upload or URL)")
            return

        with st.spinner("Analyzing image..."):
            try:
                if input_method == "Upload Image" and uploaded_file:
                    # Upload file to API
                    files = {"file": uploaded_file.getvalue()}
                    data = {
                        "analysis_type": analysis_type,
                        "provider": provider
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/analyze/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        params=data,
                        timeout=30
                    )
                else:
                    # Use image URL
                    data = {
                        "image_url": image_url,
                        "analysis_type": analysis_type,
                        "provider": provider
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/analyze",
                        json=data,
                        timeout=30
                    )

                if response.status_code in [200, 201]:
                    result = response.json()
                    analysis_id = result["id"]

                    # Poll for results
                    with st.spinner("Processing... This may take a few seconds"):
                        time.sleep(2)  # Initial wait
                        for _ in range(30):  # Poll for up to 30 seconds
                            status_response = requests.get(
                                f"{API_BASE_URL}/analyze/{analysis_id}",
                                timeout=10
                            )
                            if status_response.status_code == 200:
                                analysis_result = status_response.json()
                                if analysis_result["status"] == "completed":
                                    display_analysis_results(analysis_result, image)
                                    break
                                elif analysis_result["status"] == "failed":
                                    st.error(f"Analysis failed: {analysis_result.get('error_message', 'Unknown error')}")
                                    break
                            time.sleep(1)
                        else:
                            st.info("Analysis is still processing. Check the History page for results.")
                            st.write(f"Analysis ID: {analysis_id}")

                else:
                    st.error(f"API Error: {response.text}")

            except Exception as e:
                st.error(f"Error: {str(e)}")


def display_analysis_results(result, image):
    """Display analysis results"""
    st.success("✅ Analysis Complete!")

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", result["status"].upper())
    with col2:
        st.metric("Provider", result["provider"].replace("_", " ").title())
    with col3:
        if result.get("confidence_score"):
            st.metric("Avg Confidence", f"{result['confidence_score']:.2%}")

    # Display results based on analysis type
    analysis_type = result["analysis_type"]

    if analysis_type == "object_detection" and result.get("objects"):
        st.subheader("🎯 Detected Objects")
        objects_df = pd.DataFrame([
            {
                "Object": obj["name"],
                "Confidence": f"{obj['confidence']:.2%}",
                "Bounding Box": f"({obj['bbox']['x']:.2f}, {obj['bbox']['y']:.2f})" if obj.get("bbox") else "N/A"
            }
            for obj in result["objects"]
        ])
        st.dataframe(objects_df, use_container_width=True)

    elif analysis_type == "image_classification" and result.get("labels"):
        st.subheader("🏷️ Image Labels")
        labels_df = pd.DataFrame([
            {
                "Label": label["name"],
                "Confidence": f"{label['confidence']:.2%}",
                "Category": label.get("category", "N/A")
            }
            for label in result["labels"]
        ])
        st.dataframe(labels_df, use_container_width=True)

    elif analysis_type == "face_detection" and result.get("faces"):
        st.subheader("👤 Detected Faces")
        for i, face in enumerate(result["faces"], 1):
            with st.expander(f"Face {i} (Confidence: {face['confidence']:.2%})"):
                col1, col2 = st.columns(2)
                with col1:
                    if face.get("age_range"):
                        st.write(f"**Age Range:** {face['age_range']['low']}-{face['age_range']['high']}")
                    if face.get("gender"):
                        st.write(f"**Gender:** {face['gender']}")
                with col2:
                    if face.get("emotions"):
                        st.write("**Emotions:**")
                        for emotion, score in face["emotions"].items():
                            st.write(f"- {emotion.title()}: {score:.2%}")

    elif analysis_type == "scene_recognition" and result.get("scenes"):
        st.subheader("🌍 Detected Scenes")
        scenes_df = pd.DataFrame([
            {
                "Scene": scene["scene_type"],
                "Confidence": f"{scene['confidence']:.2%}"
            }
            for scene in result["scenes"]
        ])
        st.dataframe(scenes_df, use_container_width=True)


def batch_processing_page():
    """Batch processing page"""
    st.title("📦 Batch Image Processing")
    st.write("Process multiple images at once")

    # Batch input
    image_urls = st.text_area(
        "Enter image URLs (one per line)",
        height=200,
        placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg"
    )

    col1, col2 = st.columns(2)
    with col1:
        analysis_type = st.selectbox(
            "Analysis Type",
            [
                "object_detection",
                "image_classification",
                "face_detection",
                "scene_recognition"
            ],
            format_func=lambda x: x.replace("_", " ").title(),
            key="batch_analysis_type"
        )

    with col2:
        provider = st.selectbox(
            "Provider",
            ["google_vision", "aws_rekognition"],
            format_func=lambda x: x.replace("_", " ").title(),
            key="batch_provider"
        )

    if st.button("🚀 Start Batch Processing", type="primary"):
        if not image_urls.strip():
            st.error("Please enter at least one image URL")
            return

        urls = [url.strip() for url in image_urls.split("\n") if url.strip()]

        with st.spinner(f"Processing {len(urls)} images..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze/batch",
                    json={
                        "images": urls,
                        "analysis_type": analysis_type,
                        "provider": provider
                    },
                    timeout=30
                )

                if response.status_code == 202:
                    result = response.json()
                    st.success(f"✅ Batch processing started!")
                    st.json(result)
                else:
                    st.error(f"Error: {response.text}")

            except Exception as e:
                st.error(f"Error: {str(e)}")


def analytics_page():
    """Analytics dashboard page"""
    st.title("📊 Analytics Dashboard")

    try:
        response = requests.get(f"{API_BASE_URL}/analytics", timeout=10)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

        if response.status_code == 200:
            data = response.json()

<<<<<<< HEAD
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Analyses", data['total_analyses'])

            with col2:
                st.metric("Objects Detected", data['total_objects_detected'])

            with col3:
                st.metric("Faces Detected", data['total_faces_detected'])

            with col4:
                avg_time = data.get('average_processing_time_ms')
                if avg_time:
                    st.metric("Avg Processing", f"{avg_time:.0f}ms")
                else:
                    st.metric("Avg Processing", "N/A")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                # Analyses by type
                if data['analyses_by_type']:
                    st.markdown("#### Analyses by Type")
                    type_df = pd.DataFrame(list(data['analyses_by_type'].items()), columns=['Type', 'Count'])
                    fig = px.pie(type_df, values='Count', names='Type', title='Analysis Types')
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Analyses by status
                if data['analyses_by_status']:
                    st.markdown("#### Analyses by Status")
                    status_df = pd.DataFrame(list(data['analyses_by_status'].items()), columns=['Status', 'Count'])
                    fig = px.pie(status_df, values='Count', names='Status', title='Analysis Status')
                    st.plotly_chart(fig, use_container_width=True)

            # Most detected labels
            if data['most_detected_labels']:
                st.markdown("#### 🏆 Most Detected Labels")
                labels_df = pd.DataFrame(data['most_detected_labels'])
                fig = px.bar(labels_df, x='count', y='label', orientation='h', title='Top Detected Labels')
                st.plotly_chart(fig, use_container_width=True)
=======
            # Overview metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Analyses", data["total_analyses"])
            with col2:
                st.metric("Average Confidence", f"{data['average_confidence']:.2%}")
            with col3:
                completed = data["analyses_by_status"].get("completed", 0)
                st.metric("Completed", completed)

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Analyses by Type")
                if data["analyses_by_type"]:
                    st.bar_chart(data["analyses_by_type"])

            with col2:
                st.subheader("Analyses by Status")
                if data["analyses_by_status"]:
                    st.bar_chart(data["analyses_by_status"])

            # Top detections
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🎯 Most Detected Objects")
                if data["most_detected_objects"]:
                    objects_df = pd.DataFrame(data["most_detected_objects"])
                    st.dataframe(objects_df, use_container_width=True)

            with col2:
                st.subheader("🏷️ Most Detected Labels")
                if data["most_detected_labels"]:
                    labels_df = pd.DataFrame(data["most_detected_labels"])
                    st.dataframe(labels_df, use_container_width=True)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

        else:
            st.error("Failed to load analytics")

    except Exception as e:
        st.error(f"Error: {str(e)}")


<<<<<<< HEAD
def show_models(user_id):
    """Custom models page"""
    st.markdown("### 🤖 Custom Models")

    tab1, tab2 = st.tabs(["📋 My Models", "➕ Train New Model"])

    with tab1:
        try:
            response = requests.get(f"{API_BASE_URL}/models?user_id={user_id}")

            if response.status_code == 200:
                models = response.json()

                if models:
                    for model in models:
                        with st.expander(f"{model['name']} - {model['training_status']}"):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write(f"**Type:** {model['model_type']}")
                                st.write(f"**Status:** {model['training_status']}")
                                st.write(f"**Created:** {model['created_at']}")

                            with col2:
                                if model['accuracy']:
                                    st.metric("Accuracy", f"{model['accuracy']:.2%}")
                                if model['precision']:
                                    st.metric("Precision", f"{model['precision']:.2%}")
                                if model['recall']:
                                    st.metric("Recall", f"{model['recall']:.2%}")

                            if model['description']:
                                st.write(f"**Description:** {model['description']}")
                else:
                    st.info("No custom models found. Train your first model!")

            else:
                st.error("Failed to load models")

        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
        st.markdown("#### Train New Custom Model")

        with st.form("train_model_form"):
            name = st.text_input("Model Name*")
            description = st.text_area("Description")
            model_type = st.selectbox("Model Type*", ["classification", "detection", "segmentation"])
            dataset_id = st.number_input("Dataset ID*", min_value=1, value=1)

            submitted = st.form_submit_button("🚀 Start Training")

            if submitted:
                if name and model_type:
                    try:
                        payload = {
                            "name": name,
                            "description": description,
                            "model_type": model_type,
                            "dataset_id": dataset_id,
                            "user_id": user_id
                        }

                        response = requests.post(f"{API_BASE_URL}/models/train", json=payload)

                        if response.status_code == 200:
                            st.success("✅ Model training started!")
                            st.json(response.json())
                        else:
                            st.error(f"Error: {response.text}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")


def show_history(user_id):
    """Analysis history page"""
    st.markdown("### 📋 Analysis History")

    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_type_filter = st.selectbox(
            "Analysis Type",
            ["All", "object_detection", "image_classification", "face_detection", "scene_recognition"]
        )

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "pending", "processing", "completed", "failed"]
        )

    with col3:
        limit = st.number_input("Results per page", min_value=10, max_value=100, value=50)

    try:
        params = {"user_id": user_id, "limit": limit}

        if analysis_type_filter != "All":
            params["analysis_type"] = analysis_type_filter

        if status_filter != "All":
            params["status"] = status_filter

        response = requests.get(f"{API_BASE_URL}/analyses", params=params)
=======
def custom_models_page():
    """Custom models management page"""
    st.title("🤖 Custom Models")

    # List existing models
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            if models:
                st.subheader("Available Models")
                models_df = pd.DataFrame([
                    {
                        "Name": m["name"],
                        "Type": m["model_type"],
                        "Version": m["model_version"],
                        "Classes": len(m["classes"]),
                        "Accuracy": f"{m['training_accuracy']:.2%}" if m.get("training_accuracy") else "N/A",
                        "Created": m["created_at"]
                    }
                    for m in models
                ])
                st.dataframe(models_df, use_container_width=True)
            else:
                st.info("No custom models available")
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")

    # Add new model form
    st.subheader("➕ Add New Model")
    with st.form("add_model_form"):
        name = st.text_input("Model Name")
        description = st.text_area("Description")
        model_type = st.selectbox("Model Type", ["classification", "detection", "segmentation"])
        model_path = st.text_input("Model Path")

        submitted = st.form_submit_button("Add Model")
        if submitted and name and model_path:
            st.info("Model creation feature coming soon!")


def history_page():
    """Analysis history page"""
    st.title("📜 Analysis History")

    try:
        response = requests.get(f"{API_BASE_URL}/analyses?limit=50", timeout=10)
>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a

        if response.status_code == 200:
            analyses = response.json()

            if analyses:
<<<<<<< HEAD
                for analysis in analyses:
                    with st.expander(f"{analysis['image_name']} - {analysis['created_at']}"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**ID:** {analysis['id']}")
                            st.write(f"**Type:** {analysis['analysis_type']}")
                            st.write(f"**Status:** {analysis['status']}")

                        with col2:
                            if analysis['confidence_score']:
                                st.write(f"**Confidence:** {analysis['confidence_score']:.2f}")
                            if analysis['processing_time_ms']:
                                st.write(f"**Processing Time:** {analysis['processing_time_ms']}ms")

                        with col3:
                            if st.button("View Details", key=f"view_{analysis['id']}"):
                                st.json(analysis)

                            if st.button("Delete", key=f"delete_{analysis['id']}"):
                                delete_response = requests.delete(f"{API_BASE_URL}/analyses/{analysis['id']}")
                                if delete_response.status_code == 200:
                                    st.success("Deleted!")
                                    st.rerun()
=======
                df = pd.DataFrame([
                    {
                        "ID": a["id"],
                        "Type": a["analysis_type"].replace("_", " ").title(),
                        "Status": a["status"].upper(),
                        "Provider": a["provider"].replace("_", " ").title(),
                        "Confidence": f"{a['confidence_score']:.2%}" if a.get("confidence_score") else "N/A",
                        "Created": a["created_at"],
                        "Image": a.get("image_url", a.get("image_path", "N/A"))[:50] + "..."
                    }
                    for a in analyses
                ])

                st.dataframe(df, use_container_width=True)

                # View details
                selected_id = st.number_input("Enter Analysis ID to view details", min_value=1, step=1)
                if st.button("View Details"):
                    detail_response = requests.get(f"{API_BASE_URL}/analyze/{selected_id}", timeout=10)
                    if detail_response.status_code == 200:
                        result = detail_response.json()
                        display_analysis_results(result, None)
                    else:
                        st.error("Analysis not found")

>>>>>>> origin/claude/image-recognition-testing-modules-01EHvbuBeofcgPwBsgHTbh4a
            else:
                st.info("No analyses found")

        else:
            st.error("Failed to load history")

    except Exception as e:
        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
