"""
NEXUS Image Recognition Module

Production-ready image recognition system with support for:
- Image classification (single and multi-label)
- Object detection and localization
- Face recognition and verification
- Logo and product detection
- Scene understanding and context analysis
- Image segmentation (semantic and instance)
- Feature extraction and similarity search
- Custom model training and fine-tuning
- Real-time and batch processing
- Quality assessment and preprocessing
- Annotation tools and dataset management
- Multiple AI model support (VGG16, ResNet, Inception, EfficientNet, YOLO, GPT-4 Vision)

Author: NEXUS Platform Team
Version: 1.0.0
"""

from typing import Dict, Any

__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"

# Module metadata
MODULE_NAME = "image_recognition"
MODULE_DESCRIPTION = "Production-ready image recognition and computer vision module"
MODULE_VERSION = __version__

# Export main classes
__all__ = [
    "ImageRecognitionModule",
    "ImageClassifier",
    "ObjectDetector",
    "FaceDetector",
    "ImageSegmenter",
    "FeatureExtractor",
    "ModelTrainer",
    "BatchPredictor",
    "SceneClassifier",
    "ImageQualityAssessment",
    "CustomModelManager",
    "AnnotationTool",
    "ExportManager",
]


def get_module_info() -> Dict[str, Any]:
    """Get module information."""
    return {
        "name": MODULE_NAME,
        "version": MODULE_VERSION,
        "description": MODULE_DESCRIPTION,
        "features": [
            "Image Classification",
            "Object Detection",
            "Face Recognition",
            "Logo Detection",
            "Product Recognition",
            "Scene Understanding",
            "Image Segmentation",
            "Feature Extraction",
            "Similarity Search",
            "Custom Model Training",
            "Transfer Learning",
            "Real-time Processing",
            "Batch Processing",
            "Quality Assessment",
            "Annotation Tools",
            "Model Management",
            "Export & Reporting",
            "API Access",
            "WebSocket Support",
            "AI Integration (GPT-4 Vision)",
        ],
        "supported_models": [
            "VGG16",
            "ResNet50",
            "InceptionV3",
            "EfficientNet",
            "YOLO",
            "GPT-4 Vision",
            "Custom Models",
        ],
    }
