"""
Tests for Model Wrappers

Tests:
- TensorFlowModelWrapper
- PyTorchModelWrapper
- YOLOModelWrapper
- GPT4VisionWrapper
- ModelFactory
- ModelRegistry
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.image_recognition.models import (
    BaseModelWrapper,
    TensorFlowModelWrapper,
    PyTorchModelWrapper,
    YOLOModelWrapper,
    GPT4VisionWrapper,
    ModelFactory,
    ModelRegistry
)


# ============================================================================
# Test BaseModelWrapper
# ============================================================================

class TestBaseModelWrapper:
    """Test BaseModelWrapper abstract class."""

    def test_initialization(self):
        """Test base model initialization."""
        class TestWrapper(BaseModelWrapper):
            def load_model(self): pass
            def predict(self, image, **kwargs): pass
            def preprocess_image(self, image): pass

        wrapper = TestWrapper("test_model", "/path/to/model", {"key": "value"})

        assert wrapper.model_name == "test_model"
        assert wrapper.model_path == "/path/to/model"
        assert wrapper.config == {"key": "value"}
        assert wrapper.model is None
        assert wrapper.is_loaded is False

    def test_unload_model(self):
        """Test unloading model."""
        class TestWrapper(BaseModelWrapper):
            def load_model(self): pass
            def predict(self, image, **kwargs): pass
            def preprocess_image(self, image): pass

        wrapper = TestWrapper("test_model")
        wrapper.model = MagicMock()
        wrapper.is_loaded = True

        result = wrapper.unload_model()

        assert result is True
        assert wrapper.model is None
        assert wrapper.is_loaded is False

    def test_get_info(self):
        """Test getting model information."""
        class TestWrapper(BaseModelWrapper):
            def load_model(self): pass
            def predict(self, image, **kwargs): pass
            def preprocess_image(self, image): pass

        wrapper = TestWrapper("test_model", "/path/to/model", {"key": "value"})
        info = wrapper.get_info()

        assert info['model_name'] == "test_model"
        assert info['model_path'] == "/path/to/model"
        assert info['is_loaded'] is False
        assert info['input_shape'] == (224, 224)
        assert info['config'] == {"key": "value"}


# ============================================================================
# Test TensorFlowModelWrapper
# ============================================================================

class TestTensorFlowModelWrapper:
    """Test TensorFlow model wrapper."""

    @patch('modules.image_recognition.models.keras')
    def test_load_model_vgg16(self, mock_keras):
        """Test loading VGG16 model."""
        mock_model = MagicMock()
        mock_keras.applications.VGG16.return_value = mock_model

        wrapper = TensorFlowModelWrapper("vgg16")
        result = wrapper.load_model()

        assert result is True
        assert wrapper.is_loaded is True
        mock_keras.applications.VGG16.assert_called_once()

    @patch('modules.image_recognition.models.keras')
    def test_load_model_resnet50(self, mock_keras):
        """Test loading ResNet50 model."""
        mock_model = MagicMock()
        mock_keras.applications.ResNet50.return_value = mock_model

        wrapper = TensorFlowModelWrapper("resnet50")
        result = wrapper.load_model()

        assert result is True
        assert wrapper.is_loaded is True

    @patch('modules.image_recognition.models.keras')
    def test_load_model_inceptionv3(self, mock_keras):
        """Test loading InceptionV3 model."""
        mock_model = MagicMock()
        mock_keras.applications.InceptionV3.return_value = mock_model

        wrapper = TensorFlowModelWrapper("inceptionv3")
        result = wrapper.load_model()

        assert result is True
        assert wrapper.input_shape == (299, 299)

    @patch('modules.image_recognition.models.keras')
    def test_load_custom_model(self, mock_keras):
        """Test loading custom model from path."""
        mock_model = MagicMock()
        mock_keras.models.load_model.return_value = mock_model

        with patch('os.path.exists', return_value=True):
            wrapper = TensorFlowModelWrapper("custom", "/path/to/model.h5")
            result = wrapper.load_model()

            assert result is True
            mock_keras.models.load_model.assert_called_once_with("/path/to/model.h5")

    def test_load_model_unsupported(self):
        """Test loading unsupported model raises error."""
        with patch('modules.image_recognition.models.keras'):
            wrapper = TensorFlowModelWrapper("unsupported_model")
            result = wrapper.load_model()

            assert result is False

    @patch('modules.image_recognition.models.keras')
    def test_preprocess_image_pil(self, mock_keras, sample_image):
        """Test preprocessing PIL image."""
        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        wrapper = TensorFlowModelWrapper("resnet50")
        result = wrapper.preprocess_image(sample_image)

        assert result is not None
        assert result.shape[0] == 1  # Batch dimension

    @patch('modules.image_recognition.models.keras')
    def test_preprocess_image_numpy(self, mock_keras, sample_image_array):
        """Test preprocessing numpy array."""
        mock_keras.preprocessing.image.img_to_array.return_value = sample_image_array

        wrapper = TensorFlowModelWrapper("resnet50")
        result = wrapper.preprocess_image(sample_image_array)

        assert result is not None

    @patch('modules.image_recognition.models.keras')
    @patch('modules.image_recognition.models.keras.applications.resnet50.decode_predictions')
    def test_predict(self, mock_decode, mock_keras, sample_image):
        """Test prediction on image."""
        # Setup mocks
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.1, 0.7, 0.2]])
        mock_keras.applications.ResNet50.return_value = mock_model

        mock_decode.return_value = [[
            ('n01', 'cat', 0.7),
            ('n02', 'dog', 0.2),
            ('n03', 'bird', 0.1)
        ]]

        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        wrapper = TensorFlowModelWrapper("resnet50")
        wrapper.load_model()
        result = wrapper.predict(sample_image, top_k=3)

        assert result['predictions'] is not None
        assert len(result['predictions']) == 3
        assert result['predictions'][0]['label'] == 'cat'
        assert result['predictions'][0]['confidence'] == 0.7
        assert 'processing_time_ms' in result

    @patch('modules.image_recognition.models.keras')
    def test_predict_auto_loads_model(self, mock_keras, sample_image):
        """Test prediction automatically loads model if not loaded."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.1, 0.7, 0.2]])
        mock_keras.applications.ResNet50.return_value = mock_model
        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        wrapper = TensorFlowModelWrapper("resnet50")
        assert wrapper.is_loaded is False

        # This should auto-load
        with patch('modules.image_recognition.models.keras.applications.resnet50.decode_predictions'):
            wrapper.predict(sample_image)

        assert wrapper.is_loaded is True


