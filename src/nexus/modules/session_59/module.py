"""
Session 59: Voice Assistant Module
Features: Speech-to-text, voice commands, multi-language
"""
import asyncio
import io
import base64
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from loguru import logger

# Speech recognition
import speech_recognition as sr
import whisper

# Text-to-speech
from gtts import gTTS
import pyttsx3

from ..base_module import BaseModule, ModuleConfig
from ...core.claude_client import ClaudeClient


class VoiceAssistantModule(BaseModule):
    """Multi-language voice assistant with speech-to-text and text-to-speech"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=59,
            name="Voice Assistant",
            icon="🎤",
            description="Speech-to-text, voice commands, multi-language",
            version="1.0.0",
            features=["speech_to_text", "text_to_speech", "voice_commands", "multilingual"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.whisper_model = None
        self.recognizer = sr.Recognizer()
        self.tts_engine = None
        self.command_handlers: Dict[str, callable] = self._register_commands()

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return "action" in input_data

    def _register_commands(self) -> Dict[str, callable]:
        """Register voice command handlers"""
        return {
            "search": self._command_search,
            "open": self._command_open,
            "create": self._command_create,
            "send": self._command_send,
            "remind": self._command_remind,
            "weather": self._command_weather,
            "time": self._command_time,
            "translate": self._command_translate,
        }

    def _load_whisper_model(self, model_size: str = "base"):
        """Load Whisper model for transcription"""
        if not self.whisper_model:
            logger.info(f"Loading Whisper model: {model_size}")
            self.whisper_model = whisper.load_model(model_size)
        return self.whisper_model

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        engine: str = "whisper"
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text

        Args:
            audio_data: Audio bytes (WAV, MP3, etc.)
            language: Target language code (e.g., 'en', 'es', 'fr')
            engine: Recognition engine ('whisper', 'google', 'sphinx')

        Returns:
            Transcription result with text and confidence
        """
        try:
            if engine == "whisper":
                # Use OpenAI Whisper
                model = self._load_whisper_model()

                # Save audio temporarily
                temp_audio = Path("/tmp/temp_audio.wav")
                temp_audio.write_bytes(audio_data)

                result = model.transcribe(
                    str(temp_audio),
                    language=language,
                    task="transcribe"
                )

                return {
                    "success": True,
                    "text": result["text"],
                    "language": result.get("language"),
                    "segments": result.get("segments", []),
                    "engine": "whisper"
                }

            elif engine in ["google", "sphinx"]:
                # Use SpeechRecognition library
                audio_file = io.BytesIO(audio_data)
                with sr.AudioFile(audio_file) as source:
                    audio = self.recognizer.record(source)

                if engine == "google":
                    text = self.recognizer.recognize_google(audio, language=language)
                else:  # sphinx
                    text = self.recognizer.recognize_sphinx(audio)

                return {
                    "success": True,
                    "text": text,
                    "language": language,
                    "engine": engine
                }

            else:
                raise ValueError(f"Unknown engine: {engine}")

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return self.handle_error(e, "transcribe_audio")

    async def text_to_speech(
        self,
        text: str,
        language: str = "en",
        engine: str = "gtts",
        voice: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech

        Args:
            text: Text to convert
            language: Language code
            engine: TTS engine ('gtts', 'pyttsx3')
            voice: Specific voice ID (for pyttsx3)

        Returns:
            Audio bytes (MP3 or WAV)
        """
        try:
            if engine == "gtts":
                # Use Google Text-to-Speech
                tts = gTTS(text=text, lang=language)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                return audio_buffer.read()

            elif engine == "pyttsx3":
                # Use pyttsx3 offline TTS
                if not self.tts_engine:
                    self.tts_engine = pyttsx3.init()

                if voice:
                    self.tts_engine.setProperty('voice', voice)

                # Save to file
                temp_file = Path("/tmp/tts_output.wav")
                self.tts_engine.save_to_file(text, str(temp_file))
                self.tts_engine.runAndWait()

                return temp_file.read_bytes()

            else:
                raise ValueError(f"Unknown TTS engine: {engine}")

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    async def process_voice_command(
        self,
        audio_data: bytes,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process voice command end-to-end

        Args:
            audio_data: Audio containing command
            language: Language code

        Returns:
            Command execution result
        """
        try:
            # Step 1: Transcribe
            transcription = await self.transcribe_audio(audio_data, language)

            if not transcription.get("success"):
                return transcription

            text = transcription["text"].strip()
            logger.info(f"Transcribed command: {text}")

            # Step 2: Parse command using AI
            parse_prompt = f"""Parse this voice command and extract:
1. The action/command type
2. The parameters or arguments
3. The intent

Voice command: "{text}"

Return as JSON:
{{
    "command": "command_type",
    "parameters": {{}},
    "intent": "user_intent"
}}"""

            parsed_str = await self.claude.agenerate(
                parse_prompt,
                system_prompt=self.get_system_prompt()
            )

            try:
                parsed = json.loads(parsed_str)
            except json.JSONDecodeError:
                parsed = {"command": "unknown", "parameters": {}, "intent": text}

            # Step 3: Execute command
            command_type = parsed.get("command", "unknown")
            handler = self.command_handlers.get(command_type, self._command_unknown)

            result = await handler(parsed)

            # Step 4: Generate response
            response_text = result.get("response", "Command executed successfully.")

            # Step 5: Convert response to speech
            response_audio = await self.text_to_speech(response_text, language)

            return {
                "success": True,
                "transcription": text,
                "parsed_command": parsed,
                "result": result,
                "response_text": response_text,
                "response_audio": base64.b64encode(response_audio).decode()
            }

        except Exception as e:
            logger.error(f"Voice command error: {e}")
            return self.handle_error(e, "process_voice_command")

    # Command Handlers

    async def _command_search(self, parsed: Dict) -> Dict:
        """Search command"""
        query = parsed["parameters"].get("query", "")
        response = await self.claude.agenerate(f"Provide a brief answer to: {query}")
        return {"response": response, "action": "search", "query": query}

    async def _command_open(self, parsed: Dict) -> Dict:
        """Open command"""
        target = parsed["parameters"].get("target", "")
        return {"response": f"Opening {target}", "action": "open", "target": target}

    async def _command_create(self, parsed: Dict) -> Dict:
        """Create command"""
        item_type = parsed["parameters"].get("type", "file")
        name = parsed["parameters"].get("name", "")
        return {"response": f"Creating {item_type}: {name}", "action": "create"}

    async def _command_send(self, parsed: Dict) -> Dict:
        """Send command"""
        recipient = parsed["parameters"].get("recipient", "")
        message = parsed["parameters"].get("message", "")
        return {"response": f"Sending message to {recipient}", "action": "send"}

    async def _command_remind(self, parsed: Dict) -> Dict:
        """Reminder command"""
        time = parsed["parameters"].get("time", "")
        message = parsed["parameters"].get("message", "")
        return {"response": f"Reminder set for {time}: {message}", "action": "remind"}

    async def _command_weather(self, parsed: Dict) -> Dict:
        """Weather command"""
        location = parsed["parameters"].get("location", "your location")
        # In production, integrate with weather API
        return {"response": f"Fetching weather for {location}", "action": "weather"}

    async def _command_time(self, parsed: Dict) -> Dict:
        """Time command"""
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        return {"response": f"The current time is {current_time}", "action": "time"}

    async def _command_translate(self, parsed: Dict) -> Dict:
        """Translation command"""
        text = parsed["parameters"].get("text", "")
        target_lang = parsed["parameters"].get("target_language", "Spanish")

        prompt = f"Translate this to {target_lang}: {text}"
        translation = await self.claude.agenerate(prompt)

        return {
            "response": f"Translation: {translation}",
            "action": "translate",
            "translation": translation
        }

    async def _command_unknown(self, parsed: Dict) -> Dict:
        """Handle unknown commands"""
        intent = parsed.get("intent", "")
        response = await self.claude.agenerate(f"Help the user with this request: {intent}")
        return {"response": response, "action": "unknown", "intent": intent}

    async def real_time_transcription(
        self,
        duration: int = 5,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Real-time microphone transcription

        Args:
            duration: Recording duration in seconds
            language: Language code

        Returns:
            Transcription result
        """
        try:
            with sr.Microphone() as source:
                logger.info(f"Recording for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=duration)

            # Convert to bytes
            audio_data = audio.get_wav_data()

            # Transcribe
            result = await self.transcribe_audio(audio_data, language)
            return result

        except Exception as e:
            logger.error(f"Real-time transcription error: {e}")
            return self.handle_error(e, "real_time_transcription")

    async def translate_speech(
        self,
        audio_data: bytes,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """
        Translate speech to another language

        Args:
            audio_data: Source audio
            source_language: Source language code
            target_language: Target language code

        Returns:
            Translation with audio
        """
        try:
            # Transcribe source audio
            transcription = await self.transcribe_audio(audio_data, source_language)

            if not transcription.get("success"):
                return transcription

            source_text = transcription["text"]

            # Translate using AI
            translation_prompt = f"Translate this from {source_language} to {target_language}: {source_text}"
            translated_text = await self.claude.agenerate(translation_prompt)

            # Generate speech in target language
            translated_audio = await self.text_to_speech(translated_text, target_language)

            return {
                "success": True,
                "source_text": source_text,
                "translated_text": translated_text,
                "translated_audio": base64.b64encode(translated_audio).decode(),
                "source_language": source_language,
                "target_language": target_language
            }

        except Exception as e:
            logger.error(f"Speech translation error: {e}")
            return self.handle_error(e, "translate_speech")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice assistant request (sync wrapper)"""
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice assistant request"""
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        action = input_data["action"]
        self.log_operation(action, input_data)

        try:
            if action == "transcribe":
                audio_data = base64.b64decode(input_data["audio"])
                return await self.transcribe_audio(
                    audio_data,
                    input_data.get("language"),
                    input_data.get("engine", "whisper")
                )

            elif action == "text_to_speech":
                audio = await self.text_to_speech(
                    input_data["text"],
                    input_data.get("language", "en"),
                    input_data.get("engine", "gtts")
                )
                return {
                    "success": True,
                    "audio": base64.b64encode(audio).decode()
                }

            elif action == "process_command":
                audio_data = base64.b64decode(input_data["audio"])
                return await self.process_voice_command(
                    audio_data,
                    input_data.get("language", "en")
                )

            elif action == "translate_speech":
                audio_data = base64.b64decode(input_data["audio"])
                return await self.translate_speech(
                    audio_data,
                    input_data["source_language"],
                    input_data["target_language"]
                )

            elif action == "real_time":
                return await self.real_time_transcription(
                    input_data.get("duration", 5),
                    input_data.get("language", "en")
                )

            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return self.handle_error(e, action)
