# NEXUS Voice Assistant Module

A comprehensive voice assistant module for the NEXUS platform with speech recognition, text-to-speech, natural language processing, and intelligent voice command execution.

## Features

- **🎤 Speech-to-Text**: Convert speech to text using Google Cloud Speech or AWS Transcribe
- **🔊 Text-to-Speech**: Generate natural-sounding speech from text using Google Cloud TTS or AWS Polly
- **🧠 NLP Intent Recognition**: Understand user intent using AI/LLM (Claude or GPT)
- **📝 Entity Extraction**: Extract dates, times, names, emails, and more from speech
- **🎯 Voice Commands**: Execute NEXUS commands via voice
- **💬 Context Management**: Maintain conversation history and context
- **🎨 Streamlit UI**: Beautiful, interactive voice interface
- **🚀 FastAPI Backend**: High-performance REST API

## Architecture

```
modules/voice/
├── api/                    # FastAPI endpoints
│   └── main.py            # API routes and handlers
├── config/                # Configuration
│   ├── settings.py        # Application settings
│   └── database.py        # Database configuration
├── models/                # Database models
│   ├── voice_interaction.py
│   ├── voice_command.py
│   └── user_preference.py
├── nlp/                   # NLP & AI
│   ├── intent_recognizer.py
│   ├── entity_extractor.py
│   └── context_manager.py
├── services/              # Core services
│   ├── speech_to_text.py
│   ├── text_to_speech.py
│   └── audio_processor.py
├── ui/                    # Streamlit UI
│   └── app.py
└── utils/                 # Utilities
    ├── command_processor.py
    └── command_registry.py
```

## Installation

### 1. Install Dependencies

```bash
cd modules/voice
pip install -r requirements.txt
```

### 2. Set Up Speech Services

#### Google Cloud (Recommended)

1. Create a Google Cloud project
2. Enable Cloud Speech-to-Text API and Cloud Text-to-Speech API
3. Create a service account and download credentials JSON
4. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
   ```

#### AWS

1. Create an AWS account
2. Set up IAM credentials with Transcribe and Polly permissions
3. Create an S3 bucket for transcription jobs
4. Set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_S3_BUCKET=your_bucket
   ```

### 3. Set Up AI/LLM

#### Anthropic Claude (Recommended)

```bash
export ANTHROPIC_API_KEY=your_api_key
export LLM_PROVIDER=anthropic
```

#### OpenAI GPT

```bash
export OPENAI_API_KEY=your_api_key
export LLM_PROVIDER=openai
```

### 4. Configure Database

```bash
# PostgreSQL (recommended)
export DATABASE_URL=postgresql://user:password@localhost:5432/nexus_voice
```

### 5. Initialize Database

```python
from modules.voice.config.database import init_db
init_db()
```

## Quick Start

### Running the API Server

```bash
cd modules/voice
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Running the Streamlit UI

```bash
cd modules/voice
streamlit run ui/app.py
```

The UI will open in your browser at `http://localhost:8501`

## Usage

### Voice Commands

The voice assistant recognizes these command categories:

#### Productivity
- "Create a new document called Project Report"
- "Create a spreadsheet for budget tracking"
- "Schedule a meeting for tomorrow at 2pm"
- "Send an email to john@example.com"
- "Create a task to review the proposal"

#### Navigation
- "Open email module"
- "Go to calendar"
- "Show analytics"

#### Query
- "Search for project files"
- "Find emails from last week"

#### System
- "Help"
- "What can you do?"
- "Show commands"

### Using the API

#### Transcribe Audio

```python
import requests

files = {'audio_file': open('recording.wav', 'rb')}
params = {'language_code': 'en-US'}

response = requests.post(
    'http://localhost:8000/api/voice/transcribe',
    files=files,
    params=params
)

result = response.json()
print(result['transcript'])
```

#### Synthesize Speech

```python
import requests

data = {
    'text': 'Hello, welcome to NEXUS!',
    'language_code': 'en-US',
    'audio_format': 'mp3'
}

response = requests.post(
    'http://localhost:8000/api/voice/synthesize',
    json=data
)

with open('output.mp3', 'wb') as f:
    f.write(response.content)
```

#### Process Voice Command

```python
import requests

data = {
    'transcript': 'Create a new document',
    'user_id': 'user123'
}

response = requests.post(
    'http://localhost:8000/api/voice/command',
    json=data
)

result = response.json()
print(f"Intent: {result['intent']}")
print(f"Response: {result['response']}")
```

### Using as a Library

