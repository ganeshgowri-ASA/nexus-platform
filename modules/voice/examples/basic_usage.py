"""Basic usage examples for NEXUS Voice Assistant."""

import os
from modules.voice import (
    SpeechToTextService,
    TextToSpeechService,
    IntentRecognizer,
    EntityExtractor,
    ContextManager,
    CommandProcessor,
    CommandRegistry
)


def example_speech_to_text():
    """Example: Convert speech to text."""
    print("\n=== Speech-to-Text Example ===")

    # Initialize service
    stt = SpeechToTextService(provider='google')

    # Transcribe audio file
    result = stt.transcribe_audio(
        audio_file='example_audio.wav',
        language_code='en-US',
        enable_automatic_punctuation=True
    )

    print(f"Transcript: {result['transcript']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Processing time: {result['processing_time_ms']:.0f}ms")


def example_text_to_speech():
    """Example: Convert text to speech."""
    print("\n=== Text-to-Speech Example ===")

    # Initialize service
    tts = TextToSpeechService(provider='google')

    # Synthesize speech
    text = "Hello! Welcome to the NEXUS voice assistant."

    result = tts.synthesize_speech(
        text=text,
        output_file='output.mp3',
        language_code='en-US',
        speaking_rate=1.0
    )

    print(f"Generated audio: {result['output_file']}")
    print(f"Voice: {result['voice_name']}")


def example_intent_recognition():
    """Example: Recognize intent from text."""
    print("\n=== Intent Recognition Example ===")

    # Initialize recognizer
    api_key = os.getenv('ANTHROPIC_API_KEY')
    recognizer = IntentRecognizer(llm_provider='anthropic', api_key=api_key)

    # Recognize intent
    text = "Create a new document called Project Report"
    result = recognizer.recognize_intent(text)

    print(f"Text: {text}")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Category: {result['category']}")
    print(f"Entities: {result['entities']}")


def example_entity_extraction():
    """Example: Extract entities from text."""
    print("\n=== Entity Extraction Example ===")

    # Initialize extractor
    extractor = EntityExtractor()

    # Extract entities
    text = "Schedule a meeting for tomorrow at 2pm with john@example.com"
    entities = extractor.extract_entities(text)

    print(f"Text: {text}")
    print("\nExtracted entities:")
    for entity_type, values in entities.items():
        print(f"  {entity_type}: {values}")


def example_command_processing():
    """Example: Process voice commands."""
    print("\n=== Command Processing Example ===")

    # Initialize components
    api_key = os.getenv('ANTHROPIC_API_KEY')
    intent_recognizer = IntentRecognizer('anthropic', api_key)
    entity_extractor = EntityExtractor()
    context_manager = ContextManager()
    command_registry = CommandRegistry()

    # Create processor
    processor = CommandProcessor(
        intent_recognizer=intent_recognizer,
        entity_extractor=entity_extractor,
        context_manager=context_manager,
        command_registry=command_registry
    )

    # Process command
    result = processor.process_command(
        transcript="Create a new spreadsheet for budget tracking",
        session_id="example_session",
        user_id="user123"
    )

    print(f"Transcript: {result['transcript']}")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Command: {result['command']}")
    print(f"Response: {result['response']}")


def example_context_management():
    """Example: Manage conversation context."""
    print("\n=== Context Management Example ===")

    # Initialize manager
    context = ContextManager()

    # Create session
    session = context.create_session(
        session_id="session123",
        user_id="user456"
    )

    print(f"Created session: {session['session_id']}")

    # Add interactions
    interactions = [
        {
            "user_input": "Create a document",
            "transcript": "Create a document",
            "intent": "create_document",
            "entities": {},
            "response": "Creating document..."
        },
        {
            "user_input": "Call it Project Report",
            "transcript": "Call it Project Report",
            "intent": "set_title",
            "entities": {"title": "Project Report"},
            "response": "Document titled 'Project Report' created"
        }
    ]

    for interaction in interactions:
        context.add_interaction(
            session_id="session123",
            **interaction
        )

    # Get history
    history = context.get_conversation_history("session123")
    print(f"\nConversation history ({len(history)} interactions):")
    for i, h in enumerate(history, 1):
        print(f"{i}. {h['intent']}: {h['transcript']}")

    # Get context for intent
    ctx = context.get_context_for_intent("session123")
    print(f"\nContext: {ctx}")


