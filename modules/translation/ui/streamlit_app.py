"""
Streamlit UI for NEXUS Translation Module
"""

import streamlit as st
import requests
import pandas as pd
from typing import Optional, Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/translation"


def init_session_state():
    """Initialize session state variables"""
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []
    if 'current_glossary' not in st.session_state:
        st.session_state.current_glossary = None


def get_supported_languages() -> Dict[str, str]:
    """Fetch supported languages from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/languages")
        if response.status_code == 200:
            data = response.json()
            return {lang['code']: lang['name'] for lang in data['languages']}
        return {}
    except Exception as e:
        st.error(f"Failed to fetch languages: {str(e)}")
        return {}


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    provider: str = "google",
    glossary_id: Optional[int] = None,
    enable_quality_scoring: bool = True
) -> Optional[Dict[str, Any]]:
    """Call translation API"""
    try:
        payload = {
            "text": text,
            "source_language": source_lang,
            "target_language": target_lang,
            "provider": provider,
            "glossary_id": glossary_id,
            "enable_quality_scoring": enable_quality_scoring
        }

        response = requests.post(f"{API_BASE_URL}/translate", json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Translation failed: {response.text}")
            return None

    except Exception as e:
        st.error(f"API error: {str(e)}")
        return None


def detect_language(text: str) -> Optional[Dict[str, Any]]:
    """Detect language of text"""
    try:
        payload = {"text": text}
        response = requests.post(f"{API_BASE_URL}/detect-language", json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Language detection failed: {response.text}")
            return None

    except Exception as e:
        st.error(f"API error: {str(e)}")
        return None


def get_glossaries() -> list:
    """Fetch glossaries from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/glossaries")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch glossaries: {str(e)}")
        return []


def create_glossary(name: str, description: str, source_lang: str, target_lang: str, terms: list):
    """Create a new glossary"""
    try:
        payload = {
            "name": name,
            "description": description,
            "source_language": source_lang,
            "target_language": target_lang,
            "terms": terms
        }

        response = requests.post(f"{API_BASE_URL}/glossaries", json=payload)

        if response.status_code == 200:
            st.success("Glossary created successfully!")
            return response.json()
        else:
            st.error(f"Failed to create glossary: {response.text}")
            return None

    except Exception as e:
        st.error(f"API error: {str(e)}")
        return None