# ============================================================================
# Test PyTorchModelWrapper
# ============================================================================

class TestPyTorchModelWrapper:
    """Test PyTorch model wrapper."""

    @patch('modules.image_recognition.models.torch')
    @patch('modules.image_recognition.models.models')
    def test_load_model_resnet50(self, mock_models, mock_torch):
        """Test loading PyTorch ResNet50."""
        mock_model = MagicMock()
        mock_models.resnet50.return_value = mock_model
        mock_torch.device.return_value = "cpu"

        wrapper = PyTorchModelWrapper("resnet50")
        result = wrapper.load_model()

        assert result is True
        assert wrapper.is_loaded is True
        mock_model.eval.assert_called_once()

    @patch('modules.image_recognition.models.torch')
    @patch('modules.image_recognition.models.models')
    def test_load_model_gpu(self, mock_models, mock_torch):
        """Test loading model on GPU."""
        mock_model = MagicMock()
        mock_models.resnet50.return_value = mock_model
        mock_torch.cuda.is_available.return_value = True
        mock_torch.device.return_value = "cuda"

        wrapper = PyTorchModelWrapper("resnet50")
        wrapper.load_model()

        assert wrapper.device == "cuda"

    @patch('modules.image_recognition.models.torch')
    @patch('modules.image_recognition.models.transforms')
    def test_preprocess_image(self, mock_transforms, mock_torch, sample_image):
        """Test image preprocessing."""
        mock_compose = MagicMock()
        mock_compose.return_value = torch.zeros(3, 224, 224)
        mock_transforms.Compose.return_value = mock_compose

        wrapper = PyTorchModelWrapper("resnet50")
        wrapper.device = "cpu"
        result = wrapper.preprocess_image(sample_image)

        assert result is not None

    @patch('modules.image_recognition.models.torch')
    @patch('modules.image_recognition.models.models')
    @patch('modules.image_recognition.models.transforms')
    def test_predict(self, mock_transforms, mock_models, mock_torch, sample_image):
        """Test PyTorch prediction."""
        # Setup mocks
        mock_model = MagicMock()
        mock_output = MagicMock()
        mock_model.return_value = (mock_output,)
        mock_models.resnet50.return_value = mock_model

        mock_torch.device.return_value = "cpu"
        mock_torch.no_grad.return_value.__enter__ = lambda *args: None
        mock_torch.no_grad.return_value.__exit__ = lambda *args: None

        # Mock softmax and topk
        mock_probs = MagicMock()
        mock_probs.topk.return_value = (
            MagicMock(item=lambda: 0.95),
            MagicMock(item=lambda: 0)
        )
        mock_torch.nn.functional.softmax.return_value = mock_probs
        mock_torch.topk.return_value = (
            [MagicMock(item=lambda: 0.95)],
            [MagicMock(item=lambda: 0)]
        )

        wrapper = PyTorchModelWrapper("resnet50")
        wrapper.load_model()

        with patch.object(wrapper, 'preprocess_image', return_value=MagicMock()):
            result = wrapper.predict(sample_image, top_k=5)

        assert 'predictions' in result
        assert 'processing_time_ms' in result


