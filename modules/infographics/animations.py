"""
Infographics Designer - Animations Module

This module provides animation effects including entrance animations,
transitions, and interactive elements for infographics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class AnimationType(Enum):
    """Types of animations."""
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"
    ROTATE = "rotate"
    BOUNCE = "bounce"
    FLIP = "flip"
    ELASTIC = "elastic"
    PULSE = "pulse"
    SHAKE = "shake"
    SWING = "swing"
    ROLL = "roll"
    GROW = "grow"
    SHRINK = "shrink"
    TYPEWRITER = "typewriter"
    MORPH = "morph"


class AnimationDirection(Enum):
    """Direction for directional animations."""
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


class EasingFunction(Enum):
    """Easing functions for animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_QUART = "ease_in_quart"
    EASE_OUT_QUART = "ease_out_quart"
    EASE_IN_OUT_QUART = "ease_in_out_quart"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_IN_OUT_BACK = "ease_in_out_back"
    EASE_IN_ELASTIC = "ease_in_elastic"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_IN_OUT_ELASTIC = "ease_in_out_elastic"
    EASE_IN_BOUNCE = "ease_in_bounce"
    EASE_OUT_BOUNCE = "ease_out_bounce"
    EASE_IN_OUT_BOUNCE = "ease_in_out_bounce"


class TriggerType(Enum):
    """Animation trigger types."""
    ON_LOAD = "on_load"
    ON_CLICK = "on_click"
    ON_HOVER = "on_hover"
    ON_SCROLL = "on_scroll"
    AFTER_DELAY = "after_delay"
    AFTER_PREVIOUS = "after_previous"
    WITH_PREVIOUS = "with_previous"


@dataclass
class AnimationConfig:
    """Configuration for an animation."""
    animation_type: AnimationType = AnimationType.FADE
    duration: float = 1000  # milliseconds
    delay: float = 0  # milliseconds
    easing: EasingFunction = EasingFunction.EASE_IN_OUT
    direction: Optional[AnimationDirection] = None
    loop: bool = False
    loop_count: int = 0  # 0 = infinite
    reverse: bool = False
    alternate: bool = False
    trigger: TriggerType = TriggerType.ON_LOAD
    intensity: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'animation_type': self.animation_type.value,
            'duration': self.duration,
            'delay': self.delay,
            'easing': self.easing.value,
            'direction': self.direction.value if self.direction else None,
            'loop': self.loop,
            'loop_count': self.loop_count,
            'reverse': self.reverse,
            'alternate': self.alternate,
            'trigger': self.trigger.value,
            'intensity': self.intensity
        }


@dataclass
class Animation:
    """Represents an animation applied to an element."""
    element_id: str
    name: str
    config: AnimationConfig
    enabled: bool = True
    order: int = 0  # For sequencing animations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'element_id': self.element_id,
            'name': self.name,
            'config': self.config.to_dict(),
            'enabled': self.enabled,
            'order': self.order
        }


