"""
NEXUS LMS - Course Management Module
Handles course creation, enrollment, curriculum design, and course management.
Rival to Moodle and Canvas LMS platforms.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class CourseStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    IN_PROGRESS = "in_progress"


class CourseLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class CourseModule:
    """Represents a module/section within a course"""
    id: str
    title: str
    description: str
    order: int
    lessons: List[str] = field(default_factory=list)  # lesson IDs
    duration_hours: float = 0.0
    is_locked: bool = False
    prerequisites: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Course:
    """Main course entity with full curriculum management"""
    id: str
    title: str
    description: str
    instructor_id: str
    category: str
    level: CourseLevel
    status: CourseStatus

    # Course content
    modules: List[CourseModule] = field(default_factory=list)
    syllabus: str = ""
    learning_objectives: List[str] = field(default_factory=list)

    # Enrollment and pricing
    enrolled_students: List[str] = field(default_factory=list)
    max_students: Optional[int] = None
    price: float = 0.0
    is_free: bool = True

    # Scheduling
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    enrollment_deadline: Optional[datetime] = None

    # Course settings
    allow_discussions: bool = True
    allow_peer_review: bool = False
    certificate_enabled: bool = True
    passing_grade: float = 70.0

    # Media and resources
    thumbnail_url: str = ""
    preview_video_url: str = ""
    resources: List[Dict[str, str]] = field(default_factory=list)

    # Analytics
    total_enrollments: int = 0
    completion_rate: float = 0.0
    average_rating: float = 0.0
    total_reviews: int = 0

    # Metadata
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None


class CourseManager:
    """Manages course CRUD operations and business logic"""

    def __init__(self):
        self.courses: Dict[str, Course] = {}
        self.categories: List[str] = [
            "Technology", "Business", "Arts", "Science",
            "Health", "Language", "Marketing", "Design"
        ]

    def create_course(
        self,
        title: str,
        description: str,
        instructor_id: str,
        category: str,
        level: CourseLevel,
        **kwargs
    ) -> Course:
        """Create a new course"""
        import uuid
        course_id = kwargs.get('id', str(uuid.uuid4()))

        course = Course(
            id=course_id,
            title=title,
            description=description,
            instructor_id=instructor_id,
            category=category,
            level=level,
            status=CourseStatus.DRAFT,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.courses[course_id] = course
        return course

    def update_course(self, course_id: str, **updates) -> Optional[Course]:
        """Update course details"""
        if course_id not in self.courses:
            return None

        course = self.courses[course_id]
        for key, value in updates.items():
            if hasattr(course, key):
                setattr(course, key, value)

        course.updated_at = datetime.now()
        return course

    def publish_course(self, course_id: str) -> bool:
        """Publish a course to make it available to students"""
        if course_id not in self.courses:
            return False

        course = self.courses[course_id]

        # Validation before publishing
        if not course.modules:
            raise ValueError("Course must have at least one module to publish")
        if not course.learning_objectives:
            raise ValueError("Course must have learning objectives")

        course.status = CourseStatus.PUBLISHED
        course.published_at = datetime.now()
        course.updated_at = datetime.now()

        return True

    def archive_course(self, course_id: str) -> bool:
        """Archive a course"""
        if course_id not in self.courses:
            return False

        self.courses[course_id].status = CourseStatus.ARCHIVED
        self.courses[course_id].updated_at = datetime.now()
        return True

    def enroll_student(self, course_id: str, student_id: str) -> bool:
        """Enroll a student in a course"""
        if course_id not in self.courses:
            return False

        course = self.courses[course_id]

        # Check if course is published
        if course.status != CourseStatus.PUBLISHED:
            raise ValueError("Cannot enroll in unpublished course")

        # Check enrollment deadline
        if course.enrollment_deadline and datetime.now() > course.enrollment_deadline:
            raise ValueError("Enrollment deadline has passed")

        # Check max students
        if course.max_students and len(course.enrolled_students) >= course.max_students:
            raise ValueError("Course is full")

        # Check if already enrolled
        if student_id in course.enrolled_students:
            return False

        course.enrolled_students.append(student_id)
        course.total_enrollments += 1
        course.updated_at = datetime.now()

        return True

    def unenroll_student(self, course_id: str, student_id: str) -> bool:
        """Unenroll a student from a course"""
        if course_id not in self.courses:
            return False

        course = self.courses[course_id]
        if student_id not in course.enrolled_students:
            return False

        course.enrolled_students.remove(student_id)
        course.updated_at = datetime.now()

        return True

    def add_module(self, course_id: str, module: CourseModule) -> bool:
        """Add a module to a course"""
        if course_id not in self.courses:
            return False

        course = self.courses[course_id]
        course.modules.append(module)
        course.modules.sort(key=lambda m: m.order)
        course.updated_at = datetime.now()

        return True

    def get_course(self, course_id: str) -> Optional[Course]:
        """Get a course by ID"""
        return self.courses.get(course_id)

    def get_courses_by_instructor(self, instructor_id: str) -> List[Course]:
        """Get all courses by an instructor"""
        return [
            course for course in self.courses.values()
            if course.instructor_id == instructor_id
        ]

    def get_courses_by_category(self, category: str) -> List[Course]:
        """Get all courses in a category"""
        return [
            course for course in self.courses.values()
            if course.category == category and course.status == CourseStatus.PUBLISHED
        ]

    def search_courses(
        self,
        query: str = "",
        category: Optional[str] = None,
        level: Optional[CourseLevel] = None,
        is_free: Optional[bool] = None,
        min_rating: float = 0.0
    ) -> List[Course]:
        """Search courses with filters"""
        results = list(self.courses.values())

        # Filter by status (only published)
        results = [c for c in results if c.status == CourseStatus.PUBLISHED]

        # Text search
        if query:
            query_lower = query.lower()
            results = [
                c for c in results
                if query_lower in c.title.lower()
                or query_lower in c.description.lower()
                or any(query_lower in tag.lower() for tag in c.tags)
            ]

        # Category filter
        if category:
            results = [c for c in results if c.category == category]

        # Level filter
        if level:
            results = [c for c in results if c.level == level]

        # Price filter
        if is_free is not None:
            results = [c for c in results if c.is_free == is_free]

        # Rating filter
        if min_rating > 0:
            results = [c for c in results if c.average_rating >= min_rating]

        return results

    def get_student_courses(self, student_id: str) -> List[Course]:
        """Get all courses a student is enrolled in"""
        return [
            course for course in self.courses.values()
            if student_id in course.enrolled_students
        ]

    def update_course_rating(self, course_id: str, rating: float) -> bool:
        """Update course rating (called when new review is added)"""
        if course_id not in self.courses:
            return False

        course = self.courses[course_id]
        total_rating = course.average_rating * course.total_reviews
        course.total_reviews += 1
        course.average_rating = (total_rating + rating) / course.total_reviews

        return True

    def clone_course(self, course_id: str, new_title: str, instructor_id: str) -> Optional[Course]:
        """Clone an existing course"""
        if course_id not in self.courses:
            return None

        original = self.courses[course_id]
        import uuid
        new_id = str(uuid.uuid4())

        # Deep copy the course
        cloned = Course(
            id=new_id,
            title=new_title,
            description=original.description,
            instructor_id=instructor_id,
            category=original.category,
            level=original.level,
            status=CourseStatus.DRAFT,
            modules=original.modules.copy(),
            syllabus=original.syllabus,
            learning_objectives=original.learning_objectives.copy(),
            price=original.price,
            is_free=original.is_free,
            allow_discussions=original.allow_discussions,
            allow_peer_review=original.allow_peer_review,
            certificate_enabled=original.certificate_enabled,
            passing_grade=original.passing_grade,
            tags=original.tags.copy()
        )

        self.courses[new_id] = cloned
        return cloned

    def get_course_analytics(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a course"""
        if course_id not in self.courses:
            return None

        course = self.courses[course_id]

        return {
            "course_id": course_id,
            "title": course.title,
            "total_enrollments": course.total_enrollments,
            "active_students": len(course.enrolled_students),
            "completion_rate": course.completion_rate,
            "average_rating": course.average_rating,
            "total_reviews": course.total_reviews,
            "revenue": course.total_enrollments * course.price if not course.is_free else 0,
            "modules_count": len(course.modules),
            "status": course.status.value
        }


# Example usage and testing
if __name__ == "__main__":
    manager = CourseManager()

    # Create a sample course
    course = manager.create_course(
        title="Python for Data Science",
        description="Learn Python programming with focus on data science applications",
        instructor_id="instructor_001",
        category="Technology",
        level=CourseLevel.INTERMEDIATE,
        tags=["python", "data-science", "programming"],
        learning_objectives=[
            "Master Python fundamentals",
            "Work with NumPy and Pandas",
            "Create data visualizations",
            "Build ML models"
        ]
    )

    # Add a module
    module = CourseModule(
        id="mod_001",
        title="Introduction to Python",
        description="Python basics and setup",
        order=1,
        duration_hours=5.0
    )
    manager.add_module(course.id, module)

    # Publish the course
    manager.publish_course(course.id)

    # Enroll students
    manager.enroll_student(course.id, "student_001")
    manager.enroll_student(course.id, "student_002")

    print(f"Course created: {course.title}")
    print(f"Enrolled students: {len(course.enrolled_students)}")
