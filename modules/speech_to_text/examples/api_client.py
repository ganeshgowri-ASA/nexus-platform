"""Example API client for NEXUS Speech-to-Text."""

import requests
import time
from pathlib import Path


class SpeechToTextClient:
    """Client for NEXUS Speech-to-Text API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client."""
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1/speech"

    def health_check(self):
        """Check API health."""
        response = requests.get(f"{self.api_url}/health")
        return response.json()

    def transcribe_file(
        self,
        file_path: str,
        provider: str = "whisper",
        language: str = None,
        enable_diarization: bool = False,
        user_id: str = "demo",
    ):
        """
        Transcribe audio file.

        Args:
            file_path: Path to audio file
            provider: Provider (whisper, google, aws)
            language: Language code
            enable_diarization: Enable speaker diarization
            user_id: User ID

        Returns:
            Transcription result
        """
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            params = {
                "provider": provider,
                "enable_diarization": enable_diarization,
                "user_id": user_id,
            }
            if language:
                params["language"] = language

            response = requests.post(
                f"{self.api_url}/transcribe",
                files=files,
                params=params,
            )

            if response.status_code == 201:
                return response.json()
            else:
                raise Exception(f"Error: {response.status_code} - {response.text}")

    def get_transcription(self, transcription_id: int, include_segments: bool = True):
        """Get transcription by ID."""
        response = requests.get(
            f"{self.api_url}/transcriptions/{transcription_id}",
            params={"include_segments": include_segments},
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def list_transcriptions(self, user_id: str = None, limit: int = 10):
        """List transcriptions."""
        params = {"limit": limit}
        if user_id:
            params["user_id"] = user_id

        response = requests.get(f"{self.api_url}/transcriptions", params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}")

    def delete_transcription(self, transcription_id: int):
        """Delete transcription."""
        response = requests.delete(
            f"{self.api_url}/transcriptions/{transcription_id}"
        )
        return response.status_code == 204

    def poll_until_complete(self, transcription_id: int, max_attempts: int = 60):
        """Poll transcription until complete."""
        for attempt in range(max_attempts):
            result = self.get_transcription(transcription_id, include_segments=False)
            status = result["status"]

            print(f"Attempt {attempt + 1}/{max_attempts}: Status = {status}")

            if status == "completed":
                return self.get_transcription(transcription_id, include_segments=True)
            elif status == "failed":
                raise Exception(f"Transcription failed: {result.get('error_message')}")

            time.sleep(5)

        raise Exception("Transcription timeout")


def main():
    """Example usage."""
    # Initialize client
    client = SpeechToTextClient()

    # Check health
    print("Checking API health...")
    health = client.health_check()
    print(f"API Status: {health['status']}")
    print(f"Supported providers: {health['supported_providers']}")

    # Transcribe file
    audio_file = "path/to/your/audio.mp3"
    print(f"\nTranscribing {audio_file}...")

    result = client.transcribe_file(
        file_path=audio_file,
        provider="whisper",
        language="en",
        enable_diarization=False,
    )

    transcription_id = result["id"]
    print(f"Transcription started! ID: {transcription_id}")

    # Poll for completion
    print("\nWaiting for transcription to complete...")
    final_result = client.poll_until_complete(transcription_id)

    # Display results
    print("\n=== Transcription Complete ===")
    print(f"Language: {final_result['language']}")
    print(f"Confidence: {final_result.get('confidence', 'N/A')}")
    print(f"\nFull Text:\n{final_result['full_text']}")

    if final_result.get("segments"):
        print(f"\nTotal segments: {len(final_result['segments'])}")

    # List all transcriptions
    print("\n=== Recent Transcriptions ===")
    transcriptions = client.list_transcriptions(limit=5)
    for trans in transcriptions["items"]:
        print(f"- ID {trans['id']}: {trans['filename']} ({trans['status']})")


if __name__ == "__main__":
    main()
