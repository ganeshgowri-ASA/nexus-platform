"""
Feature Extraction and Similarity Search Module

Provides comprehensive feature extraction capabilities including:
- Deep feature extraction from pre-trained models
- Image embeddings generation
- Similarity search and matching
- Visual search engine
- Feature-based clustering
- Duplicate detection
- Content-based image retrieval (CBIR)

Integrates with NEXUS database for efficient vector search.
"""

import logging
import time
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
from datetime import datetime

from .models import BaseModelWrapper, ModelFactory

logger = logging.getLogger(__name__)


class FeatureVector:
    """
    Represents an image feature vector with metadata.
    """

    def __init__(
        self,
        features: np.ndarray,
        image_id: Optional[str] = None,
        model_name: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize feature vector.

        Args:
            features: Feature vector as numpy array
            image_id: Associated image ID
            model_name: Model used for extraction
            metadata: Additional metadata
        """
        self.features = features
        self.image_id = image_id
        self.model_name = model_name
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.dimension = len(features)

    def normalize(self) -> 'FeatureVector':
        """Normalize feature vector to unit length."""
        norm = np.linalg.norm(self.features)
        if norm > 0:
            normalized_features = self.features / norm
        else:
            normalized_features = self.features

        return FeatureVector(
            features=normalized_features,
            image_id=self.image_id,
            model_name=self.model_name,
            metadata=self.metadata
        )

    def to_list(self) -> List[float]:
        """Convert to list."""
        return self.features.tolist()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'features': self.to_list(),
            'image_id': self.image_id,
            'model_name': self.model_name,
            'dimension': self.dimension,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return f"<FeatureVector(dim={self.dimension}, model={self.model_name})>"


class FeatureExtractor:
    """
    Extracts deep features from images using pre-trained models.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        layer: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize feature extractor.

        Args:
            model_type: Type of model to use
            layer: Specific layer to extract features from
            config: Extractor configuration
        """
        self.model_type = model_type
        self.layer = layer
        self.config = config or {}
        self.model = None
        self.feature_model = None
        self.is_loaded = False
        self.logger = logging.getLogger(f"{__name__}.FeatureExtractor")

    def load_model(self) -> bool:
        """Load feature extraction model."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            # Load base model
            if self.model_type.lower() == 'resnet50':
                base_model = keras.applications.ResNet50(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg'
                )
            elif self.model_type.lower() == 'vgg16':
                base_model = keras.applications.VGG16(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg'
                )
            elif self.model_type.lower() == 'inceptionv3':
                base_model = keras.applications.InceptionV3(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg'
                )
            elif self.model_type.lower() == 'efficientnet':
                base_model = keras.applications.EfficientNetB0(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg'
                )
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")

            # Extract features from specific layer if requested
            if self.layer:
                try:
                    output = base_model.get_layer(self.layer).output
                    self.feature_model = keras.Model(inputs=base_model.input, outputs=output)
                except:
                    self.logger.warning(f"Layer {self.layer} not found, using default output")
                    self.feature_model = base_model
            else:
                self.feature_model = base_model

            self.model = base_model
            self.is_loaded = True
            self.logger.info(f"Loaded {self.model_type} feature extractor")
            return True

        except ImportError:
            self.logger.error("TensorFlow not installed. Install with: pip install tensorflow")
            return False
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def extract(
        self,
        image: Union[str, np.ndarray, Image.Image],
        normalize: bool = True,
        image_id: Optional[str] = None
    ) -> FeatureVector:
        """
        Extract features from image.

        Args:
            image: Input image
            normalize: Whether to normalize features
            image_id: Optional image identifier

        Returns:
            Feature vector
        """
        if not self.is_loaded:
            self.load_model()

        try:
            import tensorflow as tf
            from tensorflow import keras

            # Load and preprocess image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Resize to model input size
            image = image.resize((224, 224))
            img_array = keras.preprocessing.image.img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)

            # Model-specific preprocessing
            if self.model_type.lower() == 'resnet50':
                from tensorflow.keras.applications.resnet50 import preprocess_input
            elif self.model_type.lower() == 'vgg16':
                from tensorflow.keras.applications.vgg16 import preprocess_input
            elif self.model_type.lower() == 'inceptionv3':
                from tensorflow.keras.applications.inception_v3 import preprocess_input
            elif self.model_type.lower() == 'efficientnet':
                from tensorflow.keras.applications.efficientnet import preprocess_input
            else:
                preprocess_input = lambda x: x / 255.0

            img_array = preprocess_input(img_array)

            # Extract features
            start_time = time.time()
            features = self.feature_model.predict(img_array, verbose=0)[0]
            extraction_time = (time.time() - start_time) * 1000

            # Create feature vector
            feature_vec = FeatureVector(
                features=features,
                image_id=image_id,
                model_name=self.model_type,
                metadata={
                    'extraction_time_ms': extraction_time,
                    'layer': self.layer or 'output'
                }
            )

            # Normalize if requested
            if normalize:
                feature_vec = feature_vec.normalize()

            self.logger.debug(f"Extracted {len(features)}-dim features in {extraction_time:.2f}ms")
            return feature_vec

        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            raise

    def extract_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[FeatureVector]:
        """
        Extract features from multiple images.

        Args:
            images: List of images
            normalize: Whether to normalize features
            batch_size: Batch size for processing

        Returns:
            List of feature vectors
        """
        feature_vectors = []

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            for image in batch:
                try:
                    features = self.extract(image, normalize=normalize)
                    feature_vectors.append(features)
                except Exception as e:
                    self.logger.error(f"Error extracting features from image: {e}")
                    continue

        return feature_vectors


