"""
Tests for Feature Extraction Module

Tests:
- FeatureExtractor
- SimilaritySearchEngine
- DuplicateDetector
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ============================================================================
# Test FeatureExtractor
# ============================================================================

class TestFeatureExtractor:
    """Test FeatureExtractor."""

    @patch('modules.image_recognition.features.ModelFactory')
    def test_initialization(self, mock_factory):
        """Test feature extractor initialization."""
        from modules.image_recognition.features import FeatureExtractor

        extractor = FeatureExtractor(model_type='resnet50')

        assert extractor.model_type == 'resnet50'

    @patch('modules.image_recognition.features.ModelFactory')
    def test_extract_features(self, mock_factory, sample_image):
        """Test extracting features from image."""
        from modules.image_recognition.features import FeatureExtractor

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'features': np.random.rand(2048).tolist(),
            'processing_time_ms': 50
        }
        mock_factory.create_model.return_value = mock_model

        extractor = FeatureExtractor()
        extractor.model = mock_model
        features = extractor.extract(sample_image)

        assert features is not None
        assert len(features) > 0

    @patch('modules.image_recognition.features.ModelFactory')
    def test_extract_features_batch(self, mock_factory, multiple_sample_images):
        """Test batch feature extraction."""
        from modules.image_recognition.features import FeatureExtractor

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'features': np.random.rand(2048).tolist()
        }
        mock_factory.create_model.return_value = mock_model

        extractor = FeatureExtractor()
        extractor.model = mock_model
        features_list = extractor.extract_batch(multiple_sample_images)

        assert len(features_list) == len(multiple_sample_images)

    @pytest.mark.parametrize("layer", ['global_average', 'fc', 'last_conv'])
    @patch('modules.image_recognition.features.ModelFactory')
    def test_extract_from_different_layers(self, mock_factory, sample_image, layer):
        """Test extracting features from different layers."""
        from modules.image_recognition.features import FeatureExtractor

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'features': np.random.rand(2048).tolist()
        }
        mock_factory.create_model.return_value = mock_model

        extractor = FeatureExtractor(layer=layer)
        extractor.model = mock_model
        features = extractor.extract(sample_image)

        assert features is not None

    @patch('modules.image_recognition.features.ModelFactory')
    def test_dimensionality_reduction(self, mock_factory, sample_image):
        """Test feature dimensionality reduction."""
        from modules.image_recognition.features import FeatureExtractor

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'features': np.random.rand(2048).tolist()
        }
        mock_factory.create_model.return_value = mock_model

        extractor = FeatureExtractor(reduce_dims=True, target_dims=128)
        extractor.model = mock_model
        features = extractor.extract(sample_image)

        assert features is not None


# ============================================================================
# Test SimilaritySearchEngine
# ============================================================================

class TestSimilaritySearchEngine:
    """Test SimilaritySearchEngine."""

    def test_initialization(self):
        """Test similarity search engine initialization."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine(metric='cosine')

        assert engine.metric == 'cosine'

    def test_add_features(self):
        """Test adding features to index."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()
        features = np.random.rand(10, 128)
        ids = [f'img_{i}' for i in range(10)]

        engine.add(features, ids)

        assert engine.num_features == 10

    def test_search_similar(self):
        """Test searching for similar features."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()

        # Add features to index
        features = np.random.rand(100, 128)
        ids = [f'img_{i}' for i in range(100)]
        engine.add(features, ids)

        # Search
        query = np.random.rand(128)
        results = engine.search(query, k=5)

        assert len(results) == 5
        assert all('id' in r and 'distance' in r for r in results)

    def test_search_batch(self):
        """Test batch similarity search."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()

        # Add features
        features = np.random.rand(100, 128)
        ids = [f'img_{i}' for i in range(100)]
        engine.add(features, ids)

        # Batch search
        queries = np.random.rand(5, 128)
        results = engine.search_batch(queries, k=3)

        assert len(results) == 5
        assert all(len(r) == 3 for r in results)

    @pytest.mark.parametrize("metric", ['cosine', 'euclidean', 'manhattan'])
    def test_different_metrics(self, metric):
        """Test different distance metrics."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine(metric=metric)
        features = np.random.rand(50, 128)
        ids = [f'img_{i}' for i in range(50)]
        engine.add(features, ids)

        query = np.random.rand(128)
        results = engine.search(query, k=5)

        assert len(results) == 5

    def test_remove_features(self):
        """Test removing features from index."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()
        features = np.random.rand(10, 128)
        ids = [f'img_{i}' for i in range(10)]
        engine.add(features, ids)

        engine.remove(['img_0', 'img_1'])

        assert engine.num_features == 8

    def test_update_features(self):
        """Test updating features in index."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()
        features = np.random.rand(10, 128)
        ids = [f'img_{i}' for i in range(10)]
        engine.add(features, ids)

        # Update
        new_features = np.random.rand(2, 128)
        engine.update(['img_0', 'img_1'], new_features)

        assert engine.num_features == 10


# ============================================================================
# Test DuplicateDetector
# ============================================================================

