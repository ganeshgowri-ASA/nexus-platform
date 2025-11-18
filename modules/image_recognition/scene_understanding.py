"""
Scene Understanding Module

Provides comprehensive scene analysis capabilities including:
- Scene classification
- Context analysis
- Object relationship detection
- Spatial reasoning
- Activity recognition
- Scene attributes extraction
- Scene graph generation

Integrates with NEXUS AI orchestrator for advanced scene understanding.
"""

import logging
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
from datetime import datetime

from .models import BaseModelWrapper, ModelFactory, GPT4VisionWrapper
from .detection import ObjectDetector
from .classifier import ImageClassifier

logger = logging.getLogger(__name__)


class SceneAttributes:
    """
    Represents scene attributes and characteristics.
    """

    def __init__(
        self,
        scene_type: str,
        confidence: float,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize scene attributes.

        Args:
            scene_type: Type of scene
            confidence: Confidence score
            attributes: Additional attributes
        """
        self.scene_type = scene_type
        self.confidence = confidence
        self.attributes = attributes or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'scene_type': self.scene_type,
            'confidence': float(self.confidence),
            'attributes': self.attributes,
            'timestamp': self.timestamp.isoformat()
        }


class SceneClassifier:
    """
    Classifies images into scene categories.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize scene classifier.

        Args:
            model_type: Type of model to use
            model_path: Path to scene classification model
            config: Classifier configuration
        """
        self.model_type = model_type
        self.model_path = model_path
        self.config = config or {}
        self.classifier = ImageClassifier(model_type, model_path, config)
        self.scene_categories = self._load_scene_categories()
        self.logger = logging.getLogger(f"{__name__}.SceneClassifier")

    def _load_scene_categories(self) -> List[str]:
        """Load scene category labels."""
        # Places365 scene categories (simplified)
        return [
            'indoor', 'outdoor', 'urban', 'natural', 'commercial',
            'residential', 'office', 'restaurant', 'park', 'beach',
            'forest', 'mountain', 'street', 'building', 'room'
        ]

    def classify_scene(
        self,
        image: Union[str, np.ndarray, Image.Image],
        top_k: int = 3,
        confidence_threshold: float = 0.1
    ) -> SceneAttributes:
        """
        Classify scene in image.

        Args:
            image: Input image
            top_k: Number of top scene predictions
            confidence_threshold: Minimum confidence

        Returns:
            Scene attributes
        """
        try:
            # Run classification
            result = self.classifier.classify(
                image,
                top_k=top_k,
                confidence_threshold=confidence_threshold
            )

            if result['success'] and result['predictions']:
                top_prediction = result['predictions'][0]

                # Extract scene attributes
                attributes = {
                    'all_predictions': result['predictions'],
                    'processing_time_ms': result.get('processing_time_ms', 0),
                    'model_name': result.get('model_name', self.model_type)
                }

                return SceneAttributes(
                    scene_type=top_prediction['label'],
                    confidence=top_prediction['confidence'],
                    attributes=attributes
                )
            else:
                raise Exception("Scene classification failed")

        except Exception as e:
            self.logger.error(f"Error classifying scene: {e}")
            raise


class ContextAnalyzer:
    """
    Analyzes image context and semantics.
    """

    def __init__(
        self,
        scene_classifier: Optional[SceneClassifier] = None,
        object_detector: Optional[ObjectDetector] = None
    ):
        """
        Initialize context analyzer.

        Args:
            scene_classifier: Scene classifier instance
            object_detector: Object detector instance
        """
        self.scene_classifier = scene_classifier or SceneClassifier()
        self.object_detector = object_detector or ObjectDetector()
        self.logger = logging.getLogger(f"{__name__}.ContextAnalyzer")

    def analyze_context(
        self,
        image: Union[str, np.ndarray, Image.Image]
    ) -> Dict[str, Any]:
        """
        Analyze image context.

        Args:
            image: Input image

        Returns:
            Context analysis results
        """
        try:
            # Classify scene
            scene_attrs = self.scene_classifier.classify_scene(image)

            # Detect objects
            objects = self.object_detector.detect(image, confidence_threshold=0.3)

            # Analyze relationships
            relationships = self._analyze_object_relationships(objects)

            # Determine setting
            setting = self._determine_setting(scene_attrs, objects)

            # Extract context features
            context = {
                'scene': scene_attrs.to_dict(),
                'objects': [obj.to_dict() for obj in objects],
                'num_objects': len(objects),
                'relationships': relationships,
                'setting': setting,
                'context_summary': self._generate_context_summary(
                    scene_attrs,
                    objects,
                    setting
                )
            }

            self.logger.info(f"Context analysis completed: {len(objects)} objects detected")
            return context

        except Exception as e:
            self.logger.error(f"Error analyzing context: {e}")
            raise

    def _analyze_object_relationships(
        self,
        objects: List[Any]
    ) -> List[Dict[str, Any]]:
        """Analyze spatial relationships between objects."""
        relationships = []

        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                # Calculate spatial relationship
                relationship = self._compute_spatial_relationship(
                    obj1.bbox,
                    obj2.bbox
                )

                if relationship:
                    relationships.append({
                        'object1': obj1.label,
                        'object2': obj2.label,
                        'relationship': relationship
                    })

        return relationships

    def _compute_spatial_relationship(
        self,
        bbox1: Dict[str, float],
        bbox2: Dict[str, float]
    ) -> Optional[str]:
        """Compute spatial relationship between two bounding boxes."""
        # Get centers
        center1_x = bbox1['x'] + bbox1['width'] / 2
        center1_y = bbox1['y'] + bbox1['height'] / 2
        center2_x = bbox2['x'] + bbox2['width'] / 2
        center2_y = bbox2['y'] + bbox2['height'] / 2

        # Calculate relative position
        dx = center2_x - center1_x
        dy = center2_y - center1_y

        # Determine relationship
        if abs(dx) > abs(dy) * 2:
            return 'next_to'
        elif dy < -bbox1['height']:
            return 'above'
        elif dy > bbox2['height']:
            return 'below'
        elif abs(dx) < bbox1['width'] / 2 and abs(dy) < bbox1['height'] / 2:
            return 'near'
        else:
            return None

    def _determine_setting(
        self,
        scene_attrs: SceneAttributes,
        objects: List[Any]
    ) -> str:
        """Determine overall setting from scene and objects."""
        scene_type = scene_attrs.scene_type.lower()

        if 'indoor' in scene_type or any(obj.label in ['furniture', 'table', 'chair'] for obj in objects):
            return 'indoor'
        elif 'outdoor' in scene_type or any(obj.label in ['tree', 'sky', 'grass'] for obj in objects):
            return 'outdoor'
        else:
            return 'unknown'

    def _generate_context_summary(
        self,
        scene_attrs: SceneAttributes,
        objects: List[Any],
        setting: str
    ) -> str:
        """Generate human-readable context summary."""
        object_labels = [obj.label for obj in objects]
        unique_objects = list(set(object_labels))

        summary = f"A {setting} {scene_attrs.scene_type} scene"

        if unique_objects:
            if len(unique_objects) <= 3:
                summary += f" with {', '.join(unique_objects)}"
            else:
                summary += f" containing {len(unique_objects)} different objects"

        return summary


class RelationshipDetector:
    """
    Detects relationships and interactions between objects.
    """

    def __init__(self):
        """Initialize relationship detector."""
        self.logger = logging.getLogger(f"{__name__}.RelationshipDetector")

    def detect_relationships(
        self,
        objects: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect relationships between objects.

        Args:
            objects: List of detected objects

        Returns:
            List of relationships
        """
        relationships = []

        for i, obj1 in enumerate(objects):
            for j, obj2 in enumerate(objects):
                if i != j:
                    # Check for common relationships
                    rel = self._check_relationship(obj1, obj2)
                    if rel:
                        relationships.append({
                            'subject': obj1.label,
                            'relation': rel,
                            'object': obj2.label,
                            'confidence': min(obj1.confidence, obj2.confidence)
                        })

        return relationships

    def _check_relationship(self, obj1: Any, obj2: Any) -> Optional[str]:
        """Check if two objects have a semantic relationship."""
        # Define common relationships
        relationships_map = {
            ('person', 'chair'): 'sitting_on',
            ('person', 'bicycle'): 'riding',
            ('person', 'car'): 'driving',
            ('dog', 'person'): 'with',
            ('cat', 'person'): 'with',
            ('bird', 'tree'): 'in',
        }

        key = (obj1.label, obj2.label)
        return relationships_map.get(key)


class ActivityRecognizer:
    """
    Recognizes activities and actions in images.
    """

    def __init__(
        self,
        model_path: Optional[str] = None
    ):
        """
        Initialize activity recognizer.

        Args:
            model_path: Path to activity recognition model
        """
        self.model_path = model_path
        self.logger = logging.getLogger(f"{__name__}.ActivityRecognizer")

    def recognize_activity(
        self,
        image: Union[str, np.ndarray, Image.Image],
        objects: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Recognize activities in image.

        Args:
            image: Input image
            objects: Optional list of detected objects

        Returns:
            Activity recognition results
        """
        try:
            # Placeholder - in production, use action recognition model
            # For now, infer from objects
            activities = self._infer_activities_from_objects(objects) if objects else []

            return {
                'activities': activities,
                'confidence': 0.7,
                'method': 'object_based_inference'
            }

        except Exception as e:
            self.logger.error(f"Error recognizing activity: {e}")
            raise

    def _infer_activities_from_objects(self, objects: List[Any]) -> List[str]:
        """Infer possible activities from detected objects."""
        activities = []
        object_labels = [obj.label for obj in objects]

        # Define activity patterns
        if 'person' in object_labels:
            if 'bicycle' in object_labels:
                activities.append('cycling')
            if 'sports ball' in object_labels:
                activities.append('playing_sports')
            if 'laptop' in object_labels:
                activities.append('working')
            if 'dining table' in object_labels or 'fork' in object_labels:
                activities.append('eating')

        return activities


class SceneGraphGenerator:
    """
    Generates scene graphs representing relationships.
    """

    def __init__(self):
        """Initialize scene graph generator."""
        self.logger = logging.getLogger(f"{__name__}.SceneGraphGenerator")

    def generate_scene_graph(
        self,
        image: Union[str, np.ndarray, Image.Image],
        objects: List[Any],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate scene graph.

        Args:
            image: Input image
            objects: Detected objects
            relationships: Object relationships

        Returns:
            Scene graph
        """
        try:
            # Create nodes for objects
            nodes = []
            for idx, obj in enumerate(objects):
                nodes.append({
                    'id': idx,
                    'label': obj.label,
                    'confidence': obj.confidence,
                    'bbox': obj.bbox,
                    'attributes': obj.attributes
                })

            # Create edges for relationships
            edges = []
            for rel in relationships:
                # Find node IDs
                subject_id = next((i for i, obj in enumerate(objects) if obj.label == rel['subject']), None)
                object_id = next((i for i, obj in enumerate(objects) if obj.label == rel['object']), None)

                if subject_id is not None and object_id is not None:
                    edges.append({
                        'source': subject_id,
                        'target': object_id,
                        'relation': rel['relation'],
                        'confidence': rel.get('confidence', 1.0)
                    })

            scene_graph = {
                'nodes': nodes,
                'edges': edges,
                'num_nodes': len(nodes),
                'num_edges': len(edges)
            }

            self.logger.info(f"Generated scene graph: {len(nodes)} nodes, {len(edges)} edges")
            return scene_graph

        except Exception as e:
            self.logger.error(f"Error generating scene graph: {e}")
            raise


class AdvancedSceneAnalyzer:
    """
    Advanced scene analyzer using AI models for deep understanding.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize advanced scene analyzer.

        Args:
            api_key: API key for GPT-4 Vision
        """
        self.vision_model = GPT4VisionWrapper(api_key=api_key)
        self.logger = logging.getLogger(f"{__name__}.AdvancedSceneAnalyzer")

    def analyze_scene_deep(
        self,
        image: Union[str, np.ndarray, Image.Image]
    ) -> Dict[str, Any]:
        """
        Perform deep scene analysis using AI.

        Args:
            image: Input image

        Returns:
            Deep analysis results
        """
        try:
            # Load vision model
            if not self.vision_model.is_loaded:
                self.vision_model.load_model()

            # Craft comprehensive prompt
            prompt = """Analyze this image comprehensively and provide:
            1. Scene type and setting
            2. Main objects and their relationships
            3. Activities or actions happening
            4. Atmosphere and mood
            5. Notable details or context
            6. Estimated time of day (if outdoor)

            Provide a structured analysis."""

            # Get AI analysis
            result = self.vision_model.predict(
                image,
                prompt=prompt,
                max_tokens=500
            )

            return {
                'success': True,
                'analysis': result.get('description', ''),
                'processing_time_ms': result.get('processing_time_ms', 0),
                'model': 'gpt-4-vision'
            }

        except Exception as e:
            self.logger.error(f"Error in deep scene analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class SceneUnderstandingEngine:
    """
    Complete scene understanding engine combining all analyzers.
    """

    def __init__(
        self,
        scene_classifier: Optional[SceneClassifier] = None,
        context_analyzer: Optional[ContextAnalyzer] = None,
        relationship_detector: Optional[RelationshipDetector] = None,
        activity_recognizer: Optional[ActivityRecognizer] = None,
        scene_graph_generator: Optional[SceneGraphGenerator] = None
    ):
        """
        Initialize scene understanding engine.

        Args:
            scene_classifier: Scene classifier instance
            context_analyzer: Context analyzer instance
            relationship_detector: Relationship detector instance
            activity_recognizer: Activity recognizer instance
            scene_graph_generator: Scene graph generator instance
        """
        self.scene_classifier = scene_classifier or SceneClassifier()
        self.context_analyzer = context_analyzer or ContextAnalyzer()
        self.relationship_detector = relationship_detector or RelationshipDetector()
        self.activity_recognizer = activity_recognizer or ActivityRecognizer()
        self.scene_graph_generator = scene_graph_generator or SceneGraphGenerator()
        self.logger = logging.getLogger(f"{__name__}.SceneUnderstandingEngine")

    def understand_scene(
        self,
        image: Union[str, np.ndarray, Image.Image],
        include_scene_graph: bool = True,
        include_activities: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete scene understanding.

        Args:
            image: Input image
            include_scene_graph: Whether to generate scene graph
            include_activities: Whether to recognize activities

        Returns:
            Complete scene understanding results
        """
        try:
            self.logger.info("Starting comprehensive scene understanding...")

            # Analyze context
            context = self.context_analyzer.analyze_context(image)

            # Detect additional relationships
            objects = context.get('objects', [])
            if objects:
                # Convert dict objects back to detection objects
                from .detection import DetectionResult
                detection_objects = [
                    DetectionResult(
                        label=obj['label'],
                        confidence=obj['confidence'],
                        bbox=obj['bbox'],
                        class_id=obj.get('class_id')
                    )
                    for obj in objects
                ]

                relationships = self.relationship_detector.detect_relationships(detection_objects)
            else:
                relationships = []

            # Recognize activities
            activities = None
            if include_activities:
                activities = self.activity_recognizer.recognize_activity(
                    image,
                    detection_objects if objects else None
                )

            # Generate scene graph
            scene_graph = None
            if include_scene_graph and objects:
                scene_graph = self.scene_graph_generator.generate_scene_graph(
                    image,
                    detection_objects,
                    relationships
                )

            # Compile results
            understanding = {
                'context': context,
                'relationships': relationships,
                'activities': activities,
                'scene_graph': scene_graph,
                'summary': self._generate_understanding_summary(context, relationships, activities)
            }

            self.logger.info("Scene understanding completed successfully")
            return understanding

        except Exception as e:
            self.logger.error(f"Error understanding scene: {e}")
            raise

    def _generate_understanding_summary(
        self,
        context: Dict[str, Any],
        relationships: List[Dict[str, Any]],
        activities: Optional[Dict[str, Any]]
    ) -> str:
        """Generate human-readable summary of scene understanding."""
        summary_parts = []

        # Add context summary
        if 'context_summary' in context:
            summary_parts.append(context['context_summary'])

        # Add relationships
        if relationships:
            summary_parts.append(f"{len(relationships)} object relationships detected")

        # Add activities
        if activities and activities.get('activities'):
            activity_list = activities['activities']
            summary_parts.append(f"Activities: {', '.join(activity_list)}")

        return ". ".join(summary_parts) + "."


# Global instances
scene_understanding_engine = SceneUnderstandingEngine()