```python
from modules.voice import (
    SpeechToTextService,
    TextToSpeechService,
    IntentRecognizer,
    CommandProcessor
)

# Speech-to-Text
stt = SpeechToTextService(provider='google')
result = stt.transcribe_audio('recording.wav')
print(result['transcript'])

# Text-to-Speech
tts = TextToSpeechService(provider='google')
tts.synthesize_speech('Hello!', 'output.mp3')

# Intent Recognition
recognizer = IntentRecognizer(llm_provider='anthropic', api_key='...')
intent = recognizer.recognize_intent('Create a new document')
print(intent['intent'])
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
# Speech Services
STT_PROVIDER=google
TTS_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# AI/LLM
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_voice
```

## Customizing Commands

### Register a Custom Command

```python
from modules.voice.utils import CommandRegistry

registry = CommandRegistry()

registry.register_command(
    name="custom_action",
    intent="custom_action",
    category="productivity",
    patterns=["do custom action", "perform custom task"],
    description="Perform a custom action",
    module="custom",
    handler="handle_custom_action",
    params=["param1", "param2"],
    examples=["Do custom action with data"]
)
```

### Implement Command Handler

```python
def handle_custom_action(params):
    """Handle custom command."""
    # Your implementation here
    return {
        "success": True,
        "message": "Custom action completed",
        "result": {}
    }
```

## API Endpoints

### Speech Recognition

- `POST /api/voice/transcribe` - Transcribe audio to text
- `POST /api/voice/audio/process` - Process audio (normalize, trim, etc.)

### Text-to-Speech

- `POST /api/voice/synthesize` - Convert text to speech
- `GET /api/voice/voices` - List available voices

### Commands

- `POST /api/voice/command` - Process voice command
- `POST /api/voice/command/confirm` - Confirm pending command
- `GET /api/voice/commands` - List available commands
- `GET /api/voice/commands/search` - Search commands
- `GET /api/voice/commands/help` - Get help text

### Sessions

- `GET /api/voice/session/{session_id}` - Get session info
- `DELETE /api/voice/session/{session_id}` - Clear session

### Health

- `GET /api/voice/health` - Health check

## Advanced Features

### Audio Processing

```python
from modules.voice.services import AudioProcessor

processor = AudioProcessor()

# Normalize audio
processor.normalize_audio('input.wav', 'normalized.wav')

# Trim silence
processor.trim_silence('input.wav', 'trimmed.wav')

# Convert to WAV
processor.convert_to_wav('input.mp3', 'output.wav')

# Get audio info
info = processor.get_audio_info('audio.wav')
print(info)
```

### Context Management

```python
from modules.voice.nlp import ContextManager

context = ContextManager()

# Create session
session = context.create_session('session123', 'user456')

# Add interaction
context.add_interaction(
    session_id='session123',
    user_input='Create a document',
    transcript='Create a document',
    intent='create_document',
    entities={},
    response='Creating document...'
)

# Get history
history = context.get_conversation_history('session123')
```

### Entity Extraction

```python
from modules.voice.nlp import EntityExtractor

extractor = EntityExtractor()

text = "Schedule a meeting for tomorrow at 2pm with john@example.com"
entities = extractor.extract_entities(text)

print(entities['dates'])  # Tomorrow's date
print(entities['times'])  # 2pm
print(entities['emails'])  # john@example.com
```

## Testing

### Run Tests

```bash
cd modules/voice
pytest tests/
```

### Test Coverage

```bash
pytest --cov=. tests/
```

## Performance

- Transcription: ~2-5 seconds for 30 second audio
- Intent Recognition: ~500ms - 1s
- Text-to-Speech: ~1-3 seconds
- Command Processing: ~100-500ms

## Security

- API key authentication supported
- CORS configuration
- Audio file size limits
- Session timeout
- Profanity filtering

## Troubleshooting

### Google Cloud credentials not found

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### AWS credentials error

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Audio import error

```bash
# Install ffmpeg for pydub
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/
```

### Database connection error

Ensure PostgreSQL is running and DATABASE_URL is correct.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- GitHub Issues: [nexus-platform/issues]
- Documentation: [docs/voice/]
- Email: support@nexus.ai

## Roadmap

- [ ] Real-time streaming transcription
- [ ] Multi-language support expansion
- [ ] Custom wake word detection
- [ ] Voice biometrics
- [ ] Advanced noise cancellation
- [ ] Speaker diarization
- [ ] Emotion detection
- [ ] Voice activity detection
- [ ] Custom voice training

## Acknowledgments

- Google Cloud Speech & TTS
- AWS Transcribe & Polly
- Anthropic Claude
- OpenAI GPT
- FastAPI
- Streamlit
