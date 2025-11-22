"""FastAPI application for voice module."""

import os
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..services.speech_to_text import SpeechToTextService
from ..services.text_to_speech import TextToSpeechService
from ..services.audio_processor import AudioProcessor
from ..nlp.intent_recognizer import IntentRecognizer
from ..nlp.entity_extractor import EntityExtractor
from ..nlp.context_manager import ContextManager
from ..utils.command_processor import CommandProcessor
from ..utils.command_registry import CommandRegistry


# Pydantic models
class TranscribeRequest(BaseModel):
    language_code: str = "en-US"
    enable_automatic_punctuation: bool = True
    enable_profanity_filter: bool = False
    model: str = "default"


class SynthesizeRequest(BaseModel):
    text: str
    voice_name: Optional[str] = None
    language_code: str = "en-US"
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain_db: float = 0.0
    audio_format: str = "mp3"


class CommandRequest(BaseModel):
    transcript: str
    session_id: Optional[str] = None
    user_id: str


class ConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool


# Initialize services
def get_services():
    """Get initialized services (singleton pattern)."""
    if not hasattr(get_services, 'initialized'):
        # Get configuration from environment
        stt_provider = os.getenv('STT_PROVIDER', 'google')
        tts_provider = os.getenv('TTS_PROVIDER', 'google')
        llm_provider = os.getenv('LLM_PROVIDER', 'anthropic')
        llm_api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')

        get_services.stt = SpeechToTextService(provider=stt_provider)
        get_services.tts = TextToSpeechService(provider=tts_provider)
        get_services.audio_processor = AudioProcessor()
        get_services.intent_recognizer = IntentRecognizer(
            llm_provider=llm_provider,
            api_key=llm_api_key
        )
        get_services.entity_extractor = EntityExtractor()
        get_services.context_manager = ContextManager(max_history=10)
        get_services.command_registry = CommandRegistry()
        get_services.command_processor = CommandProcessor(
            intent_recognizer=get_services.intent_recognizer,
            entity_extractor=get_services.entity_extractor,
            context_manager=get_services.context_manager,
            command_registry=get_services.command_registry
        )

        get_services.initialized = True

    return {
        'stt': get_services.stt,
        'tts': get_services.tts,
        'audio_processor': get_services.audio_processor,
        'intent_recognizer': get_services.intent_recognizer,
        'entity_extractor': get_services.entity_extractor,
        'context_manager': get_services.context_manager,
        'command_registry': get_services.command_registry,
        'command_processor': get_services.command_processor
    }


# Create FastAPI app
app = FastAPI(
    title="NEXUS Voice Assistant API",
    description="Voice command, speech recognition, and text-to-speech API",
    version="1.0.0"
)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Temporary directory for audio files
TEMP_AUDIO_DIR = Path("/tmp/nexus_voice")
TEMP_AUDIO_DIR.mkdir(exist_ok=True)


