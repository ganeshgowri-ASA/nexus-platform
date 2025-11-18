"""Simple transcription example using NEXUS Speech-to-Text."""

import asyncio
from pathlib import Path
from modules.speech_to_text.services.factory import SpeechServiceFactory


async def transcribe_audio(audio_path: str, provider: str = "whisper"):
    """
    Transcribe audio file using specified provider.

    Args:
        audio_path: Path to audio file
        provider: Provider name (whisper, google, aws)
    """
    # Create service
    config = {
        "model": "base",  # For Whisper
        "device": "cpu",
    }

    service = SpeechServiceFactory.create(provider, config)

    # Transcribe
    print(f"Transcribing {audio_path} with {provider}...")
    result = await service.transcribe_file(
        audio_path=Path(audio_path),
        language="en",
        enable_timestamps=True,
    )

    # Print results
    print("\n=== Transcription Results ===")
    print(f"Language: {result.language}")
    print(f"Confidence: {result.confidence:.2%}" if result.confidence else "N/A")
    print(f"\nFull Text:\n{result.full_text}")

    # Print segments
    if result.segments:
        print(f"\n=== Segments ({len(result.segments)}) ===")
        for i, segment in enumerate(result.segments[:5], 1):  # Show first 5
            print(f"\n{i}. [{segment.start_time:.2f}s - {segment.end_time:.2f}s]")
            print(f"   {segment.text}")


if __name__ == "__main__":
    # Example usage
    audio_file = "path/to/your/audio.mp3"

    # Run transcription
    asyncio.run(transcribe_audio(audio_file, provider="whisper"))
