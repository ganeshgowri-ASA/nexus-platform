"""Speaker diarization utilities using pyannote.audio."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DiarizationService:
    """
    Speaker diarization service using pyannote.audio.

    This can be used to add speaker diarization to Whisper transcriptions.
    """

    def __init__(self, model_name: str = "pyannote/speaker-diarization"):
        """
        Initialize diarization service.

        Args:
            model_name: HuggingFace model name for diarization
        """
        self.model_name = model_name
        self._pipeline = None

    def _load_pipeline(self):
        """Lazy load diarization pipeline."""
        if self._pipeline is None:
            try:
                from pyannote.audio import Pipeline
                import torch

                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self._pipeline = Pipeline.from_pretrained(
                    self.model_name,
                    use_auth_token=None,  # Add HuggingFace token if needed
                )
                self._pipeline.to(device)

            except ImportError:
                raise ImportError(
                    "pyannote.audio not installed. "
                    "Install with: pip install pyannote.audio"
                )
            except Exception as e:
                logger.error(f"Failed to load diarization pipeline: {e}")
                raise

        return self._pipeline

    def diarize(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        min_speakers: int = 1,
        max_speakers: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform speaker diarization on audio file.

        Args:
            audio_path: Path to audio file
            num_speakers: Fixed number of speakers (optional)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            List of diarization segments with speaker labels
        """
        pipeline = self._load_pipeline()

        # Run diarization
        if num_speakers:
            diarization = pipeline(str(audio_path), num_speakers=num_speakers)
        else:
            diarization = pipeline(
                str(audio_path),
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )

        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
            })

        return segments

    def align_with_transcription(
        self,
        transcription_segments: List[Dict[str, Any]],
        diarization_segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Align transcription segments with speaker diarization.

        Args:
            transcription_segments: List of transcription segments with timestamps
            diarization_segments: List of diarization segments

        Returns:
            Transcription segments with speaker labels
        """
        aligned = []

        for trans_seg in transcription_segments:
            trans_start = trans_seg["start_time"]
            trans_end = trans_seg["end_time"]
            trans_mid = (trans_start + trans_end) / 2

            # Find overlapping speaker
            best_speaker = None
            best_overlap = 0

            for dia_seg in diarization_segments:
                dia_start = dia_seg["start"]
                dia_end = dia_seg["end"]

                # Calculate overlap
                overlap_start = max(trans_start, dia_start)
                overlap_end = min(trans_end, dia_end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = dia_seg["speaker"]

            # If no overlap found, use speaker at midpoint
            if best_speaker is None:
                for dia_seg in diarization_segments:
                    if dia_seg["start"] <= trans_mid <= dia_seg["end"]:
                        best_speaker = dia_seg["speaker"]
                        break

            aligned_seg = trans_seg.copy()
            aligned_seg["speaker_id"] = best_speaker
            aligned.append(aligned_seg)

        return aligned

    def get_speaker_statistics(
        self,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate speaker statistics from segments.

        Args:
            segments: List of segments with speaker labels

        Returns:
            Dictionary of speaker statistics
        """
        stats = {}

        for seg in segments:
            speaker = seg.get("speaker") or seg.get("speaker_id")
            if not speaker:
                continue

            duration = seg["end"] - seg["start"] if "end" in seg else (
                seg["end_time"] - seg["start_time"]
            )

            if speaker not in stats:
                stats[speaker] = {
                    "total_duration": 0,
                    "num_segments": 0,
                }

            stats[speaker]["total_duration"] += duration
            stats[speaker]["num_segments"] += 1

        return stats
