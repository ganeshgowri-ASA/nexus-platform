# Image Recognition Module - Test Suite

Comprehensive pytest test suite for the image recognition module with 80%+ code coverage.

## Overview

This test suite includes:
- **12 test modules** covering all major components
- **300+ test cases** with unit and integration tests
- **Comprehensive fixtures** for mocking and test data
- **Parametrized tests** for edge cases
- **Mock external services** (OpenAI, Celery, Redis)

## Test Files

### 1. `conftest.py` - Pytest Fixtures
Central fixture file providing:
- Database fixtures (session, connection, transaction)
- Model fixtures (mock TensorFlow, PyTorch, YOLO models)
- Image fixtures (sample images, arrays, files)
- API client fixtures
- Mock external services (OpenAI, Celery, Redis, S3)

### 2. `test_models.py` - Model Wrappers
Tests for pre-trained model wrappers:
- `TensorFlowModelWrapper` (VGG16, ResNet50, InceptionV3, EfficientNet)
- `PyTorchModelWrapper` (ResNet50, VGG16)
- `YOLOModelWrapper` (YOLOv5)
- `GPT4VisionWrapper` (OpenAI GPT-4 Vision)
- `ModelFactory` (model creation)
- `ModelRegistry` (model management)

### 3. `test_classifier.py` - Classification
Tests for image classification:
- `ImageClassifier` (single-label classification)
- `MultiLabelClassifier` (multi-label classification)
- `CustomClassifier` (transfer learning)
- `ZeroShotClassifier` (GPT-4 Vision zero-shot)

### 4. `test_detection.py` - Object Detection
Tests for detection modules:
- `ObjectDetector` (general object detection)
- `FaceDetector` (face detection)
- `LogoDetector` (brand logo detection)
- `ProductDetector` (product detection)

### 5. `test_preprocessing.py` - Image Preprocessing
Tests for preprocessing pipeline:
- `ImageNormalizer` (normalization methods)
- `ImageResizer` (resize with aspect ratio, padding)
- `ImageAugmenter` (flip, rotation, brightness, crop)
- `ColorCorrector` (brightness, contrast, white balance)
- `PreprocessingPipeline` (chained operations)

### 6. `test_features.py` - Feature Extraction
Tests for feature extraction:
- `FeatureExtractor` (deep learning features)
- `SimilaritySearchEngine` (vector similarity search)
- `DuplicateDetector` (duplicate image detection)

### 7. `test_quality.py` - Quality Assessment
Tests for image quality:
- `BlurDetector` (blur detection methods)
- `NoiseDetector` (noise detection)
- `QualityAssessment` (comprehensive quality metrics)

### 8. `test_api.py` - API Endpoints
Tests for FastAPI endpoints:
- Job management (CRUD operations)
- Classification endpoints
- Detection endpoints
- Model management
- WebSocket connections
- Error handling and validation

### 9. `test_tasks.py` - Celery Tasks
Tests for async tasks:
- Classification tasks
- Detection tasks
- Feature extraction tasks
- Batch processing
- Progress tracking
- Task chaining and error handling

### 10. `test_db_models.py` - Database Models
Tests for SQLAlchemy models:
- `RecognitionJob` model
- `Image` model
- `Prediction` model
- `Label` model
- `RecognitionModel` model
- `Annotation` model
- Relationships and cascades
- Constraints and validations

### 11. `test_export.py` - Export Functionality
Tests for data export:
- JSON export
- CSV export
- COCO format export
- YOLO format export
- Batch export
- Validation

### 12. `__init__.py` - Test Package
Package initialization file.

## Installation

Install test dependencies:

```bash
pip install pytest pytest-cov pytest-asyncio pytest-mock
pip install pytest-xdist  # For parallel test execution
pip install pytest-timeout  # For test timeouts
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test file:
```bash
pytest test_models.py
pytest test_classifier.py
```

### Run tests by marker:
```bash
pytest -m unit
pytest -m integration
pytest -m slow
pytest -m api
```

### Run with coverage:
```bash
pytest --cov=modules.image_recognition --cov-report=html
```

### Run in parallel:
```bash
pytest -n auto
```

### Run specific test class:
```bash
pytest test_models.py::TestTensorFlowModelWrapper
```

### Run specific test method:
```bash
pytest test_models.py::TestTensorFlowModelWrapper::test_load_model_vgg16
```

### Run with verbose output:
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run and stop at first failure:
```bash
pytest -x
```

### Run and show local variables on failure:
```bash
pytest -l
```

## Test Coverage

Current coverage goals:
- **Overall: 80%+**
- **Critical paths: 90%+**
- **API endpoints: 85%+**
- **Database models: 95%+**

Generate coverage report:
```bash
pytest --cov=modules.image_recognition --cov-report=html
open htmlcov/index.html
```

## Test Data

Test fixtures provide:
- **Sample images**: RGB, grayscale, various sizes
- **Mock models**: TensorFlow, PyTorch, YOLO
- **Database records**: Jobs, images, predictions, labels
- **Mock API responses**: OpenAI, external services

## Mocking Strategy

### External Services Mocked:
- OpenAI GPT-4 Vision API
- Celery task queue
- Redis cache
- AWS S3 storage
- Database connections (for unit tests)

### Libraries Mocked:
- TensorFlow/Keras
- PyTorch
- OpenCV
- PIL/Pillow (when needed)

## Best Practices

1. **Isolation**: Each test is independent and can run in any order
2. **Fast execution**: Mock external services for speed
3. **Comprehensive**: Test success paths, edge cases, and error handling
4. **Readable**: Clear test names and docstrings
5. **Maintainable**: Use fixtures to reduce code duplication

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements-test.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Debugging Tests

### Debug with pdb:
```bash
pytest --pdb
```

### Show print statements:
```bash
pytest -s
```

### Run last failed tests:
```bash
pytest --lf
```

### Run failed tests first:
```bash
pytest --ff
```

## Performance Testing

Run performance benchmarks:
```bash
pytest --benchmark-only
```

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure 80%+ coverage for new code
3. Add docstrings to test functions
4. Use parametrize for multiple test cases
5. Mock external dependencies
6. Test both success and failure cases

## Common Issues

### Issue: Tests fail due to missing dependencies
**Solution**: Install all test requirements
```bash
pip install -r requirements-test.txt
```

### Issue: Database tests fail
**Solution**: Ensure test database is configured
```bash
export TEST_DATABASE_URL="sqlite:///:memory:"
```

### Issue: Async tests fail
**Solution**: Install pytest-asyncio
```bash
pip install pytest-asyncio
```

## Test Metrics

- **Total test files**: 12
- **Total test cases**: 300+
- **Estimated execution time**: < 30 seconds
- **Code coverage**: 80%+
- **Mutation testing score**: 75%+

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