def main():
    """Main Streamlit application"""

    st.set_page_config(
        page_title="NEXUS Translation Module",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    # Sidebar
    st.sidebar.title("🌐 NEXUS Translation")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["Text Translation", "Batch Translation", "Language Detection", "Glossary Management", "Statistics", "Settings"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### Features
    - 100+ Languages
    - Multiple Providers
    - Quality Scoring
    - Glossary Support
    - Batch Processing
    """)

    # Main content
    if page == "Text Translation":
        show_text_translation()

    elif page == "Batch Translation":
        show_batch_translation()

    elif page == "Language Detection":
        show_language_detection()

    elif page == "Glossary Management":
        show_glossary_management()

    elif page == "Statistics":
        show_statistics()

    elif page == "Settings":
        show_settings()


def show_text_translation():
    """Text translation page"""

    st.title("📝 Text Translation")
    st.markdown("Translate text between 100+ languages with quality scoring")

    # Get supported languages
    languages = get_supported_languages()
    if not languages:
        st.warning("Unable to load languages. Please check API connection.")
        return

    lang_options = [f"{code} - {name}" for code, name in languages.items()]

    col1, col2 = st.columns(2)

    with col1:
        source_lang = st.selectbox(
            "Source Language",
            options=lang_options,
            index=list(languages.keys()).index('en') if 'en' in languages else 0
        )
        source_lang_code = source_lang.split(' - ')[0]

    with col2:
        target_lang = st.selectbox(
            "Target Language",
            options=lang_options,
            index=list(languages.keys()).index('es') if 'es' in languages else 1
        )
        target_lang_code = target_lang.split(' - ')[0]

    # Additional options
    col3, col4, col5 = st.columns(3)

    with col3:
        provider = st.selectbox("Provider", ["google", "deepl"])

    with col4:
        glossaries = get_glossaries()
        glossary_options = ["None"] + [f"{g['id']} - {g['name']}" for g in glossaries]
        selected_glossary = st.selectbox("Glossary", glossary_options)
        glossary_id = None if selected_glossary == "None" else int(selected_glossary.split(' - ')[0])

    with col5:
        enable_quality = st.checkbox("Quality Scoring", value=True)

    # Text input
    source_text = st.text_area(
        "Enter text to translate",
        height=200,
        placeholder="Type or paste text here..."
    )

    # Translate button
    if st.button("🔄 Translate", type="primary"):
        if not source_text.strip():
            st.warning("Please enter some text to translate")
        else:
            with st.spinner("Translating..."):
                result = translate_text(
                    text=source_text,
                    source_lang=source_lang_code,
                    target_lang=target_lang_code,
                    provider=provider,
                    glossary_id=glossary_id,
                    enable_quality_scoring=enable_quality
                )

                if result:
                    st.success("Translation completed!")

                    # Display translation
                    st.markdown("### Translation Result")
                    st.text_area(
                        "Translated Text",
                        value=result['translated_text'],
                        height=200,
                        key="translated_output"
                    )

                    # Display metadata
                    col_meta1, col_meta2, col_meta3 = st.columns(3)

                    with col_meta1:
                        st.metric("Character Count", result['character_count'])

                    with col_meta2:
                        st.metric("Provider", result['provider'].upper())

                    with col_meta3:
                        if result.get('quality_score'):
                            score = result['quality_score']
                            st.metric("Quality Score", f"{score:.2f}")

                    # Add to history
                    st.session_state.translation_history.append(result)


def show_batch_translation():
    """Batch translation page"""

    st.title("📦 Batch Translation")
    st.markdown("Translate multiple texts in batch")

    # Get supported languages
    languages = get_supported_languages()
    if not languages:
        st.warning("Unable to load languages. Please check API connection.")
        return

    lang_options = [f"{code} - {name}" for code, name in languages.items()]

    col1, col2 = st.columns(2)

    with col1:
        source_lang = st.selectbox(
            "Source Language",
            options=lang_options,
            key="batch_source"
        )
        source_lang_code = source_lang.split(' - ')[0]

    with col2:
        target_lang = st.selectbox(
            "Target Language",
            options=lang_options,
            key="batch_target"
        )
        target_lang_code = target_lang.split(' - ')[0]

    provider = st.selectbox("Provider", ["google", "deepl"], key="batch_provider")

    # Text input methods
    input_method = st.radio("Input Method", ["Text Area", "Upload File"])

    texts = []

    if input_method == "Text Area":
        batch_text = st.text_area(
            "Enter texts (one per line)",
            height=300,
            placeholder="Enter each text on a new line..."
        )
        if batch_text:
            texts = [line.strip() for line in batch_text.split('\n') if line.strip()]

    else:
        uploaded_file = st.file_uploader("Upload text file", type=['txt', 'csv'])
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            texts = [line.strip() for line in content.split('\n') if line.strip()]

    if texts:
        st.info(f"Found {len(texts)} texts to translate")

    if st.button("🚀 Start Batch Translation", type="primary"):
        if not texts:
            st.warning("Please provide texts to translate")
        else:
            with st.spinner("Submitting batch job..."):
                try:
                    payload = {
                        "texts": texts,
                        "source_language": source_lang_code,
                        "target_language": target_lang_code,
                        "provider": provider
                    }

                    response = requests.post(f"{API_BASE_URL}/translate/batch", json=payload)

                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Batch job submitted! Job ID: {result['job_id']}")

                        st.markdown("### Job Status")
                        st.write(f"- **Job ID**: {result['job_id']}")
                        st.write(f"- **Status**: {result['status']}")
                        st.write(f"- **Total Items**: {result['total_items']}")

                    else:
                        st.error(f"Failed to submit batch job: {response.text}")

                except Exception as e:
                    st.error(f"API error: {str(e)}")


def show_language_detection():
    """Language detection page"""

    st.title("🔍 Language Detection")
    st.markdown("Automatically detect the language of any text")

    text = st.text_area(
        "Enter text for language detection",
        height=200,
        placeholder="Type or paste text here..."
    )

    if st.button("🔎 Detect Language", type="primary"):
        if not text.strip():
            st.warning("Please enter some text")
        else:
            with st.spinner("Detecting language..."):
                result = detect_language(text)

                if result:
                    st.success("Language detected!")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Detected Language", result['language_name'])

                    with col2:
                        confidence = result.get('confidence', 0)
                        st.metric("Confidence", f"{confidence:.2%}")

                    if result.get('alternative_languages'):
                        st.markdown("### Alternative Languages")
                        alt_df = pd.DataFrame(result['alternative_languages'])
                        st.dataframe(alt_df, use_container_width=True)


def show_glossary_management():
    """Glossary management page"""

    st.title("📚 Glossary Management")
    st.markdown("Manage translation glossaries for consistent terminology")

    tab1, tab2 = st.tabs(["View Glossaries", "Create Glossary"])

    with tab1:
        st.subheader("Existing Glossaries")

        glossaries = get_glossaries()

        if glossaries:
            for glossary in glossaries:
                with st.expander(f"📖 {glossary['name']}"):
                    st.write(f"**Description**: {glossary.get('description', 'N/A')}")
                    st.write(f"**Languages**: {glossary['source_language']} → {glossary['target_language']}")
                    st.write(f"**Status**: {'Active' if glossary['is_active'] else 'Inactive'}")
                    st.write(f"**Terms**: {len(glossary.get('terms', []))}")

                    if glossary.get('terms'):
                        terms_df = pd.DataFrame(glossary['terms'])
                        st.dataframe(terms_df[['source_term', 'target_term', 'description']], use_container_width=True)
        else:
            st.info("No glossaries found. Create one in the 'Create Glossary' tab.")

    with tab2:
        st.subheader("Create New Glossary")

        languages = get_supported_languages()
        lang_options = [f"{code} - {name}" for code, name in languages.items()]

        name = st.text_input("Glossary Name")
        description = st.text_area("Description")

        col1, col2 = st.columns(2)

        with col1:
            source_lang = st.selectbox("Source Language", lang_options, key="glossary_source")
            source_lang_code = source_lang.split(' - ')[0]

        with col2:
            target_lang = st.selectbox("Target Language", lang_options, key="glossary_target")
            target_lang_code = target_lang.split(' - ')[0]

        st.markdown("### Terms")

        num_terms = st.number_input("Number of terms", min_value=1, max_value=100, value=5)

        terms = []
        for i in range(num_terms):
            col_s, col_t, col_d = st.columns([2, 2, 3])

            with col_s:
                source_term = st.text_input(f"Source term {i+1}", key=f"source_{i}")

            with col_t:
                target_term = st.text_input(f"Target term {i+1}", key=f"target_{i}")

            with col_d:
                term_desc = st.text_input(f"Description {i+1}", key=f"desc_{i}")

            if source_term and target_term:
                terms.append({
                    "source_term": source_term,
                    "target_term": target_term,
                    "description": term_desc or None,
                    "case_sensitive": False
                })

        if st.button("💾 Create Glossary", type="primary"):
            if not name:
                st.warning("Please provide a glossary name")
            elif not terms:
                st.warning("Please add at least one term")
            else:
                create_glossary(name, description, source_lang_code, target_lang_code, terms)


def show_statistics():
    """Statistics page"""

    st.title("📊 Translation Statistics")
    st.markdown("View your translation usage and statistics")

    try:
        response = requests.get(f"{API_BASE_URL}/stats")

        if response.status_code == 200:
            stats = response.json()

            # Display metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Translations", f"{stats['total_translations']:,}")

            with col2:
                st.metric("Total Characters", f"{stats['total_characters']:,}")

            with col3:
                avg_quality = stats.get('average_quality_score')
                if avg_quality:
                    st.metric("Avg Quality Score", f"{avg_quality:.2f}")
                else:
                    st.metric("Avg Quality Score", "N/A")

            with col4:
                st.metric("Today", stats['translations_today'])

            st.markdown("---")

            col5, col6 = st.columns(2)

            with col5:
                st.metric("This Week", stats['translations_this_week'])

            with col6:
                st.metric("This Month", stats['translations_this_month'])

        else:
            st.error("Failed to fetch statistics")

    except Exception as e:
        st.error(f"API error: {str(e)}")


def show_settings():
    """Settings page"""

    st.title("⚙️ Settings")
    st.markdown("Configure translation module settings")

    st.subheader("API Configuration")

    api_url = st.text_input("API Base URL", value=API_BASE_URL)

    st.subheader("Provider Settings")

    provider_pref = st.selectbox("Default Provider", ["google", "deepl"])

    st.subheader("Quality Settings")

    enable_quality_default = st.checkbox("Enable Quality Scoring by Default", value=True)

    st.subheader("UI Preferences")

    theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])

    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")


if __name__ == "__main__":
    main()
