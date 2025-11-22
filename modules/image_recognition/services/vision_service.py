"""
Computer Vision Service - Integration with Google Vision and AWS Rekognition
"""
import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class GoogleVisionService:
    """Google Cloud Vision API integration"""

    def __init__(self, api_key: Optional[str] = None, credentials_path: Optional[str] = None):
        self.api_key = api_key
        self.credentials_path = credentials_path
        self._client = None

    def _get_client(self):
        """Lazy load Google Vision client"""
        if self._client is None:
            try:
                from google.cloud import vision
                if self.credentials_path:
                    import os
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                self._client = vision.ImageAnnotatorClient()
            except ImportError:
                logger.error("google-cloud-vision not installed")
                raise
        return self._client

    async def detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect objects in image using Google Vision"""
        try:
            from google.cloud import vision

            client = self._get_client()
            image = vision.Image(content=image_data)

            response = client.object_localization(image=image)
            objects = response.localized_object_annotations

            results = []
            for obj in objects:
                vertices = obj.bounding_poly.normalized_vertices
                results.append({
                    "label": obj.name,
                    "confidence": obj.score,
                    "bbox": {
                        "x": vertices[0].x,
                        "y": vertices[0].y,
                        "width": vertices[2].x - vertices[0].x,
                        "height": vertices[2].y - vertices[0].y
                    }
                })

            return results

        except Exception as e:
            logger.error(f"Google Vision object detection error: {e}")
            raise

    async def classify_image(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Classify image using Google Vision"""
        try:
            from google.cloud import vision

            client = self._get_client()
            image = vision.Image(content=image_data)

            response = client.label_detection(image=image)
            labels = response.label_annotations

            results = []
            for label in labels:
                results.append({
                    "label": label.description,
                    "confidence": label.score,
                    "topicality": label.topicality
                })

            return results

        except Exception as e:
            logger.error(f"Google Vision classification error: {e}")
            raise

    async def detect_faces(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect faces using Google Vision"""
        try:
            from google.cloud import vision

            client = self._get_client()
            image = vision.Image(content=image_data)

            response = client.face_detection(image=image)
            faces = response.face_annotations

            results = []
            for face in faces:
                vertices = face.bounding_poly.vertices
                results.append({
                    "confidence": face.detection_confidence,
                    "bbox": {
                        "x": vertices[0].x,
                        "y": vertices[0].y,
                        "width": vertices[2].x - vertices[0].x,
                        "height": vertices[2].y - vertices[0].y
                    },
                    "emotions": {
                        "joy": self._likelihood_to_score(face.joy_likelihood),
                        "sorrow": self._likelihood_to_score(face.sorrow_likelihood),
                        "anger": self._likelihood_to_score(face.anger_likelihood),
                        "surprise": self._likelihood_to_score(face.surprise_likelihood)
                    },
                    "pose": {
                        "roll": face.roll_angle,
                        "pan": face.pan_angle,
                        "tilt": face.tilt_angle
                    }
                })

            return results

        except Exception as e:
            logger.error(f"Google Vision face detection error: {e}")
            raise

    @staticmethod
    def _likelihood_to_score(likelihood) -> float:
        """Convert Google Vision likelihood to confidence score"""
        likelihood_map = {
            0: 0.0,  # UNKNOWN
            1: 0.1,  # VERY_UNLIKELY
            2: 0.3,  # UNLIKELY
            3: 0.5,  # POSSIBLE
            4: 0.7,  # LIKELY
            5: 0.9   # VERY_LIKELY
        }
        return likelihood_map.get(likelihood, 0.0)


class AWSRekognitionService:
    """AWS Rekognition API integration"""

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, region: str = "us-east-1"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self._client = None

    def _get_client(self):
        """Lazy load AWS Rekognition client"""
        if self._client is None:
            try:
                import boto3
                if self.access_key and self.secret_key:
                    self._client = boto3.client(
                        'rekognition',
                        aws_access_key_id=self.access_key,
                        aws_secret_access_key=self.secret_key,
                        region_name=self.region
                    )
                else:
                    self._client = boto3.client('rekognition', region_name=self.region)
            except ImportError:
                logger.error("boto3 not installed")
                raise
        return self._client

    async def detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect objects using AWS Rekognition"""
        try:
            client = self._get_client()

            response = client.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=100,
                MinConfidence=50
            )

            results = []
            for label in response['Labels']:
                for instance in label.get('Instances', [{}]):
                    bbox = instance.get('BoundingBox', {})
                    results.append({
                        "label": label['Name'],
                        "confidence": label['Confidence'] / 100.0,
                        "bbox": {
                            "x": bbox.get('Left', 0),
                            "y": bbox.get('Top', 0),
                            "width": bbox.get('Width', 0),
                            "height": bbox.get('Height', 0)
                        } if bbox else None,
                        "category": label.get('Categories', [{}])[0].get('Name') if label.get('Categories') else None
                    })

                # Add labels without instances
                if not label.get('Instances'):
                    results.append({
                        "label": label['Name'],
                        "confidence": label['Confidence'] / 100.0,
                        "bbox": None,
                        "category": label.get('Categories', [{}])[0].get('Name') if label.get('Categories') else None
                    })

            return results

        except Exception as e:
            logger.error(f"AWS Rekognition object detection error: {e}")
            raise

    async def classify_image(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Classify image using AWS Rekognition"""
        try:
            client = self._get_client()

            response = client.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=50,
                MinConfidence=50
            )

            results = []
            for label in response['Labels']:
                results.append({
                    "label": label['Name'],
                    "confidence": label['Confidence'] / 100.0,
                    "parents": [p['Name'] for p in label.get('Parents', [])]
                })

            return results

        except Exception as e:
            logger.error(f"AWS Rekognition classification error: {e}")
            raise

    async def detect_faces(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect faces using AWS Rekognition"""
        try:
            client = self._get_client()

            response = client.detect_faces(
                Image={'Bytes': image_data},
                Attributes=['ALL']
            )

            results = []
            for face in response['FaceDetails']:
                bbox = face['BoundingBox']

                # Extract emotions
                emotions = {}
                for emotion in face.get('Emotions', []):
                    emotions[emotion['Type'].lower()] = emotion['Confidence'] / 100.0

                results.append({
                    "confidence": face['Confidence'] / 100.0,
                    "bbox": {
                        "x": bbox['Left'],
                        "y": bbox['Top'],
                        "width": bbox['Width'],
                        "height": bbox['Height']
                    },
                    "age_range": {
                        "low": face.get('AgeRange', {}).get('Low'),
                        "high": face.get('AgeRange', {}).get('High')
                    },
                    "gender": face.get('Gender', {}).get('Value'),
                    "emotions": emotions,
                    "has_smile": face.get('Smile', {}).get('Value'),
                    "has_eyeglasses": face.get('Eyeglasses', {}).get('Value'),
                    "has_sunglasses": face.get('Sunglasses', {}).get('Value'),
                    "has_beard": face.get('Beard', {}).get('Value'),
                    "pose": {
                        "roll": face.get('Pose', {}).get('Roll'),
                        "yaw": face.get('Pose', {}).get('Yaw'),
                        "pitch": face.get('Pose', {}).get('Pitch')
                    }
                })

            return results

        except Exception as e:
            logger.error(f"AWS Rekognition face detection error: {e}")
            raise

    async def recognize_scene(self, image_data: bytes) -> Dict[str, Any]:
        """Recognize scene using AWS Rekognition"""
        try:
            client = self._get_client()

            response = client.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=20,
                MinConfidence=50
            )

            # Extract scene-related labels
            scenes = []
            for label in response['Labels']:
                if label.get('Categories') and any(
                    cat.get('Name') in ['Scene', 'Environment']
                    for cat in label.get('Categories', [])
                ):
                    scenes.append({
                        "scene": label['Name'],
                        "confidence": label['Confidence'] / 100.0
                    })

            return {
                "scenes": scenes,
                "primary_scene": scenes[0] if scenes else None
            }

        except Exception as e:
            logger.error(f"AWS Rekognition scene recognition error: {e}")
            raise


class ImageProcessor:
    """Image processing utilities"""

    @staticmethod
    def load_image(image_data: bytes) -> Tuple[Image.Image, Dict[str, Any]]:
        """Load and get image metadata"""
        try:
            image = Image.open(io.BytesIO(image_data))

            metadata = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": len(image_data)
            }

            return image, metadata

        except Exception as e:
            logger.error(f"Image loading error: {e}")
            raise

    @staticmethod
    def resize_image(image: Image.Image, max_size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image

    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = "JPEG") -> bytes:
        """Convert PIL Image to bytes"""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    @staticmethod
    def base64_to_bytes(base64_string: str) -> bytes:
        """Convert base64 string to bytes"""
        return base64.b64decode(base64_string)

    @staticmethod
    def bytes_to_base64(image_bytes: bytes) -> str:
        """Convert bytes to base64 string"""
        return base64.b64encode(image_bytes).decode('utf-8')
