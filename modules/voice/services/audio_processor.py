"""Audio processing utilities."""

import io
import wave
import numpy as np
from typing import Optional, Tuple
from pathlib import Path


class AudioProcessor:
    """Utility class for audio processing tasks."""

    @staticmethod
    def convert_to_wav(input_file: str, output_file: str, sample_rate: int = 16000) -> str:
        """
        Convert audio file to WAV format.

        Args:
            input_file: Input audio file path
            output_file: Output WAV file path
            sample_rate: Target sample rate in Hz

        Returns:
            Path to converted file
        """
        try:
            from pydub import AudioSegment

            # Load audio file
            audio = AudioSegment.from_file(input_file)

            # Convert to mono and set sample rate
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(sample_rate)

            # Export as WAV
            audio.export(output_file, format="wav")

            return output_file
        except ImportError:
            raise ImportError(
                "pydub not installed. Install with: pip install pydub"
            )

    @staticmethod
    def get_audio_duration(audio_file: str) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            audio_file: Path to audio file

        Returns:
            Duration in seconds
        """
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_file)
            return len(audio) / 1000.0  # Convert ms to seconds
        except ImportError:
            # Fallback for WAV files
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)

    @staticmethod
    def trim_silence(
        audio_file: str,
        output_file: str,
        silence_threshold: int = -40,
        min_silence_len: int = 500
    ) -> str:
        """
        Remove silence from beginning and end of audio.

        Args:
            audio_file: Input audio file
            output_file: Output file path
            silence_threshold: Silence threshold in dBFS
            min_silence_len: Minimum silence length in ms

        Returns:
            Path to trimmed file
        """
        try:
            from pydub import AudioSegment
            from pydub.silence import detect_nonsilent

            audio = AudioSegment.from_file(audio_file)

            # Detect non-silent chunks
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_threshold
            )

            if not nonsilent_ranges:
                # No non-silent audio found, return original
                return audio_file

            # Extract non-silent portion
            start = nonsilent_ranges[0][0]
            end = nonsilent_ranges[-1][1]
            trimmed_audio = audio[start:end]

            # Export
            trimmed_audio.export(output_file, format=Path(output_file).suffix[1:])

            return output_file
        except ImportError:
            raise ImportError(
                "pydub not installed. Install with: pip install pydub"
            )

    @staticmethod
    def normalize_audio(audio_file: str, output_file: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume.

        Args:
            audio_file: Input audio file
            output_file: Output file path
            target_dBFS: Target volume in dBFS

        Returns:
            Path to normalized file
        """
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_file)

            # Calculate the change needed
            change_in_dBFS = target_dBFS - audio.dBFS

            # Apply normalization
            normalized_audio = audio.apply_gain(change_in_dBFS)

            # Export
            normalized_audio.export(output_file, format=Path(output_file).suffix[1:])

            return output_file
        except ImportError:
            raise ImportError(
                "pydub not installed. Install with: pip install pydub"
            )

    @staticmethod
    def split_audio_chunks(
        audio_file: str,
        chunk_length_ms: int = 30000,
        output_dir: str = None
    ) -> list:
        """
        Split audio into chunks.

        Args:
            audio_file: Input audio file
            chunk_length_ms: Length of each chunk in milliseconds
            output_dir: Directory to save chunks

        Returns:
            List of chunk file paths
        """
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_file)

            if output_dir is None:
                output_dir = Path(audio_file).parent / "chunks"

            Path(output_dir).mkdir(parents=True, exist_ok=True)

            chunks = []
            for i, start_ms in enumerate(range(0, len(audio), chunk_length_ms)):
                end_ms = min(start_ms + chunk_length_ms, len(audio))
                chunk = audio[start_ms:end_ms]

                chunk_file = Path(output_dir) / f"chunk_{i:04d}.wav"
                chunk.export(chunk_file, format="wav")
                chunks.append(str(chunk_file))

            return chunks
        except ImportError:
            raise ImportError(
                "pydub not installed. Install with: pip install pydub"
            )

    @staticmethod
    def merge_audio_files(audio_files: list, output_file: str) -> str:
        """
        Merge multiple audio files into one.

        Args:
            audio_files: List of audio file paths
            output_file: Output file path

        Returns:
            Path to merged file
        """
        try:
            from pydub import AudioSegment

            combined = AudioSegment.empty()

            for audio_file in audio_files:
                audio = AudioSegment.from_file(audio_file)
                combined += audio

            combined.export(output_file, format=Path(output_file).suffix[1:])

            return output_file
        except ImportError:
            raise ImportError(
                "pydub not installed. Install with: pip install pydub"
            )

    @staticmethod
    def detect_voice_activity(audio_file: str, aggressiveness: int = 2) -> list:
        """
        Detect voice activity in audio file.

        Args:
            audio_file: Input audio file
            aggressiveness: VAD aggressiveness (0-3)

        Returns:
            List of (start_time, end_time) tuples with voice activity
        """
        try:
            import webrtcvad
            from pydub import AudioSegment

            vad = webrtcvad.Vad(aggressiveness)

            # Load and convert to 16kHz mono WAV
            audio = AudioSegment.from_file(audio_file)
            audio = audio.set_frame_rate(16000).set_channels(1)

            # Convert to raw PCM
            raw_data = audio.raw_data

            # Process in 30ms frames
            frame_duration = 30  # ms
            frame_size = int(16000 * frame_duration / 1000) * 2  # 2 bytes per sample

            voiced_frames = []
            for i in range(0, len(raw_data), frame_size):
                frame = raw_data[i:i + frame_size]
                if len(frame) < frame_size:
                    break

                is_speech = vad.is_speech(frame, 16000)
                voiced_frames.append((i / frame_size, is_speech))

            # Merge consecutive voice segments
            voice_segments = []
            current_segment = None

            for frame_idx, is_speech in voiced_frames:
                timestamp = frame_idx * frame_duration / 1000  # Convert to seconds

                if is_speech:
                    if current_segment is None:
                        current_segment = [timestamp, timestamp]
                    else:
                        current_segment[1] = timestamp
                else:
                    if current_segment is not None:
                        voice_segments.append(tuple(current_segment))
                        current_segment = None

            if current_segment is not None:
                voice_segments.append(tuple(current_segment))

            return voice_segments

        except ImportError:
            raise ImportError(
                "webrtcvad not installed. Install with: pip install webrtcvad"
            )

    @staticmethod
    def get_audio_info(audio_file: str) -> dict:
        """
        Get information about audio file.

        Args:
            audio_file: Path to audio file

        Returns:
            Dict with audio information
        """
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_file)

            return {
                "duration_seconds": len(audio) / 1000.0,
                "channels": audio.channels,
                "sample_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
                "frame_count": audio.frame_count(),
                "frame_width": audio.frame_width,
                "dBFS": audio.dBFS,
                "max_dBFS": audio.max_dBFS,
                "file_size_bytes": Path(audio_file).stat().st_size
            }
        except ImportError:
            raise ImportError(
                "pydub not installed. Install with: pip install pydub"
            )
