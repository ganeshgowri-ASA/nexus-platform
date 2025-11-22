"""
Pre-trained Models Wrapper for Image Recognition

Supports multiple state-of-the-art models:
- VGG16
- ResNet50
- InceptionV3
- EfficientNet
- YOLO (You Only Look Once)
- GPT-4 Vision API

This module provides a unified interface for loading and using different models.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)


class BaseModelWrapper(ABC):
    """
    Abstract base class for all model wrappers.
    Provides a unified interface for different model types.
    """

    def __init__(
        self,
        model_name: str,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the model wrapper.

        Args:
            model_name: Name of the model
            model_path: Path to model weights (optional)
            config: Model configuration dict
        """
        self.model_name = model_name
        self.model_path = model_path
        self.config = config or {}
        self.model = None
        self.is_loaded = False
        self.input_shape = self.config.get('input_shape', (224, 224))
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def load_model(self) -> bool:
        """Load the model into memory."""
        pass

    @abstractmethod
    def predict(
        self,
        image: Union[np.ndarray, Image.Image],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run prediction on an image.

        Args:
            image: Input image as numpy array or PIL Image
            **kwargs: Additional prediction parameters

        Returns:
            Dict containing predictions and metadata
        """
        pass

    @abstractmethod
    def preprocess_image(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> np.ndarray:
        """
        Preprocess image for model input.

        Args:
            image: Input image

        Returns:
            Preprocessed image as numpy array
        """
        pass

    def unload_model(self) -> bool:
        """Unload model from memory."""
        try:
            self.model = None
            self.is_loaded = False
            self.logger.info(f"Model {self.model_name} unloaded")
            return True
        except Exception as e:
            self.logger.error(f"Error unloading model: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_name': self.model_name,
            'model_path': self.model_path,
            'is_loaded': self.is_loaded,
            'input_shape': self.input_shape,
            'config': self.config
        }


class TensorFlowModelWrapper(BaseModelWrapper):
    """Wrapper for TensorFlow/Keras models."""

    def __init__(self, model_name: str, model_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, model_path, config)
        self.framework = 'tensorflow'

    def load_model(self) -> bool:
        """Load TensorFlow model."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            if self.model_path and os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                self.logger.info(f"Loaded custom model from {self.model_path}")
            else:
                # Load pre-trained model
                if self.model_name.lower() == 'vgg16':
                    self.model = keras.applications.VGG16(
                        weights='imagenet',
                        include_top=True
                    )
                elif self.model_name.lower() == 'resnet50':
                    self.model = keras.applications.ResNet50(
                        weights='imagenet',
                        include_top=True
                    )
                elif self.model_name.lower() == 'inceptionv3':
                    self.model = keras.applications.InceptionV3(
                        weights='imagenet',
                        include_top=True
                    )
                    self.input_shape = (299, 299)
                elif self.model_name.lower() == 'efficientnet':
                    self.model = keras.applications.EfficientNetB0(
                        weights='imagenet',
                        include_top=True
                    )
                else:
                    raise ValueError(f"Unsupported model: {self.model_name}")

                self.logger.info(f"Loaded pre-trained {self.model_name} model")

            self.is_loaded = True
            return True

        except ImportError:
            self.logger.error("TensorFlow not installed. Install with: pip install tensorflow")
            return False
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def preprocess_image(self, image: Union[np.ndarray, Image.Image]) -> np.ndarray:
        """Preprocess image for TensorFlow models."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            # Convert to PIL if numpy
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Resize to model input shape
            image = image.resize(self.input_shape)

            # Convert to array
            img_array = keras.preprocessing.image.img_to_array(image)

            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)

            # Model-specific preprocessing
            if self.model_name.lower() == 'vgg16':
                from tensorflow.keras.applications.vgg16 import preprocess_input
            elif self.model_name.lower() == 'resnet50':
                from tensorflow.keras.applications.resnet50 import preprocess_input
            elif self.model_name.lower() == 'inceptionv3':
                from tensorflow.keras.applications.inception_v3 import preprocess_input
            elif self.model_name.lower() == 'efficientnet':
                from tensorflow.keras.applications.efficientnet import preprocess_input
            else:
                # Default preprocessing
                img_array = img_array / 255.0
                return img_array

            img_array = preprocess_input(img_array)
            return img_array

        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            raise

    def predict(self, image: Union[np.ndarray, Image.Image], top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """Run prediction on image."""
        if not self.is_loaded:
            self.load_model()

        try:
            import tensorflow as tf
            from tensorflow import keras
            import time

            start_time = time.time()

            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Run prediction
            predictions = self.model.predict(processed_image)

            # Decode predictions
            if self.model_name.lower() == 'vgg16':
                from tensorflow.keras.applications.vgg16 import decode_predictions
            elif self.model_name.lower() == 'resnet50':
                from tensorflow.keras.applications.resnet50 import decode_predictions
            elif self.model_name.lower() == 'inceptionv3':
                from tensorflow.keras.applications.inception_v3 import decode_predictions
            elif self.model_name.lower() == 'efficientnet':
                from tensorflow.keras.applications.efficientnet import decode_predictions
            else:
                # Custom model - return raw predictions
                top_indices = np.argsort(predictions[0])[-top_k:][::-1]
                decoded = [
                    {
                        'class_id': str(idx),
                        'label': f'class_{idx}',
                        'confidence': float(predictions[0][idx])
                    }
                    for idx in top_indices
                ]
                processing_time = (time.time() - start_time) * 1000
                return {
                    'predictions': decoded,
                    'processing_time_ms': processing_time,
                    'model_name': self.model_name
                }

            decoded_predictions = decode_predictions(predictions, top=top_k)[0]

            # Format results
            results = []
            for pred in decoded_predictions:
                results.append({
                    'class_id': pred[0],
                    'label': pred[1],
                    'confidence': float(pred[2])
                })

            processing_time = (time.time() - start_time) * 1000

            return {
                'predictions': results,
                'processing_time_ms': processing_time,
                'model_name': self.model_name,
                'raw_predictions': predictions.tolist()
            }

        except Exception as e:
            self.logger.error(f"Error during prediction: {e}")
            raise


class PyTorchModelWrapper(BaseModelWrapper):
    """Wrapper for PyTorch models."""

    def __init__(self, model_name: str, model_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, model_path, config)
        self.framework = 'pytorch'
        self.device = None

    def load_model(self) -> bool:
        """Load PyTorch model."""
        try:
            import torch
            import torchvision.models as models
            from torchvision import transforms

            # Set device
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.logger.info(f"Using device: {self.device}")

            if self.model_path and os.path.exists(self.model_path):
                self.model = torch.load(self.model_path, map_location=self.device)
                self.logger.info(f"Loaded custom model from {self.model_path}")
            else:
                # Load pre-trained model
                if self.model_name.lower() == 'resnet50':
                    self.model = models.resnet50(pretrained=True)
                elif self.model_name.lower() == 'vgg16':
                    self.model = models.vgg16(pretrained=True)
                elif self.model_name.lower() == 'efficientnet':
                    self.model = models.efficientnet_b0(pretrained=True)
                else:
                    raise ValueError(f"Unsupported PyTorch model: {self.model_name}")

                self.logger.info(f"Loaded pre-trained {self.model_name} model")

            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            return True

        except ImportError:
            self.logger.error("PyTorch not installed. Install with: pip install torch torchvision")
            return False
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def preprocess_image(self, image: Union[np.ndarray, Image.Image]) -> "torch.Tensor":
        """Preprocess image for PyTorch models."""
        try:
            import torch
            from torchvision import transforms

            # Convert to PIL if numpy
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Define transforms
            preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

            # Apply transforms
            img_tensor = preprocess(image)
            img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension

            return img_tensor.to(self.device)

        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            raise

    def predict(self, image: Union[np.ndarray, Image.Image], top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """Run prediction on image."""
        if not self.is_loaded:
            self.load_model()

        try:
            import torch
            import time

            start_time = time.time()

            # Preprocess image
            input_tensor = self.preprocess_image(image)

            # Run prediction
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

            # Get top K predictions
            top_probs, top_indices = torch.topk(probabilities, top_k)

            # Load ImageNet class labels
            class_labels = self._load_imagenet_labels()

            # Format results
            results = []
            for i in range(top_k):
                idx = top_indices[i].item()
                prob = top_probs[i].item()
                label = class_labels.get(idx, f'class_{idx}')

                results.append({
                    'class_id': idx,
                    'label': label,
                    'confidence': prob
                })

            processing_time = (time.time() - start_time) * 1000

            return {
                'predictions': results,
                'processing_time_ms': processing_time,
                'model_name': self.model_name
            }

        except Exception as e:
            self.logger.error(f"Error during prediction: {e}")
            raise

    def _load_imagenet_labels(self) -> Dict[int, str]:
        """Load ImageNet class labels."""
        # Simplified - in production, load from file
        return {i: f"class_{i}" for i in range(1000)}


class YOLOModelWrapper(BaseModelWrapper):
    """Wrapper for YOLO object detection models."""

    def __init__(self, model_name: str = "yolov5", model_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, model_path, config)
        self.framework = 'yolo'

    def load_model(self) -> bool:
        """Load YOLO model."""
        try:
            import torch

            # Load YOLOv5 from torch hub
            if self.model_path and os.path.exists(self.model_path):
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
                self.logger.info(f"Loaded custom YOLO model from {self.model_path}")
            else:
                # Load pre-trained YOLOv5
                model_size = self.config.get('model_size', 's')  # n, s, m, l, x
                self.model = torch.hub.load('ultralytics/yolov5', f'yolov5{model_size}')
                self.logger.info(f"Loaded pre-trained YOLOv5{model_size} model")

            self.is_loaded = True
            return True

        except ImportError:
            self.logger.error("PyTorch not installed. Install with: pip install torch")
            return False
        except Exception as e:
            self.logger.error(f"Error loading YOLO model: {e}")
            return False

    def preprocess_image(self, image: Union[np.ndarray, Image.Image]) -> Union[np.ndarray, Image.Image]:
        """YOLO handles preprocessing internally, just ensure correct format."""
        if isinstance(image, np.ndarray):
            return Image.fromarray(image)
        return image

    def predict(
        self,
        image: Union[np.ndarray, Image.Image],
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        **kwargs
    ) -> Dict[str, Any]:
        """Run object detection on image."""
        if not self.is_loaded:
            self.load_model()

        try:
            import time

            start_time = time.time()

            # Preprocess
            processed_image = self.preprocess_image(image)

            # Run detection
            self.model.conf = confidence_threshold
            self.model.iou = iou_threshold
            results = self.model(processed_image)

            # Parse results
            detections = []
            for *box, conf, cls in results.xyxy[0].tolist():
                x1, y1, x2, y2 = box
                detections.append({
                    'label': results.names[int(cls)],
                    'confidence': conf,
                    'bbox': {
                        'x': x1,
                        'y': y1,
                        'width': x2 - x1,
                        'height': y2 - y1
                    },
                    'class_id': int(cls)
                })

            processing_time = (time.time() - start_time) * 1000

            return {
                'detections': detections,
                'num_detections': len(detections),
                'processing_time_ms': processing_time,
                'model_name': self.model_name
            }

        except Exception as e:
            self.logger.error(f"Error during detection: {e}")
            raise


class GPT4VisionWrapper(BaseModelWrapper):
    """Wrapper for GPT-4 Vision API."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__("gpt4_vision", None, config)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None

    def load_model(self) -> bool:
        """Initialize GPT-4 Vision client."""
        try:
            from openai import OpenAI

            if not self.api_key:
                raise ValueError("OpenAI API key not provided")

            self.client = OpenAI(api_key=self.api_key)
            self.is_loaded = True
            self.logger.info("Initialized GPT-4 Vision client")
            return True

        except ImportError:
            self.logger.error("OpenAI package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            self.logger.error(f"Error initializing GPT-4 Vision: {e}")
            return False

    def preprocess_image(self, image: Union[np.ndarray, Image.Image]) -> str:
        """Convert image to base64 string for API."""
        try:
            # Convert to PIL if numpy
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/jpeg;base64,{img_str}"

        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            raise

    def predict(
        self,
        image: Union[np.ndarray, Image.Image],
        prompt: str = "Describe this image in detail. Identify objects, scenes, and notable features.",
        max_tokens: int = 300,
        **kwargs
    ) -> Dict[str, Any]:
        """Run GPT-4 Vision analysis on image."""
        if not self.is_loaded:
            self.load_model()

        try:
            import time

            start_time = time.time()

            # Preprocess image
            image_data = self.preprocess_image(image)

            # Call API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data}
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens
            )

            processing_time = (time.time() - start_time) * 1000

            return {
                'description': response.choices[0].message.content,
                'processing_time_ms': processing_time,
                'model_name': 'gpt-4-vision',
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
            }

        except Exception as e:
            self.logger.error(f"Error during GPT-4 Vision prediction: {e}")
            raise


class ModelFactory:
    """Factory for creating model wrappers."""

    @staticmethod
    def create_model(
        model_type: str,
        model_name: Optional[str] = None,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None
    ) -> BaseModelWrapper:
        """
        Create appropriate model wrapper.

        Args:
            model_type: Type of model (vgg16, resnet50, yolo, gpt4_vision, etc.)
            model_name: Custom name for the model
            model_path: Path to custom model weights
            config: Model configuration
            api_key: API key for cloud models

        Returns:
            Initialized model wrapper
        """
        model_type = model_type.lower()

        if model_type in ['vgg16', 'resnet50', 'inceptionv3', 'efficientnet']:
            return TensorFlowModelWrapper(
                model_name=model_name or model_type,
                model_path=model_path,
                config=config
            )
        elif model_type.startswith('yolo'):
            return YOLOModelWrapper(
                model_name=model_name or model_type,
                model_path=model_path,
                config=config
            )
        elif model_type == 'gpt4_vision':
            return GPT4VisionWrapper(
                api_key=api_key,
                config=config
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


class ModelRegistry:
    """Registry for managing multiple loaded models."""

    def __init__(self):
        """Initialize model registry."""
        self.models: Dict[str, BaseModelWrapper] = {}
        self.logger = logging.getLogger(f"{__name__}.ModelRegistry")

    def register_model(self, model_id: str, model: BaseModelWrapper) -> None:
        """Register a model."""
        self.models[model_id] = model
        self.logger.info(f"Registered model: {model_id}")

    def get_model(self, model_id: str) -> Optional[BaseModelWrapper]:
        """Get a registered model."""
        return self.models.get(model_id)

    def unregister_model(self, model_id: str) -> bool:
        """Unregister and unload a model."""
        if model_id in self.models:
            self.models[model_id].unload_model()
            del self.models[model_id]
            self.logger.info(f"Unregistered model: {model_id}")
            return True
        return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        return [
            {
                'model_id': model_id,
                **model.get_info()
            }
            for model_id, model in self.models.items()
        ]

    def unload_all(self) -> None:
        """Unload all models."""
        for model_id in list(self.models.keys()):
            self.unregister_model(model_id)
        self.logger.info("Unloaded all models")


# Global model registry instance
model_registry = ModelRegistry()