def example_custom_command():
    """Example: Register and use custom command."""
    print("\n=== Custom Command Example ===")

    # Initialize registry
    registry = CommandRegistry()

    # Register custom command
    registry.register_command(
        name="weather_check",
        intent="check_weather",
        category="query",
        patterns=[
            "what's the weather",
            "weather forecast",
            "check weather"
        ],
        description="Check the weather",
        module="weather",
        handler="get_weather",
        params=["location"],
        examples=[
            "What's the weather in New York?",
            "Check weather for tomorrow"
        ]
    )

    # Get command
    cmd = registry.get_command("weather_check")
    print(f"Command: {cmd['name']}")
    print(f"Description: {cmd['description']}")
    print(f"Examples: {cmd['examples']}")

    # Search commands
    results = registry.search_commands("weather")
    print(f"\nSearch results for 'weather': {len(results)} commands")
    for cmd in results:
        print(f"  - {cmd['name']}: {cmd['description']}")


def example_list_voices():
    """Example: List available TTS voices."""
    print("\n=== List Voices Example ===")

    # Initialize service
    tts = TextToSpeechService(provider='google')

    # List voices
    voices = tts.list_voices(language_code='en-US')

    print(f"Provider: {voices['provider']}")
    print(f"Total voices: {voices['count']}")
    print("\nSample voices:")
    for voice in voices['voices'][:5]:
        print(f"  - {voice['name']} ({voice.get('gender', 'N/A')})")


def example_full_workflow():
    """Example: Complete voice command workflow."""
    print("\n=== Full Workflow Example ===")

    # This example shows how all components work together

    # 1. Initialize services
    print("1. Initializing services...")
    stt = SpeechToTextService(provider='google')
    tts = TextToSpeechService(provider='google')

    api_key = os.getenv('ANTHROPIC_API_KEY')
    recognizer = IntentRecognizer('anthropic', api_key)
    extractor = EntityExtractor()
    context = ContextManager()
    registry = CommandRegistry()

    processor = CommandProcessor(
        intent_recognizer=recognizer,
        entity_extractor=extractor,
        context_manager=context,
        command_registry=registry
    )

    # 2. Create session
    print("2. Creating session...")
    session_id = "workflow_session"
    user_id = "demo_user"
    context.create_session(session_id, user_id)

    # 3. Transcribe audio (simulated)
    print("3. Transcribing audio...")
    # In real usage: result = stt.transcribe_audio('recording.wav')
    transcript = "Create a new document called Project Plan"

    # 4. Process command
    print("4. Processing command...")
    result = processor.process_command(
        transcript=transcript,
        session_id=session_id,
        user_id=user_id
    )

    print(f"   Intent: {result['intent']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Response: {result['response']}")

    # 5. Generate speech response
    print("5. Generating speech response...")
    # In real usage:
    # tts.synthesize_speech(
    #     text=result['response'],
    #     output_file='response.mp3'
    # )

    # 6. Get conversation history
    print("6. Retrieving conversation history...")
    history = context.get_conversation_history(session_id)
    print(f"   Total interactions: {len(history)}")

    print("\n✓ Workflow completed successfully!")


if __name__ == "__main__":
    print("NEXUS Voice Assistant - Usage Examples")
    print("=" * 50)

    # Run examples
    try:
        # Basic examples
        # example_speech_to_text()  # Requires audio file
        # example_text_to_speech()  # Requires credentials
        example_intent_recognition()
        example_entity_extraction()
        example_command_processing()
        example_context_management()
        example_custom_command()
        # example_list_voices()  # Requires credentials

        # Full workflow
        # example_full_workflow()

        print("\n" + "=" * 50)
        print("Examples completed!")

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure you have set up credentials and configuration.")