class AnimationPresets:
    """Predefined animation presets."""

    @staticmethod
    def fade_in(duration: float = 1000, delay: float = 0) -> AnimationConfig:
        """Fade in animation."""
        return AnimationConfig(
            animation_type=AnimationType.FADE,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_IN
        )

    @staticmethod
    def fade_out(duration: float = 1000, delay: float = 0) -> AnimationConfig:
        """Fade out animation."""
        return AnimationConfig(
            animation_type=AnimationType.FADE,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_OUT,
            reverse=True
        )

    @staticmethod
    def slide_in(direction: AnimationDirection = AnimationDirection.LEFT,
                duration: float = 800, delay: float = 0) -> AnimationConfig:
        """Slide in animation."""
        return AnimationConfig(
            animation_type=AnimationType.SLIDE,
            duration=duration,
            delay=delay,
            direction=direction,
            easing=EasingFunction.EASE_OUT_CUBIC
        )

    @staticmethod
    def slide_out(direction: AnimationDirection = AnimationDirection.RIGHT,
                 duration: float = 800, delay: float = 0) -> AnimationConfig:
        """Slide out animation."""
        return AnimationConfig(
            animation_type=AnimationType.SLIDE,
            duration=duration,
            delay=delay,
            direction=direction,
            easing=EasingFunction.EASE_IN_CUBIC,
            reverse=True
        )

    @staticmethod
    def zoom_in(duration: float = 600, delay: float = 0) -> AnimationConfig:
        """Zoom in animation."""
        return AnimationConfig(
            animation_type=AnimationType.ZOOM,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_OUT_BACK
        )

    @staticmethod
    def zoom_out(duration: float = 600, delay: float = 0) -> AnimationConfig:
        """Zoom out animation."""
        return AnimationConfig(
            animation_type=AnimationType.ZOOM,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_IN_BACK,
            reverse=True
        )

    @staticmethod
    def bounce_in(duration: float = 1000, delay: float = 0) -> AnimationConfig:
        """Bounce in animation."""
        return AnimationConfig(
            animation_type=AnimationType.BOUNCE,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_OUT_BOUNCE
        )

    @staticmethod
    def flip(duration: float = 800, delay: float = 0) -> AnimationConfig:
        """Flip animation."""
        return AnimationConfig(
            animation_type=AnimationType.FLIP,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_IN_OUT
        )

    @staticmethod
    def rotate(duration: float = 1000, delay: float = 0,
              loop: bool = False) -> AnimationConfig:
        """Rotate animation."""
        return AnimationConfig(
            animation_type=AnimationType.ROTATE,
            duration=duration,
            delay=delay,
            easing=EasingFunction.LINEAR,
            loop=loop
        )

    @staticmethod
    def pulse(duration: float = 1500, loop: bool = True) -> AnimationConfig:
        """Pulse animation."""
        return AnimationConfig(
            animation_type=AnimationType.PULSE,
            duration=duration,
            easing=EasingFunction.EASE_IN_OUT,
            loop=loop,
            alternate=True
        )

    @staticmethod
    def shake(duration: float = 500, delay: float = 0) -> AnimationConfig:
        """Shake animation."""
        return AnimationConfig(
            animation_type=AnimationType.SHAKE,
            duration=duration,
            delay=delay,
            easing=EasingFunction.LINEAR
        )

    @staticmethod
    def swing(duration: float = 1000, loop: bool = True) -> AnimationConfig:
        """Swing animation."""
        return AnimationConfig(
            animation_type=AnimationType.SWING,
            duration=duration,
            easing=EasingFunction.EASE_IN_OUT,
            loop=loop,
            alternate=True
        )

    @staticmethod
    def typewriter(duration: float = 2000, delay: float = 0) -> AnimationConfig:
        """Typewriter animation."""
        return AnimationConfig(
            animation_type=AnimationType.TYPEWRITER,
            duration=duration,
            delay=delay,
            easing=EasingFunction.LINEAR
        )

    @staticmethod
    def elastic(duration: float = 1000, delay: float = 0) -> AnimationConfig:
        """Elastic animation."""
        return AnimationConfig(
            animation_type=AnimationType.ELASTIC,
            duration=duration,
            delay=delay,
            easing=EasingFunction.EASE_OUT_ELASTIC
        )


class AnimationSequence:
    """Manages a sequence of animations."""

    def __init__(self, name: str = "Sequence"):
        """Initialize animation sequence."""
        self.name = name
        self.animations: List[Animation] = []

    def add_animation(self, animation: Animation) -> None:
        """Add animation to sequence."""
        animation.order = len(self.animations)
        self.animations.append(animation)

    def remove_animation(self, element_id: str) -> None:
        """Remove animation for element."""
        self.animations = [a for a in self.animations if a.element_id != element_id]
        self._reorder()

    def _reorder(self) -> None:
        """Reorder animations."""
        for i, anim in enumerate(self.animations):
            anim.order = i

    def get_duration(self) -> float:
        """Get total duration of sequence."""
        if not self.animations:
            return 0

        max_time = 0
        for anim in self.animations:
            anim_end = anim.config.delay + anim.config.duration
            if anim_end > max_time:
                max_time = anim_end

        return max_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'animations': [a.to_dict() for a in self.animations],
            'total_duration': self.get_duration()
        }


class TransitionEffect:
    """Transition effects between states."""

    @staticmethod
    def create_hover_effect(scale: float = 1.1,
                          duration: float = 300) -> AnimationConfig:
        """Create hover effect."""
        return AnimationConfig(
            animation_type=AnimationType.GROW,
            duration=duration,
            trigger=TriggerType.ON_HOVER,
            easing=EasingFunction.EASE_OUT,
            intensity=scale
        )

    @staticmethod
    def create_click_effect(duration: float = 200) -> AnimationConfig:
        """Create click effect."""
        return AnimationConfig(
            animation_type=AnimationType.SHRINK,
            duration=duration,
            trigger=TriggerType.ON_CLICK,
            easing=EasingFunction.EASE_IN_OUT,
            intensity=0.95
        )

    @staticmethod
    def create_scroll_reveal(direction: AnimationDirection = AnimationDirection.UP,
                           duration: float = 1000) -> AnimationConfig:
        """Create scroll reveal effect."""
        return AnimationConfig(
            animation_type=AnimationType.SLIDE,
            duration=duration,
            direction=direction,
            trigger=TriggerType.ON_SCROLL,
            easing=EasingFunction.EASE_OUT_CUBIC
        )


