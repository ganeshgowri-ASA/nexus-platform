"""
Tests for Image Preprocessing Module

Tests:
- ImageNormalizer
- ImageResizer
- ImageAugmenter
- ColorCorrector
- PreprocessingPipeline
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ============================================================================
# Test ImageNormalizer
# ============================================================================

class TestImageNormalizer:
    """Test ImageNormalizer."""

    def test_normalize_standard(self, sample_image_array):
        """Test standard normalization (0-1)."""
        from modules.image_recognition.preprocessing import ImageNormalizer

        normalizer = ImageNormalizer(method='standard')
        normalized = normalizer.normalize(sample_image_array)

        assert normalized.min() >= 0
        assert normalized.max() <= 1
        assert normalized.dtype == np.float32 or normalized.dtype == np.float64

    def test_normalize_mean_std(self, sample_image_array):
        """Test mean-std normalization."""
        from modules.image_recognition.preprocessing import ImageNormalizer

        normalizer = ImageNormalizer(
            method='mean_std',
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
        normalized = normalizer.normalize(sample_image_array)

        assert normalized.shape == sample_image_array.shape

    def test_normalize_min_max(self, sample_image_array):
        """Test min-max normalization."""
        from modules.image_recognition.preprocessing import ImageNormalizer

        normalizer = ImageNormalizer(method='min_max', min_val=0, max_val=1)
        normalized = normalizer.normalize(sample_image_array)

        assert normalized.min() >= 0
        assert normalized.max() <= 1

    @pytest.mark.parametrize("method", ['standard', 'mean_std', 'min_max'])
    def test_different_normalization_methods(self, sample_image_array, method):
        """Test different normalization methods."""
        from modules.image_recognition.preprocessing import ImageNormalizer

        normalizer = ImageNormalizer(method=method)
        result = normalizer.normalize(sample_image_array)

        assert result is not None
        assert result.shape == sample_image_array.shape


# ============================================================================
# Test ImageResizer
# ============================================================================

class TestImageResizer:
    """Test ImageResizer."""

    @pytest.mark.parametrize("target_size", [(224, 224), (299, 299), (512, 512)])
    def test_resize_image(self, sample_image, target_size):
        """Test resizing image to different sizes."""
        from modules.image_recognition.preprocessing import ImageResizer

        resizer = ImageResizer(target_size=target_size)
        resized = resizer.resize(sample_image)

        assert resized.size == target_size

    def test_resize_with_aspect_ratio(self, sample_image):
        """Test resizing while maintaining aspect ratio."""
        from modules.image_recognition.preprocessing import ImageResizer

        resizer = ImageResizer(target_size=(224, 224), keep_aspect_ratio=True)
        resized = resizer.resize(sample_image)

        assert resized is not None
        assert max(resized.size) == 224

    def test_resize_with_padding(self, sample_image):
        """Test resizing with padding."""
        from modules.image_recognition.preprocessing import ImageResizer

        resizer = ImageResizer(
            target_size=(224, 224),
            keep_aspect_ratio=True,
            pad=True,
            pad_color=(0, 0, 0)
        )
        resized = resizer.resize(sample_image)

        assert resized.size == (224, 224)

    @pytest.mark.parametrize("method", ['bilinear', 'bicubic', 'lanczos', 'nearest'])
    def test_different_resize_methods(self, sample_image, method):
        """Test different resize interpolation methods."""
        from modules.image_recognition.preprocessing import ImageResizer

        resizer = ImageResizer(target_size=(224, 224), method=method)
        resized = resizer.resize(sample_image)

        assert resized.size == (224, 224)


# ============================================================================
# Test ImageAugmenter
# ============================================================================

class TestImageAugmenter:
    """Test ImageAugmenter."""

    def test_random_flip(self, sample_image):
        """Test random horizontal/vertical flip."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(flip_horizontal=True, flip_vertical=True)
        augmented = augmenter.augment(sample_image)

        assert augmented.size == sample_image.size

    def test_random_rotation(self, sample_image):
        """Test random rotation."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(rotate=True, rotation_range=30)
        augmented = augmenter.augment(sample_image)

        assert augmented.size == sample_image.size

    def test_random_brightness(self, sample_image):
        """Test random brightness adjustment."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(brightness=True, brightness_range=(0.5, 1.5))
        augmented = augmenter.augment(sample_image)

        assert augmented.size == sample_image.size

    def test_random_crop(self, sample_image):
        """Test random cropping."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(crop=True, crop_size=(200, 200))
        augmented = augmenter.augment(sample_image)

        assert augmented is not None

    def test_gaussian_noise(self, sample_image_array):
        """Test adding Gaussian noise."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(noise=True, noise_std=0.1)
        augmented = augmenter.augment(sample_image_array)

        assert augmented.shape == sample_image_array.shape

    def test_multiple_augmentations(self, sample_image):
        """Test applying multiple augmentations."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(
            flip_horizontal=True,
            rotate=True,
            brightness=True,
            contrast=True
        )
        augmented = augmenter.augment(sample_image)

        assert augmented.size == sample_image.size

    def test_augment_batch(self, multiple_sample_images):
        """Test batch augmentation."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        augmenter = ImageAugmenter(flip_horizontal=True)
        augmented = augmenter.augment_batch(multiple_sample_images)

        assert len(augmented) == len(multiple_sample_images)


