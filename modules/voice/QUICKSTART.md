# Quick Start Guide

Get started with NEXUS Voice Assistant in 5 minutes!

## 1. Install Dependencies

```bash
cd modules/voice
pip install -r requirements.txt
```

## 2. Set Up Credentials

### Option A: Google Cloud (Recommended)

1. Create a Google Cloud project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable these APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API
3. Create a service account and download JSON credentials
4. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Option B: AWS

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_REGION=us-east-1
export AWS_S3_BUCKET=your-bucket-name
```

## 3. Set Up AI/LLM

### Anthropic Claude (Recommended)

```bash
export ANTHROPIC_API_KEY=your_api_key
export LLM_PROVIDER=anthropic
```

### OpenAI GPT

```bash
export OPENAI_API_KEY=your_api_key
export LLM_PROVIDER=openai
```

## 4. Configure Database (Optional)

For development, SQLite is used by default. For production:

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/nexus_voice
```

## 5. Run the Services

### Start API Server

```bash
./scripts/run_api.sh
```

Or manually:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at: http://localhost:8000

API docs: http://localhost:8000/docs

### Start UI

In a new terminal:

```bash
./scripts/run_ui.sh
```

Or manually:

```bash
streamlit run ui/app.py
```

UI will open at: http://localhost:8501

## 6. Try It Out!

### Using the UI

1. Open http://localhost:8501
2. Go to "Text Input" tab
3. Type: "Create a new document called Project Report"
4. Click "Process"
5. See the intent recognition and response!

### Using the API

```bash
# Test health check
curl http://localhost:8000/api/voice/health

# Process a command
curl -X POST http://localhost:8000/api/voice/command \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Create a new document",
    "user_id": "demo_user"
  }'

# Get available commands
curl http://localhost:8000/api/voice/commands
```

### Using Python

```python
from modules.voice import IntentRecognizer
import os

# Initialize recognizer
api_key = os.getenv('ANTHROPIC_API_KEY')
recognizer = IntentRecognizer('anthropic', api_key)

# Recognize intent
result = recognizer.recognize_intent("Create a new document")
print(f"Intent: {result['intent']}")
print(f"Confidence: {result['confidence']:.2%}")
```

## Available Voice Commands

Try these commands:

### Productivity
- "Create a new document called Project Report"
- "Create a spreadsheet for budget tracking"
- "Schedule a meeting for tomorrow at 2pm"
- "Send an email to john@example.com"

### Navigation
- "Open email module"
- "Go to calendar"
- "Show analytics"

### Query
- "Search for project files"
- "Find emails from last week"

### System
- "Help"
- "What can you do?"
- "Show commands"

## Troubleshooting

### "Google credentials not found"

Make sure you set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### "Module not found"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "Connection refused"

Make sure the API server is running on port 8000.

### "Audio recorder not available"

Install the audio recorder package:
```bash
pip install audio-recorder-streamlit
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [examples](examples/basic_usage.py)
- Customize commands in `utils/command_registry.py`
- Add your own handlers for commands
- Integrate with other NEXUS modules

## Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review [examples/basic_usage.py](examples/basic_usage.py)
- Open an issue on GitHub

Happy voice commanding! 🎤
