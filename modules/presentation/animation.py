"""
Animation Engine - Transitions and Animations

Handles slide transitions, element animations, motion paths, and animation timing.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class TransitionType(Enum):
    """Slide transition types."""
    NONE = "none"
    FADE = "fade"
    PUSH = "push"
    WIPE = "wipe"
    SPLIT = "split"
    REVEAL = "reveal"
    RANDOM_BARS = "random_bars"
    SHAPE = "shape"
    UNCOVER = "uncover"
    COVER = "cover"
    FLASH = "flash"
    DISSOLVE = "dissolve"
    CHECKERBOARD = "checkerboard"
    BLINDS = "blinds"
    CLOCK = "clock"
    RIPPLE = "ripple"
    HONEYCOMB = "honeycomb"
    GLITTER = "glitter"
    VORTEX = "vortex"
    SHRED = "shred"
    SWITCH = "switch"
    FLIP = "flip"
    GALLERY = "gallery"
    CUBE = "cube"
    DOORS = "doors"
    BOX = "box"
    COMB = "comb"
    ZOOM = "zoom"
    PAN = "pan"


class AnimationType(Enum):
    """Element animation types."""
    # Entrance effects
    APPEAR = "appear"
    FADE_IN = "fade_in"
    FLY_IN = "fly_in"
    FLOAT_IN = "float_in"
    SPLIT_IN = "split_in"
    WIPE_IN = "wipe_in"
    SHAPE_IN = "shape_in"
    WHEEL = "wheel"
    RANDOM_BARS_IN = "random_bars_in"
    GROW_TURN = "grow_turn"
    ZOOM_IN = "zoom_in"
    SWIVEL = "swivel"
    BOUNCE = "bounce"

    # Exit effects
    DISAPPEAR = "disappear"
    FADE_OUT = "fade_out"
    FLY_OUT = "fly_out"
    FLOAT_OUT = "float_out"
    SPLIT_OUT = "split_out"
    WIPE_OUT = "wipe_out"
    SHAPE_OUT = "shape_out"
    RANDOM_BARS_OUT = "random_bars_out"
    SHRINK_TURN = "shrink_turn"
    ZOOM_OUT = "zoom_out"

    # Emphasis effects
    PULSE = "pulse"
    COLOR_PULSE = "color_pulse"
    TEETER = "teeter"
    SPIN = "spin"
    GROW_SHRINK = "grow_shrink"
    DESATURATE = "desaturate"
    DARKEN = "darken"
    LIGHTEN = "lighten"
    TRANSPARENCY = "transparency"
    COMPLEMENTARY_COLOR = "complementary_color"
    LINE_COLOR = "line_color"
    FILL_COLOR = "fill_color"

    # Motion path
    CUSTOM_PATH = "custom_path"
    LINES = "lines"
    ARCS = "arcs"
    TURNS = "turns"
    SHAPES_PATH = "shapes_path"
    LOOPS = "loops"


class AnimationTiming(Enum):
    """Animation timing functions."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE_IN = "bounce_in"
    BOUNCE_OUT = "bounce_out"
    ELASTIC = "elastic"


class AnimationTrigger(Enum):
    """Animation trigger types."""
    ON_CLICK = "on_click"
    WITH_PREVIOUS = "with_previous"
    AFTER_PREVIOUS = "after_previous"
    AUTO = "auto"


class Direction(Enum):
    """Animation direction."""
    FROM_LEFT = "from_left"
    FROM_RIGHT = "from_right"
    FROM_TOP = "from_top"
    FROM_BOTTOM = "from_bottom"
    FROM_TOP_LEFT = "from_top_left"
    FROM_TOP_RIGHT = "from_top_right"
    FROM_BOTTOM_LEFT = "from_bottom_left"
    FROM_BOTTOM_RIGHT = "from_bottom_right"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    CENTER = "center"


