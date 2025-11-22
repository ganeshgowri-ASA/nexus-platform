"""
NEXUS LMS - Lessons Module
Handles video lessons, content delivery, progress tracking, and interactive learning materials.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class LessonType(Enum):
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    LIVE_SESSION = "live_session"
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"


class ContentFormat(Enum):
    MP4 = "mp4"
    PDF = "pdf"
    HTML = "html"
    SCORM = "scorm"
    MARKDOWN = "markdown"


@dataclass
class VideoContent:
    """Video lesson content"""
    url: str
    duration_seconds: int
    thumbnail_url: str
    quality_options: List[str] = field(default_factory=lambda: ["720p", "1080p"])
    subtitles: Dict[str, str] = field(default_factory=dict)  # language: url
    chapters: List[Dict[str, Any]] = field(default_factory=list)  # timestamp markers
    allow_download: bool = False
    allow_speed_control: bool = True


@dataclass
class TextContent:
    """Text-based lesson content"""
    content: str
    format: ContentFormat = ContentFormat.MARKDOWN
    estimated_reading_time: int = 0  # minutes
    attachments: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class InteractiveContent:
    """Interactive lesson content (simulations, code exercises, etc.)"""
    content_type: str  # "code_exercise", "simulation", "drag_drop", etc.
    content_data: Dict[str, Any] = field(default_factory=dict)
    instructions: str = ""
    solution: str = ""


@dataclass
class LessonProgress:
    """Track student progress on a lesson"""
    student_id: str
    lesson_id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    last_position: int = 0  # for videos: seconds, for text: scroll position
    time_spent: int = 0  # total seconds spent
    completion_percentage: float = 0.0
    is_completed: bool = False
    notes: str = ""
    bookmarks: List[int] = field(default_factory=list)


@dataclass
class Lesson:
    """Main lesson entity"""
    id: str
    course_id: str
    module_id: str
    title: str
    description: str
    lesson_type: LessonType
    order: int

    # Content
    video_content: Optional[VideoContent] = None
    text_content: Optional[TextContent] = None
    interactive_content: Optional[InteractiveContent] = None

    # Settings
    is_preview: bool = False  # free preview lesson
    is_mandatory: bool = True
    allow_comments: bool = True
    prerequisites: List[str] = field(default_factory=list)  # lesson IDs

    # Resources
    resources: List[Dict[str, str]] = field(default_factory=list)
    external_links: List[Dict[str, str]] = field(default_factory=list)

    # Live session (if applicable)
    live_session_url: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    duration_minutes: int = 0

    # Analytics
    total_views: int = 0
    average_completion_rate: float = 0.0
    average_time_spent: int = 0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None


@dataclass
class LessonComment:
    """Comments/discussions on lessons"""
    id: str
    lesson_id: str
    user_id: str
    content: str
    timestamp: int = 0  # video timestamp if applicable
    parent_id: Optional[str] = None  # for replies
    likes: int = 0
    is_instructor_reply: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class LessonManager:
    """Manages lesson CRUD operations and student progress"""

    def __init__(self):
        self.lessons: Dict[str, Lesson] = {}
        self.progress: Dict[str, LessonProgress] = {}  # key: f"{student_id}_{lesson_id}"
        self.comments: Dict[str, List[LessonComment]] = {}  # key: lesson_id

    def create_lesson(
        self,
        course_id: str,
        module_id: str,
        title: str,
        description: str,
        lesson_type: LessonType,
        order: int,
        **kwargs
    ) -> Lesson:
        """Create a new lesson"""
        import uuid
        lesson_id = kwargs.get('id', str(uuid.uuid4()))

        lesson = Lesson(
            id=lesson_id,
            course_id=course_id,
            module_id=module_id,
            title=title,
            description=description,
            lesson_type=lesson_type,
            order=order,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.lessons[lesson_id] = lesson
        return lesson

    def create_video_lesson(
        self,
        course_id: str,
        module_id: str,
        title: str,
        description: str,
        video_url: str,
        duration_seconds: int,
        thumbnail_url: str,
        order: int,
        **kwargs
    ) -> Lesson:
        """Create a video lesson"""
        video_content = VideoContent(
            url=video_url,
            duration_seconds=duration_seconds,
            thumbnail_url=thumbnail_url,
            **{k: v for k, v in kwargs.items() if k in VideoContent.__annotations__}
        )

        return self.create_lesson(
            course_id=course_id,
            module_id=module_id,
            title=title,
            description=description,
            lesson_type=LessonType.VIDEO,
            order=order,
            video_content=video_content,
            duration_minutes=duration_seconds // 60
        )

    def create_text_lesson(
        self,
        course_id: str,
        module_id: str,
        title: str,
        description: str,
        content: str,
        order: int,
        **kwargs
    ) -> Lesson:
        """Create a text-based lesson"""
        text_content = TextContent(
            content=content,
            **{k: v for k, v in kwargs.items() if k in TextContent.__annotations__}
        )

        return self.create_lesson(
            course_id=course_id,
            module_id=module_id,
            title=title,
            description=description,
            lesson_type=LessonType.TEXT,
            order=order,
            text_content=text_content
        )

    def update_lesson(self, lesson_id: str, **updates) -> Optional[Lesson]:
        """Update lesson details"""
        if lesson_id not in self.lessons:
            return None

        lesson = self.lessons[lesson_id]
        for key, value in updates.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        lesson.updated_at = datetime.now()
        return lesson

    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete a lesson"""
        if lesson_id not in self.lessons:
            return False

        del self.lessons[lesson_id]
        return True

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Get a lesson by ID"""
        return self.lessons.get(lesson_id)

    def get_course_lessons(self, course_id: str) -> List[Lesson]:
        """Get all lessons in a course"""
        lessons = [
            lesson for lesson in self.lessons.values()
            if lesson.course_id == course_id
        ]
        return sorted(lessons, key=lambda l: l.order)

    def get_module_lessons(self, module_id: str) -> List[Lesson]:
        """Get all lessons in a module"""
        lessons = [
            lesson for lesson in self.lessons.values()
            if lesson.module_id == module_id
        ]
        return sorted(lessons, key=lambda l: l.order)

    # Progress tracking

    def start_lesson(self, student_id: str, lesson_id: str) -> LessonProgress:
        """Start a lesson (track first access)"""
        if lesson_id not in self.lessons:
            raise ValueError("Lesson not found")

        progress_key = f"{student_id}_{lesson_id}"

        if progress_key in self.progress:
            return self.progress[progress_key]

        progress = LessonProgress(
            student_id=student_id,
            lesson_id=lesson_id
        )

        self.progress[progress_key] = progress

        # Update lesson analytics
        lesson = self.lessons[lesson_id]
        lesson.total_views += 1

        return progress

    def update_progress(
        self,
        student_id: str,
        lesson_id: str,
        last_position: int = 0,
        time_spent: int = 0,
        completion_percentage: float = 0.0
    ) -> Optional[LessonProgress]:
        """Update student progress on a lesson"""
        progress_key = f"{student_id}_{lesson_id}"

        if progress_key not in self.progress:
            progress = self.start_lesson(student_id, lesson_id)
        else:
            progress = self.progress[progress_key]

        progress.last_position = last_position
        progress.time_spent += time_spent
        progress.completion_percentage = completion_percentage

        # Auto-complete if 95% or more
        if completion_percentage >= 95.0 and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.now()

        return progress

    def mark_lesson_complete(self, student_id: str, lesson_id: str) -> bool:
        """Mark a lesson as completed"""
        progress_key = f"{student_id}_{lesson_id}"

        if progress_key not in self.progress:
            progress = self.start_lesson(student_id, lesson_id)
        else:
            progress = self.progress[progress_key]

        progress.is_completed = True
        progress.completion_percentage = 100.0
        progress.completed_at = datetime.now()

        return True

    def get_student_progress(self, student_id: str, lesson_id: str) -> Optional[LessonProgress]:
        """Get student progress for a specific lesson"""
        progress_key = f"{student_id}_{lesson_id}"
        return self.progress.get(progress_key)

    def get_student_course_progress(self, student_id: str, course_id: str) -> Dict[str, Any]:
        """Get overall progress for a student in a course"""
        lessons = self.get_course_lessons(course_id)
        total_lessons = len(lessons)

        if total_lessons == 0:
            return {
                "total_lessons": 0,
                "completed_lessons": 0,
                "in_progress_lessons": 0,
                "completion_percentage": 0.0,
                "total_time_spent": 0
            }

        completed = 0
        in_progress = 0
        total_time = 0

        for lesson in lessons:
            progress = self.get_student_progress(student_id, lesson.id)
            if progress:
                total_time += progress.time_spent
                if progress.is_completed:
                    completed += 1
                elif progress.completion_percentage > 0:
                    in_progress += 1

        return {
            "total_lessons": total_lessons,
            "completed_lessons": completed,
            "in_progress_lessons": in_progress,
            "completion_percentage": (completed / total_lessons) * 100,
            "total_time_spent": total_time
        }

    # Comments and discussions

    def add_comment(
        self,
        lesson_id: str,
        user_id: str,
        content: str,
        timestamp: int = 0,
        parent_id: Optional[str] = None,
        is_instructor_reply: bool = False
    ) -> LessonComment:
        """Add a comment to a lesson"""
        if lesson_id not in self.lessons:
            raise ValueError("Lesson not found")

        lesson = self.lessons[lesson_id]
        if not lesson.allow_comments:
            raise ValueError("Comments not allowed on this lesson")

        import uuid
        comment = LessonComment(
            id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            user_id=user_id,
            content=content,
            timestamp=timestamp,
            parent_id=parent_id,
            is_instructor_reply=is_instructor_reply
        )

        if lesson_id not in self.comments:
            self.comments[lesson_id] = []

        self.comments[lesson_id].append(comment)
        return comment

    def get_lesson_comments(self, lesson_id: str) -> List[LessonComment]:
        """Get all comments for a lesson"""
        return self.comments.get(lesson_id, [])

    def add_bookmark(self, student_id: str, lesson_id: str, position: int) -> bool:
        """Add a bookmark at a specific position in the lesson"""
        progress = self.get_student_progress(student_id, lesson_id)
        if not progress:
            progress = self.start_lesson(student_id, lesson_id)

        if position not in progress.bookmarks:
            progress.bookmarks.append(position)
            progress.bookmarks.sort()

        return True

    def get_next_lesson(self, current_lesson_id: str) -> Optional[Lesson]:
        """Get the next lesson in sequence"""
        if current_lesson_id not in self.lessons:
            return None

        current = self.lessons[current_lesson_id]
        module_lessons = self.get_module_lessons(current.module_id)

        for i, lesson in enumerate(module_lessons):
            if lesson.id == current_lesson_id and i < len(module_lessons) - 1:
                return module_lessons[i + 1]

        return None

    def get_lesson_analytics(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a lesson"""
        if lesson_id not in self.lessons:
            return None

        lesson = self.lessons[lesson_id]

        # Calculate completion stats
        lesson_progress = [
            p for p in self.progress.values()
            if p.lesson_id == lesson_id
        ]

        completed_count = sum(1 for p in lesson_progress if p.is_completed)
        total_started = len(lesson_progress)

        avg_completion = (completed_count / total_started * 100) if total_started > 0 else 0
        avg_time = sum(p.time_spent for p in lesson_progress) // total_started if total_started > 0 else 0

        return {
            "lesson_id": lesson_id,
            "title": lesson.title,
            "type": lesson.lesson_type.value,
            "total_views": lesson.total_views,
            "students_started": total_started,
            "students_completed": completed_count,
            "completion_rate": avg_completion,
            "average_time_spent": avg_time,
            "total_comments": len(self.comments.get(lesson_id, []))
        }


# Example usage
if __name__ == "__main__":
    manager = LessonManager()

    # Create a video lesson
    lesson = manager.create_video_lesson(
        course_id="course_001",
        module_id="module_001",
        title="Introduction to Python",
        description="Learn Python basics",
        video_url="https://example.com/video.mp4",
        duration_seconds=1800,  # 30 minutes
        thumbnail_url="https://example.com/thumb.jpg",
        order=1
    )

    # Student starts the lesson
    progress = manager.start_lesson("student_001", lesson.id)

    # Update progress
    manager.update_progress(
        "student_001",
        lesson.id,
        last_position=900,  # 15 minutes in
        time_spent=900,
        completion_percentage=50.0
    )

    # Add a comment
    manager.add_comment(
        lesson.id,
        "student_001",
        "Great explanation!",
        timestamp=450
    )

    print(f"Lesson created: {lesson.title}")
    print(f"Progress: {progress.completion_percentage}%")
