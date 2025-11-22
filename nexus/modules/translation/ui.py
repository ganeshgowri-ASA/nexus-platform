"""
Streamlit UI for Translation Module

Interactive web interface for translation features.
"""

import streamlit as st
from typing import Optional
from nexus.core.database import get_db_session
from nexus.modules.translation.translator import Translator
from nexus.modules.translation.language_detection import LanguageDetector
from nexus.modules.translation.glossary import GlossaryManager
from config.logging import get_logger

logger = get_logger(__name__)


def render_translation_ui():
    """Render main translation interface."""
    st.title("🌐 NEXUS Translation Module")
    st.markdown("---")

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")

        engine = st.selectbox(
            "Translation Engine",
            ["google", "deepl", "azure", "aws", "openai", "claude"],
            index=1,  # DeepL default
        )

        use_cache = st.checkbox("Use Cache", value=True)
        use_glossary = st.checkbox("Apply Glossaries", value=True)
        use_ai = st.checkbox("AI-Enhanced Translation", value=False)

    # Main translation interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Translate",
        "🔍 Language Detection",
        "📚 Glossaries",
        "📊 Statistics",
    ])

    with tab1:
        render_translation_tab(engine, use_cache, use_glossary, use_ai)

    with tab2:
        render_detection_tab()

    with tab3:
        render_glossary_tab()

    with tab4:
        render_statistics_tab()


