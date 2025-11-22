"""
Custom Model Management Module

Provides comprehensive model management capabilities including:
- Custom model registration and versioning
- Model storage and retrieval
- Model metadata management
- Model deployment and serving
- Model performance tracking
- Model comparison and A/B testing
- Model archival and cleanup

Integrates with NEXUS database and storage for persistence.
"""

import logging
import os
import json
import shutil
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ModelVersion:
    """
    Represents a model version with metadata.
    """

    def __init__(
        self,
        model_id: str,
        version: str,
        model_path: str,
        model_type: str,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize model version.

        Args:
            model_id: Unique model identifier
            version: Version string
            model_path: Path to model file
            model_type: Type of model
            created_at: Creation timestamp
            metadata: Additional metadata
        """
        self.model_id = model_id
        self.version = version
        self.model_path = model_path
        self.model_type = model_type
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate model file checksum."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
            return ""
        except Exception:
            return ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'model_id': self.model_id,
            'version': self.version,
            'model_path': self.model_path,
            'model_type': self.model_type,
            'created_at': self.created_at.isoformat(),
            'checksum': self.checksum,
            'metadata': self.metadata
        }

    def __repr__(self) -> str:
        return f"<ModelVersion(id={self.model_id}, version={self.version})>"


class ModelRegistry:
    """
    Registry for managing custom models.
    """

    def __init__(self, registry_path: str):
        """
        Initialize model registry.

        Args:
            registry_path: Path to registry directory
        """
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.registry_path / "registry_index.json"
        self.models: Dict[str, Dict[str, ModelVersion]] = {}
        self.logger = logging.getLogger(f"{__name__}.ModelRegistry")
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    data = json.load(f)

                for model_id, versions_data in data.items():
                    self.models[model_id] = {}
                    for version, version_data in versions_data.items():
                        version_data['created_at'] = datetime.fromisoformat(version_data['created_at'])
                        self.models[model_id][version] = ModelVersion(**version_data)

                self.logger.info(f"Loaded registry with {len(self.models)} models")
        except Exception as e:
            self.logger.error(f"Error loading registry: {e}")

    def _save_registry(self) -> None:
        """Save registry to disk."""
        try:
            data = {}
            for model_id, versions in self.models.items():
                data[model_id] = {}
                for version, model_version in versions.items():
                    data[model_id][version] = model_version.to_dict()

            with open(self.index_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.info("Registry saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving registry: {e}")

    def register_model(
        self,
        model_id: str,
        version: str,
        model_path: str,
        model_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        copy_model: bool = True
    ) -> ModelVersion:
        """
        Register a new model or version.

        Args:
            model_id: Unique model identifier
            version: Version string
            model_path: Path to model file
            model_type: Type of model
            metadata: Additional metadata
            copy_model: Whether to copy model to registry

        Returns:
            Model version object
        """
        try:
            # Create model directory
            model_dir = self.registry_path / model_id
            model_dir.mkdir(exist_ok=True)

            # Copy model if requested
            if copy_model:
                model_filename = f"{model_id}_v{version}{Path(model_path).suffix}"
                dest_path = model_dir / model_filename
                shutil.copy2(model_path, dest_path)
                final_model_path = str(dest_path)
            else:
                final_model_path = model_path

            # Create model version
            model_version = ModelVersion(
                model_id=model_id,
                version=version,
                model_path=final_model_path,
                model_type=model_type,
                metadata=metadata
            )

            # Add to registry
            if model_id not in self.models:
                self.models[model_id] = {}

            self.models[model_id][version] = model_version

            # Save registry
            self._save_registry()

            self.logger.info(f"Registered model: {model_id} v{version}")
            return model_version

        except Exception as e:
            self.logger.error(f"Error registering model: {e}")
            raise

    def get_model(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> Optional[ModelVersion]:
        """
        Get model by ID and version.

        Args:
            model_id: Model identifier
            version: Version string (latest if not specified)

        Returns:
            Model version object or None
        """
        if model_id not in self.models:
            return None

        if version:
            return self.models[model_id].get(version)
        else:
            # Return latest version
            versions = sorted(
                self.models[model_id].items(),
                key=lambda x: x[1].created_at,
                reverse=True
            )
            return versions[0][1] if versions else None

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all registered models.

        Returns:
            List of model information dictionaries
        """
        models_list = []
        for model_id, versions in self.models.items():
            latest_version = max(versions.values(), key=lambda v: v.created_at)
            models_list.append({
                'model_id': model_id,
                'latest_version': latest_version.version,
                'model_type': latest_version.model_type,
                'num_versions': len(versions),
                'created_at': latest_version.created_at.isoformat()
            })

        return models_list

    def list_versions(self, model_id: str) -> List[str]:
        """
        List all versions of a model.

        Args:
            model_id: Model identifier

        Returns:
            List of version strings
        """
        if model_id in self.models:
            return sorted(self.models[model_id].keys())
        return []

    def delete_model(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Delete model or specific version.

        Args:
            model_id: Model identifier
            version: Version to delete (all if not specified)

        Returns:
            True if successful
        """
        try:
            if model_id not in self.models:
                return False

            if version:
                # Delete specific version
                if version in self.models[model_id]:
                    model_version = self.models[model_id][version]
                    # Delete model file
                    if os.path.exists(model_version.model_path):
                        os.remove(model_version.model_path)
                    # Remove from registry
                    del self.models[model_id][version]
                    # If no versions left, remove model entry
                    if not self.models[model_id]:
                        del self.models[model_id]
            else:
                # Delete all versions
                for model_version in self.models[model_id].values():
                    if os.path.exists(model_version.model_path):
                        os.remove(model_version.model_path)
                # Remove from registry
                del self.models[model_id]

            # Save registry
            self._save_registry()

            self.logger.info(f"Deleted model: {model_id} {f'v{version}' if version else '(all versions)'}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting model: {e}")
            return False


class ModelDeploymentManager:
    """
    Manages model deployment and serving.
    """

    def __init__(self, registry: ModelRegistry):
        """
        Initialize deployment manager.

        Args:
            registry: Model registry instance
        """
        self.registry = registry
        self.deployed_models: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.ModelDeploymentManager")

    def deploy_model(
        self,
        model_id: str,
        version: Optional[str] = None,
        deployment_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Deploy a model for serving.

        Args:
            model_id: Model identifier
            version: Version to deploy (latest if not specified)
            deployment_name: Name for deployment (model_id if not specified)
            config: Deployment configuration

        Returns:
            True if successful
        """
        try:
            # Get model from registry
            model_version = self.registry.get_model(model_id, version)
            if not model_version:
                raise ValueError(f"Model not found: {model_id} v{version}")

            # Create deployment
            deployment_name = deployment_name or model_id
            self.deployed_models[deployment_name] = {
                'model_id': model_id,
                'version': model_version.version,
                'model_path': model_version.model_path,
                'model_type': model_version.model_type,
                'deployed_at': datetime.utcnow().isoformat(),
                'config': config or {},
                'status': 'active'
            }

            self.logger.info(f"Deployed model: {deployment_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error deploying model: {e}")
            return False

    def undeploy_model(self, deployment_name: str) -> bool:
        """
        Undeploy a model.

        Args:
            deployment_name: Deployment name

        Returns:
            True if successful
        """
        if deployment_name in self.deployed_models:
            del self.deployed_models[deployment_name]
            self.logger.info(f"Undeployed model: {deployment_name}")
            return True
        return False

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployed models."""
        return list(self.deployed_models.values())

    def get_deployment(self, deployment_name: str) -> Optional[Dict[str, Any]]:
        """Get deployment information."""
        return self.deployed_models.get(deployment_name)


class ModelPerformanceTracker:
    """
    Tracks model performance metrics.
    """

    def __init__(self):
        """Initialize performance tracker."""
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = logging.getLogger(f"{__name__}.ModelPerformanceTracker")

    def record_prediction(
        self,
        model_id: str,
        prediction_result: Dict[str, Any]
    ) -> None:
        """
        Record a prediction for performance tracking.

        Args:
            model_id: Model identifier
            prediction_result: Prediction result dictionary
        """
        if model_id not in self.metrics:
            self.metrics[model_id] = []

        self.metrics[model_id].append({
            'timestamp': datetime.utcnow().isoformat(),
            'processing_time_ms': prediction_result.get('processing_time_ms', 0),
            'confidence': prediction_result.get('predictions', [{}])[0].get('confidence', 0),
            'success': prediction_result.get('success', False)
        })

        # Keep only recent metrics (last 1000)
        if len(self.metrics[model_id]) > 1000:
            self.metrics[model_id] = self.metrics[model_id][-1000:]

    def get_performance_stats(self, model_id: str) -> Dict[str, Any]:
        """
        Get performance statistics for model.

        Args:
            model_id: Model identifier

        Returns:
            Performance statistics
        """
        if model_id not in self.metrics or not self.metrics[model_id]:
            return {}

        metrics = self.metrics[model_id]

        # Calculate statistics
        processing_times = [m['processing_time_ms'] for m in metrics]
        confidences = [m['confidence'] for m in metrics]
        successes = [m['success'] for m in metrics]

        return {
            'model_id': model_id,
            'total_predictions': len(metrics),
            'success_rate': sum(successes) / len(successes) if successes else 0,
            'avg_processing_time_ms': sum(processing_times) / len(processing_times) if processing_times else 0,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'min_processing_time_ms': min(processing_times) if processing_times else 0,
            'max_processing_time_ms': max(processing_times) if processing_times else 0
        }


class ModelComparator:
    """
    Compares performance of different models.
    """

    def __init__(self, performance_tracker: ModelPerformanceTracker):
        """
        Initialize model comparator.

        Args:
            performance_tracker: Performance tracker instance
        """
        self.performance_tracker = performance_tracker
        self.logger = logging.getLogger(f"{__name__}.ModelComparator")

    def compare_models(
        self,
        model_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare performance of multiple models.

        Args:
            model_ids: List of model identifiers

        Returns:
            Comparison results
        """
        try:
            comparisons = {}

            for model_id in model_ids:
                stats = self.performance_tracker.get_performance_stats(model_id)
                if stats:
                    comparisons[model_id] = stats

            if not comparisons:
                return {'error': 'No performance data available'}

            # Determine best model
            best_model = max(
                comparisons.items(),
                key=lambda x: (x[1].get('success_rate', 0), -x[1].get('avg_processing_time_ms', float('inf')))
            )

            return {
                'comparisons': comparisons,
                'best_model': {
                    'model_id': best_model[0],
                    'stats': best_model[1]
                },
                'comparison_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error comparing models: {e}")
            return {'error': str(e)}


class ModelManager:
    """
    Complete model management system.
    """

    def __init__(self, registry_path: str):
        """
        Initialize model manager.

        Args:
            registry_path: Path to registry directory
        """
        self.registry = ModelRegistry(registry_path)
        self.deployment_manager = ModelDeploymentManager(self.registry)
        self.performance_tracker = ModelPerformanceTracker()
        self.comparator = ModelComparator(self.performance_tracker)
        self.logger = logging.getLogger(f"{__name__}.ModelManager")

    def register_model(
        self,
        model_id: str,
        version: str,
        model_path: str,
        model_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelVersion:
        """Register a new model."""
        return self.registry.register_model(
            model_id,
            version,
            model_path,
            model_type,
            metadata
        )

    def deploy_model(
        self,
        model_id: str,
        version: Optional[str] = None,
        deployment_name: Optional[str] = None
    ) -> bool:
        """Deploy a model."""
        return self.deployment_manager.deploy_model(
            model_id,
            version,
            deployment_name
        )

    def get_model_path(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> Optional[str]:
        """Get path to model file."""
        model_version = self.registry.get_model(model_id, version)
        return model_version.model_path if model_version else None

    def track_prediction(
        self,
        model_id: str,
        prediction_result: Dict[str, Any]
    ) -> None:
        """Track model prediction for performance monitoring."""
        self.performance_tracker.record_prediction(model_id, prediction_result)

    def get_model_stats(self, model_id: str) -> Dict[str, Any]:
        """Get model performance statistics."""
        return self.performance_tracker.get_performance_stats(model_id)

    def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple models."""
        return self.comparator.compare_models(model_ids)

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        return self.registry.list_models()

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployed models."""
        return self.deployment_manager.list_deployments()


# Global model manager instance (would be initialized with proper path in production)
# model_manager = ModelManager("/path/to/model/registry")