@dataclass
class SlideTransition:
    """Slide transition configuration."""
    type: TransitionType = TransitionType.NONE
    duration: float = 0.5  # seconds
    direction: Optional[Direction] = None
    sound: Optional[str] = None
    advance_on_click: bool = True
    advance_after_time: Optional[float] = None  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "duration": self.duration,
            "direction": self.direction.value if self.direction else None,
            "sound": self.sound,
            "advance_on_click": self.advance_on_click,
            "advance_after_time": self.advance_after_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SlideTransition':
        """Create from dictionary."""
        direction = None
        if data.get("direction"):
            direction = Direction(data["direction"])

        return cls(
            type=TransitionType(data.get("type", "none")),
            duration=data.get("duration", 0.5),
            direction=direction,
            sound=data.get("sound"),
            advance_on_click=data.get("advance_on_click", True),
            advance_after_time=data.get("advance_after_time"),
        )


@dataclass
class MotionPath:
    """Custom motion path for animations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    points: List[Tuple[float, float]] = field(default_factory=list)
    closed: bool = False
    smooth: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "points": self.points,
            "closed": self.closed,
            "smooth": self.smooth,
        }


@dataclass
class ElementAnimation:
    """Element animation configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_id: str = ""
    animation_type: AnimationType = AnimationType.FADE_IN
    duration: float = 0.5  # seconds
    delay: float = 0.0  # seconds
    timing: AnimationTiming = AnimationTiming.EASE_IN_OUT
    trigger: AnimationTrigger = AnimationTrigger.ON_CLICK
    direction: Optional[Direction] = None
    motion_path: Optional[MotionPath] = None
    order: int = 0
    repeat_count: int = 1
    reverse: bool = False
    auto_reverse: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "element_id": self.element_id,
            "animation_type": self.animation_type.value,
            "duration": self.duration,
            "delay": self.delay,
            "timing": self.timing.value,
            "trigger": self.trigger.value,
            "direction": self.direction.value if self.direction else None,
            "motion_path": self.motion_path.to_dict() if self.motion_path else None,
            "order": self.order,
            "repeat_count": self.repeat_count,
            "reverse": self.reverse,
            "auto_reverse": self.auto_reverse,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElementAnimation':
        """Create from dictionary."""
        direction = None
        if data.get("direction"):
            direction = Direction(data["direction"])

        motion_path = None
        if data.get("motion_path"):
            motion_path = MotionPath(**data["motion_path"])

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            element_id=data.get("element_id", ""),
            animation_type=AnimationType(data.get("animation_type", "fade_in")),
            duration=data.get("duration", 0.5),
            delay=data.get("delay", 0.0),
            timing=AnimationTiming(data.get("timing", "ease_in_out")),
            trigger=AnimationTrigger(data.get("trigger", "on_click")),
            direction=direction,
            motion_path=motion_path,
            order=data.get("order", 0),
            repeat_count=data.get("repeat_count", 1),
            reverse=data.get("reverse", False),
            auto_reverse=data.get("auto_reverse", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )


