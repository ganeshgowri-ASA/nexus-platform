"""
Image Classification Module

Provides image classification capabilities including:
- Single-label classification
- Multi-label classification
- Custom classifiers with transfer learning
"""

import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import numpy as np
from PIL import Image
import time

from .models import ModelFactory, BaseModelWrapper, model_registry

logger = logging.getLogger(__name__)


class ImageClassifier:
    """
    Image classifier for single-label classification.
    Uses pre-trained models or custom trained models.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize image classifier.

        Args:
            model_type: Type of model to use (vgg16, resnet50, inceptionv3, efficientnet)
            model_path: Path to custom model weights
            config: Model configuration
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}
        self.model: Optional[BaseModelWrapper] = None
        self.logger = logging.getLogger(f"{__name__}.ImageClassifier")

    def load_model(self) -> bool:
        """Load the classification model."""
        try:
            self.model = ModelFactory.create_model(
                model_type=self.model_type,
                model_path=self.model_path,
                config=self.config
            )
            return self.model.load_model()
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def classify(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int = 5,
        confidence_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        Classify an image.

        Args:
            image: Image path, numpy array, or PIL Image
            top_k: Number of top predictions to return
            confidence_threshold: Minimum confidence threshold

        Returns:
            Dict containing predictions and metadata
        """
        try:
            # Load model if not already loaded
            if self.model is None or not self.model.is_loaded:
                self.load_model()

            # Load image if path provided
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Run prediction
            results = self.model.predict(image, top_k=top_k)

            # Filter by confidence threshold
            if confidence_threshold > 0:
                results['predictions'] = [
                    pred for pred in results['predictions']
                    if pred['confidence'] >= confidence_threshold
                ]

            return {
                'success': True,
                'predictions': results['predictions'],
                'processing_time_ms': results['processing_time_ms'],
                'model_name': results['model_name'],
                'model_type': self.model_type
            }

        except Exception as e:
            self.logger.error(f"Error during classification: {e}")
            return {
                'success': False,
                'error': str(e),
                'predictions': []
            }

    def classify_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        top_k: int = 5,
        confidence_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Classify multiple images.

        Args:
            images: List of images
            top_k: Number of top predictions per image
            confidence_threshold: Minimum confidence threshold

        Returns:
            List of prediction dicts
        """
        results = []
        for image in images:
            result = self.classify(image, top_k, confidence_threshold)
            results.append(result)
        return results


class MultiLabelClassifier:
    """
    Multi-label classifier for images that can have multiple categories.
    """

    def __init__(
        self,
        model_path: str,
        labels: List[str],
        threshold: float = 0.5,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize multi-label classifier.

        Args:
            model_path: Path to trained multi-label model
            labels: List of possible labels
            threshold: Confidence threshold for each label
            config: Model configuration
        """
        self.model_path = model_path
        self.labels = labels
        self.threshold = threshold
        self.config = config or {}
        self.model: Optional[BaseModelWrapper] = None
        self.logger = logging.getLogger(f"{__name__}.MultiLabelClassifier")

    def load_model(self) -> bool:
        """Load the multi-label model."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            self.model = keras.models.load_model(self.model_path)
            self.logger.info(f"Loaded multi-label model from {self.model_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def classify(
        self,
        image: Union[str, np.ndarray, Image.Image]
    ) -> Dict[str, Any]:
        """
        Classify image with multiple labels.

        Args:
            image: Image to classify

        Returns:
            Dict with all applicable labels
        """
        try:
            if self.model is None:
                self.load_model()

            # Load and preprocess image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Preprocess
            import tensorflow as tf
            from tensorflow import keras

            image = image.resize((224, 224))
            img_array = keras.preprocessing.image.img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0

            # Predict
            start_time = time.time()
            predictions = self.model.predict(img_array)[0]
            processing_time = (time.time() - start_time) * 1000

            # Get labels above threshold
            active_labels = []
            for idx, prob in enumerate(predictions):
                if prob >= self.threshold:
                    active_labels.append({
                        'label': self.labels[idx],
                        'confidence': float(prob),
                        'index': idx
                    })

            # Sort by confidence
            active_labels.sort(key=lambda x: x['confidence'], reverse=True)

            return {
                'success': True,
                'labels': active_labels,
                'num_labels': len(active_labels),
                'all_predictions': {
                    label: float(prob)
                    for label, prob in zip(self.labels, predictions)
                },
                'processing_time_ms': processing_time
            }

        except Exception as e:
            self.logger.error(f"Error during multi-label classification: {e}")
            return {
                'success': False,
                'error': str(e),
                'labels': []
            }


class CustomClassifier:
    """
    Custom classifier with transfer learning support.
    Allows fine-tuning pre-trained models for specific tasks.
    """

    def __init__(
        self,
        base_model: str = "resnet50",
        num_classes: int = 10,
        model_path: Optional[str] = None
    ):
        """
        Initialize custom classifier.

        Args:
            base_model: Base model architecture
            num_classes: Number of output classes
            model_path: Path to saved model
        """
        self.base_model = base_model
        self.num_classes = num_classes
        self.model_path = model_path
        self.model = None
        self.class_names: Optional[List[str]] = None
        self.logger = logging.getLogger(f"{__name__}.CustomClassifier")

    def build_model(self, trainable_layers: int = 0) -> bool:
        """
        Build custom model with transfer learning.

        Args:
            trainable_layers: Number of base model layers to make trainable

        Returns:
            True if successful
        """
        try:
            import tensorflow as tf
            from tensorflow import keras

            # Load base model
            if self.base_model.lower() == 'resnet50':
                base = keras.applications.ResNet50(
                    weights='imagenet',
                    include_top=False,
                    input_shape=(224, 224, 3)
                )
            elif self.base_model.lower() == 'vgg16':
                base = keras.applications.VGG16(
                    weights='imagenet',
                    include_top=False,
                    input_shape=(224, 224, 3)
                )
            elif self.base_model.lower() == 'efficientnet':
                base = keras.applications.EfficientNetB0(
                    weights='imagenet',
                    include_top=False,
                    input_shape=(224, 224, 3)
                )
            else:
                raise ValueError(f"Unsupported base model: {self.base_model}")

            # Freeze base layers
            for layer in base.layers[:-trainable_layers]:
                layer.trainable = False

            # Add custom head
            x = keras.layers.GlobalAveragePooling2D()(base.output)
            x = keras.layers.Dense(512, activation='relu')(x)
            x = keras.layers.Dropout(0.5)(x)
            x = keras.layers.Dense(256, activation='relu')(x)
            x = keras.layers.Dropout(0.3)(x)
            outputs = keras.layers.Dense(self.num_classes, activation='softmax')(x)

            self.model = keras.Model(inputs=base.input, outputs=outputs)

            # Compile
            self.model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=0.001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            self.logger.info(f"Built custom model with {self.base_model} base")
            return True

        except Exception as e:
            self.logger.error(f"Error building model: {e}")
            return False

    def load_model(self) -> bool:
        """Load pre-trained custom model."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            if not self.model_path or not Path(self.model_path).exists():
                raise ValueError("Model path not provided or doesn't exist")

            self.model = keras.models.load_model(self.model_path)
            self.logger.info(f"Loaded custom model from {self.model_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def save_model(self, path: str) -> bool:
        """Save model to disk."""
        try:
            if self.model is None:
                raise ValueError("No model to save")

            self.model.save(path)
            self.logger.info(f"Saved model to {path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            return False

    def train(
        self,
        train_data,
        val_data,
        epochs: int = 10,
        batch_size: int = 32,
        callbacks: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Train the custom classifier.

        Args:
            train_data: Training dataset
            val_data: Validation dataset
            epochs: Number of training epochs
            batch_size: Batch size
            callbacks: Training callbacks

        Returns:
            Training history
        """
        try:
            if self.model is None:
                self.build_model()

            history = self.model.fit(
                train_data,
                validation_data=val_data,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks or []
            )

            return {
                'success': True,
                'history': history.history,
                'final_train_accuracy': float(history.history['accuracy'][-1]),
                'final_val_accuracy': float(history.history['val_accuracy'][-1])
            }

        except Exception as e:
            self.logger.error(f"Error during training: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def predict(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Predict class for image.

        Args:
            image: Input image
            top_k: Number of top predictions

        Returns:
            Predictions dict
        """
        try:
            if self.model is None:
                if self.model_path:
                    self.load_model()
                else:
                    raise ValueError("Model not loaded or trained")

            # Load and preprocess image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            import tensorflow as tf
            from tensorflow import keras

            image = image.resize((224, 224))
            img_array = keras.preprocessing.image.img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0

            # Predict
            start_time = time.time()
            predictions = self.model.predict(img_array)[0]
            processing_time = (time.time() - start_time) * 1000

            # Get top K
            top_indices = np.argsort(predictions)[-top_k:][::-1]

            results = []
            for idx in top_indices:
                label = self.class_names[idx] if self.class_names else f"class_{idx}"
                results.append({
                    'label': label,
                    'confidence': float(predictions[idx]),
                    'class_id': int(idx)
                })

            return {
                'success': True,
                'predictions': results,
                'processing_time_ms': processing_time,
                'model_name': self.base_model
            }

        except Exception as e:
            self.logger.error(f"Error during prediction: {e}")
            return {
                'success': False,
                'error': str(e),
                'predictions': []
            }

    def set_class_names(self, class_names: List[str]) -> None:
        """Set human-readable class names."""
        if len(class_names) != self.num_classes:
            raise ValueError(f"Expected {self.num_classes} class names, got {len(class_names)}")
        self.class_names = class_names
        self.logger.info(f"Set {len(class_names)} class names")


class ZeroShotClassifier:
    """
    Zero-shot classifier using GPT-4 Vision.
    Can classify images without training data.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize zero-shot classifier.

        Args:
            api_key: OpenAI API key
        """
        from .models import GPT4VisionWrapper
        self.model = GPT4VisionWrapper(api_key=api_key)
        self.logger = logging.getLogger(f"{__name__}.ZeroShotClassifier")

    def classify(
        self,
        image: Union[str, np.ndarray, Image.Image],
        candidate_labels: List[str],
        hypothesis_template: str = "This is a photo of {}"
    ) -> Dict[str, Any]:
        """
        Classify image using zero-shot learning.

        Args:
            image: Input image
            candidate_labels: Possible labels
            hypothesis_template: Template for label hypothesis

        Returns:
            Classification results
        """
        try:
            if not self.model.is_loaded:
                self.model.load_model()

            # Load image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Create prompt
            labels_str = ", ".join(candidate_labels)
            prompt = f"""Analyze this image and determine which of these categories best describes it: {labels_str}

            Respond with a JSON object containing:
            - predicted_label: the most appropriate category
            - confidence: your confidence level (0-1)
            - reasoning: brief explanation
            """

            # Get prediction
            result = self.model.predict(image, prompt=prompt)

            return {
                'success': True,
                'prediction': result.get('description', ''),
                'candidate_labels': candidate_labels,
                'processing_time_ms': result.get('processing_time_ms', 0)
            }

        except Exception as e:
            self.logger.error(f"Error during zero-shot classification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
