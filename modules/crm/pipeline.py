"""
CRM Pipeline Module - Custom pipeline management with Kanban views and stage customization.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json


class StageType(Enum):
    """Pipeline stage types."""
    OPEN = "open"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


@dataclass
class PipelineStage:
    """Custom pipeline stage definition."""
    id: str
    name: str
    order: int
    stage_type: StageType = StageType.OPEN
    probability: int = 50  # Default probability percentage
    color: str = "#3B82F6"  # Hex color for UI
    is_active: bool = True

    # Stage metrics
    deals_count: int = 0
    total_value: float = 0.0
    avg_days_in_stage: float = 0.0

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'stage_type': self.stage_type.value,
            'probability': self.probability,
            'color': self.color,
            'is_active': self.is_active,
            'deals_count': self.deals_count,
            'total_value': self.total_value,
            'avg_days_in_stage': self.avg_days_in_stage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class Pipeline:
    """Custom sales pipeline with stages."""
    id: str
    name: str
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True

    # Stages in this pipeline
    stages: List[PipelineStage] = field(default_factory=list)

    # Pipeline owner
    owner_id: Optional[str] = None

    # Pipeline metrics
    total_deals: int = 0
    total_value: float = 0.0
    weighted_value: float = 0.0
    win_rate: float = 0.0

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'stages': [s.to_dict() for s in self.stages],
            'owner_id': self.owner_id,
            'total_deals': self.total_deals,
            'total_value': self.total_value,
            'weighted_value': self.weighted_value,
            'win_rate': self.win_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class DealMovement:
    """Track deal movements between stages."""
    deal_id: str
    deal_name: str
    from_stage_id: Optional[str]
    from_stage_name: Optional[str]
    to_stage_id: str
    to_stage_name: str
    moved_by: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'deal_id': self.deal_id,
            'deal_name': self.deal_name,
            'from_stage_id': self.from_stage_id,
            'from_stage_name': self.from_stage_name,
            'to_stage_id': self.to_stage_id,
            'to_stage_name': self.to_stage_name,
            'moved_by': self.moved_by,
            'timestamp': self.timestamp.isoformat(),
            'notes': self.notes,
        }


class PipelineManager:
    """Manage pipelines, stages, and deal movements."""

    # Default pipeline stages
    DEFAULT_STAGES = [
        {"name": "Lead In", "order": 0, "type": StageType.OPEN, "probability": 10, "color": "#94A3B8"},
        {"name": "Qualification", "order": 1, "type": StageType.OPEN, "probability": 20, "color": "#60A5FA"},
        {"name": "Needs Analysis", "order": 2, "type": StageType.OPEN, "probability": 30, "color": "#3B82F6"},
        {"name": "Proposal", "order": 3, "type": StageType.OPEN, "probability": 50, "color": "#8B5CF6"},
        {"name": "Negotiation", "order": 4, "type": StageType.OPEN, "probability": 75, "color": "#A855F7"},
        {"name": "Closed Won", "order": 5, "type": StageType.CLOSED_WON, "probability": 100, "color": "#10B981"},
        {"name": "Closed Lost", "order": 6, "type": StageType.CLOSED_LOST, "probability": 0, "color": "#EF4444"},
    ]

    def __init__(self):
        """Initialize pipeline manager."""
        self.pipelines: Dict[str, Pipeline] = {}
        self.stages: Dict[str, PipelineStage] = {}  # All stages across pipelines
        self.movements: List[DealMovement] = []
        self._pipeline_deals: Dict[str, Dict[str, List[str]]] = {}  # pipeline_id -> stage_id -> [deal_ids]

    def create_pipeline(self, pipeline: Pipeline) -> Pipeline:
        """Create a new pipeline."""
        # If this is the first pipeline or marked as default, set it as default
        if not self.pipelines or pipeline.is_default:
            # Unset other defaults
            for p in self.pipelines.values():
                p.is_default = False
            pipeline.is_default = True

        self.pipelines[pipeline.id] = pipeline

        # Add stages to global stages dict
        for stage in pipeline.stages:
            self.stages[stage.id] = stage

        # Initialize deal tracking for this pipeline
        self._pipeline_deals[pipeline.id] = {}
        for stage in pipeline.stages:
            self._pipeline_deals[pipeline.id][stage.id] = []

        return pipeline

    def create_default_pipeline(self, name: str = "Sales Pipeline") -> Pipeline:
        """Create a pipeline with default stages."""
        pipeline_id = self._generate_id()
        stages = []

        for i, stage_data in enumerate(self.DEFAULT_STAGES):
            stage = PipelineStage(
                id=f"{pipeline_id}_stage_{i}",
                name=stage_data["name"],
                order=stage_data["order"],
                stage_type=stage_data["type"],
                probability=stage_data["probability"],
                color=stage_data["color"],
            )
            stages.append(stage)

        pipeline = Pipeline(
            id=pipeline_id,
            name=name,
            stages=stages,
            is_default=True,
        )

        return self.create_pipeline(pipeline)

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID."""
        return self.pipelines.get(pipeline_id)

    def get_default_pipeline(self) -> Optional[Pipeline]:
        """Get the default pipeline."""
        for pipeline in self.pipelines.values():
            if pipeline.is_default:
                return pipeline
        return None

    def list_pipelines(self, active_only: bool = True) -> List[Pipeline]:
        """List all pipelines."""
        pipelines = list(self.pipelines.values())
        if active_only:
            pipelines = [p for p in pipelines if p.is_active]
        return sorted(pipelines, key=lambda p: p.name)

    def update_pipeline(self, pipeline_id: str, updates: Dict[str, Any]) -> Optional[Pipeline]:
        """Update a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None

        # Handle default pipeline change
        if updates.get('is_default'):
            for p in self.pipelines.values():
                p.is_default = False

        for key, value in updates.items():
            if hasattr(pipeline, key) and key != 'stages':
                setattr(pipeline, key, value)

        pipeline.updated_at = datetime.now()
        return pipeline

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline."""
        if pipeline_id not in self.pipelines:
            return False

        pipeline = self.pipelines[pipeline_id]

        # Can't delete default pipeline if it has deals
        if pipeline.is_default and pipeline.total_deals > 0:
            raise ValueError("Cannot delete default pipeline with active deals")

        # Remove stages
        for stage in pipeline.stages:
            if stage.id in self.stages:
                del self.stages[stage.id]

        # Remove deal tracking
        if pipeline_id in self._pipeline_deals:
            del self._pipeline_deals[pipeline_id]

        del self.pipelines[pipeline_id]

        # Set a new default if we deleted the default
        if pipeline.is_default and self.pipelines:
            next_pipeline = next(iter(self.pipelines.values()))
            next_pipeline.is_default = True

        return True

    def add_stage(
        self,
        pipeline_id: str,
        name: str,
        order: Optional[int] = None,
        stage_type: StageType = StageType.OPEN,
        probability: int = 50,
        color: str = "#3B82F6"
    ) -> Optional[PipelineStage]:
        """Add a new stage to a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None

        # Determine order
        if order is None:
            order = len(pipeline.stages)

        # Create stage
        stage = PipelineStage(
            id=f"{pipeline_id}_stage_{len(pipeline.stages)}",
            name=name,
            order=order,
            stage_type=stage_type,
            probability=probability,
            color=color,
        )

        # Insert at correct position
        pipeline.stages.insert(order, stage)

        # Reorder stages
        for i, s in enumerate(pipeline.stages):
            s.order = i

        # Add to global stages
        self.stages[stage.id] = stage

        # Initialize deal tracking
        if pipeline_id in self._pipeline_deals:
            self._pipeline_deals[pipeline_id][stage.id] = []

        pipeline.updated_at = datetime.now()
        return stage

    def update_stage(
        self,
        stage_id: str,
        updates: Dict[str, Any]
    ) -> Optional[PipelineStage]:
        """Update a stage."""
        stage = self.stages.get(stage_id)
        if not stage:
            return None

        for key, value in updates.items():
            if hasattr(stage, key) and key != 'id':
                if key == 'stage_type' and isinstance(value, str):
                    value = StageType(value)
                setattr(stage, key, value)

        stage.updated_at = datetime.now()
        return stage

    def delete_stage(self, pipeline_id: str, stage_id: str) -> bool:
        """Delete a stage from a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return False

        # Check if stage has deals
        if pipeline_id in self._pipeline_deals and stage_id in self._pipeline_deals[pipeline_id]:
            if self._pipeline_deals[pipeline_id][stage_id]:
                raise ValueError("Cannot delete stage with active deals")

        # Remove stage
        pipeline.stages = [s for s in pipeline.stages if s.id != stage_id]

        # Reorder remaining stages
        for i, s in enumerate(pipeline.stages):
            s.order = i

        # Remove from global stages
        if stage_id in self.stages:
            del self.stages[stage_id]

        # Remove from deal tracking
        if pipeline_id in self._pipeline_deals and stage_id in self._pipeline_deals[pipeline_id]:
            del self._pipeline_deals[pipeline_id][stage_id]

        pipeline.updated_at = datetime.now()
        return True

    def reorder_stages(self, pipeline_id: str, stage_order: List[str]) -> Optional[Pipeline]:
        """Reorder stages in a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None

        # Create new order
        stage_map = {s.id: s for s in pipeline.stages}
        new_stages = []

        for i, stage_id in enumerate(stage_order):
            if stage_id in stage_map:
                stage = stage_map[stage_id]
                stage.order = i
                new_stages.append(stage)

        pipeline.stages = new_stages
        pipeline.updated_at = datetime.now()
        return pipeline

    def add_deal_to_stage(
        self,
        pipeline_id: str,
        stage_id: str,
        deal_id: str
    ) -> bool:
        """Add a deal to a stage."""
        if pipeline_id not in self._pipeline_deals:
            return False
        if stage_id not in self._pipeline_deals[pipeline_id]:
            return False

        if deal_id not in self._pipeline_deals[pipeline_id][stage_id]:
            self._pipeline_deals[pipeline_id][stage_id].append(deal_id)

        # Update stage metrics
        stage = self.stages.get(stage_id)
        if stage:
            stage.deals_count = len(self._pipeline_deals[pipeline_id][stage_id])

        return True

    def move_deal(
        self,
        pipeline_id: str,
        deal_id: str,
        deal_name: str,
        from_stage_id: Optional[str],
        to_stage_id: str,
        moved_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Move a deal from one stage to another."""
        if pipeline_id not in self._pipeline_deals:
            return False

        # Remove from old stage
        if from_stage_id and from_stage_id in self._pipeline_deals[pipeline_id]:
            if deal_id in self._pipeline_deals[pipeline_id][from_stage_id]:
                self._pipeline_deals[pipeline_id][from_stage_id].remove(deal_id)

                # Update old stage metrics
                from_stage = self.stages.get(from_stage_id)
                if from_stage:
                    from_stage.deals_count = len(self._pipeline_deals[pipeline_id][from_stage_id])

        # Add to new stage
        if to_stage_id in self._pipeline_deals[pipeline_id]:
            if deal_id not in self._pipeline_deals[pipeline_id][to_stage_id]:
                self._pipeline_deals[pipeline_id][to_stage_id].append(deal_id)

                # Update new stage metrics
                to_stage = self.stages.get(to_stage_id)
                if to_stage:
                    to_stage.deals_count = len(self._pipeline_deals[pipeline_id][to_stage_id])

        # Record movement
        from_stage_name = self.stages[from_stage_id].name if from_stage_id and from_stage_id in self.stages else None
        to_stage_name = self.stages[to_stage_id].name if to_stage_id in self.stages else None

        movement = DealMovement(
            deal_id=deal_id,
            deal_name=deal_name,
            from_stage_id=from_stage_id,
            from_stage_name=from_stage_name,
            to_stage_id=to_stage_id,
            to_stage_name=to_stage_name,
            moved_by=moved_by,
            notes=notes,
        )
        self.movements.append(movement)

        return True

    def get_kanban_view(
        self,
        pipeline_id: str,
        deals_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get Kanban board view for a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return {}

        kanban = {
            'pipeline': pipeline.to_dict(),
            'stages': []
        }

        for stage in sorted(pipeline.stages, key=lambda s: s.order):
            stage_data = stage.to_dict()
            stage_data['deals'] = []

            # Get deals in this stage
            if pipeline_id in self._pipeline_deals and stage.id in self._pipeline_deals[pipeline_id]:
                deal_ids = self._pipeline_deals[pipeline_id][stage.id]
                for deal_id in deal_ids:
                    if deal_id in deals_data:
                        stage_data['deals'].append(deals_data[deal_id])

            kanban['stages'].append(stage_data)

        return kanban

    def get_stage_metrics(self, stage_id: str) -> Dict[str, Any]:
        """Get detailed metrics for a stage."""
        stage = self.stages.get(stage_id)
        if not stage:
            return {}

        return {
            'stage': stage.to_dict(),
            'deals_count': stage.deals_count,
            'total_value': stage.total_value,
            'avg_days_in_stage': stage.avg_days_in_stage,
        }

    def get_pipeline_metrics(self, pipeline_id: str) -> Dict[str, Any]:
        """Get detailed metrics for a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return {}

        stages_metrics = []
        for stage in sorted(pipeline.stages, key=lambda s: s.order):
            stages_metrics.append(self.get_stage_metrics(stage.id))

        return {
            'pipeline': pipeline.to_dict(),
            'stages': stages_metrics,
        }

    def get_deal_movements_history(
        self,
        deal_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get deal movement history."""
        movements = self.movements

        # Filter by deal
        if deal_id:
            movements = [m for m in movements if m.deal_id == deal_id]

        # Sort by timestamp descending
        movements = sorted(movements, key=lambda m: m.timestamp, reverse=True)

        # Apply limit
        movements = movements[:limit]

        return [m.to_dict() for m in movements]

    def get_conversion_funnel(self, pipeline_id: str) -> Dict[str, Any]:
        """Get conversion funnel data for a pipeline."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return {}

        funnel = []
        for stage in sorted(pipeline.stages, key=lambda s: s.order):
            if stage.stage_type == StageType.OPEN:
                funnel.append({
                    'stage_name': stage.name,
                    'stage_id': stage.id,
                    'deals_count': stage.deals_count,
                    'total_value': stage.total_value,
                    'probability': stage.probability,
                })

        # Calculate conversion rates between stages
        for i in range(len(funnel) - 1):
            current = funnel[i]
            next_stage = funnel[i + 1]
            if current['deals_count'] > 0:
                conversion = (next_stage['deals_count'] / current['deals_count']) * 100
                current['conversion_to_next'] = round(conversion, 2)

        return {
            'pipeline_id': pipeline_id,
            'pipeline_name': pipeline.name,
            'funnel': funnel,
        }

    def export_pipeline_config(self, pipeline_id: str) -> str:
        """Export pipeline configuration as JSON."""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return ""

        config = {
            'name': pipeline.name,
            'description': pipeline.description,
            'stages': [
                {
                    'name': s.name,
                    'order': s.order,
                    'type': s.stage_type.value,
                    'probability': s.probability,
                    'color': s.color,
                }
                for s in sorted(pipeline.stages, key=lambda s: s.order)
            ]
        }

        return json.dumps(config, indent=2)

    def import_pipeline_config(self, config_json: str, pipeline_name: Optional[str] = None) -> Pipeline:
        """Import pipeline configuration from JSON."""
        config = json.loads(config_json)

        pipeline_id = self._generate_id()
        stages = []

        for i, stage_data in enumerate(config['stages']):
            stage = PipelineStage(
                id=f"{pipeline_id}_stage_{i}",
                name=stage_data['name'],
                order=stage_data.get('order', i),
                stage_type=StageType(stage_data.get('type', 'open')),
                probability=stage_data.get('probability', 50),
                color=stage_data.get('color', '#3B82F6'),
            )
            stages.append(stage)

        pipeline = Pipeline(
            id=pipeline_id,
            name=pipeline_name or config['name'],
            description=config.get('description'),
            stages=stages,
        )

        return self.create_pipeline(pipeline)

    def _generate_id(self) -> str:
        """Generate a unique ID."""
        import uuid
        return f"pipeline_{uuid.uuid4().hex[:12]}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        total_pipelines = len(self.pipelines)
        total_stages = len(self.stages)
        total_movements = len(self.movements)

        active_pipelines = [p for p in self.pipelines.values() if p.is_active]

        return {
            'total_pipelines': total_pipelines,
            'active_pipelines': len(active_pipelines),
            'total_stages': total_stages,
            'total_movements': total_movements,
        }
