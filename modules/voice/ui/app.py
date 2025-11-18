"""Streamlit UI for NEXUS Voice Assistant."""

import streamlit as st
import requests
import io
import os
from datetime import datetime
from pathlib import Path
import json

# Audio recording libraries
try:
    from audio_recorder_streamlit import audio_recorder
    HAS_AUDIO_RECORDER = True
except ImportError:
    HAS_AUDIO_RECORDER = False

# Configuration
API_BASE_URL = os.getenv("VOICE_API_URL", "http://localhost:8000/api/voice")

# Page config
st.set_page_config(
    page_title="NEXUS Voice Assistant",
    page_icon="🎤",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .command-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .response-box {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
    st.session_state.user_id = "demo_user"
    st.session_state.conversation_history = []
    st.session_state.current_transcript = ""


def create_session():
    """Create a new session."""
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.conversation_history = []


def transcribe_audio(audio_bytes, language_code="en-US"):
    """Transcribe audio using the API."""
    try:
        files = {'audio_file': ('audio.wav', audio_bytes, 'audio/wav')}
        params = {
            'language_code': language_code,
            'enable_automatic_punctuation': True
        }

        response = requests.post(
            f"{API_BASE_URL}/transcribe",
            files=files,
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Transcription failed: {response.text}")
            return None

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def process_command(transcript):
    """Process a voice command."""
    try:
        data = {
            "transcript": transcript,
            "session_id": st.session_state.session_id,
            "user_id": st.session_state.user_id
        }

        response = requests.post(
            f"{API_BASE_URL}/command",
            json=data
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Command processing failed: {response.text}")
            return None

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def synthesize_speech(text, voice_name=None, language_code="en-US"):
    """Convert text to speech."""
    try:
        data = {
            "text": text,
            "voice_name": voice_name,
            "language_code": language_code,
            "audio_format": "mp3"
        }

        response = requests.post(
            f"{API_BASE_URL}/synthesize",
            json=data
        )

        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Speech synthesis failed: {response.text}")
            return None

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_commands(category=None):
    """Get available commands."""
    try:
        params = {'category': category} if category else {}
        response = requests.get(f"{API_BASE_URL}/commands", params=params)

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_session_info():
    """Get session information."""
    if not st.session_state.session_id:
        return None

    try:
        response = requests.get(
            f"{API_BASE_URL}/session/{st.session_state.session_id}"
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except Exception as e:
        return None


# Main UI
st.markdown('<div class="main-header">🎤 NEXUS Voice Assistant</div>', unsafe_allow_html=True)

# Create session if needed
if not st.session_state.session_id:
    create_session()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Language selection
    language = st.selectbox(
        "Language",
        ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "ja-JP", "ko-KR"],
        index=0
    )

    # Voice selection for TTS
    voice_enabled = st.checkbox("Enable voice responses", value=True)

    st.divider()

    st.header("📊 Session Info")
    if st.session_state.session_id:
        st.text(f"Session: {st.session_state.session_id[:8]}...")
        st.text(f"User: {st.session_state.user_id}")

        session_info = get_session_info()
        if session_info:
            st.text(f"Interactions: {session_info['session']['history_count']}")
            if session_info['session'].get('current_module'):
                st.text(f"Module: {session_info['session']['current_module']}")

    if st.button("🔄 New Session"):
        create_session()
        st.rerun()

    st.divider()

    st.header("❓ Help")
    if st.button("Show Available Commands"):
        st.session_state.show_help = True

# Main content
tab1, tab2, tab3 = st.tabs(["🎤 Voice Input", "💬 Text Input", "📚 Commands"])

with tab1:
    st.header("Voice Input")

    if HAS_AUDIO_RECORDER:
        st.info("Click the microphone to start recording. Click again to stop.")

        # Audio recorder
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_size="3x"
        )

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

            if st.button("🎯 Process Recording"):
                with st.spinner("Transcribing..."):
                    result = transcribe_audio(audio_bytes, language)

                    if result and result.get('success'):
                        transcript = result['transcript']
                        confidence = result.get('confidence', 0)

                        st.success(f"Transcribed (confidence: {confidence:.2%})")
                        st.markdown(f'<div class="response-box"><strong>You said:</strong> {transcript}</div>',
                                    unsafe_allow_html=True)

                        # Process command
                        with st.spinner("Processing command..."):
                            cmd_result = process_command(transcript)

                            if cmd_result and cmd_result.get('success'):
                                st.markdown(
                                    f'<div class="success-box"><strong>Response:</strong> {cmd_result["response"]}</div>',
                                    unsafe_allow_html=True
                                )

                                # Show details
                                with st.expander("📋 Details"):
                                    st.json({
                                        "intent": cmd_result.get('intent'),
                                        "confidence": cmd_result.get('confidence'),
                                        "entities": cmd_result.get('entities'),
                                        "command": cmd_result.get('command')
                                    })

                                # Text-to-speech response
                                if voice_enabled and cmd_result.get('response'):
                                    with st.spinner("Generating speech..."):
                                        audio = synthesize_speech(
                                            cmd_result['response'],
                                            language_code=language
                                        )
                                        if audio:
                                            st.audio(audio, format="audio/mp3")

                                # Add to history
                                st.session_state.conversation_history.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'transcript': transcript,
                                    'intent': cmd_result.get('intent'),
                                    'response': cmd_result.get('response')
                                })
    else:
        st.warning("Audio recorder not available. Install with: pip install audio-recorder-streamlit")
        st.info("You can use the Text Input tab instead.")

with tab2:
    st.header("Text Input")

    # Text input
    user_input = st.text_input(
        "Type your command:",
        placeholder="e.g., Create a new document called Project Report"
    )

    col1, col2 = st.columns([1, 5])

    with col1:
        process_btn = st.button("🚀 Process", use_container_width=True)

    if process_btn and user_input:
        with st.spinner("Processing..."):
            result = process_command(user_input)

            if result and result.get('success'):
                st.markdown(
                    f'<div class="success-box"><strong>Response:</strong> {result["response"]}</div>',
                    unsafe_allow_html=True
                )

                # Show details
                with st.expander("📋 Details"):
                    st.json({
                        "intent": result.get('intent'),
                        "confidence": result.get('confidence'),
                        "entities": result.get('entities'),
                        "command": result.get('command')
                    })

                # Text-to-speech response
                if voice_enabled and result.get('response'):
                    with st.spinner("Generating speech..."):
                        audio = synthesize_speech(
                            result['response'],
                            language_code=language
                        )
                        if audio:
                            st.audio(audio, format="audio/mp3")

                # Add to history
                st.session_state.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'transcript': user_input,
                    'intent': result.get('intent'),
                    'response': result.get('response')
                })

    # Show conversation history
    if st.session_state.conversation_history:
        st.divider()
        st.subheader("💬 Conversation History")

        for i, item in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.container():
                st.markdown(f"**{item['timestamp'][:19]}** - Intent: `{item['intent']}`")
                st.markdown(f"👤 **You:** {item['transcript']}")
                st.markdown(f"🤖 **Assistant:** {item['response']}")
                if i < len(st.session_state.conversation_history) - 1:
                    st.divider()

