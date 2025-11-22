"""Audio processing utilities."""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AudioUtils:
    """Utilities for audio file processing."""

    @staticmethod
    def get_audio_duration(file_path: Path) -> Optional[float]:
        """
        Get duration of audio file in seconds.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds, or None if error
        """
        try:
            import librosa
            duration = librosa.get_duration(path=str(file_path))
            return duration
        except ImportError:
            logger.warning("librosa not installed. Cannot get audio duration.")
            return None
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None

    @staticmethod
    def get_audio_info(file_path: Path) -> dict:
        """
        Get audio file information.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio info
        """
        info = {
            "path": str(file_path),
            "filename": file_path.name,
            "format": file_path.suffix.lower(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        }

        try:
            import librosa
            import soundfile as sf

            # Get duration
            info["duration"] = librosa.get_duration(path=str(file_path))

            # Get sample rate and channels
            audio_info = sf.info(str(file_path))
            info["sample_rate"] = audio_info.samplerate
            info["channels"] = audio_info.channels
            info["format_type"] = audio_info.format

        except ImportError:
            logger.warning("librosa/soundfile not installed. Limited audio info.")
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")

        return info

    @staticmethod
    def convert_audio_format(
        input_path: Path,
        output_path: Path,
        target_format: str = "wav",
        sample_rate: Optional[int] = None,
    ) -> bool:
        """
        Convert audio file to different format.

        Args:
            input_path: Input audio file
            output_path: Output audio file
            target_format: Target format (wav, mp3, etc.)
            sample_rate: Target sample rate (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(str(input_path))

            if sample_rate:
                audio = audio.set_frame_rate(sample_rate)

            audio.export(str(output_path), format=target_format)
            return True

        except ImportError:
            logger.error("pydub not installed. Cannot convert audio format.")
            return False
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return False

    @staticmethod
    def split_audio_chunks(
        file_path: Path,
        chunk_length_seconds: float = 30.0,
    ) -> list:
        """
        Split audio file into chunks for processing.

        Args:
            file_path: Path to audio file
            chunk_length_seconds: Length of each chunk in seconds

        Returns:
            List of audio chunks
        """
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(str(file_path))
            chunk_length_ms = int(chunk_length_seconds * 1000)

            chunks = []
            for i in range(0, len(audio), chunk_length_ms):
                chunk = audio[i:i + chunk_length_ms]
                chunks.append(chunk)

            return chunks

        except ImportError:
            logger.error("pydub not installed. Cannot split audio.")
            return []
        except Exception as e:
            logger.error(f"Error splitting audio: {e}")
            return []
