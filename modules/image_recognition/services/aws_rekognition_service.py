"""
AWS Rekognition API integration service
"""
import os
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError
import requests


class AWSRekognitionService:
    """Service for AWS Rekognition API integration"""

    def __init__(self, region_name: Optional[str] = None):
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.client = boto3.client(
            'rekognition',
            region_name=self.region_name,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

    def _get_image_bytes(self, image_path: str = None, image_url: str = None) -> bytes:
        """Get image bytes from path or URL"""
        if image_path:
            with open(image_path, "rb") as image_file:
                return image_file.read()
        elif image_url:
            response = requests.get(image_url)
            response.raise_for_status()
            return response.content
        else:
            raise ValueError("Either image_path or image_url must be provided")

    def detect_objects(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Detect objects and instances in an image
        """
        image_bytes = self._get_image_bytes(image_path, image_url)

        try:
            response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=50,
                MinConfidence=70,
                Features=['GENERAL_LABELS'],
                Settings={
                    'GeneralLabels': {
                        'LabelInclusionFilters': [],
                        'LabelExclusionFilters': []
                    }
                }
            )

            return self._parse_object_detection(response)

        except ClientError as e:
            raise Exception(f"AWS Rekognition error: {str(e)}")

    def classify_image(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Classify image with labels
        """
        image_bytes = self._get_image_bytes(image_path, image_url)

        try:
            response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=20,
                MinConfidence=60
            )

            return self._parse_image_classification(response)

        except ClientError as e:
            raise Exception(f"AWS Rekognition error: {str(e)}")

    def detect_faces(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Detect faces and analyze facial attributes
        """
        image_bytes = self._get_image_bytes(image_path, image_url)

        try:
            response = self.client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )

            return self._parse_face_detection(response)

        except ClientError as e:
            raise Exception(f"AWS Rekognition error: {str(e)}")

    def recognize_scene(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Recognize scene and context in an image
        """
        image_bytes = self._get_image_bytes(image_path, image_url)

        try:
            # Detect labels for scene context
            labels_response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=20,
                MinConfidence=70
            )

            # Try to detect text for additional context
            text_response = self.client.detect_text(
                Image={'Bytes': image_bytes}
            )

            return self._parse_scene_recognition(labels_response, text_response)

        except ClientError as e:
            raise Exception(f"AWS Rekognition error: {str(e)}")

    def detect_moderation(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Detect inappropriate or unsafe content
        """
        image_bytes = self._get_image_bytes(image_path, image_url)

        try:
            response = self.client.detect_moderation_labels(
                Image={'Bytes': image_bytes},
                MinConfidence=60
            )

            return {
                "moderation_labels": [
                    {
                        "name": label["Name"],
                        "confidence": label["Confidence"],
                        "parent_name": label.get("ParentName", "")
                    }
                    for label in response.get("ModerationLabels", [])
                ],
                "raw_response": response
            }

        except ClientError as e:
            raise Exception(f"AWS Rekognition error: {str(e)}")

    def _parse_object_detection(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse object detection results"""
        objects = []

        for label in response.get("Labels", []):
            # Get instances with bounding boxes
            instances = label.get("Instances", [])

            if instances:
                for instance in instances:
                    bbox = instance.get("BoundingBox", {})
                    objects.append({
                        "name": label.get("Name", ""),
                        "confidence": label.get("Confidence", 0) / 100.0,  # Normalize to 0-1
                        "bbox": {
                            "x": bbox.get("Left", 0),
                            "y": bbox.get("Top", 0),
                            "width": bbox.get("Width", 0),
                            "height": bbox.get("Height", 0)
                        }
                    })
            else:
                # Label without specific instances
                objects.append({
                    "name": label.get("Name", ""),
                    "confidence": label.get("Confidence", 0) / 100.0,
                    "bbox": None
                })

        return {
            "objects": objects,
            "raw_response": response
        }

    def _parse_image_classification(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse image classification results"""
        labels = []

        for label in response.get("Labels", []):
            categories = [cat["Name"] for cat in label.get("Categories", [])]
            labels.append({
                "name": label.get("Name", ""),
                "confidence": label.get("Confidence", 0) / 100.0,
                "category": categories[0] if categories else None
            })

        return {
            "labels": labels,
            "raw_response": response
        }

    def _parse_face_detection(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse face detection results"""
        faces = []

        for face_detail in response.get("FaceDetails", []):
            bbox = face_detail.get("BoundingBox", {})

            # Parse emotions
            emotions = {}
            for emotion in face_detail.get("Emotions", []):
                emotions[emotion["Type"].lower()] = emotion["Confidence"] / 100.0

            # Parse age range
            age_range = face_detail.get("AgeRange", {})

            # Parse attributes
            attributes = {
                "smile": face_detail.get("Smile", {}).get("Value", False),
                "eyeglasses": face_detail.get("Eyeglasses", {}).get("Value", False),
                "sunglasses": face_detail.get("Sunglasses", {}).get("Value", False),
                "beard": face_detail.get("Beard", {}).get("Value", False),
                "mustache": face_detail.get("Mustache", {}).get("Value", False),
                "eyes_open": face_detail.get("EyesOpen", {}).get("Value", False),
                "mouth_open": face_detail.get("MouthOpen", {}).get("Value", False)
            }

            faces.append({
                "confidence": face_detail.get("Confidence", 0) / 100.0,
                "bbox": {
                    "x": bbox.get("Left", 0),
                    "y": bbox.get("Top", 0),
                    "width": bbox.get("Width", 0),
                    "height": bbox.get("Height", 0)
                },
                "age_range": {
                    "low": age_range.get("Low", 0),
                    "high": age_range.get("High", 0)
                },
                "gender": face_detail.get("Gender", {}).get("Value", ""),
                "emotions": emotions,
                "attributes": attributes,
                "quality": {
                    "brightness": face_detail.get("Quality", {}).get("Brightness", 0),
                    "sharpness": face_detail.get("Quality", {}).get("Sharpness", 0)
                }
            })

        return {
            "faces": faces,
            "raw_response": response
        }

    def _parse_scene_recognition(self, labels_response: Dict[str, Any], text_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse scene recognition results"""
        scenes = []

        # Parse labels for scene context
        for label in labels_response.get("Labels", []):
            categories = [cat["Name"] for cat in label.get("Categories", [])]

            scenes.append({
                "scene_type": categories[0] if categories else "general",
                "name": label.get("Name", ""),
                "confidence": label.get("Confidence", 0) / 100.0,
                "attributes": {
                    "categories": categories
                }
            })

        # Add detected text as scene context
        detected_texts = []
        for text_detection in text_response.get("TextDetections", []):
            if text_detection.get("Type") == "LINE":
                detected_texts.append(text_detection.get("DetectedText", ""))

        return {
            "scenes": scenes,
            "detected_text": detected_texts,
            "raw_response": {
                "labels": labels_response,
                "text": text_response
            }
        }