class AnimationEngine:
    """
    Manages all animations and transitions.

    Features:
    - Slide transitions
    - Element entrance/exit animations
    - Emphasis animations
    - Custom motion paths
    - Animation timeline
    - Trigger management
    """

    def __init__(self):
        """Initialize animation engine."""
        self.slide_transitions: Dict[str, SlideTransition] = {}
        self.element_animations: Dict[str, List[ElementAnimation]] = {}
        self.animation_timeline: List[ElementAnimation] = []

    # Slide Transitions

    def set_slide_transition(
        self,
        slide_id: str,
        transition_type: TransitionType,
        duration: float = 0.5,
        direction: Optional[Direction] = None
    ) -> SlideTransition:
        """Set transition for a slide."""
        transition = SlideTransition(
            type=transition_type,
            duration=duration,
            direction=direction
        )
        self.slide_transitions[slide_id] = transition
        return transition

    def get_slide_transition(self, slide_id: str) -> Optional[SlideTransition]:
        """Get transition for a slide."""
        return self.slide_transitions.get(slide_id)

    def remove_slide_transition(self, slide_id: str) -> bool:
        """Remove transition from a slide."""
        if slide_id in self.slide_transitions:
            del self.slide_transitions[slide_id]
            return True
        return False

    def apply_transition_to_all(self, transition: SlideTransition) -> None:
        """Apply same transition to all slides."""
        # This would be called with slide IDs from the slide manager
        pass

    # Element Animations

    def add_animation(
        self,
        element_id: str,
        animation_type: AnimationType,
        duration: float = 0.5,
        delay: float = 0.0,
        trigger: AnimationTrigger = AnimationTrigger.ON_CLICK,
        direction: Optional[Direction] = None
    ) -> ElementAnimation:
        """Add animation to an element."""
        animation = ElementAnimation(
            element_id=element_id,
            animation_type=animation_type,
            duration=duration,
            delay=delay,
            trigger=trigger,
            direction=direction
        )

        if element_id not in self.element_animations:
            self.element_animations[element_id] = []

        animation.order = len(self.element_animations[element_id])
        self.element_animations[element_id].append(animation)
        self._rebuild_timeline()

        return animation

    def get_element_animations(self, element_id: str) -> List[ElementAnimation]:
        """Get all animations for an element."""
        return self.element_animations.get(element_id, [])

    def remove_animation(self, animation_id: str) -> bool:
        """Remove an animation."""
        for element_id, animations in self.element_animations.items():
            for i, anim in enumerate(animations):
                if anim.id == animation_id:
                    animations.pop(i)
                    self._reorder_animations(element_id)
                    self._rebuild_timeline()
                    return True
        return False

    def remove_all_animations(self, element_id: str) -> int:
        """Remove all animations from an element. Returns count removed."""
        if element_id in self.element_animations:
            count = len(self.element_animations[element_id])
            del self.element_animations[element_id]
            self._rebuild_timeline()
            return count
        return 0

    def update_animation(
        self,
        animation_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update animation properties."""
        for animations in self.element_animations.values():
            for anim in animations:
                if anim.id == animation_id:
                    for key, value in properties.items():
                        if hasattr(anim, key):
                            setattr(anim, key, value)
                    self._rebuild_timeline()
                    return True
        return False

    def reorder_animation(self, animation_id: str, new_order: int) -> bool:
        """Change animation order."""
        for element_id, animations in self.element_animations.items():
            for i, anim in enumerate(animations):
                if anim.id == animation_id:
                    if 0 <= new_order < len(animations):
                        anim = animations.pop(i)
                        animations.insert(new_order, anim)
                        self._reorder_animations(element_id)
                        self._rebuild_timeline()
                        return True
        return False

    def _reorder_animations(self, element_id: str) -> None:
        """Update order values for element animations."""
        if element_id in self.element_animations:
            for i, anim in enumerate(self.element_animations[element_id]):
                anim.order = i

    # Motion Paths

    def create_motion_path(
        self,
        element_id: str,
        points: List[Tuple[float, float]],
        duration: float = 2.0,
        closed: bool = False,
        smooth: bool = True
    ) -> ElementAnimation:
        """Create custom motion path animation."""
        motion_path = MotionPath(
            points=points,
            closed=closed,
            smooth=smooth
        )

        animation = ElementAnimation(
            element_id=element_id,
            animation_type=AnimationType.CUSTOM_PATH,
            duration=duration,
            motion_path=motion_path
        )

        if element_id not in self.element_animations:
            self.element_animations[element_id] = []

        animation.order = len(self.element_animations[element_id])
        self.element_animations[element_id].append(animation)
        self._rebuild_timeline()

        return animation

    def add_preset_motion_path(
        self,
        element_id: str,
        path_type: AnimationType,
        duration: float = 2.0
    ) -> ElementAnimation:
        """Add preset motion path (lines, arcs, etc.)."""
        if path_type not in [
            AnimationType.LINES,
            AnimationType.ARCS,
            AnimationType.TURNS,
            AnimationType.SHAPES_PATH,
            AnimationType.LOOPS
        ]:
            path_type = AnimationType.LINES

        return self.add_animation(
            element_id=element_id,
            animation_type=path_type,
            duration=duration
        )

    # Animation Timeline

    def _rebuild_timeline(self) -> None:
        """Rebuild animation timeline."""
        self.animation_timeline.clear()

        # Collect all animations
        all_animations = []
        for animations in self.element_animations.values():
            all_animations.extend(animations)

        # Sort by trigger and order
        trigger_order = {
            AnimationTrigger.AUTO: 0,
            AnimationTrigger.WITH_PREVIOUS: 1,
            AnimationTrigger.AFTER_PREVIOUS: 2,
            AnimationTrigger.ON_CLICK: 3,
        }

        all_animations.sort(
            key=lambda a: (trigger_order.get(a.trigger, 3), a.order)
        )

        self.animation_timeline = all_animations

    def get_timeline(self) -> List[ElementAnimation]:
        """Get animation timeline."""
        return self.animation_timeline

    def get_click_sequence(self) -> List[List[ElementAnimation]]:
        """Get animations grouped by click sequence."""
        sequences = []
        current_sequence = []

        for anim in self.animation_timeline:
            if anim.trigger == AnimationTrigger.ON_CLICK:
                if current_sequence:
                    sequences.append(current_sequence)
                current_sequence = [anim]
            elif anim.trigger == AnimationTrigger.WITH_PREVIOUS:
                current_sequence.append(anim)
            elif anim.trigger == AnimationTrigger.AFTER_PREVIOUS:
                current_sequence.append(anim)
            elif anim.trigger == AnimationTrigger.AUTO:
                current_sequence.append(anim)

        if current_sequence:
            sequences.append(current_sequence)

        return sequences

    # Animation Presets

    def apply_entrance_preset(
        self,
        element_id: str,
        preset: str = "fade"
    ) -> ElementAnimation:
        """Apply entrance animation preset."""
        presets = {
            "fade": AnimationType.FADE_IN,
            "fly": AnimationType.FLY_IN,
            "zoom": AnimationType.ZOOM_IN,
            "bounce": AnimationType.BOUNCE,
            "spin": AnimationType.SWIVEL,
        }

        anim_type = presets.get(preset, AnimationType.FADE_IN)
        return self.add_animation(element_id, anim_type)

    def apply_exit_preset(
        self,
        element_id: str,
        preset: str = "fade"
    ) -> ElementAnimation:
        """Apply exit animation preset."""
        presets = {
            "fade": AnimationType.FADE_OUT,
            "fly": AnimationType.FLY_OUT,
            "zoom": AnimationType.ZOOM_OUT,
            "spin": AnimationType.SHRINK_TURN,
        }

        anim_type = presets.get(preset, AnimationType.FADE_OUT)
        return self.add_animation(element_id, anim_type)

    def apply_emphasis_preset(
        self,
        element_id: str,
        preset: str = "pulse"
    ) -> ElementAnimation:
        """Apply emphasis animation preset."""
        presets = {
            "pulse": AnimationType.PULSE,
            "spin": AnimationType.SPIN,
            "grow": AnimationType.GROW_SHRINK,
            "color": AnimationType.COLOR_PULSE,
        }

        anim_type = presets.get(preset, AnimationType.PULSE)
        return self.add_animation(
            element_id,
            anim_type,
            trigger=AnimationTrigger.WITH_PREVIOUS
        )

    # Copy/Paste Animations

    def copy_animations(
        self,
        source_element_id: str,
        target_element_id: str
    ) -> List[ElementAnimation]:
        """Copy all animations from one element to another."""
        source_animations = self.get_element_animations(source_element_id)
        if not source_animations:
            return []

        new_animations = []
        for anim in source_animations:
            anim_dict = anim.to_dict()
            anim_dict["id"] = str(uuid.uuid4())
            anim_dict["element_id"] = target_element_id

            new_anim = ElementAnimation.from_dict(anim_dict)
            if target_element_id not in self.element_animations:
                self.element_animations[target_element_id] = []

            self.element_animations[target_element_id].append(new_anim)
            new_animations.append(new_anim)

        self._rebuild_timeline()
        return new_animations

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "slide_transitions": {
                slide_id: transition.to_dict()
                for slide_id, transition in self.slide_transitions.items()
            },
            "element_animations": {
                element_id: [anim.to_dict() for anim in animations]
                for element_id, animations in self.element_animations.items()
            }
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load from dictionary."""
        # Load slide transitions
        self.slide_transitions = {
            slide_id: SlideTransition.from_dict(trans_data)
            for slide_id, trans_data in data.get("slide_transitions", {}).items()
        }

        # Load element animations
        self.element_animations = {}
        for element_id, animations_data in data.get("element_animations", {}).items():
            self.element_animations[element_id] = [
                ElementAnimation.from_dict(anim_data)
                for anim_data in animations_data
            ]

        self._rebuild_timeline()

    def clear_all(self) -> None:
        """Clear all animations and transitions."""
        self.slide_transitions.clear()
        self.element_animations.clear()
        self.animation_timeline.clear()
