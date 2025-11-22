"""
Model Training Module

Provides comprehensive model training capabilities including:
- Transfer learning from pre-trained models
- Fine-tuning and optimization
- Dataset management and loading
- Training pipeline with callbacks
- Model checkpointing and versioning
- Hyperparameter tuning
- Training metrics and visualization
- Distributed training support

Integrates with NEXUS database and storage for model persistence.
"""

import logging
import os
import time
import json
from typing import Optional, Dict, Any, List, Union, Tuple, Callable
from pathlib import Path
import numpy as np
from PIL import Image
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TrainingStatus(str, Enum):
    """Training job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class OptimizerType(str, Enum):
    """Optimizer types."""
    ADAM = "adam"
    SGD = "sgd"
    RMSPROP = "rmsprop"
    ADAMW = "adamw"


class TrainingConfig:
    """
    Configuration for model training.
    """

    def __init__(
        self,
        base_model: str = "resnet50",
        num_classes: int = 10,
        input_shape: Tuple[int, int, int] = (224, 224, 3),
        batch_size: int = 32,
        epochs: int = 10,
        learning_rate: float = 0.001,
        optimizer: OptimizerType = OptimizerType.ADAM,
        loss: str = "categorical_crossentropy",
        metrics: Optional[List[str]] = None,
        validation_split: float = 0.2,
        early_stopping_patience: int = 5,
        reduce_lr_patience: int = 3,
        trainable_layers: Optional[int] = None,
        augmentation: bool = True,
        **kwargs
    ):
        """
        Initialize training configuration.

        Args:
            base_model: Base model architecture
            num_classes: Number of output classes
            input_shape: Input shape (height, width, channels)
            batch_size: Batch size for training
            epochs: Number of training epochs
            learning_rate: Initial learning rate
            optimizer: Optimizer type
            loss: Loss function
            metrics: Training metrics
            validation_split: Validation data split ratio
            early_stopping_patience: Patience for early stopping
            reduce_lr_patience: Patience for reducing learning rate
            trainable_layers: Number of layers to make trainable
            augmentation: Whether to use data augmentation
            **kwargs: Additional configuration parameters
        """
        self.base_model = base_model
        self.num_classes = num_classes
        self.input_shape = input_shape
        self.batch_size = batch_size
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.optimizer = optimizer
        self.loss = loss
        self.metrics = metrics or ['accuracy']
        self.validation_split = validation_split
        self.early_stopping_patience = early_stopping_patience
        self.reduce_lr_patience = reduce_lr_patience
        self.trainable_layers = trainable_layers
        self.augmentation = augmentation
        self.extra_config = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'base_model': self.base_model,
            'num_classes': self.num_classes,
            'input_shape': self.input_shape,
            'batch_size': self.batch_size,
            'epochs': self.epochs,
            'learning_rate': self.learning_rate,
            'optimizer': self.optimizer.value if isinstance(self.optimizer, OptimizerType) else self.optimizer,
            'loss': self.loss,
            'metrics': self.metrics,
            'validation_split': self.validation_split,
            'early_stopping_patience': self.early_stopping_patience,
            'reduce_lr_patience': self.reduce_lr_patience,
            'trainable_layers': self.trainable_layers,
            'augmentation': self.augmentation,
            **self.extra_config
        }

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> 'TrainingConfig':
        """Create configuration from dictionary."""
        return TrainingConfig(**config_dict)


class DatasetManager:
    """
    Manages training datasets.
    """

    def __init__(
        self,
        dataset_path: str,
        config: Optional[TrainingConfig] = None
    ):
        """
        Initialize dataset manager.

        Args:
            dataset_path: Path to dataset directory
            config: Training configuration
        """
        self.dataset_path = Path(dataset_path)
        self.config = config or TrainingConfig()
        self.class_names: List[str] = []
        self.train_data = None
        self.val_data = None
        self.test_data = None
        self.logger = logging.getLogger(f"{__name__}.DatasetManager")

    def load_dataset(
        self,
        validation_split: Optional[float] = None,
        test_split: Optional[float] = None
    ) -> Tuple[Any, Any, Any]:
        """
        Load and prepare dataset.

        Args:
            validation_split: Validation split ratio
            test_split: Test split ratio

        Returns:
            Tuple of (train_data, val_data, test_data)
        """
        try:
            import tensorflow as tf
            from tensorflow import keras

            val_split = validation_split or self.config.validation_split
            test_split = test_split or 0.0

            # Load dataset from directory
            if not self.dataset_path.exists():
                raise ValueError(f"Dataset path not found: {self.dataset_path}")

            # Create image data generator with augmentation
            if self.config.augmentation:
                train_datagen = keras.preprocessing.image.ImageDataGenerator(
                    rescale=1./255,
                    rotation_range=20,
                    width_shift_range=0.2,
                    height_shift_range=0.2,
                    horizontal_flip=True,
                    zoom_range=0.2,
                    shear_range=0.2,
                    validation_split=val_split
                )
            else:
                train_datagen = keras.preprocessing.image.ImageDataGenerator(
                    rescale=1./255,
                    validation_split=val_split
                )

            val_datagen = keras.preprocessing.image.ImageDataGenerator(rescale=1./255)

            # Load training data
            self.train_data = train_datagen.flow_from_directory(
                str(self.dataset_path),
                target_size=self.config.input_shape[:2],
                batch_size=self.config.batch_size,
                class_mode='categorical',
                subset='training'
            )

            # Load validation data
            if val_split > 0:
                self.val_data = train_datagen.flow_from_directory(
                    str(self.dataset_path),
                    target_size=self.config.input_shape[:2],
                    batch_size=self.config.batch_size,
                    class_mode='categorical',
                    subset='validation'
                )

            # Store class names
            self.class_names = list(self.train_data.class_indices.keys())

            self.logger.info(f"Loaded dataset with {len(self.class_names)} classes")
            self.logger.info(f"Training samples: {self.train_data.samples}")
            if self.val_data:
                self.logger.info(f"Validation samples: {self.val_data.samples}")

            return self.train_data, self.val_data, self.test_data

        except ImportError:
            self.logger.error("TensorFlow not installed. Install with: pip install tensorflow")
            raise
        except Exception as e:
            self.logger.error(f"Error loading dataset: {e}")
            raise

    def get_class_names(self) -> List[str]:
        """Get list of class names."""
        return self.class_names

    def get_dataset_info(self) -> Dict[str, Any]:
        """Get dataset information."""
        info = {
            'dataset_path': str(self.dataset_path),
            'num_classes': len(self.class_names),
            'class_names': self.class_names
        }

        if self.train_data:
            info['train_samples'] = self.train_data.samples
        if self.val_data:
            info['val_samples'] = self.val_data.samples
        if self.test_data:
            info['test_samples'] = self.test_data.samples

        return info


class ModelBuilder:
    """
    Builds and configures models for training.
    """

    def __init__(self, config: TrainingConfig):
        """
        Initialize model builder.

        Args:
            config: Training configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ModelBuilder")

    def build_model(self) -> Any:
        """
        Build model architecture.

        Returns:
            Compiled model
        """
        try:
            import tensorflow as tf
            from tensorflow import keras

            # Load base model
            base_model = self._load_base_model()

            # Freeze base layers
            if self.config.trainable_layers is not None:
                for layer in base_model.layers[:-self.config.trainable_layers]:
                    layer.trainable = False
            else:
                base_model.trainable = False

            # Build model
            inputs = keras.Input(shape=self.config.input_shape)
            x = base_model(inputs, training=False)
            x = keras.layers.GlobalAveragePooling2D()(x)
            x = keras.layers.Dropout(0.5)(x)
            x = keras.layers.Dense(512, activation='relu')(x)
            x = keras.layers.Dropout(0.3)(x)
            outputs = keras.layers.Dense(self.config.num_classes, activation='softmax')(x)

            model = keras.Model(inputs, outputs)

            # Compile model
            optimizer = self._get_optimizer()
            model.compile(
                optimizer=optimizer,
                loss=self.config.loss,
                metrics=self.config.metrics
            )

            self.logger.info(f"Built model with {self.config.base_model} base")
            return model

        except Exception as e:
            self.logger.error(f"Error building model: {e}")
            raise

    def _load_base_model(self) -> Any:
        """Load pre-trained base model."""
        import tensorflow as tf
        from tensorflow import keras

        base = self.config.base_model.lower()

        if base == 'resnet50':
            return keras.applications.ResNet50(
                weights='imagenet',
                include_top=False,
                input_shape=self.config.input_shape
            )
        elif base == 'vgg16':
            return keras.applications.VGG16(
                weights='imagenet',
                include_top=False,
                input_shape=self.config.input_shape
            )
        elif base == 'inceptionv3':
            return keras.applications.InceptionV3(
                weights='imagenet',
                include_top=False,
                input_shape=self.config.input_shape
            )
        elif base == 'efficientnet':
            return keras.applications.EfficientNetB0(
                weights='imagenet',
                include_top=False,
                input_shape=self.config.input_shape
            )
        elif base == 'mobilenet':
            return keras.applications.MobileNetV2(
                weights='imagenet',
                include_top=False,
                input_shape=self.config.input_shape
            )
        else:
            raise ValueError(f"Unsupported base model: {base}")

    def _get_optimizer(self) -> Any:
        """Get configured optimizer."""
        import tensorflow as tf

        if self.config.optimizer == OptimizerType.ADAM:
            return tf.keras.optimizers.Adam(learning_rate=self.config.learning_rate)
        elif self.config.optimizer == OptimizerType.SGD:
            return tf.keras.optimizers.SGD(learning_rate=self.config.learning_rate, momentum=0.9)
        elif self.config.optimizer == OptimizerType.RMSPROP:
            return tf.keras.optimizers.RMSprop(learning_rate=self.config.learning_rate)
        elif self.config.optimizer == OptimizerType.ADAMW:
            return tf.keras.optimizers.AdamW(learning_rate=self.config.learning_rate)
        else:
            raise ValueError(f"Unsupported optimizer: {self.config.optimizer}")


