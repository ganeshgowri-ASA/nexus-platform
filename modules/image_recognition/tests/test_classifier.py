"""
Tests for Image Classification Module

Tests:
- ImageClassifier
- MultiLabelClassifier
- CustomClassifier
- ZeroShotClassifier
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.image_recognition.classifier import (
    ImageClassifier,
    MultiLabelClassifier,
    CustomClassifier,
    ZeroShotClassifier
)


# ============================================================================
# Test ImageClassifier
# ============================================================================

class TestImageClassifier:
    """Test ImageClassifier."""

    def test_initialization(self):
        """Test classifier initialization."""
        classifier = ImageClassifier(
            model_type="resnet50",
            model_path="/path/to/model",
            config={"batch_size": 32}
        )

        assert classifier.model_type == "resnet50"
        assert classifier.model_path == "/path/to/model"
        assert classifier.config == {"batch_size": 32}
        assert classifier.model is None

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_load_model(self, mock_factory):
        """Test loading model."""
        mock_model = MagicMock()
        mock_model.load_model.return_value = True
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        result = classifier.load_model()

        assert result is True
        assert classifier.model is not None
        mock_factory.create_model.assert_called_once()

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_load_model_failure(self, mock_factory):
        """Test model loading failure."""
        mock_factory.create_model.side_effect = Exception("Load failed")

        classifier = ImageClassifier("resnet50")
        result = classifier.load_model()

        assert result is False

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_image_path(self, mock_factory, sample_image_file):
        """Test classifying image from file path."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'predictions': [
                {'class_id': '1', 'label': 'cat', 'confidence': 0.95},
                {'class_id': '2', 'label': 'dog', 'confidence': 0.85}
            ],
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        result = classifier.classify(str(sample_image_file), top_k=5)

        assert result['success'] is True
        assert len(result['predictions']) == 2
        assert result['predictions'][0]['label'] == 'cat'

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_pil_image(self, mock_factory, sample_image):
        """Test classifying PIL image."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'predictions': [
                {'class_id': '1', 'label': 'cat', 'confidence': 0.95}
            ],
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        result = classifier.classify(sample_image)

        assert result['success'] is True
        assert len(result['predictions']) == 1

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_numpy_array(self, mock_factory, sample_image_array):
        """Test classifying numpy array."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'predictions': [{'class_id': '1', 'label': 'cat', 'confidence': 0.95}],
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        result = classifier.classify(sample_image_array)

        assert result['success'] is True

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_with_confidence_threshold(self, mock_factory, sample_image):
        """Test classification with confidence threshold."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'predictions': [
                {'class_id': '1', 'label': 'cat', 'confidence': 0.95},
                {'class_id': '2', 'label': 'dog', 'confidence': 0.45},
                {'class_id': '3', 'label': 'bird', 'confidence': 0.30}
            ],
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        result = classifier.classify(sample_image, confidence_threshold=0.5)

        assert result['success'] is True
        assert len(result['predictions']) == 1
        assert result['predictions'][0]['confidence'] >= 0.5

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_auto_loads_model(self, mock_factory, sample_image):
        """Test classification auto-loads model if not loaded."""
        mock_model = MagicMock()
        mock_model.is_loaded = False
        mock_model.load_model.return_value = True
        mock_model.predict.return_value = {
            'predictions': [{'class_id': '1', 'label': 'cat', 'confidence': 0.95}],
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        result = classifier.classify(sample_image)

        assert result['success'] is True

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_error_handling(self, mock_factory, sample_image):
        """Test error handling during classification."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.side_effect = Exception("Prediction failed")
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        result = classifier.classify(sample_image)

        assert result['success'] is False
        assert 'error' in result
        assert result['predictions'] == []

    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_batch(self, mock_factory, multiple_sample_images):
        """Test batch classification."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'predictions': [{'class_id': '1', 'label': 'cat', 'confidence': 0.95}],
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        results = classifier.classify_batch(multiple_sample_images)

        assert len(results) == len(multiple_sample_images)
        assert all(r['success'] for r in results)

    @pytest.mark.parametrize("top_k", [1, 3, 5, 10])
    @patch('modules.image_recognition.classifier.ModelFactory')
    def test_classify_different_top_k(self, mock_factory, sample_image, top_k):
        """Test classification with different top_k values."""
        predictions = [
            {'class_id': str(i), 'label': f'class_{i}', 'confidence': 0.9 - i*0.1}
            for i in range(top_k)
        ]
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'predictions': predictions,
            'processing_time_ms': 100,
            'model_name': 'resnet50'
        }
        mock_factory.create_model.return_value = mock_model

        classifier = ImageClassifier("resnet50")
        classifier.model = mock_model
        result = classifier.classify(sample_image, top_k=top_k)

        assert len(result['predictions']) == top_k


# ============================================================================
# Test MultiLabelClassifier
# ============================================================================

class TestMultiLabelClassifier:
    """Test MultiLabelClassifier."""

    def test_initialization(self):
        """Test multi-label classifier initialization."""
        labels = ['cat', 'dog', 'bird', 'car']
        classifier = MultiLabelClassifier(
            model_path="/path/to/model.h5",
            labels=labels,
            threshold=0.6
        )

        assert classifier.model_path == "/path/to/model.h5"
        assert classifier.labels == labels
        assert classifier.threshold == 0.6

    @patch('modules.image_recognition.classifier.keras')
    def test_load_model(self, mock_keras):
        """Test loading multi-label model."""
        mock_model = MagicMock()
        mock_keras.models.load_model.return_value = mock_model

        classifier = MultiLabelClassifier(
            "/path/to/model.h5",
            ['cat', 'dog']
        )
        result = classifier.load_model()

        assert result is True
        mock_keras.models.load_model.assert_called_once()

    @patch('modules.image_recognition.classifier.keras')
    def test_classify(self, mock_keras, sample_image):
        """Test multi-label classification."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.9, 0.7, 0.3, 0.1]])
        mock_keras.models.load_model.return_value = mock_model
        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        labels = ['cat', 'dog', 'bird', 'car']
        classifier = MultiLabelClassifier("/path/to/model.h5", labels, threshold=0.5)
        classifier.model = mock_model

        result = classifier.classify(sample_image)

        assert result['success'] is True
        assert result['num_labels'] == 2  # cat and dog above threshold
        assert result['labels'][0]['label'] == 'cat'
        assert result['labels'][0]['confidence'] == 0.9

    @patch('modules.image_recognition.classifier.keras')
    def test_classify_no_labels_above_threshold(self, mock_keras, sample_image):
        """Test when no labels exceed threshold."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.3, 0.2, 0.1, 0.05]])
        mock_keras.models.load_model.return_value = mock_model
        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        classifier = MultiLabelClassifier(
            "/path/to/model.h5",
            ['cat', 'dog', 'bird', 'car'],
            threshold=0.5
        )
        classifier.model = mock_model

        result = classifier.classify(sample_image)

        assert result['success'] is True
        assert result['num_labels'] == 0

    @patch('modules.image_recognition.classifier.keras')
    def test_classify_all_predictions_returned(self, mock_keras, sample_image):
        """Test all predictions are returned."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.9, 0.7, 0.3, 0.1]])
        mock_keras.models.load_model.return_value = mock_model
        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        labels = ['cat', 'dog', 'bird', 'car']
        classifier = MultiLabelClassifier("/path/to/model.h5", labels)
        classifier.model = mock_model

        result = classifier.classify(sample_image)

        assert 'all_predictions' in result
        assert len(result['all_predictions']) == 4


