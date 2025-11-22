"""Translation Module Page"""
import streamlit as st
import requests
import pandas as pd
import os


def show():
    """Display Translation page"""
    st.markdown("# 🌐 Translation Module")
    st.markdown("### Translate text to 100+ languages")

    # Get API URL from environment
    api_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    # Tabs for different functionality
    tab1, tab2, tab3, tab4 = st.tabs(["🔤 Translate", "📦 Batch Translation", "📚 Glossaries", "📋 History"])

    with tab1:
        st.markdown("### Single Text Translation")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Text input
            source_text = st.text_area(
                "Enter text to translate",
                height=200,
                placeholder="Type or paste your text here...",
                help="Enter the text you want to translate"
            )

            # Character count
            char_count = len(source_text)
            st.caption(f"Characters: {char_count:,}")

        with col2:
            st.markdown("### Translation Options")

            # Language selection
            source_lang = st.selectbox(
                "Source Language",
                ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi"],
                help="Select 'auto' for automatic detection"
            )

            target_lang = st.selectbox(
                "Target Language",
                ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi"],
                index=1
            )

            service = st.selectbox(
                "Translation Service",
                ["google", "anthropic", "deepl"],
                help="Select the translation service"
            )

            # Advanced options
            with st.expander("Advanced Options"):
                context = st.text_area(
                    "Context (optional)",
                    help="Provide context to improve translation quality"
                )

                # Glossary selection (placeholder)
                use_glossary = st.checkbox("Use Custom Glossary")
                if use_glossary:
                    st.info("Load your glossaries from the Glossaries tab")

                user_id = st.text_input("User ID (optional)")

        # Translate button
        if source_text and st.button("🚀 Translate", type="primary"):
            with st.spinner("Translating..."):
                try:
                    # Prepare request
                    payload = {
                        "text": source_text,
                        "source_language": source_lang,
                        "target_language": target_lang,
                        "service": service
                    }

                    if context:
                        payload["context"] = context

                    params = {}
                    if user_id:
                        params["user_id"] = user_id

                    # Make API request
                    response = requests.post(
                        f"{api_url}/api/v1/translation/translate",
                        json=payload,
                        params=params,
                        timeout=60
                    )

                    if response.status_code == 201:
                        result = response.json()

                        st.success("✅ Translation completed!")

                        # Display translation
                        st.markdown("---")
                        st.markdown("### 📝 Translation Result")

                        translated_text = result.get("translated_text", "")
                        st.text_area(
                            "Translated Text",
                            value=translated_text,
                            height=200,
                            help="Copy or download the translation"
                        )

                        # Download button
                        st.download_button(
                            label="📥 Download Translation",
                            data=translated_text,
                            file_name=f"translation_{target_lang}.txt",
                            mime="text/plain"
                        )

                        # Metrics
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "Quality Score",
                                f"{result.get('quality_score', 0):.1f}/100"
                            )

                        with col2:
                            st.metric(
                                "Confidence",
                                f"{result.get('confidence_score', 0) * 100:.1f}%"
                            )

                        with col3:
                            detected = result.get('detected_language', source_lang)
                            st.metric(
                                "Detected Language",
                                detected.upper() if detected else "N/A"
                            )

                        with col4:
                            st.metric(
                                "Processing Time",
                                f"{result.get('processing_time', 0):.2f}s"
                            )

                    else:
                        error_detail = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Translation failed: {error_detail}")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                    st.info("💡 Make sure the backend API is running at " + api_url)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with tab2:
        st.markdown("### 📦 Batch Translation")
        st.markdown("Translate multiple texts at once")

        # Batch input
        batch_method = st.radio(
            "Input Method",
            ["Text Area (one per line)", "Upload CSV"]
        )

        texts_to_translate = []

        if batch_method == "Text Area (one per line)":
            batch_text = st.text_area(
                "Enter texts to translate (one per line)",
                height=200,
                placeholder="Line 1\nLine 2\nLine 3..."
            )

            if batch_text:
                texts_to_translate = [line.strip() for line in batch_text.split('\n') if line.strip()]
                st.info(f"Found {len(texts_to_translate)} texts to translate")

        else:
            uploaded_csv = st.file_uploader(
                "Upload CSV file with 'text' column",
                type=["csv"]
            )

            if uploaded_csv:
                df = pd.read_csv(uploaded_csv)
                if 'text' in df.columns:
                    texts_to_translate = df['text'].tolist()
                    st.success(f"Loaded {len(texts_to_translate)} texts from CSV")
                    st.dataframe(df.head(), use_container_width=True)
                else:
                    st.error("CSV must have a 'text' column")

        # Batch options
        col1, col2 = st.columns(2)

        with col1:
            batch_source_lang = st.selectbox(
                "Source Language",
                ["auto", "en", "es", "fr", "de"],
                key="batch_source"
            )

        with col2:
            batch_target_lang = st.selectbox(
                "Target Language",
                ["en", "es", "fr", "de"],
                key="batch_target"
            )

        batch_service = st.selectbox(
            "Translation Service",
            ["google", "anthropic"],
            key="batch_service"
        )

        # Translate batch
        if texts_to_translate and st.button("🚀 Translate Batch", type="primary"):
            with st.spinner(f"Translating {len(texts_to_translate)} texts..."):
                try:
                    payload = {
                        "texts": texts_to_translate,
                        "source_language": batch_source_lang,
                        "target_language": batch_target_lang,
                        "service": batch_service
                    }

                    response = requests.post(
                        f"{api_url}/api/v1/translation/batch",
                        json=payload,
                        timeout=300
                    )

                    if response.status_code == 201:
                        result = response.json()

                        st.success(f"✅ Batch translation completed!")
                        st.markdown(f"**Completed:** {result['completed_items']} | **Failed:** {result['failed_items']}")

                        # Show batch ID for reference
                        st.info(f"Batch ID: {result['id']}")

                    else:
                        st.error(f"❌ Batch translation failed: {response.json().get('detail')}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with tab3:
        st.markdown("### 📚 Custom Glossaries")
        st.markdown("Create and manage translation glossaries for consistent terminology")

        # Create new glossary
        with st.expander("➕ Create New Glossary", expanded=False):
            glossary_name = st.text_input("Glossary Name")
            glossary_desc = st.text_area("Description (optional)")

            col1, col2 = st.columns(2)
            with col1:
                gloss_source_lang = st.selectbox("Source Language", ["en", "es", "fr", "de"], key="gloss_source")
            with col2:
                gloss_target_lang = st.selectbox("Target Language", ["en", "es", "fr", "de"], key="gloss_target")

            st.markdown("**Glossary Entries**")
            st.caption("Enter term pairs (source term → translation)")

            # Dynamic entry input
            num_entries = st.number_input("Number of entries", min_value=1, max_value=50, value=5)

            entries = {}
            for i in range(num_entries):
                col1, col2 = st.columns(2)
                with col1:
                    term = st.text_input(f"Term {i+1}", key=f"term_{i}")
                with col2:
                    translation = st.text_input(f"Translation {i+1}", key=f"trans_{i}")

                if term and translation:
                    entries[term] = translation

            if st.button("💾 Create Glossary"):
                if glossary_name and entries:
                    try:
                        payload = {
                            "name": glossary_name,
                            "description": glossary_desc,
                            "source_language": gloss_source_lang,
                            "target_language": gloss_target_lang,
                            "entries": entries
                        }

                        response = requests.post(
                            f"{api_url}/api/v1/translation/glossaries",
                            json=payload
                        )

                        if response.status_code == 201:
                            st.success("✅ Glossary created successfully!")
                            st.json(response.json())
                        else:
                            st.error(f"❌ Failed to create glossary: {response.json().get('detail')}")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("Please provide a name and at least one entry")

        # List existing glossaries
        st.markdown("---")
        st.markdown("### Existing Glossaries")

        if st.button("🔄 Load Glossaries"):
            try:
                response = requests.get(f"{api_url}/api/v1/translation/glossaries")

                if response.status_code == 200:
                    glossaries = response.json()

                    if glossaries:
                        for gloss in glossaries:
                            with st.expander(f"📚 {gloss['name']} ({gloss['entry_count']} entries)"):
                                st.markdown(f"**Languages:** {gloss['source_language']} → {gloss['target_language']}")
                                st.markdown(f"**Created:** {gloss['created_at'][:10]}")
                                if gloss.get('description'):
                                    st.markdown(f"**Description:** {gloss['description']}")
                    else:
                        st.info("No glossaries found. Create one above!")
                else:
                    st.error("Failed to load glossaries")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    with tab4:
        st.markdown("### 📋 Translation History")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            history_user_id = st.text_input("Filter by User ID", key="history_user")

        with col2:
            history_status = st.selectbox(
                "Filter by Status",
                ["All", "pending", "processing", "completed", "failed"],
                key="history_status"
            )

        with col3:
            history_page_size = st.number_input("Items per page", min_value=5, max_value=50, value=10, key="history_page")

        if st.button("🔍 Load History", key="load_history"):
            try:
                params = {"page": 1, "page_size": history_page_size}

                if history_user_id:
                    params["user_id"] = history_user_id

                if history_status != "All":
                    params["status"] = history_status

                response = requests.get(
                    f"{api_url}/api/v1/translation/translations",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])

                    if items:
                        st.success(f"Found {data.get('total', 0)} translations")

                        # Display as table
                        df = pd.DataFrame([
                            {
                                "ID": item["id"][:8] + "...",
                                "Source": item["source_text"][:50] + "..." if len(item["source_text"]) > 50 else item["source_text"],
                                "Languages": f"{item['source_language']} → {item['target_language']}",
                                "Status": item["status"],
                                "Quality": f"{item.get('quality_score', 0):.1f}",
                                "Created": item["created_at"][:10]
                            }
                            for item in items
                        ])

                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No translations found")
                else:
                    st.error("Failed to load history")

            except Exception as e:
                st.error(f"Error: {str(e)}")