class SimilaritySearchEngine:
    """
    Performs similarity search on image features.
    """

    def __init__(
        self,
        metric: str = "cosine",
        index_type: str = "flat"
    ):
        """
        Initialize similarity search engine.

        Args:
            metric: Distance metric (cosine, euclidean, manhattan)
            index_type: Index type for search (flat, approximate)
        """
        self.metric = metric
        self.index_type = index_type
        self.feature_database: List[FeatureVector] = []
        self.index = None
        self.logger = logging.getLogger(f"{__name__}.SimilaritySearchEngine")

    def add_features(
        self,
        features: Union[FeatureVector, List[FeatureVector]]
    ) -> None:
        """
        Add feature vectors to search database.

        Args:
            features: Feature vector(s) to add
        """
        if isinstance(features, FeatureVector):
            features = [features]

        self.feature_database.extend(features)
        self.logger.info(f"Added {len(features)} feature vectors to database")

        # Rebuild index if using approximate search
        if self.index_type == "approximate" and len(self.feature_database) > 100:
            self._build_approximate_index()

    def search(
        self,
        query_features: FeatureVector,
        top_k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar images.

        Args:
            query_features: Query feature vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of similar images with scores
        """
        if not self.feature_database:
            return []

        try:
            # Compute similarities
            similarities = []
            for idx, db_features in enumerate(self.feature_database):
                similarity = self._compute_similarity(
                    query_features.features,
                    db_features.features
                )

                if threshold is None or similarity >= threshold:
                    similarities.append({
                        'index': idx,
                        'image_id': db_features.image_id,
                        'similarity': float(similarity),
                        'distance': float(1.0 - similarity),
                        'metadata': db_features.metadata
                    })

            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)

            # Return top K
            results = similarities[:top_k]
            self.logger.info(f"Found {len(results)} similar images")
            return results

        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            raise

    def search_batch(
        self,
        query_features_list: List[FeatureVector],
        top_k: int = 10,
        threshold: Optional[float] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Search for multiple queries.

        Args:
            query_features_list: List of query feature vectors
            top_k: Number of results per query
            threshold: Minimum similarity threshold

        Returns:
            List of search results for each query
        """
        results = []
        for query_features in query_features_list:
            try:
                query_results = self.search(query_features, top_k, threshold)
                results.append(query_results)
            except Exception as e:
                self.logger.error(f"Error in batch search: {e}")
                results.append([])

        return results

    def _compute_similarity(
        self,
        features1: np.ndarray,
        features2: np.ndarray
    ) -> float:
        """Compute similarity between two feature vectors."""
        if self.metric == "cosine":
            # Cosine similarity
            dot_product = np.dot(features1, features2)
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        elif self.metric == "euclidean":
            # Euclidean distance (converted to similarity)
            distance = np.linalg.norm(features1 - features2)
            return 1.0 / (1.0 + distance)

        elif self.metric == "manhattan":
            # Manhattan distance (converted to similarity)
            distance = np.sum(np.abs(features1 - features2))
            return 1.0 / (1.0 + distance)

        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def _build_approximate_index(self) -> None:
        """Build approximate nearest neighbor index for faster search."""
        try:
            # This is a placeholder for integration with libraries like FAISS or Annoy
            self.logger.info("Building approximate index...")

            # For now, just log - in production, implement FAISS or similar
            self.logger.warning("Approximate indexing not yet implemented, using exact search")

        except Exception as e:
            self.logger.error(f"Error building index: {e}")

    def clear_database(self) -> None:
        """Clear the feature database."""
        self.feature_database.clear()
        self.index = None
        self.logger.info("Cleared feature database")

    def get_database_size(self) -> int:
        """Get number of vectors in database."""
        return len(self.feature_database)


class DuplicateDetector:
    """
    Detects duplicate or near-duplicate images.
    """

    def __init__(
        self,
        feature_extractor: FeatureExtractor,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize duplicate detector.

        Args:
            feature_extractor: Feature extractor to use
            similarity_threshold: Threshold for considering images as duplicates
        """
        self.feature_extractor = feature_extractor
        self.similarity_threshold = similarity_threshold
        self.search_engine = SimilaritySearchEngine(metric="cosine")
        self.logger = logging.getLogger(f"{__name__}.DuplicateDetector")

    def find_duplicates(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        image_ids: Optional[List[str]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Find duplicate images in a collection.

        Args:
            images: List of images to check
            image_ids: Optional list of image IDs

        Returns:
            List of duplicate groups
        """
        try:
            # Extract features for all images
            self.logger.info(f"Extracting features from {len(images)} images...")
            features_list = []

            for idx, image in enumerate(images):
                img_id = image_ids[idx] if image_ids else f"image_{idx}"
                features = self.feature_extractor.extract(image, normalize=True, image_id=img_id)
                features_list.append(features)

            # Find duplicates
            duplicate_groups = []
            processed = set()

            for idx, features in enumerate(features_list):
                if idx in processed:
                    continue

                # Add current features to search database temporarily
                temp_search = SimilaritySearchEngine(metric="cosine")
                temp_search.add_features(features_list)

                # Search for similar images
                similar = temp_search.search(
                    features,
                    top_k=len(features_list),
                    threshold=self.similarity_threshold
                )

                # Filter out self and create group
                duplicate_group = []
                for result in similar:
                    result_idx = result['index']
                    if result_idx != idx and result_idx not in processed:
                        duplicate_group.append({
                            'image_id': result['image_id'],
                            'index': result_idx,
                            'similarity': result['similarity']
                        })
                        processed.add(result_idx)

                if duplicate_group:
                    # Add the query image to the group
                    duplicate_group.insert(0, {
                        'image_id': features.image_id,
                        'index': idx,
                        'similarity': 1.0
                    })
                    duplicate_groups.append(duplicate_group)
                    processed.add(idx)

            self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
            return duplicate_groups

        except Exception as e:
            self.logger.error(f"Error finding duplicates: {e}")
            raise

    def is_duplicate(
        self,
        image1: Union[str, np.ndarray, Image.Image],
        image2: Union[str, np.ndarray, Image.Image]
    ) -> Tuple[bool, float]:
        """
        Check if two images are duplicates.

        Args:
            image1: First image
            image2: Second image

        Returns:
            Tuple of (is_duplicate, similarity_score)
        """
        try:
            # Extract features
            features1 = self.feature_extractor.extract(image1, normalize=True)
            features2 = self.feature_extractor.extract(image2, normalize=True)

            # Compute similarity
            similarity = np.dot(features1.features, features2.features)

            is_dup = similarity >= self.similarity_threshold

            return is_dup, float(similarity)

        except Exception as e:
            self.logger.error(f"Error checking duplicates: {e}")
            raise


class FeatureClustering:
    """
    Clusters images based on visual features.
    """

    def __init__(
        self,
        n_clusters: int = 10,
        method: str = "kmeans"
    ):
        """
        Initialize feature clustering.

        Args:
            n_clusters: Number of clusters
            method: Clustering method (kmeans, dbscan, hierarchical)
        """
        self.n_clusters = n_clusters
        self.method = method
        self.cluster_model = None
        self.cluster_centers = None
        self.logger = logging.getLogger(f"{__name__}.FeatureClustering")

    def fit(
        self,
        features_list: List[FeatureVector]
    ) -> None:
        """
        Fit clustering model on features.

        Args:
            features_list: List of feature vectors
        """
        try:
            from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering

            # Extract feature arrays
            features_array = np.array([f.features for f in features_list])

            self.logger.info(f"Clustering {len(features_list)} feature vectors...")

            if self.method == "kmeans":
                self.cluster_model = KMeans(
                    n_clusters=self.n_clusters,
                    random_state=42,
                    n_init=10
                )
                self.cluster_model.fit(features_array)
                self.cluster_centers = self.cluster_model.cluster_centers_

            elif self.method == "dbscan":
                self.cluster_model = DBSCAN(
                    eps=0.3,
                    min_samples=5,
                    metric='euclidean'
                )
                self.cluster_model.fit(features_array)

            elif self.method == "hierarchical":
                self.cluster_model = AgglomerativeClustering(
                    n_clusters=self.n_clusters,
                    linkage='ward'
                )
                self.cluster_model.fit(features_array)

            else:
                raise ValueError(f"Unsupported clustering method: {self.method}")

            self.logger.info("Clustering completed successfully")

        except ImportError:
            self.logger.error("scikit-learn not installed. Install with: pip install scikit-learn")
            raise
        except Exception as e:
            self.logger.error(f"Error during clustering: {e}")
            raise

    def predict(
        self,
        features: FeatureVector
    ) -> int:
        """
        Predict cluster for new features.

        Args:
            features: Feature vector

        Returns:
            Cluster ID
        """
        if self.cluster_model is None:
            raise ValueError("Clustering model not fitted yet")

        try:
            features_array = features.features.reshape(1, -1)
            cluster_id = self.cluster_model.predict(features_array)[0]
            return int(cluster_id)

        except Exception as e:
            self.logger.error(f"Error predicting cluster: {e}")
            raise

    def get_cluster_assignments(
        self,
        features_list: List[FeatureVector]
    ) -> List[int]:
        """
        Get cluster assignments for feature vectors.

        Args:
            features_list: List of feature vectors

        Returns:
            List of cluster IDs
        """
        if self.cluster_model is None:
            raise ValueError("Clustering model not fitted yet")

        try:
            features_array = np.array([f.features for f in features_list])
            if hasattr(self.cluster_model, 'labels_'):
                # For methods that store labels (DBSCAN, Hierarchical during fit)
                return self.cluster_model.labels_.tolist()
            else:
                # For methods that need prediction (KMeans)
                labels = self.cluster_model.predict(features_array)
                return labels.tolist()

        except Exception as e:
            self.logger.error(f"Error getting cluster assignments: {e}")
            raise


class VisualSearchEngine:
    """
    Complete visual search engine combining extraction and search.
    """

    def __init__(
        self,
        model_type: str = "resnet50",
        metric: str = "cosine"
    ):
        """
        Initialize visual search engine.

        Args:
            model_type: Feature extraction model type
            metric: Similarity metric
        """
        self.feature_extractor = FeatureExtractor(model_type=model_type)
        self.search_engine = SimilaritySearchEngine(metric=metric)
        self.logger = logging.getLogger(f"{__name__}.VisualSearchEngine")

    def index_images(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        image_ids: Optional[List[str]] = None,
        batch_size: int = 32
    ) -> None:
        """
        Index images for search.

        Args:
            images: List of images to index
            image_ids: Optional list of image IDs
            batch_size: Batch size for processing
        """
        self.logger.info(f"Indexing {len(images)} images...")

        for idx, image in enumerate(images):
            try:
                img_id = image_ids[idx] if image_ids else f"image_{idx}"
                features = self.feature_extractor.extract(
                    image,
                    normalize=True,
                    image_id=img_id
                )
                self.search_engine.add_features(features)

            except Exception as e:
                self.logger.error(f"Error indexing image {idx}: {e}")
                continue

        self.logger.info(f"Indexing completed. Database size: {self.search_engine.get_database_size()}")

    def search_by_image(
        self,
        query_image: Union[str, np.ndarray, Image.Image],
        top_k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar images.

        Args:
            query_image: Query image
            top_k: Number of results
            threshold: Minimum similarity threshold

        Returns:
            List of similar images
        """
        try:
            # Extract features from query
            query_features = self.feature_extractor.extract(
                query_image,
                normalize=True
            )

            # Search
            results = self.search_engine.search(
                query_features,
                top_k=top_k,
                threshold=threshold
            )

            return results

        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            'model_type': self.feature_extractor.model_type,
            'metric': self.search_engine.metric,
            'database_size': self.search_engine.get_database_size(),
            'feature_dimension': len(self.search_engine.feature_database[0].features) if self.search_engine.feature_database else 0
        }


# Global instances
visual_search_engine = VisualSearchEngine()
