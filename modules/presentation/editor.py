"""
Presentation Editor - Main Engine

Central presentation engine that coordinates all modules and provides
a unified interface for presentation creation and editing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from .slide_manager import SlideManager, Slide, SlideLayout, SlideSize
from .element_handler import ElementHandler, ElementType, ShapeType
from .animation import AnimationEngine, AnimationType, TransitionType
from .template_manager import TemplateManager, TemplateCategory
from .theme_builder import ThemeBuilder, ThemeStyle
from .export_renderer import ExportRenderer, ExportFormat, ExportQuality
from .presenter_view import PresenterView, PresentationSettings
from .collaboration import CollaborationManager, User, PermissionLevel
from .ai_assistant import AIAssistant, AIFeature


class PresentationEditor:
    """
    Main presentation editor engine.

    Coordinates all presentation modules and provides unified interface
    for creating, editing, and managing presentations.

    Features:
    - Complete presentation lifecycle management
    - Slide creation and editing
    - Element management
    - Animations and transitions
    - Templates and themes
    - Export to multiple formats
    - Collaboration support
    - AI assistance
    - Presentation mode
    """

    def __init__(self, presentation_id: Optional[str] = None):
        """
        Initialize presentation editor.

        Args:
            presentation_id: Optional existing presentation ID
        """
        self.presentation_id = presentation_id or str(uuid.uuid4())
        self.title = "Untitled Presentation"
        self.author = ""
        self.description = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}

        # Initialize components
        self.slide_manager = SlideManager()
        self.element_handler = ElementHandler()
        self.animation_engine = AnimationEngine()
        self.template_manager = TemplateManager()
        self.theme_builder = ThemeBuilder()
        self.export_renderer = ExportRenderer()
        self.presenter_view = PresenterView()
        self.collaboration_manager = CollaborationManager()
        self.ai_assistant = AIAssistant()

        # Active theme
        self.active_theme_id: Optional[str] = None

    # Presentation Management

    def set_presentation_info(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Set presentation information.

        Args:
            title: Presentation title
            author: Author name
            description: Presentation description
            metadata: Additional metadata
        """
        if title:
            self.title = title
        if author:
            self.author = author
        if description:
            self.description = description
        if metadata:
            self.metadata.update(metadata)

        self._mark_updated()

    def get_presentation_info(self) -> Dict[str, Any]:
        """Get presentation information."""
        return {
            "id": self.presentation_id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "slide_count": self.slide_manager.get_slide_count(),
            "theme_id": self.active_theme_id,
        }

    # Slide Operations

    def add_slide(
        self,
        layout: SlideLayout = SlideLayout.BLANK,
        title: str = "Untitled Slide",
        position: Optional[int] = None,
        template_id: Optional[str] = None
    ) -> Slide:
        """
        Add a new slide.

        Args:
            layout: Slide layout
            title: Slide title
            position: Insert position
            template_id: Optional template to apply

        Returns:
            Created slide
        """
        slide = self.slide_manager.create_slide(layout, title, position)

        # Apply template if specified
        if template_id:
            self.apply_template_to_slide(slide.id, template_id)

        self._mark_updated()
        return slide

    def delete_slide(self, slide_id: str) -> bool:
        """Delete a slide."""
        success = self.slide_manager.delete_slide(slide_id)
        if success:
            # Clean up related data
            self.animation_engine.remove_slide_transition(slide_id)
            self._mark_updated()
        return success

    def duplicate_slide(self, slide_id: str) -> Optional[Slide]:
        """Duplicate a slide."""
        slide = self.slide_manager.duplicate_slide(slide_id)
        if slide:
            self._mark_updated()
        return slide

    def reorder_slide(self, slide_id: str, new_position: int) -> bool:
        """Reorder a slide."""
        success = self.slide_manager.reorder_slide(slide_id, new_position)
        if success:
            self._mark_updated()
        return success

    def get_all_slides(self) -> List[Slide]:
        """Get all slides."""
        return self.slide_manager.get_all_slides()

    def get_slide(self, slide_id: str) -> Optional[Slide]:
        """Get slide by ID."""
        return self.slide_manager.get_slide(slide_id)

    # Element Operations

    def add_text_element(
        self,
        slide_id: str,
        content: str,
        x: float = 100,
        y: float = 100,
        width: float = 300,
        height: float = 100
    ) -> Optional[str]:
        """
        Add text element to slide.

        Returns:
            Element ID if successful
        """
        from .element_handler import Position, Size

        element = self.element_handler.create_text_element(
            content=content,
            position=Position(x, y),
            size=Size(width, height)
        )

        # Add element to slide
        slide = self.slide_manager.get_slide(slide_id)
        if slide:
            slide.elements.append(element.to_dict())
            slide.update()
            self._mark_updated()
            return element.id

        return None

    def add_image_element(
        self,
        slide_id: str,
        image_url: str,
        x: float = 100,
        y: float = 100,
        width: float = 400,
        height: float = 300
    ) -> Optional[str]:
        """Add image element to slide."""
        from .element_handler import Position, Size

        element = self.element_handler.create_image_element(
            source=image_url,
            position=Position(x, y),
            size=Size(width, height)
        )

        slide = self.slide_manager.get_slide(slide_id)
        if slide:
            slide.elements.append(element.to_dict())
            slide.update()
            self._mark_updated()
            return element.id

        return None

    def add_shape_element(
        self,
        slide_id: str,
        shape_type: ShapeType,
        x: float = 100,
        y: float = 100,
        width: float = 200,
        height: float = 200
    ) -> Optional[str]:
        """Add shape element to slide."""
        from .element_handler import Position, Size

        element = self.element_handler.create_shape_element(
            shape_type=shape_type,
            position=Position(x, y),
            size=Size(width, height)
        )

        slide = self.slide_manager.get_slide(slide_id)
        if slide:
            slide.elements.append(element.to_dict())
            slide.update()
            self._mark_updated()
            return element.id

        return None

    def delete_element(self, slide_id: str, element_id: str) -> bool:
        """Delete element from slide."""
        slide = self.slide_manager.get_slide(slide_id)
        if slide:
            slide.elements = [
                e for e in slide.elements
                if e.get("id") != element_id
            ]
            slide.update()
            self.animation_engine.remove_all_animations(element_id)
            self._mark_updated()
            return True
        return False

    # Animation Operations

    def add_animation(
        self,
        element_id: str,
        animation_type: AnimationType,
        duration: float = 0.5
    ) -> Optional[str]:
        """
        Add animation to element.

        Returns:
            Animation ID if successful
        """
        animation = self.animation_engine.add_animation(
            element_id=element_id,
            animation_type=animation_type,
            duration=duration
        )
        self._mark_updated()
        return animation.id

    def set_slide_transition(
        self,
        slide_id: str,
        transition_type: TransitionType,
        duration: float = 0.5
    ) -> None:
        """Set transition for slide."""
        self.animation_engine.set_slide_transition(
            slide_id=slide_id,
            transition_type=transition_type,
            duration=duration
        )
        self._mark_updated()

    # Template and Theme Operations

    def apply_template_to_slide(
        self,
        slide_id: str,
        template_id: str,
        replacements: Optional[Dict[str, str]] = None
    ) -> bool:
        """Apply template to slide."""
        template_data = self.template_manager.apply_template(
            template_id=template_id,
            replacements=replacements
        )

        if not template_data:
            return False

        slide = self.slide_manager.get_slide(slide_id)
        if slide:
            slide.elements = template_data["elements"]
            slide.background = template_data["background"]
            slide.update()
            self._mark_updated()
            return True

        return False

    def apply_theme(self, theme_id: str) -> bool:
        """Apply theme to entire presentation."""
        theme = self.theme_builder.get_theme(theme_id)
        if not theme:
            return False

        self.active_theme_id = theme_id

        # Apply theme to all slides
        for slide in self.slide_manager.get_all_slides():
            slide.background = theme.background.to_dict()
            slide.update()

        self._mark_updated()
        return True

    def get_available_templates(
        self,
        category: Optional[TemplateCategory] = None
    ) -> List[Dict[str, Any]]:
        """Get available templates."""
        if category:
            templates = self.template_manager.get_templates_by_category(category)
        else:
            templates = self.template_manager.get_all_templates()

        return [t.to_dict() for t in templates]

    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Get available themes."""
        themes = self.theme_builder.get_all_themes()
        return [t.to_dict() for t in themes]

    # Export Operations

    def export(
        self,
        format: ExportFormat,
        quality: ExportQuality = ExportQuality.HIGH,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Export presentation.

        Args:
            format: Export format
            quality: Export quality
            options: Format-specific options

        Returns:
            BytesIO buffer with exported data
        """
        presentation_data = self.to_dict()
        return self.export_renderer.export(
            presentation_data=presentation_data,
            format=format,
            quality=quality,
            options=options
        )

    # Presentation Mode

    def start_presentation(
        self,
        settings: Optional[PresentationSettings] = None,
        target_duration_minutes: Optional[float] = None
    ) -> None:
        """Start presentation mode."""
        slides = [s.to_dict() for s in self.slide_manager.get_all_slides()]
        self.presenter_view.load_presentation(slides, settings)
        self.presenter_view.start_presentation(target_duration_minutes)

    def get_presenter_view(self) -> PresenterView:
        """Get presenter view instance."""
        return self.presenter_view

    # Collaboration

    def add_collaborator(
        self,
        user: User,
        permission: PermissionLevel = PermissionLevel.EDITOR
    ) -> None:
        """Add collaborator to presentation."""
        self.collaboration_manager.join_session(user, permission)

    def add_comment(
        self,
        user: User,
        content: str,
        slide_id: Optional[str] = None,
        element_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Add comment to presentation.

        Returns:
            Comment ID if successful
        """
        comment = self.collaboration_manager.add_comment(
            user=user,
            content=content,
            slide_id=slide_id,
            element_id=element_id
        )
        return comment.id if comment else None

    def create_version(self, user: User, description: str = "") -> str:
        """
        Create version snapshot.

        Returns:
            Version ID
        """
        version = self.collaboration_manager.create_version(
            user=user,
            presentation_data=self.to_dict(),
            description=description
        )
        return version.id

    # AI Assistance

    def generate_presentation_from_topic(
        self,
        topic: str,
        num_slides: int = 10
    ) -> bool:
        """
        Generate presentation from topic using AI.

        Args:
            topic: Presentation topic
            num_slides: Number of slides to generate

        Returns:
            True if successful
        """
        response = self.ai_assistant.generate_presentation_outline(
            topic=topic,
            num_slides=num_slides
        )

        if response.success and response.result:
            self.title = topic
            self.slide_manager.clear_all_slides()

            for slide_data in response.result:
                slide = self.slide_manager.create_slide(
                    title=slide_data.get("title", ""),
                    layout=SlideLayout.TITLE_CONTENT
                )

                # Add content as text elements
                content = slide_data.get("content", [])
                if content:
                    self.add_text_element(
                        slide.id,
                        "\n".join(f"• {item}" for item in content),
                        100, 200, 1720, 700
                    )

            self._mark_updated()
            return True

        return False

    def get_ai_design_suggestions(self, slide_id: str) -> Dict[str, Any]:
        """Get AI design suggestions for slide."""
        slide = self.slide_manager.get_slide(slide_id)
        if not slide:
            return {}

        response = self.ai_assistant.suggest_design_improvements(
            slide.to_dict()
        )

        return response.to_dict()

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Export complete presentation data."""
        return {
            "id": self.presentation_id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "theme_id": self.active_theme_id,
            "slides": [s.to_dict() for s in self.slide_manager.get_all_slides()],
            "animations": self.animation_engine.to_dict(),
            "collaboration": self.collaboration_manager.to_dict(),
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load presentation from data."""
        self.presentation_id = data.get("id", str(uuid.uuid4()))
        self.title = data.get("title", "Untitled Presentation")
        self.author = data.get("author", "")
        self.description = data.get("description", "")

        self.created_at = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        self.updated_at = datetime.fromisoformat(
            data.get("updated_at", datetime.now().isoformat())
        )

        self.metadata = data.get("metadata", {})
        self.active_theme_id = data.get("theme_id")

        # Load slides
        self.slide_manager.from_dict({"slides": data.get("slides", [])})

        # Load animations
        if "animations" in data:
            self.animation_engine.from_dict(data["animations"])

    def save_to_file(self, filepath: str) -> None:
        """Save presentation to JSON file."""
        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, filepath: str) -> None:
        """Load presentation from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.from_dict(data)

    # Utility Methods

    def _mark_updated(self) -> None:
        """Mark presentation as updated."""
        self.updated_at = datetime.now()

    def get_statistics(self) -> Dict[str, Any]:
        """Get presentation statistics."""
        return {
            "total_slides": self.slide_manager.get_slide_count(),
            "visible_slides": self.slide_manager.get_visible_slide_count(),
            "total_elements": sum(
                len(s.elements) for s in self.slide_manager.get_all_slides()
            ),
            "total_animations": len(self.animation_engine.animation_timeline),
            "total_comments": len(self.collaboration_manager.comments),
            "active_collaborators": len(self.collaboration_manager.get_active_users()),
            "versions": len(self.collaboration_manager.versions),
        }

    def validate(self) -> List[str]:
        """
        Validate presentation.

        Returns:
            List of validation errors/warnings
        """
        issues = []

        if not self.title or self.title == "Untitled Presentation":
            issues.append("Presentation needs a title")

        if self.slide_manager.get_slide_count() == 0:
            issues.append("Presentation has no slides")

        # Check for slides with no content
        for slide in self.slide_manager.get_all_slides():
            if not slide.elements:
                issues.append(f"Slide '{slide.title}' has no content")

        return issues
