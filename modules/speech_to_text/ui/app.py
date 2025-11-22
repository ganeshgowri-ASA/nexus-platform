"""Streamlit UI for speech-to-text module."""

import streamlit as st
import requests
import time
from pathlib import Path
from typing import Optional
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="NEXUS Speech-to-Text",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")


def main():
    """Main Streamlit application."""
    st.title("🎙️ NEXUS Speech-to-Text")
    st.markdown("Transcribe audio files with speaker diarization and multilingual support")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Provider selection
        provider = st.selectbox(
            "Provider",
            options=["whisper", "google", "aws"],
            help="Choose speech-to-text provider"
        )

        # Language selection
        language = st.text_input(
            "Language Code",
            value="en",
            help="e.g., 'en' for English, 'es' for Spanish"
        )

        auto_detect = st.checkbox("Auto-detect language", value=True)

        # Diarization options
        st.subheader("Speaker Diarization")
        enable_diarization = st.checkbox("Enable diarization", value=False)

        max_speakers = None
        if enable_diarization:
            max_speakers = st.number_input(
                "Max speakers",
                min_value=1,
                max_value=20,
                value=5
            )

        # Timestamps
        enable_timestamps = st.checkbox("Include timestamps", value=True)

        # User ID
        user_id = st.text_input("User ID", value="demo_user")

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Transcribe", "📋 Transcriptions", "ℹ️ Info"])

    with tab1:
        upload_tab(provider, language, auto_detect, enable_diarization,
                   enable_timestamps, max_speakers, user_id)

    with tab2:
        transcriptions_tab(user_id)

    with tab3:
        info_tab()


def upload_tab(
    provider: str,
    language: str,
    auto_detect: bool,
    enable_diarization: bool,
    enable_timestamps: bool,
    max_speakers: Optional[int],
    user_id: str,
):
    """Upload and transcribe tab."""
    st.header("Upload Audio File")

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "flac", "ogg", "aac", "wma"],
        help="Supported formats: MP3, WAV, M4A, FLAC, OGG, AAC, WMA"
    )

    if uploaded_file is not None:
        st.audio(uploaded_file, format=f"audio/{Path(uploaded_file.name).suffix[1:]}")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🎯 Transcribe", type="primary", use_container_width=True):
                transcribe_audio(
                    uploaded_file,
                    provider,
                    language if not auto_detect else None,
                    enable_diarization,
                    enable_timestamps,
                    max_speakers,
                    user_id,
                )


