"""OCR Module Page"""
import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
import os


def show():
    """Display OCR page"""
    st.markdown("# 📄 OCR Module")
    st.markdown("### Extract text from images and PDFs")

    # Get API URL from environment
    api_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    # Tabs for different functionality
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Extract", "📋 History", "📊 Statistics"])

    with tab1:
        st.markdown("### Upload Document for OCR")

        col1, col2 = st.columns([2, 1])

        with col1:
            # File uploader
            uploaded_file = st.file_uploader(
                "Choose an image or PDF file",
                type=["png", "jpg", "jpeg", "tiff", "pdf"],
                help="Supported formats: PNG, JPEG, TIFF, PDF"
            )

            if uploaded_file:
                # Display image preview (if it's an image)
                if uploaded_file.type.startswith("image"):
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Uploaded Image", use_column_width=True)
                else:
                    st.info(f"📄 PDF uploaded: {uploaded_file.name}")

        with col2:
            st.markdown("### OCR Options")

            engine = st.selectbox(
                "OCR Engine",
                ["tesseract", "google_vision", "aws_textract"],
                help="Select the OCR engine to use"
            )

            detect_language = st.checkbox("Detect Language", value=True)
            extract_tables = st.checkbox("Extract Tables", value=True)
            detect_handwriting = st.checkbox("Detect Handwriting", value=True)
            analyze_layout = st.checkbox("Analyze Layout", value=True)

            user_id = st.text_input("User ID (optional)", help="Optional user identifier")

        # Process button
        if uploaded_file and st.button("🚀 Extract Text", type="primary"):
            with st.spinner("Processing OCR... This may take a moment..."):
                try:
                    # Prepare the request
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                    }

                    data = {
                        "engine": engine,
                        "detect_language": detect_language,
                        "extract_tables": extract_tables,
                        "detect_handwriting": detect_handwriting,
                        "analyze_layout": analyze_layout,
                    }

                    if user_id:
                        data["user_id"] = user_id

                    # Make API request
                    response = requests.post(
                        f"{api_url}/api/v1/ocr/extract",
                        files=files,
                        data=data,
                        timeout=300  # 5 minutes timeout
                    )

                    if response.status_code == 201:
                        result = response.json()

                        st.success("✅ Text extraction completed!")

                        # Display results
                        st.markdown("---")
                        st.markdown("### 📝 Extracted Text")

                        # Show extracted text
                        extracted_text = result.get("extracted_text", "")
                        st.text_area(
                            "Extracted Text",
                            value=extracted_text,
                            height=300,
                            help="Copy this text or download below"
                        )

                        # Download button
                        st.download_button(
                            label="📥 Download Text",
                            data=extracted_text,
                            file_name=f"{uploaded_file.name}_extracted.txt",
                            mime="text/plain"
                        )

                        # Metadata
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "Confidence Score",
                                f"{result.get('confidence_score', 0) * 100:.1f}%"
                            )

                        with col2:
                            st.metric(
                                "Language",
                                result.get('detected_language', 'N/A').upper()
                            )

                        with col3:
                            st.metric(
                                "Tables Found",
                                result.get('tables_detected', 0)
                            )

                        with col4:
                            st.metric(
                                "Processing Time",
                                f"{result.get('processing_time', 0):.2f}s"
                            )

                        # Show tables if extracted
                        if result.get('tables_detected', 0) > 0 and result.get('table_data'):
                            st.markdown("---")
                            st.markdown("### 📊 Extracted Tables")

                            for idx, table in enumerate(result.get('table_data', []), 1):
                                with st.expander(f"Table {idx}"):
                                    if table.get('data'):
                                        df = pd.DataFrame(table['data'])
                                        st.dataframe(df, use_container_width=True)
                                    else:
                                        st.info("Table structure detected but data extraction pending")

                        # Show layout analysis
                        if analyze_layout and result.get('layout_analysis'):
                            with st.expander("🔍 Layout Analysis"):
                                st.json(result['layout_analysis'])

                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                    st.info("💡 Make sure the backend API is running at " + api_url)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with tab2:
        st.markdown("### 📋 OCR History")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            history_user_id = st.text_input("Filter by User ID")

        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "pending", "processing", "completed", "failed"]
            )

        with col3:
            page_size = st.number_input("Items per page", min_value=5, max_value=50, value=10)

        if st.button("🔍 Load History"):
            try:
                params = {"page": 1, "page_size": page_size}

                if history_user_id:
                    params["user_id"] = history_user_id

                if status_filter != "All":
                    params["status"] = status_filter

                response = requests.get(
                    f"{api_url}/api/v1/ocr/documents",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])

                    if items:
                        st.success(f"Found {data.get('total', 0)} documents")

                        # Display as table
                        df = pd.DataFrame([
                            {
                                "ID": item["id"][:8] + "...",
                                "File Name": item["file_name"],
                                "Status": item["status"],
                                "Language": item.get("detected_language", "N/A"),
                                "Confidence": f"{item.get('confidence_score', 0) * 100:.1f}%",
                                "Created": item["created_at"][:10]
                            }
                            for item in items
                        ])

                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No documents found")
                else:
                    st.error("Failed to load history")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    with tab3:
        st.markdown("### 📊 OCR Statistics")

        st.info("Statistics dashboard coming soon!")
        st.markdown("""
        Future features:
        - Total documents processed
        - Success rate
        - Average processing time
        - Language distribution
        - Engine performance comparison
        """)