with tab3:
    st.header("Available Commands")

    # Category filter
    categories = ["All", "productivity", "communication", "navigation", "query", "system"]
    selected_category = st.selectbox("Filter by category:", categories)

    # Get commands
    category_param = None if selected_category == "All" else selected_category
    commands_data = get_commands(category_param)

    if commands_data and commands_data.get('success'):
        commands = commands_data['commands']

        st.info(f"Found {len(commands)} commands")

        # Group by category
        by_category = {}
        for cmd in commands:
            cat = cmd['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(cmd)

        # Display commands
        for cat, cmds in sorted(by_category.items()):
            st.subheader(f"📁 {cat.upper()}")

            for cmd in sorted(cmds, key=lambda x: x['name']):
                with st.expander(f"🎯 {cmd['name']}", expanded=False):
                    st.markdown(f"**Description:** {cmd['description']}")
                    st.markdown(f"**Intent:** `{cmd['intent']}`")
                    st.markdown(f"**Module:** `{cmd['module']}`")

                    if cmd.get('params'):
                        st.markdown(f"**Parameters:** {', '.join(cmd['params'])}")

                    if cmd.get('examples'):
                        st.markdown("**Examples:**")
                        for ex in cmd['examples']:
                            st.markdown(f"- {ex}")

# Footer
st.divider()
st.caption("NEXUS Voice Assistant - Powered by AI 🚀")