# ============================================================================
# Test YOLOModelWrapper
# ============================================================================

class TestYOLOModelWrapper:
    """Test YOLO model wrapper."""

    @patch('modules.image_recognition.models.torch')
    def test_load_model(self, mock_torch):
        """Test loading YOLO model."""
        mock_hub = MagicMock()
        mock_model = MagicMock()
        mock_hub.load.return_value = mock_model
        mock_torch.hub = mock_hub

        wrapper = YOLOModelWrapper("yolov5")
        result = wrapper.load_model()

        assert result is True
        assert wrapper.is_loaded is True

    @patch('modules.image_recognition.models.torch')
    def test_load_custom_model(self, mock_torch):
        """Test loading custom YOLO model."""
        mock_hub = MagicMock()
        mock_model = MagicMock()
        mock_hub.load.return_value = mock_model
        mock_torch.hub = mock_hub

        with patch('os.path.exists', return_value=True):
            wrapper = YOLOModelWrapper("yolov5", "/path/to/custom.pt")
            result = wrapper.load_model()

            assert result is True

    def test_preprocess_image_pil(self, sample_image):
        """Test preprocessing PIL image."""
        wrapper = YOLOModelWrapper("yolov5")
        result = wrapper.preprocess_image(sample_image)

        assert isinstance(result, Image.Image)

    def test_preprocess_image_numpy(self, sample_image_array):
        """Test preprocessing numpy array."""
        wrapper = YOLOModelWrapper("yolov5")
        result = wrapper.preprocess_image(sample_image_array)

        assert isinstance(result, Image.Image)

    @patch('modules.image_recognition.models.torch')
    def test_predict(self, mock_torch, sample_image):
        """Test YOLO object detection."""
        # Setup mock model
        mock_hub = MagicMock()
        mock_model = MagicMock()
        mock_model.names = {0: "person", 1: "car", 2: "dog"}

        # Mock detection results
        mock_result = MagicMock()
        mock_result.xyxy = [np.array([[10, 20, 100, 200, 0.95, 0]])]
        mock_result.names = {0: "person", 1: "car", 2: "dog"}
        mock_model.return_value = mock_result

        mock_hub.load.return_value = mock_model
        mock_torch.hub = mock_hub

        wrapper = YOLOModelWrapper("yolov5")
        wrapper.load_model()
        result = wrapper.predict(sample_image)

        assert 'detections' in result
        assert 'num_detections' in result
        assert result['num_detections'] == 1
        assert result['detections'][0]['label'] == 'person'
        assert result['detections'][0]['confidence'] == 0.95


# ============================================================================
# Test GPT4VisionWrapper
# ============================================================================

class TestGPT4VisionWrapper:
    """Test GPT-4 Vision wrapper."""

    @patch('modules.image_recognition.models.OpenAI')
    def test_load_model(self, mock_openai):
        """Test initializing GPT-4 Vision client."""
        wrapper = GPT4VisionWrapper(api_key="test_key")
        result = wrapper.load_model()

        assert result is True
        assert wrapper.is_loaded is True
        mock_openai.assert_called_once_with(api_key="test_key")

    def test_load_model_no_api_key(self):
        """Test error when no API key provided."""
        with patch.dict('os.environ', {}, clear=True):
            wrapper = GPT4VisionWrapper()
            result = wrapper.load_model()

            assert result is False

    def test_preprocess_image(self, sample_image):
        """Test image preprocessing to base64."""
        wrapper = GPT4VisionWrapper(api_key="test_key")
        result = wrapper.preprocess_image(sample_image)

        assert result.startswith("data:image/jpeg;base64,")

    @patch('modules.image_recognition.models.OpenAI')
    def test_predict(self, mock_openai, sample_image):
        """Test GPT-4 Vision prediction."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "A red image"
        mock_response.usage.total_tokens = 150
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        wrapper = GPT4VisionWrapper(api_key="test_key")
        wrapper.load_model()
        result = wrapper.predict(sample_image, prompt="Describe this image")

        assert result['description'] == "A red image"
        assert result['tokens_used'] == 150
        assert 'processing_time_ms' in result

    @pytest.mark.parametrize("max_tokens", [100, 300, 500])
    @patch('modules.image_recognition.models.OpenAI')
    def test_predict_with_different_max_tokens(
        self, mock_openai, sample_image, max_tokens
    ):
        """Test prediction with different max_tokens."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.usage.total_tokens = max_tokens
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        wrapper = GPT4VisionWrapper(api_key="test_key")
        wrapper.load_model()
        result = wrapper.predict(sample_image, max_tokens=max_tokens)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs['max_tokens'] == max_tokens