class InteractiveEffect:
    """Interactive animation effects."""

    @staticmethod
    def create_button_ripple(duration: float = 600) -> AnimationConfig:
        """Create ripple effect for buttons."""
        return AnimationConfig(
            animation_type=AnimationType.GROW,
            duration=duration,
            trigger=TriggerType.ON_CLICK,
            easing=EasingFunction.EASE_OUT,
            intensity=1.5
        )

    @staticmethod
    def create_loading_spinner(duration: float = 1000) -> AnimationConfig:
        """Create loading spinner animation."""
        return AnimationConfig(
            animation_type=AnimationType.ROTATE,
            duration=duration,
            easing=EasingFunction.LINEAR,
            loop=True
        )

    @staticmethod
    def create_progress_bar(duration: float = 2000) -> AnimationConfig:
        """Create progress bar animation."""
        return AnimationConfig(
            animation_type=AnimationType.GROW,
            duration=duration,
            direction=AnimationDirection.RIGHT,
            easing=EasingFunction.EASE_OUT
        )

    @staticmethod
    def create_tooltip_appear(duration: float = 200) -> AnimationConfig:
        """Create tooltip appearance animation."""
        return AnimationConfig(
            animation_type=AnimationType.FADE,
            duration=duration,
            trigger=TriggerType.ON_HOVER,
            easing=EasingFunction.EASE_OUT
        )


class AnimationTimeline:
    """Manages animation timeline with precise timing control."""

    def __init__(self):
        """Initialize timeline."""
        self.sequences: List[AnimationSequence] = []
        self.current_time: float = 0

    def add_sequence(self, sequence: AnimationSequence,
                    start_time: float = 0) -> None:
        """Add sequence to timeline at specific time."""
        # Adjust all animation delays in sequence
        for anim in sequence.animations:
            anim.config.delay += start_time
        self.sequences.append(sequence)

    def get_total_duration(self) -> float:
        """Get total timeline duration."""
        max_duration = 0
        for sequence in self.sequences:
            seq_duration = sequence.get_duration()
            if seq_duration > max_duration:
                max_duration = seq_duration
        return max_duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sequences': [seq.to_dict() for seq in self.sequences],
            'total_duration': self.get_total_duration()
        }


class AnimationBuilder:
    """Fluent interface for building animations."""

    def __init__(self, element_id: str):
        """Initialize builder."""
        self.element_id = element_id
        self.config = AnimationConfig()
        self.name = "Animation"

    def type(self, animation_type: AnimationType) -> 'AnimationBuilder':
        """Set animation type."""
        self.config.animation_type = animation_type
        return self

    def duration(self, milliseconds: float) -> 'AnimationBuilder':
        """Set duration."""
        self.config.duration = milliseconds
        return self

    def delay(self, milliseconds: float) -> 'AnimationBuilder':
        """Set delay."""
        self.config.delay = milliseconds
        return self

    def easing(self, easing_func: EasingFunction) -> 'AnimationBuilder':
        """Set easing function."""
        self.config.easing = easing_func
        return self

    def direction(self, direction: AnimationDirection) -> 'AnimationBuilder':
        """Set direction."""
        self.config.direction = direction
        return self

    def loop(self, loop: bool = True, count: int = 0) -> 'AnimationBuilder':
        """Set looping."""
        self.config.loop = loop
        self.config.loop_count = count
        return self

    def reverse(self) -> 'AnimationBuilder':
        """Set reverse."""
        self.config.reverse = True
        return self

    def alternate(self) -> 'AnimationBuilder':
        """Set alternate."""
        self.config.alternate = True
        return self

    def trigger(self, trigger_type: TriggerType) -> 'AnimationBuilder':
        """Set trigger."""
        self.config.trigger = trigger_type
        return self

    def intensity(self, value: float) -> 'AnimationBuilder':
        """Set intensity."""
        self.config.intensity = value
        return self

    def build(self) -> Animation:
        """Build animation."""
        return Animation(
            element_id=self.element_id,
            name=self.name,
            config=self.config
        )


__all__ = [
    'AnimationType', 'AnimationDirection', 'EasingFunction', 'TriggerType',
    'AnimationConfig', 'Animation',
    'AnimationPresets', 'AnimationSequence', 'TransitionEffect',
    'InteractiveEffect', 'AnimationTimeline', 'AnimationBuilder'
]