class ModelTrainer:
    """
    Trains image recognition models.
    """

    def __init__(
        self,
        config: TrainingConfig,
        dataset_manager: DatasetManager,
        model_builder: ModelBuilder
    ):
        """
        Initialize model trainer.

        Args:
            config: Training configuration
            dataset_manager: Dataset manager
            model_builder: Model builder
        """
        self.config = config
        self.dataset_manager = dataset_manager
        self.model_builder = model_builder
        self.model = None
        self.history = None
        self.status = TrainingStatus.PENDING
        self.logger = logging.getLogger(f"{__name__}.ModelTrainer")

    def train(
        self,
        model_save_path: str,
        checkpoint_dir: Optional[str] = None,
        tensorboard_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Train the model.

        Args:
            model_save_path: Path to save trained model
            checkpoint_dir: Directory for checkpoints
            tensorboard_dir: Directory for TensorBoard logs

        Returns:
            Training results dictionary
        """
        try:
            import tensorflow as tf
            from tensorflow import keras

            self.status = TrainingStatus.RUNNING
            start_time = time.time()

            # Build model
            self.logger.info("Building model...")
            self.model = self.model_builder.build_model()

            # Load dataset
            self.logger.info("Loading dataset...")
            train_data, val_data, _ = self.dataset_manager.load_dataset()

            # Prepare callbacks
            callbacks = self._prepare_callbacks(
                model_save_path,
                checkpoint_dir,
                tensorboard_dir
            )

            # Train model
            self.logger.info("Starting training...")
            self.history = self.model.fit(
                train_data,
                validation_data=val_data,
                epochs=self.config.epochs,
                callbacks=callbacks
            )

            # Save final model
            self.logger.info(f"Saving model to {model_save_path}")
            self.model.save(model_save_path)

            # Calculate training time
            training_time = time.time() - start_time

            # Get final metrics
            final_metrics = {
                'train_loss': float(self.history.history['loss'][-1]),
                'train_accuracy': float(self.history.history['accuracy'][-1]),
                'training_time_seconds': training_time
            }

            if val_data:
                final_metrics['val_loss'] = float(self.history.history['val_loss'][-1])
                final_metrics['val_accuracy'] = float(self.history.history['val_accuracy'][-1])

            self.status = TrainingStatus.COMPLETED
            self.logger.info(f"Training completed in {training_time:.2f} seconds")

            return {
                'success': True,
                'status': self.status.value,
                'metrics': final_metrics,
                'history': self.history.history,
                'model_path': model_save_path,
                'config': self.config.to_dict()
            }

        except Exception as e:
            self.status = TrainingStatus.FAILED
            self.logger.error(f"Error during training: {e}")
            return {
                'success': False,
                'status': self.status.value,
                'error': str(e)
            }

    def _prepare_callbacks(
        self,
        model_save_path: str,
        checkpoint_dir: Optional[str] = None,
        tensorboard_dir: Optional[str] = None
    ) -> List[Any]:
        """Prepare training callbacks."""
        import tensorflow as tf
        from tensorflow import keras

        callbacks = []

        # Model checkpoint
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)
            checkpoint_path = os.path.join(checkpoint_dir, 'model_{epoch:02d}_{val_accuracy:.2f}.h5')
            callbacks.append(
                keras.callbacks.ModelCheckpoint(
                    checkpoint_path,
                    monitor='val_accuracy',
                    save_best_only=True,
                    mode='max',
                    verbose=1
                )
            )

        # Early stopping
        callbacks.append(
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=self.config.early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            )
        )

        # Reduce learning rate on plateau
        callbacks.append(
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=self.config.reduce_lr_patience,
                min_lr=1e-7,
                verbose=1
            )
        )

        # TensorBoard
        if tensorboard_dir:
            os.makedirs(tensorboard_dir, exist_ok=True)
            callbacks.append(
                keras.callbacks.TensorBoard(
                    log_dir=tensorboard_dir,
                    histogram_freq=1,
                    write_graph=True
                )
            )

        # Progress logging
        callbacks.append(
            keras.callbacks.LambdaCallback(
                on_epoch_end=lambda epoch, logs: self.logger.info(
                    f"Epoch {epoch + 1}/{self.config.epochs} - "
                    f"loss: {logs['loss']:.4f} - acc: {logs['accuracy']:.4f} - "
                    f"val_loss: {logs.get('val_loss', 0):.4f} - val_acc: {logs.get('val_accuracy', 0):.4f}"
                )
            )
        )

        return callbacks

    def evaluate(self, test_data: Any) -> Dict[str, Any]:
        """
        Evaluate trained model.

        Args:
            test_data: Test dataset

        Returns:
            Evaluation results
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        try:
            self.logger.info("Evaluating model...")
            results = self.model.evaluate(test_data)

            metrics = {}
            for i, metric_name in enumerate(self.model.metrics_names):
                metrics[metric_name] = float(results[i])

            self.logger.info(f"Evaluation results: {metrics}")
            return {
                'success': True,
                'metrics': metrics
            }

        except Exception as e:
            self.logger.error(f"Error during evaluation: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class FineTuner:
    """
    Fine-tunes pre-trained models.
    """

    def __init__(self, model_path: str):
        """
        Initialize fine-tuner.

        Args:
            model_path: Path to pre-trained model
        """
        self.model_path = model_path
        self.model = None
        self.logger = logging.getLogger(f"{__name__}.FineTuner")

    def load_model(self) -> bool:
        """Load pre-trained model."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            self.model = keras.models.load_model(self.model_path)
            self.logger.info(f"Loaded model from {self.model_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def fine_tune(
        self,
        train_data: Any,
        val_data: Any,
        num_layers_to_unfreeze: int = 10,
        learning_rate: float = 1e-5,
        epochs: int = 5,
        callbacks: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune model on new data.

        Args:
            train_data: Training dataset
            val_data: Validation dataset
            num_layers_to_unfreeze: Number of layers to unfreeze from end
            learning_rate: Fine-tuning learning rate
            epochs: Number of fine-tuning epochs
            callbacks: Training callbacks

        Returns:
            Fine-tuning results
        """
        if self.model is None:
            self.load_model()

        try:
            import tensorflow as tf

            # Unfreeze last N layers
            for layer in self.model.layers[-num_layers_to_unfreeze:]:
                layer.trainable = True

            # Recompile with lower learning rate
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            self.logger.info(f"Fine-tuning last {num_layers_to_unfreeze} layers...")

            # Train
            history = self.model.fit(
                train_data,
                validation_data=val_data,
                epochs=epochs,
                callbacks=callbacks or []
            )

            return {
                'success': True,
                'history': history.history,
                'final_train_accuracy': float(history.history['accuracy'][-1]),
                'final_val_accuracy': float(history.history['val_accuracy'][-1])
            }

        except Exception as e:
            self.logger.error(f"Error during fine-tuning: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def save_model(self, output_path: str) -> bool:
        """Save fine-tuned model."""
        try:
            self.model.save(output_path)
            self.logger.info(f"Saved fine-tuned model to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            return False


class TrainingManager:
    """
    Manages multiple training jobs.
    """

    def __init__(self):
        """Initialize training manager."""
        self.training_jobs: Dict[str, ModelTrainer] = {}
        self.logger = logging.getLogger(f"{__name__}.TrainingManager")

    def create_training_job(
        self,
        job_id: str,
        config: TrainingConfig,
        dataset_path: str
    ) -> ModelTrainer:
        """
        Create a new training job.

        Args:
            job_id: Unique job identifier
            config: Training configuration
            dataset_path: Path to dataset

        Returns:
            ModelTrainer instance
        """
        dataset_manager = DatasetManager(dataset_path, config)
        model_builder = ModelBuilder(config)
        trainer = ModelTrainer(config, dataset_manager, model_builder)

        self.training_jobs[job_id] = trainer
        self.logger.info(f"Created training job: {job_id}")

        return trainer

    def get_training_job(self, job_id: str) -> Optional[ModelTrainer]:
        """Get training job by ID."""
        return self.training_jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all training jobs."""
        jobs = []
        for job_id, trainer in self.training_jobs.items():
            jobs.append({
                'job_id': job_id,
                'status': trainer.status.value,
                'config': trainer.config.to_dict()
            })
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        """Cancel training job."""
        if job_id in self.training_jobs:
            self.training_jobs[job_id].status = TrainingStatus.CANCELLED
            self.logger.info(f"Cancelled training job: {job_id}")
            return True
        return False


# Global training manager instance
training_manager = TrainingManager()