# ============================================================================
# Test ColorCorrector
# ============================================================================

class TestColorCorrector:
    """Test ColorCorrector."""

    def test_brightness_correction(self, sample_image):
        """Test brightness correction."""
        from modules.image_recognition.preprocessing import ColorCorrector

        corrector = ColorCorrector()
        corrected = corrector.adjust_brightness(sample_image, factor=1.2)

        assert corrected.size == sample_image.size

    def test_contrast_correction(self, sample_image):
        """Test contrast correction."""
        from modules.image_recognition.preprocessing import ColorCorrector

        corrector = ColorCorrector()
        corrected = corrector.adjust_contrast(sample_image, factor=1.5)

        assert corrected.size == sample_image.size

    def test_saturation_correction(self, sample_image):
        """Test saturation correction."""
        from modules.image_recognition.preprocessing import ColorCorrector

        corrector = ColorCorrector()
        corrected = corrector.adjust_saturation(sample_image, factor=1.3)

        assert corrected.size == sample_image.size

    def test_white_balance(self, sample_image):
        """Test white balance correction."""
        from modules.image_recognition.preprocessing import ColorCorrector

        corrector = ColorCorrector()
        corrected = corrector.white_balance(sample_image)

        assert corrected.size == sample_image.size

    def test_gamma_correction(self, sample_image_array):
        """Test gamma correction."""
        from modules.image_recognition.preprocessing import ColorCorrector

        corrector = ColorCorrector()
        corrected = corrector.gamma_correction(sample_image_array, gamma=1.2)

        assert corrected.shape == sample_image_array.shape

    def test_auto_color_correct(self, sample_image):
        """Test automatic color correction."""
        from modules.image_recognition.preprocessing import ColorCorrector

        corrector = ColorCorrector()
        corrected = corrector.auto_correct(sample_image)

        assert corrected.size == sample_image.size


# ============================================================================
# Test PreprocessingPipeline
# ============================================================================