@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    request_params: TranscribeRequest = Depends()
):
    """
    Transcribe audio file to text.

    Upload an audio file and get the transcribed text.
    Supports multiple audio formats: WAV, MP3, FLAC, OGG.
    """
    services = get_services()

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_ext = Path(audio_file.filename).suffix
    temp_file = TEMP_AUDIO_DIR / f"{file_id}{file_ext}"

    try:
        with open(temp_file, "wb") as f:
            content = await audio_file.read()
            f.write(content)

        # Transcribe
        result = services['stt'].transcribe_audio(
            audio_file=str(temp_file),
            language_code=request_params.language_code,
            enable_automatic_punctuation=request_params.enable_automatic_punctuation,
            enable_profanity_filter=request_params.enable_profanity_filter,
            model=request_params.model
        )

        return {
            "success": True,
            "transcript": result["transcript"],
            "confidence": result["confidence"],
            "language_code": result["language_code"],
            "alternatives": result.get("alternatives", []),
            "processing_time_ms": result["processing_time_ms"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Convert text to speech.

    Converts text to audio and returns the audio file.
    """
    services = get_services()

    # Generate output file
    file_id = str(uuid.uuid4())
    output_file = TEMP_AUDIO_DIR / f"{file_id}.{request.audio_format}"

    try:
        # Synthesize
        result = services['tts'].synthesize_speech(
            text=request.text,
            output_file=str(output_file),
            voice_name=request.voice_name,
            language_code=request.language_code,
            speaking_rate=request.speaking_rate,
            pitch=request.pitch,
            volume_gain_db=request.volume_gain_db,
            audio_format=request.audio_format
        )

        # Return audio file
        return FileResponse(
            path=str(output_file),
            media_type=f"audio/{request.audio_format}",
            filename=f"speech.{request.audio_format}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/command")
async def process_voice_command(request: CommandRequest):
    """
    Process a voice command.

    Takes transcribed text, recognizes intent, and executes the command.
    """
    services = get_services()

    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Process command
        result = services['command_processor'].process_command(
            transcript=request.transcript,
            session_id=session_id,
            user_id=request.user_id
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/command/confirm")
async def confirm_command(request: ConfirmRequest):
    """
    Confirm or cancel a pending command.

    Used for commands that require user confirmation.
    """
    services = get_services()

    try:
        result = services['command_processor'].confirm_command(
            session_id=request.session_id,
            confirmed=request.confirmed
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commands")
async def get_commands(category: Optional[str] = None):
    """
    Get available voice commands.

    Returns all available commands, optionally filtered by category.
    """
    services = get_services()

    try:
        if category:
            commands = services['command_registry'].get_commands_by_category(category)
        else:
            commands = services['command_registry'].get_all_commands()

        return {
            "success": True,
            "count": len(commands),
            "commands": commands
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commands/search")
async def search_commands(query: str):
    """
    Search for commands.

    Search commands by name, description, or examples.
    """
    services = get_services()

    try:
        commands = services['command_registry'].search_commands(query)

        return {
            "success": True,
            "count": len(commands),
            "commands": commands
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commands/help")
async def get_help(category: Optional[str] = None):
    """
    Get help text for commands.

    Returns formatted help text for all or specific category of commands.
    """
    services = get_services()

    try:
        help_text = services['command_registry'].get_help_text(category)

        return {
            "success": True,
            "help_text": help_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session information.

    Returns conversation history and context for a session.
    """
    services = get_services()

    try:
        session = services['context_manager'].get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        history = services['context_manager'].get_conversation_history(session_id)

        return {
            "success": True,
            "session": {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "current_module": session.get("module_context"),
                "current_intent": session.get("current_intent"),
                "history_count": len(history),
                "history": history
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a session.

    Deletes all conversation history and context for a session.
    """
    services = get_services()

    try:
        services['context_manager'].clear_session(session_id)

        return {
            "success": True,
            "message": "Session cleared"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices(language_code: Optional[str] = None):
    """
    List available TTS voices.

    Returns all available voices for text-to-speech, optionally filtered by language.
    """
    services = get_services()

    try:
        voices = services['tts'].list_voices(language_code)

        return {
            "success": True,
            **voices
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/process")
async def process_audio(
    audio_file: UploadFile = File(...),
    operation: str = "normalize"
):
    """
    Process audio file.

    Operations: normalize, trim_silence, convert_to_wav
    """
    services = get_services()

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_ext = Path(audio_file.filename).suffix
    input_file = TEMP_AUDIO_DIR / f"{file_id}_input{file_ext}"
    output_file = TEMP_AUDIO_DIR / f"{file_id}_output{file_ext}"

    try:
        with open(input_file, "wb") as f:
            content = await audio_file.read()
            f.write(content)

        # Process based on operation
        if operation == "normalize":
            result = services['audio_processor'].normalize_audio(
                str(input_file),
                str(output_file)
            )
        elif operation == "trim_silence":
            result = services['audio_processor'].trim_silence(
                str(input_file),
                str(output_file)
            )
        elif operation == "convert_to_wav":
            output_file = TEMP_AUDIO_DIR / f"{file_id}_output.wav"
            result = services['audio_processor'].convert_to_wav(
                str(input_file),
                str(output_file)
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")

        # Return processed file
        return FileResponse(
            path=result,
            media_type="audio/wav" if operation == "convert_to_wav" else f"audio/{file_ext[1:]}",
            filename=f"processed{Path(result).suffix}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temp files
        if input_file.exists():
            input_file.unlink()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "NEXUS Voice Assistant"
    }


# Include router in app
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
