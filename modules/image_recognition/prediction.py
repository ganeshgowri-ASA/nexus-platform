"""
Prediction Engine Module

Provides comprehensive prediction capabilities including:
- Real-time single image prediction
- Batch prediction processing
- Asynchronous prediction
- Confidence scoring and calibration
- Prediction caching
- Model ensemble predictions
- Streaming predictions
- WebSocket real-time predictions

Optimized for production with error handling and performance monitoring.
"""

import logging
import time
import asyncio
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
from PIL import Image
from queue import Queue
from threading import Thread
import json

from .models import BaseModelWrapper, ModelFactory
from .classifier import ImageClassifier

logger = logging.getLogger(__name__)


class PredictionResult:
    """
    Represents a prediction result with metadata.
    """

    def __init__(
        self,
        predictions: List[Dict[str, Any]],
        image_id: Optional[str] = None,
        model_name: str = "unknown",
        processing_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize prediction result.

        Args:
            predictions: List of prediction dictionaries
            image_id: Associated image ID
            model_name: Model used for prediction
            processing_time_ms: Processing time in milliseconds
            metadata: Additional metadata
        """
        self.predictions = predictions
        self.image_id = image_id
        self.model_name = model_name
        self.processing_time_ms = processing_time_ms
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def get_top_prediction(self) -> Dict[str, Any]:
        """Get the top prediction."""
        if self.predictions:
            return self.predictions[0]
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'predictions': self.predictions,
            'image_id': self.image_id,
            'model_name': self.model_name,
            'processing_time_ms': self.processing_time_ms,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        top = self.get_top_prediction()
        label = top.get('label', 'unknown')
        confidence = top.get('confidence', 0.0)
        return f"<PredictionResult(label={label}, confidence={confidence:.2f})>"


class RealtimePredictor:
    """
    Real-time single image predictor.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize real-time predictor.

        Args:
            model_type: Type of model to use
            model_path: Path to custom model
            config: Predictor configuration
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}
        self.classifier = ImageClassifier(model_type, model_path, config)
        self.logger = logging.getLogger(f"{__name__}.RealtimePredictor")

    def predict(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int = 5,
        confidence_threshold: float = 0.0,
        image_id: Optional[str] = None
    ) -> PredictionResult:
        """
        Predict single image in real-time.

        Args:
            image: Input image
            top_k: Number of top predictions
            confidence_threshold: Minimum confidence
            image_id: Optional image identifier

        Returns:
            Prediction result
        """
        try:
            start_time = time.time()

            # Run classification
            result = self.classifier.classify(
                image,
                top_k=top_k,
                confidence_threshold=confidence_threshold
            )

            processing_time = (time.time() - start_time) * 1000

            if result['success']:
                return PredictionResult(
                    predictions=result['predictions'],
                    image_id=image_id,
                    model_name=result['model_name'],
                    processing_time_ms=processing_time
                )
            else:
                raise Exception(result.get('error', 'Prediction failed'))

        except Exception as e:
            self.logger.error(f"Error during prediction: {e}")
            raise


class BatchPredictor:
    """
    Batch prediction processor for multiple images.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        num_workers: int = 4
    ):
        """
        Initialize batch predictor.

        Args:
            model_type: Type of model to use
            model_path: Path to custom model
            config: Predictor configuration
            num_workers: Number of parallel workers
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}
        self.num_workers = num_workers
        self.classifier = ImageClassifier(model_type, model_path, config)
        self.logger = logging.getLogger(f"{__name__}.BatchPredictor")

    def predict_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        batch_size: int = 32,
        top_k: int = 5,
        confidence_threshold: float = 0.0,
        image_ids: Optional[List[str]] = None,
        parallel: bool = True
    ) -> List[PredictionResult]:
        """
        Predict multiple images in batch.

        Args:
            images: List of images
            batch_size: Batch size for processing
            top_k: Number of top predictions per image
            confidence_threshold: Minimum confidence
            image_ids: Optional list of image IDs
            parallel: Whether to use parallel processing

        Returns:
            List of prediction results
        """
        try:
            self.logger.info(f"Processing batch of {len(images)} images...")
            start_time = time.time()

            results = []

            if parallel and self.num_workers > 1:
                # Parallel processing
                with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                    futures = []
                    for idx, image in enumerate(images):
                        img_id = image_ids[idx] if image_ids else f"image_{idx}"
                        future = executor.submit(
                            self._predict_single,
                            image,
                            top_k,
                            confidence_threshold,
                            img_id
                        )
                        futures.append(future)

                    for future in futures:
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            self.logger.error(f"Error in parallel prediction: {e}")
                            results.append(None)
            else:
                # Sequential processing
                for idx, image in enumerate(images):
                    try:
                        img_id = image_ids[idx] if image_ids else f"image_{idx}"
                        result = self._predict_single(
                            image,
                            top_k,
                            confidence_threshold,
                            img_id
                        )
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error predicting image {idx}: {e}")
                        results.append(None)

            total_time = time.time() - start_time
            avg_time = (total_time * 1000) / len(images)

            self.logger.info(
                f"Batch prediction completed in {total_time:.2f}s "
                f"(avg {avg_time:.2f}ms per image)"
            )

            return [r for r in results if r is not None]

        except Exception as e:
            self.logger.error(f"Error during batch prediction: {e}")
            raise

    def _predict_single(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int,
        confidence_threshold: float,
        image_id: str
    ) -> PredictionResult:
        """Predict single image (internal helper)."""
        start_time = time.time()

        result = self.classifier.classify(
            image,
            top_k=top_k,
            confidence_threshold=confidence_threshold
        )

        processing_time = (time.time() - start_time) * 1000

        if result['success']:
            return PredictionResult(
                predictions=result['predictions'],
                image_id=image_id,
                model_name=result['model_name'],
                processing_time_ms=processing_time
            )
        else:
            raise Exception(result.get('error', 'Prediction failed'))