class TestPreprocessingPipeline:
    """Test PreprocessingPipeline."""

    def test_pipeline_creation(self):
        """Test creating preprocessing pipeline."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(
            steps=['resize', 'normalize', 'augment'],
            config={
                'resize': {'target_size': (224, 224)},
                'normalize': {'method': 'standard'},
                'augment': {'flip_horizontal': True}
            }
        )

        assert len(pipeline.steps) == 3

    def test_pipeline_process(self, sample_image):
        """Test processing image through pipeline."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(
            steps=['resize', 'normalize'],
            config={
                'resize': {'target_size': (224, 224)},
                'normalize': {'method': 'standard'}
            }
        )

        result = pipeline.process(sample_image)

        assert result is not None

    def test_pipeline_add_step(self):
        """Test adding step to pipeline."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(steps=['resize'])
        pipeline.add_step('normalize', {'method': 'standard'})

        assert len(pipeline.steps) == 2

    def test_pipeline_remove_step(self):
        """Test removing step from pipeline."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(steps=['resize', 'normalize', 'augment'])
        pipeline.remove_step('normalize')

        assert len(pipeline.steps) == 2
        assert 'normalize' not in pipeline.steps

    def test_pipeline_process_batch(self, multiple_sample_images):
        """Test processing batch through pipeline."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(
            steps=['resize'],
            config={'resize': {'target_size': (224, 224)}}
        )

        results = pipeline.process_batch(multiple_sample_images)

        assert len(results) == len(multiple_sample_images)

    def test_pipeline_with_custom_step(self, sample_image):
        """Test pipeline with custom preprocessing step."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        def custom_step(image):
            return image.convert('L')  # Convert to grayscale

        pipeline = PreprocessingPipeline(steps=[])
        pipeline.add_custom_step('grayscale', custom_step)

        result = pipeline.process(sample_image)

        assert result is not None

    def test_pipeline_error_handling(self, sample_image):
        """Test pipeline error handling."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(
            steps=['invalid_step'],
            config={}
        )

        with pytest.raises(Exception):
            pipeline.process(sample_image)

    @pytest.mark.parametrize("steps,expected_count", [
        (['resize'], 1),
        (['resize', 'normalize'], 2),
        (['resize', 'normalize', 'augment'], 3),
        (['resize', 'normalize', 'augment', 'color_correct'], 4)
    ])
    def test_different_pipeline_configurations(
        self, sample_image, steps, expected_count
    ):
        """Test different pipeline configurations."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(steps=steps)

        assert len(pipeline.steps) == expected_count


# ============================================================================
# Edge Cases and Performance Tests
# ============================================================================

class TestPreprocessingEdgeCases:
    """Test edge cases and performance."""

    def test_normalize_zero_image(self):
        """Test normalizing all-zero image."""
        from modules.image_recognition.preprocessing import ImageNormalizer

        zero_image = np.zeros((224, 224, 3), dtype=np.uint8)
        normalizer = ImageNormalizer()
        result = normalizer.normalize(zero_image)

        assert result is not None
        assert result.shape == zero_image.shape

    def test_resize_very_small_image(self):
        """Test resizing very small image."""
        from modules.image_recognition.preprocessing import ImageResizer

        small_image = Image.new('RGB', (10, 10))
        resizer = ImageResizer(target_size=(224, 224))
        result = resizer.resize(small_image)

        assert result.size == (224, 224)

    def test_resize_very_large_image(self):
        """Test resizing very large image."""
        from modules.image_recognition.preprocessing import ImageResizer

        large_image = Image.new('RGB', (4000, 3000))
        resizer = ImageResizer(target_size=(224, 224))
        result = resizer.resize(large_image)

        assert result.size == (224, 224)

    def test_augment_single_channel_image(self):
        """Test augmenting grayscale image."""
        from modules.image_recognition.preprocessing import ImageAugmenter

        gray_image = Image.new('L', (224, 224))
        augmenter = ImageAugmenter(flip_horizontal=True)
        result = augmenter.augment(gray_image)

        assert result is not None

    def test_pipeline_empty_steps(self, sample_image):
        """Test pipeline with no steps."""
        from modules.image_recognition.preprocessing import PreprocessingPipeline

        pipeline = PreprocessingPipeline(steps=[])
        result = pipeline.process(sample_image)

        assert result is not None