def render_translation_tab(engine, use_cache, use_glossary, use_ai):
    """Render translation tab."""
    st.header("Text Translation")

    col1, col2 = st.columns(2)

    with col1:
        source_lang = st.selectbox(
            "Source Language",
            ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
            format_func=lambda x: "Auto-detect" if x == "auto" else x.upper(),
        )

    with col2:
        target_lang = st.selectbox(
            "Target Language",
            ["es", "en", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
            format_func=lambda x: x.upper(),
        )

    text = st.text_area(
        "Enter text to translate",
        height=200,
        placeholder="Type or paste your text here...",
    )

    context = st.text_input(
        "Context (optional)",
        placeholder="Provide additional context to improve translation quality",
    )

    if st.button("🔄 Translate", type="primary", use_container_width=True):
        if not text:
            st.warning("Please enter text to translate")
            return

        with st.spinner("Translating..."):
            try:
                db = get_db_session()

                # Get or create user (simplified for demo)
                from nexus.models.user import User
                user = db.query(User).first()
                if not user:
                    from nexus.modules.auth import AuthService
                    auth = AuthService(db)
                    user = auth.register_user(
                        email="demo@nexus.com",
                        username="demo_user",
                        password="demo123",
                    )

                translator = Translator(
                    db=db,
                    user_id=user.id,
                    engine=engine,
                    use_cache=use_cache,
                    use_glossary=use_glossary,
                )

                source = None if source_lang == "auto" else source_lang

                translation = translator.translate(
                    text=text,
                    target_lang=target_lang,
                    source_lang=source,
                    context=context or None,
                )

                st.success("Translation completed!")

                # Display results
                st.markdown("### Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Engine", engine.upper())
                with col2:
                    st.metric(
                        "Quality Score",
                        f"{translation.quality_score:.2f}" if translation.quality_score else "N/A",
                    )
                with col3:
                    st.metric(
                        "Processing Time",
                        f"{translation.processing_time_ms}ms" if translation.processing_time_ms else "N/A",
                    )

                st.text_area(
                    "Translation",
                    value=translation.target_text or "",
                    height=200,
                    disabled=True,
                )

                # Additional info
                with st.expander("Translation Details"):
                    st.json({
                        "id": translation.id,
                        "source_language": translation.source_language,
                        "target_language": translation.target_language,
                        "confidence": translation.confidence_score,
                        "cached": translation.cached,
                        "status": translation.status.value,
                    })

                db.close()

            except Exception as e:
                st.error(f"Translation failed: {str(e)}")
                logger.error(f"UI translation error: {e}")


def render_detection_tab():
    """Render language detection tab."""
    st.header("Language Detection")

    text = st.text_area(
        "Enter text to detect language",
        height=150,
        placeholder="Type or paste text in any language...",
    )

    use_ai = st.checkbox("Use AI-based detection", value=False)

    if st.button("🔍 Detect Language", type="primary"):
        if not text:
            st.warning("Please enter text")
            return

        with st.spinner("Detecting language..."):
            try:
                detector = LanguageDetector()
                result = detector.detect(text, use_ai=use_ai)

                st.success(f"Detected language: **{result['language_name']}** ({result['language']})")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Language Code", result["language"].upper())
                with col2:
                    st.metric("Confidence", f"{result['confidence']:.2%}")

                if "detector" in result:
                    st.info(f"Detection method: {result['detector']}")

            except Exception as e:
                st.error(f"Detection failed: {str(e)}")
                logger.error(f"UI detection error: {e}")


def render_glossary_tab():
    """Render glossary management tab."""
    st.header("Glossary Management")

    st.info("📚 Create and manage custom glossaries for consistent terminology")

    # Create new glossary
    with st.expander("➕ Create New Glossary"):
        name = st.text_input("Glossary Name")
        description = st.text_area("Description", height=100)

        col1, col2 = st.columns(2)
        with col1:
            source_lang = st.selectbox("Source Language", ["en", "es", "fr", "de"])
        with col2:
            target_lang = st.selectbox("Target Language", ["es", "en", "fr", "de"])

        if st.button("Create Glossary"):
            if name:
                try:
                    db = get_db_session()
                    from nexus.models.user import User
                    user = db.query(User).first()

                    manager = GlossaryManager(db)
                    glossary = manager.create_glossary(
                        name=name,
                        user_id=user.id,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        description=description,
                    )

                    st.success(f"Glossary '{name}' created successfully!")
                    db.close()

                except Exception as e:
                    st.error(f"Failed to create glossary: {str(e)}")
            else:
                st.warning("Please enter a glossary name")

    # List existing glossaries
    st.markdown("### Your Glossaries")

    try:
        db = get_db_session()
        from nexus.models.user import User
        user = db.query(User).first()

        if user:
            manager = GlossaryManager(db)
            glossaries = manager.get_glossaries(user.id)

            if glossaries:
                for glossary in glossaries:
                    with st.expander(f"📖 {glossary.name}"):
                        st.write(f"**Languages:** {glossary.source_language} → {glossary.target_language}")
                        if glossary.description:
                            st.write(f"**Description:** {glossary.description}")
                        st.write(f"**Terms:** {len(glossary.terms)}")

                        # Show terms
                        if glossary.terms:
                            for term in glossary.terms[:5]:  # Show first 5
                                st.text(f"• {term.source_term} → {term.target_term}")
            else:
                st.info("No glossaries yet. Create one to get started!")

        db.close()

    except Exception as e:
        st.error(f"Failed to load glossaries: {str(e)}")


def render_statistics_tab():
    """Render statistics tab."""
    st.header("Translation Statistics")

    try:
        db = get_db_session()
        from nexus.models.translation import Translation
        from sqlalchemy import func

        # Total translations
        total = db.query(Translation).count()

        # Average quality
        avg_quality = db.query(func.avg(Translation.quality_score)).scalar() or 0

        # Language pairs
        pairs = (
            db.query(
                Translation.source_language,
                Translation.target_language,
                func.count(Translation.id).label("count"),
            )
            .group_by(Translation.source_language, Translation.target_language)
            .order_by(func.count(Translation.id).desc())
            .limit(5)
            .all()
        )

        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Translations", total)

        with col2:
            st.metric("Average Quality", f"{avg_quality:.2f}" if avg_quality else "N/A")

        with col3:
            cached_count = db.query(Translation).filter(Translation.cached == True).count()
            cache_rate = (cached_count / total * 100) if total > 0 else 0
            st.metric("Cache Hit Rate", f"{cache_rate:.1f}%")

        # Popular language pairs
        st.markdown("### Popular Language Pairs")

        if pairs:
            for source, target, count in pairs:
                st.write(f"**{source.upper()} → {target.upper()}**: {count} translations")
        else:
            st.info("No translation data yet")

        db.close()

    except Exception as e:
        st.error(f"Failed to load statistics: {str(e)}")
        logger.error(f"UI statistics error: {e}")


if __name__ == "__main__":
    render_translation_ui()