class AsyncPredictor:
    """
    Asynchronous predictor for non-blocking predictions.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize async predictor.

        Args:
            model_type: Type of model to use
            model_path: Path to custom model
            config: Predictor configuration
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}
        self.classifier = ImageClassifier(model_type, model_path, config)
        self.logger = logging.getLogger(f"{__name__}.AsyncPredictor")

    async def predict_async(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int = 5,
        confidence_threshold: float = 0.0,
        image_id: Optional[str] = None
    ) -> PredictionResult:
        """
        Predict image asynchronously.

        Args:
            image: Input image
            top_k: Number of top predictions
            confidence_threshold: Minimum confidence
            image_id: Optional image identifier

        Returns:
            Prediction result
        """
        try:
            # Run prediction in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._predict_sync,
                image,
                top_k,
                confidence_threshold,
                image_id
            )
            return result

        except Exception as e:
            self.logger.error(f"Error during async prediction: {e}")
            raise

    def _predict_sync(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int,
        confidence_threshold: float,
        image_id: Optional[str]
    ) -> PredictionResult:
        """Synchronous prediction helper."""
        start_time = time.time()

        result = self.classifier.classify(
            image,
            top_k=top_k,
            confidence_threshold=confidence_threshold
        )

        processing_time = (time.time() - start_time) * 1000

        if result['success']:
            return PredictionResult(
                predictions=result['predictions'],
                image_id=image_id,
                model_name=result['model_name'],
                processing_time_ms=processing_time
            )
        else:
            raise Exception(result.get('error', 'Prediction failed'))


class PredictionCache:
    """
    Caches prediction results for faster retrieval.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600
    ):
        """
        Initialize prediction cache.

        Args:
            max_size: Maximum cache size
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[PredictionResult, datetime]] = {}
        self.logger = logging.getLogger(f"{__name__}.PredictionCache")

    def get(self, cache_key: str) -> Optional[PredictionResult]:
        """
        Get cached prediction result.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]

            # Check if expired
            if datetime.utcnow() - timestamp < timedelta(seconds=self.ttl_seconds):
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return result
            else:
                # Remove expired entry
                del self.cache[cache_key]
                self.logger.debug(f"Cache expired for key: {cache_key}")

        return None

    def put(self, cache_key: str, result: PredictionResult) -> None:
        """
        Put prediction result in cache.

        Args:
            cache_key: Cache key
            result: Prediction result
        """
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
            self.logger.debug(f"Evicted cache entry: {oldest_key}")

        self.cache[cache_key] = (result, datetime.utcnow())
        self.logger.debug(f"Cached result for key: {cache_key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.logger.info("Cache cleared")

    def get_size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class EnsemblePredictor:
    """
    Ensemble predictor that combines multiple models.
    """

    def __init__(
        self,
        models: List[Dict[str, Any]],
        voting_method: str = "soft"
    ):
        """
        Initialize ensemble predictor.

        Args:
            models: List of model configurations
            voting_method: Voting method (soft, hard, weighted)
        """
        self.models = models
        self.voting_method = voting_method
        self.predictors: List[RealtimePredictor] = []
        self.logger = logging.getLogger(f"{__name__}.EnsemblePredictor")

        # Initialize predictors
        for model_config in models:
            predictor = RealtimePredictor(
                model_type=model_config['model_type'],
                model_path=model_config.get('model_path'),
                config=model_config.get('config')
            )
            self.predictors.append(predictor)

    def predict(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int = 5,
        confidence_threshold: float = 0.0,
        image_id: Optional[str] = None
    ) -> PredictionResult:
        """
        Predict using ensemble of models.

        Args:
            image: Input image
            top_k: Number of top predictions
            confidence_threshold: Minimum confidence
            image_id: Optional image identifier

        Returns:
            Ensemble prediction result
        """
        try:
            start_time = time.time()

            # Get predictions from all models
            all_predictions = []
            for predictor in self.predictors:
                try:
                    result = predictor.predict(image, top_k=10, confidence_threshold=0.0)
                    all_predictions.append(result.predictions)
                except Exception as e:
                    self.logger.error(f"Error in ensemble model: {e}")
                    continue

            if not all_predictions:
                raise Exception("All ensemble models failed")

            # Combine predictions
            if self.voting_method == "soft":
                combined = self._soft_voting(all_predictions)
            elif self.voting_method == "hard":
                combined = self._hard_voting(all_predictions)
            elif self.voting_method == "weighted":
                combined = self._weighted_voting(all_predictions)
            else:
                raise ValueError(f"Unsupported voting method: {self.voting_method}")

            # Filter by threshold and get top K
            filtered = [p for p in combined if p['confidence'] >= confidence_threshold]
            filtered.sort(key=lambda x: x['confidence'], reverse=True)
            final_predictions = filtered[:top_k]

            processing_time = (time.time() - start_time) * 1000

            return PredictionResult(
                predictions=final_predictions,
                image_id=image_id,
                model_name="ensemble",
                processing_time_ms=processing_time,
                metadata={'num_models': len(self.predictors)}
            )

        except Exception as e:
            self.logger.error(f"Error during ensemble prediction: {e}")
            raise

    def _soft_voting(self, all_predictions: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combine predictions using soft voting (average confidences)."""
        # Aggregate confidences by label
        label_scores: Dict[str, List[float]] = {}

        for predictions in all_predictions:
            for pred in predictions:
                label = pred['label']
                confidence = pred['confidence']

                if label not in label_scores:
                    label_scores[label] = []
                label_scores[label].append(confidence)

        # Calculate average confidence for each label
        combined = []
        for label, scores in label_scores.items():
            avg_confidence = sum(scores) / len(scores)
            combined.append({
                'label': label,
                'confidence': avg_confidence,
                'votes': len(scores)
            })

        return combined

    def _hard_voting(self, all_predictions: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combine predictions using hard voting (majority vote)."""
        # Count votes for each label (only top prediction from each model)
        label_votes: Dict[str, int] = {}

        for predictions in all_predictions:
            if predictions:
                top_label = predictions[0]['label']
                label_votes[top_label] = label_votes.get(top_label, 0) + 1

        # Convert to prediction format
        total_models = len(all_predictions)
        combined = []
        for label, votes in label_votes.items():
            combined.append({
                'label': label,
                'confidence': votes / total_models,
                'votes': votes
            })

        return combined

    def _weighted_voting(self, all_predictions: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Combine predictions using weighted voting."""
        # For simplicity, use soft voting with equal weights
        # In production, weights could be based on model performance
        return self._soft_voting(all_predictions)


class StreamingPredictor:
    """
    Streaming predictor for continuous predictions.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        queue_size: int = 100
    ):
        """
        Initialize streaming predictor.

        Args:
            model_type: Type of model to use
            model_path: Path to custom model
            config: Predictor configuration
            queue_size: Size of input queue
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}
        self.queue_size = queue_size

        self.input_queue: Queue = Queue(maxsize=queue_size)
        self.output_queue: Queue = Queue(maxsize=queue_size)
        self.is_running = False
        self.worker_thread: Optional[Thread] = None

        self.classifier = ImageClassifier(model_type, model_path, config)
        self.logger = logging.getLogger(f"{__name__}.StreamingPredictor")

    def start(self) -> None:
        """Start streaming predictor."""
        if self.is_running:
            self.logger.warning("Streaming predictor already running")
            return

        self.is_running = True
        self.worker_thread = Thread(target=self._process_stream, daemon=True)
        self.worker_thread.start()
        self.logger.info("Streaming predictor started")

    def stop(self) -> None:
        """Stop streaming predictor."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("Streaming predictor stopped")

    def submit(
        self,
        image: Union[str, np.ndarray, Image.Image],
        image_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Submit image for prediction.

        Args:
            image: Input image
            image_id: Optional image identifier
            metadata: Optional metadata

        Returns:
            True if submitted successfully
        """
        try:
            self.input_queue.put({
                'image': image,
                'image_id': image_id,
                'metadata': metadata or {}
            }, timeout=1)
            return True
        except:
            self.logger.error("Failed to submit image: queue full")
            return False

    def get_result(self, timeout: float = 1.0) -> Optional[PredictionResult]:
        """
        Get prediction result from output queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Prediction result or None
        """
        try:
            return self.output_queue.get(timeout=timeout)
        except:
            return None

    def _process_stream(self) -> None:
        """Process incoming images (worker thread)."""
        while self.is_running:
            try:
                # Get image from input queue
                item = self.input_queue.get(timeout=0.1)

                # Run prediction
                start_time = time.time()
                result = self.classifier.classify(
                    item['image'],
                    top_k=5,
                    confidence_threshold=0.0
                )
                processing_time = (time.time() - start_time) * 1000

                # Create result
                if result['success']:
                    pred_result = PredictionResult(
                        predictions=result['predictions'],
                        image_id=item['image_id'],
                        model_name=result['model_name'],
                        processing_time_ms=processing_time,
                        metadata=item['metadata']
                    )
                    # Put result in output queue
                    self.output_queue.put(pred_result)

            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error processing stream: {e}")
                continue


# Global instances
prediction_cache = PredictionCache()