# ============================================================================
# Test ModelFactory
# ============================================================================

class TestModelFactory:
    """Test ModelFactory."""

    @pytest.mark.parametrize("model_type,expected_class", [
        ('vgg16', TensorFlowModelWrapper),
        ('resnet50', TensorFlowModelWrapper),
        ('inceptionv3', TensorFlowModelWrapper),
        ('efficientnet', TensorFlowModelWrapper),
    ])
    def test_create_tensorflow_models(self, model_type, expected_class):
        """Test creating TensorFlow models."""
        model = ModelFactory.create_model(model_type)

        assert isinstance(model, expected_class)
        assert model.model_name == model_type

    def test_create_yolo_model(self):
        """Test creating YOLO model."""
        model = ModelFactory.create_model('yolo')

        assert isinstance(model, YOLOModelWrapper)

    def test_create_gpt4_vision_model(self):
        """Test creating GPT-4 Vision model."""
        model = ModelFactory.create_model('gpt4_vision', api_key='test_key')

        assert isinstance(model, GPT4VisionWrapper)

    def test_create_model_with_custom_path(self):
        """Test creating model with custom path."""
        model = ModelFactory.create_model(
            'resnet50',
            model_path='/path/to/model.h5'
        )

        assert model.model_path == '/path/to/model.h5'

    def test_create_model_with_config(self):
        """Test creating model with config."""
        config = {'batch_size': 32, 'input_shape': (256, 256)}
        model = ModelFactory.create_model('resnet50', config=config)

        assert model.config == config

    def test_create_unsupported_model(self):
        """Test creating unsupported model raises error."""
        with pytest.raises(ValueError, match="Unsupported model type"):
            ModelFactory.create_model('unsupported_model')


# ============================================================================
# Test ModelRegistry
# ============================================================================

class TestModelRegistry:
    """Test ModelRegistry."""

    def test_register_model(self):
        """Test registering a model."""
        registry = ModelRegistry()
        mock_model = MagicMock(spec=BaseModelWrapper)

        registry.register_model('test_model', mock_model)

        assert 'test_model' in registry.models
        assert registry.get_model('test_model') == mock_model

    def test_get_model(self):
        """Test getting a registered model."""
        registry = ModelRegistry()
        mock_model = MagicMock(spec=BaseModelWrapper)
        registry.register_model('test_model', mock_model)

        model = registry.get_model('test_model')

        assert model == mock_model

    def test_get_nonexistent_model(self):
        """Test getting non-existent model returns None."""
        registry = ModelRegistry()

        model = registry.get_model('nonexistent')

        assert model is None

    def test_unregister_model(self):
        """Test unregistering a model."""
        registry = ModelRegistry()
        mock_model = MagicMock(spec=BaseModelWrapper)
        mock_model.unload_model.return_value = True
        registry.register_model('test_model', mock_model)

        result = registry.unregister_model('test_model')

        assert result is True
        assert 'test_model' not in registry.models
        mock_model.unload_model.assert_called_once()

    def test_unregister_nonexistent_model(self):
        """Test unregistering non-existent model returns False."""
        registry = ModelRegistry()

        result = registry.unregister_model('nonexistent')

        assert result is False

    def test_list_models(self):
        """Test listing all registered models."""
        registry = ModelRegistry()
        mock_model1 = MagicMock(spec=BaseModelWrapper)
        mock_model1.get_info.return_value = {'model_name': 'model1'}
        mock_model2 = MagicMock(spec=BaseModelWrapper)
        mock_model2.get_info.return_value = {'model_name': 'model2'}

        registry.register_model('id1', mock_model1)
        registry.register_model('id2', mock_model2)

        models = registry.list_models()

        assert len(models) == 2
        assert models[0]['model_id'] == 'id1'
        assert models[1]['model_id'] == 'id2'

    def test_unload_all(self):
        """Test unloading all models."""
        registry = ModelRegistry()
        mock_model1 = MagicMock(spec=BaseModelWrapper)
        mock_model2 = MagicMock(spec=BaseModelWrapper)

        registry.register_model('id1', mock_model1)
        registry.register_model('id2', mock_model2)

        registry.unload_all()

        assert len(registry.models) == 0
        mock_model1.unload_model.assert_called_once()
        mock_model2.unload_model.assert_called_once()

    def test_multiple_registrations(self):
        """Test registering multiple models."""
        registry = ModelRegistry()

        for i in range(10):
            mock_model = MagicMock(spec=BaseModelWrapper)
            registry.register_model(f'model_{i}', mock_model)

        assert len(registry.models) == 10
        assert all(f'model_{i}' in registry.models for i in range(10))


# Make torch available for tests
class torch:
    """Mock torch module."""
    @staticmethod
    def zeros(*args, **kwargs):
        return np.zeros(args)