def transcribe_audio(
    file,
    provider: str,
    language: Optional[str],
    enable_diarization: bool,
    enable_timestamps: bool,
    max_speakers: Optional[int],
    user_id: str,
):
    """Transcribe audio file."""
    with st.spinner("Uploading and transcribing..."):
        try:
            # Prepare request
            files = {"file": (file.name, file.getvalue(), file.type)}
            params = {
                "provider": provider,
                "enable_diarization": enable_diarization,
                "enable_timestamps": enable_timestamps,
                "user_id": user_id,
            }

            if language:
                params["language"] = language
            if max_speakers:
                params["max_speakers"] = max_speakers

            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/api/v1/speech/transcribe",
                files=files,
                params=params,
                timeout=300,
            )

            if response.status_code == 201:
                result = response.json()
                transcription_id = result["id"]

                # Poll for completion
                st.info(f"Transcription started (ID: {transcription_id}). Polling for results...")
                poll_transcription(transcription_id)

            else:
                st.error(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            st.error(f"Error: {str(e)}")


def poll_transcription(transcription_id: int, max_attempts: int = 60):
    """Poll transcription status until complete."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/v1/speech/transcriptions/{transcription_id}",
                params={"include_segments": True},
            )

            if response.status_code == 200:
                result = response.json()
                status = result["status"]

                progress = min((attempt + 1) / max_attempts, 0.95)
                progress_bar.progress(progress)
                status_text.text(f"Status: {status}")

                if status == "completed":
                    progress_bar.progress(1.0)
                    status_text.text("✅ Transcription completed!")
                    display_transcription(result)
                    return

                elif status == "failed":
                    st.error(f"Transcription failed: {result.get('error_message', 'Unknown error')}")
                    return

            time.sleep(5)

        except Exception as e:
            st.error(f"Error polling status: {str(e)}")
            return

    st.warning("Transcription is taking longer than expected. Please check the transcriptions list.")


def display_transcription(result: dict):
    """Display transcription results."""
    st.success("Transcription completed!")

    # Display full text
    st.subheader("📝 Full Transcription")
    st.text_area(
        "Text",
        value=result.get("full_text", ""),
        height=200,
        disabled=True,
    )

    # Display metadata
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Language", result.get("language", "N/A"))
    with col2:
        confidence = result.get("confidence")
        st.metric("Confidence", f"{confidence:.2%}" if confidence else "N/A")
    with col3:
        duration = result.get("duration")
        st.metric("Duration", f"{duration:.1f}s" if duration else "N/A")
    with col4:
        st.metric("Provider", result.get("provider", "N/A"))

    # Display segments
    if result.get("segments"):
        st.subheader("📊 Segments")

        segments_data = []
        for seg in result["segments"]:
            segments_data.append({
                "Start": f"{seg['start_time']:.2f}s",
                "End": f"{seg['end_time']:.2f}s",
                "Speaker": seg.get("speaker_id", "N/A"),
                "Text": seg["text"],
                "Confidence": f"{seg['confidence']:.2%}" if seg.get("confidence") else "N/A",
            })

        df = pd.DataFrame(segments_data)
        st.dataframe(df, use_container_width=True, height=400)

        # Download as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Segments as CSV",
            data=csv,
            file_name=f"transcription_{result['id']}_segments.csv",
            mime="text/csv",
        )

    # Display speakers
    if result.get("speakers"):
        st.subheader("👥 Speakers")
        for speaker in result["speakers"]:
            st.write(f"- {speaker['speaker_id']}")


def transcriptions_tab(user_id: str):
    """Transcriptions list tab."""
    st.header("Transcription History")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        status_filter = st.selectbox(
            "Status",
            options=["all", "pending", "processing", "completed", "failed"],
        )
    with col2:
        limit = st.number_input("Results", min_value=10, max_value=100, value=50)
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Fetch transcriptions
    try:
        params = {"user_id": user_id, "limit": limit}
        if status_filter != "all":
            params["status"] = status_filter

        response = requests.get(
            f"{API_BASE_URL}/api/v1/speech/transcriptions",
            params=params,
        )

        if response.status_code == 200:
            data = response.json()
            transcriptions = data.get("items", [])

            if transcriptions:
                st.write(f"Found {data['total']} transcription(s)")

                for trans in transcriptions:
                    with st.expander(
                        f"🎵 {trans['filename']} - {trans['status'].upper()}",
                        expanded=False,
                    ):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"**ID:** {trans['id']}")
                            st.write(f"**Status:** {trans['status']}")
                            st.write(f"**Provider:** {trans['provider']}")
                            st.write(f"**Language:** {trans.get('language', 'N/A')}")
                            st.write(f"**Created:** {trans['created_at']}")

                            if trans['status'] == 'completed' and trans.get('full_text'):
                                st.text_area(
                                    "Transcription",
                                    value=trans['full_text'][:500] + "...",
                                    height=100,
                                    disabled=True,
                                )

                        with col2:
                            if st.button("👁️ View", key=f"view_{trans['id']}"):
                                view_transcription_details(trans['id'])

                            if st.button("🗑️ Delete", key=f"delete_{trans['id']}"):
                                delete_transcription(trans['id'])

            else:
                st.info("No transcriptions found.")

        else:
            st.error(f"Error fetching transcriptions: {response.status_code}")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def view_transcription_details(transcription_id: int):
    """View detailed transcription."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/speech/transcriptions/{transcription_id}",
            params={"include_segments": True},
        )

        if response.status_code == 200:
            result = response.json()
            display_transcription(result)
        else:
            st.error(f"Error: {response.status_code}")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def delete_transcription(transcription_id: int):
    """Delete transcription."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/speech/transcriptions/{transcription_id}"
        )

        if response.status_code == 204:
            st.success("Transcription deleted!")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"Error: {response.status_code}")

    except Exception as e:
        st.error(f"Error: {str(e)}")


def info_tab():
    """Information tab."""
    st.header("ℹ️ About NEXUS Speech-to-Text")

    st.markdown("""
    ### Features
    - **Multiple Providers**: Support for Whisper (local), Google Cloud, and AWS Transcribe
    - **Speaker Diarization**: Identify and separate different speakers
    - **Multilingual**: Support for 100+ languages
    - **Real-time Processing**: Async processing with status updates
    - **Timestamps**: Detailed word/segment timestamps
    - **High Accuracy**: Configurable accuracy tuning

    ### Supported Providers

    #### 🤖 Whisper (OpenAI)
    - Local processing (privacy-friendly)
    - 99 languages supported
    - Multiple model sizes (tiny to large)
    - No API costs

    #### 🌐 Google Cloud Speech-to-Text
    - 125+ languages and variants
    - Native speaker diarization
    - High accuracy
    - Streaming support

    #### ☁️ AWS Transcribe
    - 30+ languages
    - Custom vocabulary
    - Medical/legal specialization
    - Integration with AWS ecosystem

    ### Audio Formats
    Supported: MP3, WAV, M4A, FLAC, OGG, AAC, WMA

    ### API Health
    """)

    # Check API health
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/speech/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            st.success(f"✅ API Status: {health['status']}")
            st.json(health)
        else:
            st.error("❌ API is not responding")
    except Exception as e:
        st.error(f"❌ Cannot connect to API: {str(e)}")


if __name__ == "__main__":
    main()
