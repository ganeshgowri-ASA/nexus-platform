"""
Image analysis service - orchestrates different providers
"""
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
from sqlalchemy.orm import Session

from modules.image_recognition.models.database import (
    ImageAnalysis, DetectedObject, DetectedFace, ImageLabel, DetectedScene,
    AnalysisStatus, AnalysisType
)
from modules.image_recognition.services.google_vision_service import GoogleVisionService
from modules.image_recognition.services.aws_rekognition_service import AWSRekognitionService


class AnalysisService:
    """Service for orchestrating image analysis"""

    def __init__(self, db: Session):
        self.db = db
        self.google_vision = GoogleVisionService()
        self.aws_rekognition = AWSRekognitionService()

    def create_analysis(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        analysis_type: str = "object_detection",
        provider: str = "google_vision"
    ) -> ImageAnalysis:
        """Create a new analysis record"""

        # Calculate image hash for duplicate detection
        image_hash = self._calculate_image_hash(image_path, image_url)

        analysis = ImageAnalysis(
            image_path=image_path,
            image_url=image_url,
            image_hash=image_hash,
            analysis_type=AnalysisType(analysis_type),
            provider=provider,
            status=AnalysisStatus.PENDING
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return analysis

    def process_analysis(self, analysis_id: int) -> ImageAnalysis:
        """Process an image analysis"""
        analysis = self.db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()

        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        try:
            # Update status to processing
            analysis.status = AnalysisStatus.PROCESSING
            self.db.commit()

            # Route to appropriate provider and analysis type
            if analysis.provider == "google_vision":
                result = self._process_google_vision(analysis)
            elif analysis.provider == "aws_rekognition":
                result = self._process_aws_rekognition(analysis)
            else:
                raise ValueError(f"Unknown provider: {analysis.provider}")

            # Store results
            analysis.results = result.get("raw_response", {})
            analysis.status = AnalysisStatus.COMPLETED
            analysis.processed_at = datetime.utcnow()

            # Store parsed results in related tables
            self._store_parsed_results(analysis, result)

            self.db.commit()
            self.db.refresh(analysis)

        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            analysis.retry_count += 1
            self.db.commit()
            raise

        return analysis

    def _process_google_vision(self, analysis: ImageAnalysis) -> Dict[str, Any]:
        """Process analysis using Google Vision"""
        service = self.google_vision

        if analysis.analysis_type == AnalysisType.OBJECT_DETECTION:
            return service.detect_objects(analysis.image_path, analysis.image_url)
        elif analysis.analysis_type == AnalysisType.IMAGE_CLASSIFICATION:
            return service.classify_image(analysis.image_path, analysis.image_url)
        elif analysis.analysis_type == AnalysisType.FACE_DETECTION:
            return service.detect_faces(analysis.image_path, analysis.image_url)
        elif analysis.analysis_type == AnalysisType.SCENE_RECOGNITION:
            return service.recognize_scene(analysis.image_path, analysis.image_url)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis.analysis_type}")

    def _process_aws_rekognition(self, analysis: ImageAnalysis) -> Dict[str, Any]:
        """Process analysis using AWS Rekognition"""
        service = self.aws_rekognition

        if analysis.analysis_type == AnalysisType.OBJECT_DETECTION:
            return service.detect_objects(analysis.image_path, analysis.image_url)
        elif analysis.analysis_type == AnalysisType.IMAGE_CLASSIFICATION:
            return service.classify_image(analysis.image_path, analysis.image_url)
        elif analysis.analysis_type == AnalysisType.FACE_DETECTION:
            return service.detect_faces(analysis.image_path, analysis.image_url)
        elif analysis.analysis_type == AnalysisType.SCENE_RECOGNITION:
            return service.recognize_scene(analysis.image_path, analysis.image_url)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis.analysis_type}")

    def _store_parsed_results(self, analysis: ImageAnalysis, result: Dict[str, Any]):
        """Store parsed results in related tables"""

        # Store detected objects
        if "objects" in result:
            avg_confidence = 0
            for obj_data in result["objects"]:
                bbox = obj_data.get("bbox")
                obj = DetectedObject(
                    analysis_id=analysis.id,
                    name=obj_data["name"],
                    confidence=obj_data["confidence"],
                    bbox_x=bbox["x"] if bbox else None,
                    bbox_y=bbox["y"] if bbox else None,
                    bbox_width=bbox["width"] if bbox else None,
                    bbox_height=bbox["height"] if bbox else None,
                    attributes=obj_data.get("attributes")
                )
                self.db.add(obj)
                avg_confidence += obj_data["confidence"]

            if result["objects"]:
                analysis.confidence_score = avg_confidence / len(result["objects"])

        # Store detected faces
        if "faces" in result:
            avg_confidence = 0
            for face_data in result["faces"]:
                bbox = face_data.get("bbox")
                age_range = face_data.get("age_range", {})
                quality = face_data.get("quality", {})

                face = DetectedFace(
                    analysis_id=analysis.id,
                    confidence=face_data["confidence"],
                    bbox_x=bbox["x"] if bbox else None,
                    bbox_y=bbox["y"] if bbox else None,
                    bbox_width=bbox["width"] if bbox else None,
                    bbox_height=bbox["height"] if bbox else None,
                    age_range_low=age_range.get("low"),
                    age_range_high=age_range.get("high"),
                    gender=face_data.get("gender"),
                    emotions=face_data.get("emotions"),
                    brightness=quality.get("brightness"),
                    sharpness=quality.get("sharpness"),
                    attributes=face_data.get("attributes")
                )
                self.db.add(face)
                avg_confidence += face_data["confidence"]

            if result["faces"]:
                analysis.confidence_score = avg_confidence / len(result["faces"])

        # Store image labels
        if "labels" in result:
            avg_confidence = 0
            for label_data in result["labels"]:
                label = ImageLabel(
                    analysis_id=analysis.id,
                    name=label_data["name"],
                    confidence=label_data["confidence"],
                    category=label_data.get("category")
                )
                self.db.add(label)
                avg_confidence += label_data["confidence"]

            if result["labels"]:
                analysis.confidence_score = avg_confidence / len(result["labels"])

        # Store detected scenes
        if "scenes" in result:
            avg_confidence = 0
            for scene_data in result["scenes"]:
                scene = DetectedScene(
                    analysis_id=analysis.id,
                    scene_type=scene_data.get("name", scene_data.get("scene_type", "unknown")),
                    confidence=scene_data["confidence"],
                    attributes=scene_data.get("attributes")
                )
                self.db.add(scene)
                avg_confidence += scene_data["confidence"]

            if result["scenes"]:
                analysis.confidence_score = avg_confidence / len(result["scenes"])

    def get_analysis(self, analysis_id: int) -> Optional[ImageAnalysis]:
        """Get analysis by ID"""
        return self.db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()

    def list_analyses(self, skip: int = 0, limit: int = 100) -> list:
        """List all analyses"""
        return self.db.query(ImageAnalysis).offset(skip).limit(limit).all()

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and statistics"""
        from sqlalchemy import func

        total_analyses = self.db.query(func.count(ImageAnalysis.id)).scalar()

        # Analyses by type
        analyses_by_type = dict(
            self.db.query(
                ImageAnalysis.analysis_type,
                func.count(ImageAnalysis.id)
            ).group_by(ImageAnalysis.analysis_type).all()
        )

        # Analyses by status
        analyses_by_status = dict(
            self.db.query(
                ImageAnalysis.status,
                func.count(ImageAnalysis.id)
            ).group_by(ImageAnalysis.status).all()
        )

        # Average confidence
        avg_confidence = self.db.query(
            func.avg(ImageAnalysis.confidence_score)
        ).filter(ImageAnalysis.confidence_score.isnot(None)).scalar() or 0

        # Most detected objects
        most_detected_objects = self.db.query(
            DetectedObject.name,
            func.count(DetectedObject.id).label('count'),
            func.avg(DetectedObject.confidence).label('avg_confidence')
        ).group_by(DetectedObject.name).order_by(func.count(DetectedObject.id).desc()).limit(10).all()

        # Most detected labels
        most_detected_labels = self.db.query(
            ImageLabel.name,
            func.count(ImageLabel.id).label('count'),
            func.avg(ImageLabel.confidence).label('avg_confidence')
        ).group_by(ImageLabel.name).order_by(func.count(ImageLabel.id).desc()).limit(10).all()

        return {
            "total_analyses": total_analyses,
            "analyses_by_type": {str(k): v for k, v in analyses_by_type.items()},
            "analyses_by_status": {str(k): v for k, v in analyses_by_status.items()},
            "average_confidence": float(avg_confidence),
            "most_detected_objects": [
                {"name": name, "count": count, "avg_confidence": float(avg_conf)}
                for name, count, avg_conf in most_detected_objects
            ],
            "most_detected_labels": [
                {"name": name, "count": count, "avg_confidence": float(avg_conf)}
                for name, count, avg_conf in most_detected_labels
            ]
        }

    @staticmethod
    def _calculate_image_hash(image_path: Optional[str] = None, image_url: Optional[str] = None) -> str:
        """Calculate hash for image"""
        if image_path:
            with open(image_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        elif image_url:
            return hashlib.sha256(image_url.encode()).hexdigest()
        return ""
