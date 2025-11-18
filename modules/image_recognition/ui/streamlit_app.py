"""
Streamlit UI for Image Recognition Module
"""
import streamlit as st
import requests
from PIL import Image
import io
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

        if response.status_code == 200:
            data = response.json()

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

        else:
            st.error("Failed to load analytics")

    except Exception as e:
        st.error(f"Error: {str(e)}")


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

        if response.status_code == 200:
            analyses = response.json()

            if analyses:
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

            else:
                st.info("No analyses found")

        else:
            st.error("Failed to load history")

    except Exception as e:
        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