# ============================================================================
# Test CustomClassifier
# ============================================================================

class TestCustomClassifier:
    """Test CustomClassifier."""

    def test_initialization(self):
        """Test custom classifier initialization."""
        classifier = CustomClassifier(
            base_model="resnet50",
            num_classes=10,
            model_path="/path/to/model"
        )

        assert classifier.base_model == "resnet50"
        assert classifier.num_classes == 10
        assert classifier.model_path == "/path/to/model"

    @patch('modules.image_recognition.classifier.keras')
    def test_build_model_resnet50(self, mock_keras):
        """Test building model with ResNet50 base."""
        mock_base = MagicMock()
        mock_base.output = MagicMock()
        mock_base.layers = [MagicMock() for _ in range(10)]
        mock_keras.applications.ResNet50.return_value = mock_base

        classifier = CustomClassifier(base_model="resnet50", num_classes=10)
        result = classifier.build_model(trainable_layers=3)

        assert result is True
        assert classifier.model is not None

    @patch('modules.image_recognition.classifier.keras')
    def test_build_model_vgg16(self, mock_keras):
        """Test building model with VGG16 base."""
        mock_base = MagicMock()
        mock_base.output = MagicMock()
        mock_base.layers = [MagicMock() for _ in range(10)]
        mock_keras.applications.VGG16.return_value = mock_base

        classifier = CustomClassifier(base_model="vgg16", num_classes=5)
        result = classifier.build_model()

        assert result is True

    @patch('modules.image_recognition.classifier.keras')
    def test_build_model_unsupported(self, mock_keras):
        """Test building model with unsupported base."""
        classifier = CustomClassifier(base_model="unsupported", num_classes=10)
        result = classifier.build_model()

        assert result is False

    @patch('modules.image_recognition.classifier.keras')
    def test_load_model(self, mock_keras):
        """Test loading saved model."""
        mock_model = MagicMock()
        mock_keras.models.load_model.return_value = mock_model

        with patch('pathlib.Path.exists', return_value=True):
            classifier = CustomClassifier(model_path="/path/to/model.h5")
            result = classifier.load_model()

            assert result is True
            assert classifier.model is not None

    @patch('modules.image_recognition.classifier.keras')
    def test_save_model(self, mock_keras):
        """Test saving model."""
        mock_model = MagicMock()
        classifier = CustomClassifier()
        classifier.model = mock_model

        result = classifier.save_model("/path/to/save.h5")

        assert result is True
        mock_model.save.assert_called_once_with("/path/to/save.h5")

    @patch('modules.image_recognition.classifier.keras')
    def test_train(self, mock_keras):
        """Test training custom model."""
        mock_model = MagicMock()
        mock_history = MagicMock()
        mock_history.history = {
            'accuracy': [0.8, 0.85, 0.9],
            'val_accuracy': [0.75, 0.8, 0.85]
        }
        mock_model.fit.return_value = mock_history
        mock_base = MagicMock()
        mock_base.output = MagicMock()
        mock_base.layers = [MagicMock() for _ in range(10)]
        mock_keras.applications.ResNet50.return_value = mock_base

        classifier = CustomClassifier(base_model="resnet50", num_classes=10)
        classifier.build_model()
        classifier.model = mock_model

        train_data = MagicMock()
        val_data = MagicMock()
        result = classifier.train(train_data, val_data, epochs=3)

        assert result['success'] is True
        assert result['final_train_accuracy'] == 0.9
        assert result['final_val_accuracy'] == 0.85

    @patch('modules.image_recognition.classifier.keras')
    def test_predict(self, mock_keras, sample_image):
        """Test prediction with custom classifier."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([[0.1, 0.7, 0.2]])
        mock_keras.preprocessing.image.img_to_array.return_value = np.zeros((224, 224, 3))

        classifier = CustomClassifier(num_classes=3)
        classifier.model = mock_model
        classifier.set_class_names(['cat', 'dog', 'bird'])

        result = classifier.predict(sample_image, top_k=3)

        assert result['success'] is True
        assert len(result['predictions']) == 3
        assert result['predictions'][0]['label'] == 'dog'

    def test_set_class_names(self):
        """Test setting class names."""
        classifier = CustomClassifier(num_classes=3)
        class_names = ['cat', 'dog', 'bird']

        classifier.set_class_names(class_names)

        assert classifier.class_names == class_names

    def test_set_class_names_wrong_count(self):
        """Test error when setting wrong number of class names."""
        classifier = CustomClassifier(num_classes=3)

        with pytest.raises(ValueError):
            classifier.set_class_names(['cat', 'dog'])


# ============================================================================
# Test ZeroShotClassifier
# ============================================================================

class TestZeroShotClassifier:
    """Test ZeroShotClassifier."""

    @patch('modules.image_recognition.classifier.GPT4VisionWrapper')
    def test_initialization(self, mock_wrapper):
        """Test zero-shot classifier initialization."""
        classifier = ZeroShotClassifier(api_key="test_key")

        assert classifier.model is not None

    @patch('modules.image_recognition.classifier.GPT4VisionWrapper')
    def test_classify(self, mock_wrapper, sample_image):
        """Test zero-shot classification."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'description': 'This is a cat',
            'processing_time_ms': 500
        }
        mock_wrapper.return_value = mock_model

        classifier = ZeroShotClassifier(api_key="test_key")
        result = classifier.classify(
            sample_image,
            candidate_labels=['cat', 'dog', 'bird']
        )

        assert result['success'] is True
        assert 'cat' in result['prediction'].lower()
        assert result['candidate_labels'] == ['cat', 'dog', 'bird']

    @patch('modules.image_recognition.classifier.GPT4VisionWrapper')
    def test_classify_auto_loads_model(self, mock_wrapper, sample_image):
        """Test classification auto-loads model."""
        mock_model = MagicMock()
        mock_model.is_loaded = False
        mock_model.load_model.return_value = True
        mock_model.predict.return_value = {
            'description': 'A dog',
            'processing_time_ms': 500
        }
        mock_wrapper.return_value = mock_model

        classifier = ZeroShotClassifier(api_key="test_key")
        result = classifier.classify(sample_image, candidate_labels=['cat', 'dog'])

        assert result['success'] is True
        mock_model.load_model.assert_called_once()

    @patch('modules.image_recognition.classifier.GPT4VisionWrapper')
    def test_classify_error_handling(self, mock_wrapper, sample_image):
        """Test error handling in zero-shot classification."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.side_effect = Exception("API error")
        mock_wrapper.return_value = mock_model

        classifier = ZeroShotClassifier(api_key="test_key")
        result = classifier.classify(sample_image, candidate_labels=['cat', 'dog'])

        assert result['success'] is False
        assert 'error' in result

    @patch('modules.image_recognition.classifier.GPT4VisionWrapper')
    def test_classify_with_custom_template(self, mock_wrapper, sample_image):
        """Test classification with custom hypothesis template."""
        mock_model = MagicMock()
        mock_model.is_loaded = True
        mock_model.predict.return_value = {
            'description': 'A cat',
            'processing_time_ms': 500
        }
        mock_wrapper.return_value = mock_model

        classifier = ZeroShotClassifier(api_key="test_key")
        result = classifier.classify(
            sample_image,
            candidate_labels=['cat', 'dog'],
            hypothesis_template="This image shows a {}"
        )

        assert result['success'] is True
