"""
Google Cloud Vision API integration service
"""
import os
from typing import Dict, List, Any, Optional
import base64
import requests
from io import BytesIO


class GoogleVisionService:
    """Service for Google Cloud Vision API integration"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_VISION_API_KEY")
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"

    def _encode_image(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """Encode image for API request"""
        if image_url:
            return {"source": {"imageUri": image_url}}
        elif image_path:
            with open(image_path, "rb") as image_file:
                content = base64.b64encode(image_file.read()).decode("utf-8")
            return {"content": content}
        else:
            raise ValueError("Either image_path or image_url must be provided")

    def detect_objects(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Detect objects in an image
        """
        image_data = self._encode_image(image_path, image_url)

        request_body = {
            "requests": [
                {
                    "image": image_data,
                    "features": [
                        {"type": "OBJECT_LOCALIZATION", "maxResults": 50}
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}?key={self.api_key}",
            json=request_body
        )
        response.raise_for_status()

        result = response.json()
        return self._parse_object_detection(result)

    def classify_image(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Classify image with labels
        """
        image_data = self._encode_image(image_path, image_url)

        request_body = {
            "requests": [
                {
                    "image": image_data,
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 20},
                        {"type": "IMAGE_PROPERTIES"}
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}?key={self.api_key}",
            json=request_body
        )
        response.raise_for_status()

        result = response.json()
        return self._parse_image_classification(result)

    def detect_faces(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Detect faces in an image
        """
        image_data = self._encode_image(image_path, image_url)

        request_body = {
            "requests": [
                {
                    "image": image_data,
                    "features": [
                        {"type": "FACE_DETECTION", "maxResults": 50}
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}?key={self.api_key}",
            json=request_body
        )
        response.raise_for_status()

        result = response.json()
        return self._parse_face_detection(result)

    def recognize_scene(self, image_path: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        Recognize scene/landmarks in an image
        """
        image_data = self._encode_image(image_path, image_url)

        request_body = {
            "requests": [
                {
                    "image": image_data,
                    "features": [
                        {"type": "LANDMARK_DETECTION", "maxResults": 10},
                        {"type": "LABEL_DETECTION", "maxResults": 20},
                        {"type": "IMAGE_PROPERTIES"}
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}?key={self.api_key}",
            json=request_body
        )
        response.raise_for_status()

        result = response.json()
        return self._parse_scene_recognition(result)

    def _parse_object_detection(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse object detection results"""
        objects = []
        responses = result.get("responses", [])

        if responses and "localizedObjectAnnotations" in responses[0]:
            for obj in responses[0]["localizedObjectAnnotations"]:
                bbox = obj.get("boundingPoly", {}).get("normalizedVertices", [])
                if len(bbox) >= 2:
                    x = bbox[0].get("x", 0)
                    y = bbox[0].get("y", 0)
                    width = bbox[1].get("x", 0) - x
                    height = bbox[2].get("y", 0) - y if len(bbox) > 2 else 0
                else:
                    x = y = width = height = 0

                objects.append({
                    "name": obj.get("name", ""),
                    "confidence": obj.get("score", 0),
                    "bbox": {"x": x, "y": y, "width": width, "height": height}
                })

        return {
            "objects": objects,
            "raw_response": result
        }

    def _parse_image_classification(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse image classification results"""
        labels = []
        responses = result.get("responses", [])

        if responses and "labelAnnotations" in responses[0]:
            for label in responses[0]["labelAnnotations"]:
                labels.append({
                    "name": label.get("description", ""),
                    "confidence": label.get("score", 0)
                })

        return {
            "labels": labels,
            "raw_response": result
        }

    def _parse_face_detection(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse face detection results"""
        faces = []
        responses = result.get("responses", [])

        if responses and "faceAnnotations" in responses[0]:
            for face in responses[0]["faceAnnotations"]:
                bbox = face.get("boundingPoly", {}).get("vertices", [])
                if len(bbox) >= 2:
                    x = bbox[0].get("x", 0)
                    y = bbox[0].get("y", 0)
                    width = bbox[1].get("x", 0) - x
                    height = bbox[2].get("y", 0) - y if len(bbox) > 2 else 0
                else:
                    x = y = width = height = 0

                # Parse emotions
                emotions = {
                    "joy": self._likelihood_to_score(face.get("joyLikelihood")),
                    "sorrow": self._likelihood_to_score(face.get("sorrowLikelihood")),
                    "anger": self._likelihood_to_score(face.get("angerLikelihood")),
                    "surprise": self._likelihood_to_score(face.get("surpriseLikelihood"))
                }

                faces.append({
                    "confidence": face.get("detectionConfidence", 0),
                    "bbox": {"x": x, "y": y, "width": width, "height": height},
                    "emotions": emotions,
                    "attributes": {
                        "headwear": self._likelihood_to_score(face.get("headwearLikelihood")),
                        "blurred": self._likelihood_to_score(face.get("blurredLikelihood")),
                        "underExposed": self._likelihood_to_score(face.get("underExposedLikelihood"))
                    }
                })

        return {
            "faces": faces,
            "raw_response": result
        }

    def _parse_scene_recognition(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse scene recognition results"""
        scenes = []
        responses = result.get("responses", [])

        if responses:
            # Parse landmarks
            if "landmarkAnnotations" in responses[0]:
                for landmark in responses[0]["landmarkAnnotations"]:
                    scenes.append({
                        "scene_type": "landmark",
                        "name": landmark.get("description", ""),
                        "confidence": landmark.get("score", 0)
                    })

            # Parse general labels as scene indicators
            if "labelAnnotations" in responses[0]:
                for label in responses[0]["labelAnnotations"][:5]:  # Top 5 labels
                    scenes.append({
                        "scene_type": "general",
                        "name": label.get("description", ""),
                        "confidence": label.get("score", 0)
                    })

        return {
            "scenes": scenes,
            "raw_response": result
        }

    @staticmethod
    def _likelihood_to_score(likelihood: str) -> float:
        """Convert likelihood string to numeric score"""
        likelihood_map = {
            "VERY_UNLIKELY": 0.1,
            "UNLIKELY": 0.3,
            "POSSIBLE": 0.5,
            "LIKELY": 0.7,
            "VERY_LIKELY": 0.9,
            "UNKNOWN": 0.0
        }
        return likelihood_map.get(likelihood, 0.0)