class TestDuplicateDetector:
    """Test DuplicateDetector."""

    def test_initialization(self):
        """Test duplicate detector initialization."""
        from modules.image_recognition.features import DuplicateDetector

        detector = DuplicateDetector(threshold=0.95)

        assert detector.threshold == 0.95

    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_find_duplicates(self, mock_extractor, multiple_sample_images):
        """Test finding duplicate images."""
        from modules.image_recognition.features import DuplicateDetector

        # Mock feature extraction
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract.return_value = np.random.rand(128)
        mock_extractor.return_value = mock_extractor_instance

        detector = DuplicateDetector()
        duplicates = detector.find_duplicates(multiple_sample_images)

        assert duplicates is not None
        assert isinstance(duplicates, list)

    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_find_exact_duplicates(self, mock_extractor):
        """Test finding exact duplicates."""
        from modules.image_recognition.features import DuplicateDetector

        # Create identical images
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='red')
        img3 = Image.new('RGB', (100, 100), color='blue')

        # Mock feature extraction to return same features for identical images
        mock_extractor_instance = MagicMock()
        features_red = np.ones(128)
        features_blue = np.zeros(128)
        mock_extractor_instance.extract.side_effect = [
            features_red,
            features_red,
            features_blue
        ]
        mock_extractor.return_value = mock_extractor_instance

        detector = DuplicateDetector(threshold=0.99)
        duplicates = detector.find_duplicates([img1, img2, img3])

        # Should find img1 and img2 as duplicates
        assert duplicates is not None

    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_find_near_duplicates(self, mock_extractor):
        """Test finding near-duplicate images."""
        from modules.image_recognition.features import DuplicateDetector

        mock_extractor_instance = MagicMock()
        # Generate similar but not identical features
        base_features = np.random.rand(128)
        mock_extractor_instance.extract.side_effect = [
            base_features,
            base_features + np.random.rand(128) * 0.01,  # Very similar
            base_features + np.random.rand(128) * 0.5    # Less similar
        ]
        mock_extractor.return_value = mock_extractor_instance

        detector = DuplicateDetector(threshold=0.9)
        images = [
            Image.new('RGB', (100, 100)),
            Image.new('RGB', (100, 100)),
            Image.new('RGB', (100, 100))
        ]
        duplicates = detector.find_duplicates(images)

        assert duplicates is not None

    @pytest.mark.parametrize("threshold", [0.8, 0.9, 0.95, 0.99])
    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_different_thresholds(self, mock_extractor, threshold):
        """Test detection with different similarity thresholds."""
        from modules.image_recognition.features import DuplicateDetector

        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract.return_value = np.random.rand(128)
        mock_extractor.return_value = mock_extractor_instance

        detector = DuplicateDetector(threshold=threshold)
        images = [Image.new('RGB', (100, 100)) for _ in range(10)]
        duplicates = detector.find_duplicates(images)

        assert duplicates is not None

    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_hash_based_duplicate_detection(self, mock_extractor):
        """Test hash-based duplicate detection."""
        from modules.image_recognition.features import DuplicateDetector

        detector = DuplicateDetector(method='hash')

        # Create identical images
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='red')
        img3 = Image.new('RGB', (100, 100), color='blue')

        duplicates = detector.find_duplicates([img1, img2, img3])

        assert duplicates is not None

    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_perceptual_hash(self, mock_extractor):
        """Test perceptual hash for similarity."""
        from modules.image_recognition.features import DuplicateDetector

        detector = DuplicateDetector(method='phash')

        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='red')

        hash1 = detector.compute_hash(img1)
        hash2 = detector.compute_hash(img2)

        assert hash1 == hash2


# ============================================================================
# Edge Cases and Performance
# ============================================================================

class TestFeaturesEdgeCases:
    """Test edge cases."""

    @patch('modules.image_recognition.features.ModelFactory')
    def test_extract_from_corrupted_image(self, mock_factory):
        """Test feature extraction from corrupted image."""
        from modules.image_recognition.features import FeatureExtractor

        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("Corrupted image")
        mock_factory.create_model.return_value = mock_model

        extractor = FeatureExtractor()
        extractor.model = mock_model

        with pytest.raises(Exception):
            extractor.extract(Image.new('RGB', (1, 1)))

    def test_search_empty_index(self):
        """Test searching in empty index."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()
        query = np.random.rand(128)

        results = engine.search(query, k=5)

        assert len(results) == 0

    def test_search_k_larger_than_index(self):
        """Test searching with k larger than index size."""
        from modules.image_recognition.features import SimilaritySearchEngine

        engine = SimilaritySearchEngine()
        features = np.random.rand(5, 128)
        ids = [f'img_{i}' for i in range(5)]
        engine.add(features, ids)

        query = np.random.rand(128)
        results = engine.search(query, k=10)

        assert len(results) == 5  # Should return all available

    @patch('modules.image_recognition.features.FeatureExtractor')
    def test_find_duplicates_single_image(self, mock_extractor):
        """Test finding duplicates with single image."""
        from modules.image_recognition.features import DuplicateDetector

        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract.return_value = np.random.rand(128)
        mock_extractor.return_value = mock_extractor_instance

        detector = DuplicateDetector()
        duplicates = detector.find_duplicates([Image.new('RGB', (100, 100))])

        assert duplicates is not None
        assert len(duplicates) == 0  # No duplicates with single image
