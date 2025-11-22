"""
NEXUS LMS - Student Portal Module
Unified student dashboard for courses, progress, discussions, calendar, and notifications.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum


class NotificationType(Enum):
    ASSIGNMENT_DUE = "assignment_due"
    QUIZ_AVAILABLE = "quiz_available"
    GRADE_POSTED = "grade_posted"
    ANNOUNCEMENT = "announcement"
    MESSAGE = "message"
    CERTIFICATE_ISSUED = "certificate_issued"
    COURSE_UPDATE = "course_update"
    DEADLINE_REMINDER = "deadline_reminder"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Student notification"""
    id: str
    student_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: Priority = Priority.MEDIUM

    # Links
    action_url: Optional[str] = None
    action_text: Optional[str] = None

    # Related entities
    course_id: Optional[str] = None
    assignment_id: Optional[str] = None

    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class CalendarEvent:
    """Calendar event for student"""
    id: str
    student_id: str
    title: str
    description: str
    event_type: str  # "assignment", "quiz", "exam", "class", "office_hours"

    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: bool = False

    # Related entities
    course_id: Optional[str] = None
    assignment_id: Optional[str] = None

    # Reminders
    reminders: List[int] = field(default_factory=list)  # minutes before event

    # Recurrence
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "daily", "weekly", "monthly"

    # Metadata
    color: str = "#1a73e8"
    location: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Discussion:
    """Course discussion thread"""
    id: str
    course_id: str
    title: str
    content: str
    author_id: str
    author_name: str

    # Organization
    category: str = "general"
    tags: List[str] = field(default_factory=list)

    # Engagement
    replies: List[str] = field(default_factory=list)  # reply IDs
    views: int = 0
    likes: int = 0
    is_pinned: bool = False
    is_answered: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class DiscussionReply:
    """Reply to a discussion"""
    id: str
    discussion_id: str
    content: str
    author_id: str
    author_name: str

    # Engagement
    likes: int = 0
    is_instructor_reply: bool = False
    is_answer: bool = False  # marked as answer

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StudentDashboard:
    """Aggregated student dashboard data"""
    student_id: str

    # Courses
    active_courses: List[Dict[str, Any]] = field(default_factory=list)
    completed_courses: int = 0

    # Progress
    overall_gpa: float = 0.0
    total_credits: float = 0.0
    completion_rate: float = 0.0

    # Upcoming items
    upcoming_assignments: List[Dict[str, Any]] = field(default_factory=list)
    upcoming_quizzes: List[Dict[str, Any]] = field(default_factory=list)
    upcoming_events: List[CalendarEvent] = field(default_factory=list)

    # Recent activity
    recent_grades: List[Dict[str, Any]] = field(default_factory=list)
    recent_notifications: List[Notification] = field(default_factory=list)
    recent_announcements: List[Dict[str, Any]] = field(default_factory=list)

    # Achievements
    certificates_earned: int = 0
    badges_earned: int = 0

    # Analytics
    time_spent_learning: int = 0  # total hours
    streak_days: int = 0
    last_login: Optional[datetime] = None


@dataclass
class CourseProgress:
    """Detailed progress for a single course"""
    course_id: str
    course_name: str

    # Overall progress
    completion_percentage: float = 0.0
    current_grade: Optional[float] = None
    grade_letter: Optional[str] = None

    # Lessons
    total_lessons: int = 0
    completed_lessons: int = 0
    in_progress_lessons: int = 0

    # Assessments
    assignments_completed: int = 0
    assignments_pending: int = 0
    quizzes_completed: int = 0
    quizzes_pending: int = 0

    # Time tracking
    time_spent: int = 0  # total seconds
    last_accessed: Optional[datetime] = None

    # Next steps
    next_lesson: Optional[Dict[str, Any]] = None
    upcoming_deadlines: List[Dict[str, Any]] = field(default_factory=list)


class StudentPortalManager:
    """Manages student portal, dashboard, and notifications"""

    def __init__(self):
        self.notifications: Dict[str, List[Notification]] = {}  # key: student_id
        self.calendar_events: Dict[str, List[CalendarEvent]] = {}  # key: student_id
        self.discussions: Dict[str, Discussion] = {}
        self.discussion_replies: Dict[str, List[DiscussionReply]] = {}  # key: discussion_id

    # Dashboard

    def get_student_dashboard(
        self,
        student_id: str,
        # These would come from other managers in real implementation
        courses_data: Optional[Dict[str, Any]] = None
    ) -> StudentDashboard:
        """Get comprehensive dashboard for a student"""
        dashboard = StudentDashboard(student_id=student_id)

        # Get notifications
        dashboard.recent_notifications = self.get_notifications(
            student_id, limit=5, unread_only=False
        )

        # Get upcoming events
        dashboard.upcoming_events = self.get_upcoming_events(student_id, days=7)

        # Mock data for demonstration
        # In real implementation, this would query other managers
        if courses_data:
            dashboard.active_courses = courses_data.get('active_courses', [])
            dashboard.completed_courses = courses_data.get('completed_courses', 0)
            dashboard.overall_gpa = courses_data.get('gpa', 0.0)
            dashboard.total_credits = courses_data.get('credits', 0.0)

        return dashboard

    def get_course_progress(
        self,
        student_id: str,
        course_id: str,
        # These would come from other managers
        lessons_data: Optional[Dict[str, Any]] = None,
        grades_data: Optional[Dict[str, Any]] = None
    ) -> CourseProgress:
        """Get detailed progress for a course"""
        progress = CourseProgress(
            course_id=course_id,
            course_name=lessons_data.get('course_name', '') if lessons_data else ''
        )

        if lessons_data:
            progress.total_lessons = lessons_data.get('total', 0)
            progress.completed_lessons = lessons_data.get('completed', 0)
            progress.completion_percentage = (
                (progress.completed_lessons / progress.total_lessons * 100)
                if progress.total_lessons > 0 else 0
            )

        if grades_data:
            progress.current_grade = grades_data.get('percentage')
            progress.grade_letter = grades_data.get('letter')

        return progress

    # Notifications

    def create_notification(
        self,
        student_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        **kwargs
    ) -> Notification:
        """Create a notification for a student"""
        import uuid
        notification = Notification(
            id=str(uuid.uuid4()),
            student_id=student_id,
            notification_type=notification_type,
            title=title,
            message=message,
            **kwargs
        )

        if student_id not in self.notifications:
            self.notifications[student_id] = []

        self.notifications[student_id].append(notification)

        # Sort by priority and date
        self.notifications[student_id].sort(
            key=lambda n: (
                {"urgent": 0, "high": 1, "medium": 2, "low": 3}[n.priority.value],
                -n.created_at.timestamp()
            )
        )

        return notification

    def mark_notification_read(self, notification_id: str, student_id: str) -> bool:
        """Mark a notification as read"""
        if student_id not in self.notifications:
            return False

        for notification in self.notifications[student_id]:
            if notification.id == notification_id:
                notification.is_read = True
                notification.read_at = datetime.now()
                return True

        return False

    def mark_all_read(self, student_id: str) -> int:
        """Mark all notifications as read"""
        if student_id not in self.notifications:
            return 0

        count = 0
        for notification in self.notifications[student_id]:
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now()
                count += 1

        return count

    def get_notifications(
        self,
        student_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a student"""
        if student_id not in self.notifications:
            return []

        notifications = self.notifications[student_id]

        if unread_only:
            notifications = [n for n in notifications if not n.is_read]

        # Remove expired notifications
        now = datetime.now()
        notifications = [
            n for n in notifications
            if not n.expires_at or n.expires_at > now
        ]

        return notifications[:limit]

    def get_unread_count(self, student_id: str) -> int:
        """Get count of unread notifications"""
        notifications = self.get_notifications(student_id, unread_only=True)
        return len(notifications)

    # Calendar

    def create_event(
        self,
        student_id: str,
        title: str,
        description: str,
        event_type: str,
        start_time: datetime,
        **kwargs
    ) -> CalendarEvent:
        """Create a calendar event"""
        import uuid
        event = CalendarEvent(
            id=str(uuid.uuid4()),
            student_id=student_id,
            title=title,
            description=description,
            event_type=event_type,
            start_time=start_time,
            **kwargs
        )

        if student_id not in self.calendar_events:
            self.calendar_events[student_id] = []

        self.calendar_events[student_id].append(event)

        # Auto-create notification for upcoming events
        if event.reminders:
            for minutes in event.reminders:
                reminder_time = start_time - timedelta(minutes=minutes)
                if reminder_time > datetime.now():
                    self.create_notification(
                        student_id=student_id,
                        notification_type=NotificationType.DEADLINE_REMINDER,
                        title=f"Reminder: {title}",
                        message=f"{event_type.title()} starts in {minutes} minutes",
                        priority=Priority.HIGH,
                        action_url=f"/calendar/{event.id}"
                    )

        return event

    def get_events(
        self,
        student_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CalendarEvent]:
        """Get calendar events for a student"""
        if student_id not in self.calendar_events:
            return []

        events = self.calendar_events[student_id]

        if start_date:
            events = [e for e in events if e.start_time >= start_date]

        if end_date:
            events = [e for e in events if e.start_time <= end_date]

        return sorted(events, key=lambda e: e.start_time)

    def get_upcoming_events(self, student_id: str, days: int = 7) -> List[CalendarEvent]:
        """Get upcoming events for next N days"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)

        return self.get_events(student_id, start_date, end_date)

    def get_events_by_day(
        self,
        student_id: str,
        date: datetime
    ) -> List[CalendarEvent]:
        """Get all events for a specific day"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return self.get_events(student_id, start_of_day, end_of_day)

    # Discussions

    def create_discussion(
        self,
        course_id: str,
        title: str,
        content: str,
        author_id: str,
        author_name: str,
        **kwargs
    ) -> Discussion:
        """Create a discussion thread"""
        import uuid
        discussion = Discussion(
            id=str(uuid.uuid4()),
            course_id=course_id,
            title=title,
            content=content,
            author_id=author_id,
            author_name=author_name,
            **kwargs
        )

        self.discussions[discussion.id] = discussion

        return discussion

    def add_reply(
        self,
        discussion_id: str,
        content: str,
        author_id: str,
        author_name: str,
        is_instructor_reply: bool = False
    ) -> DiscussionReply:
        """Add a reply to a discussion"""
        if discussion_id not in self.discussions:
            raise ValueError("Discussion not found")

        import uuid
        reply = DiscussionReply(
            id=str(uuid.uuid4()),
            discussion_id=discussion_id,
            content=content,
            author_id=author_id,
            author_name=author_name,
            is_instructor_reply=is_instructor_reply
        )

        if discussion_id not in self.discussion_replies:
            self.discussion_replies[discussion_id] = []

        self.discussion_replies[discussion_id].append(reply)

        # Update discussion
        discussion = self.discussions[discussion_id]
        discussion.replies.append(reply.id)
        discussion.last_activity = datetime.now()

        return reply

    def mark_as_answer(self, reply_id: str, discussion_id: str) -> bool:
        """Mark a reply as the answer"""
        if discussion_id not in self.discussion_replies:
            return False

        for reply in self.discussion_replies[discussion_id]:
            if reply.id == reply_id:
                reply.is_answer = True
                self.discussions[discussion_id].is_answered = True
                return True

        return False

    def get_course_discussions(
        self,
        course_id: str,
        category: Optional[str] = None
    ) -> List[Discussion]:
        """Get all discussions for a course"""
        discussions = [
            d for d in self.discussions.values()
            if d.course_id == course_id
        ]

        if category:
            discussions = [d for d in discussions if d.category == category]

        # Sort by pinned, then last activity
        discussions.sort(key=lambda d: (not d.is_pinned, -d.last_activity.timestamp()))

        return discussions

    def get_discussion_with_replies(self, discussion_id: str) -> Optional[Dict[str, Any]]:
        """Get discussion with all replies"""
        if discussion_id not in self.discussions:
            return None

        discussion = self.discussions[discussion_id]

        # Increment views
        discussion.views += 1

        replies = self.discussion_replies.get(discussion_id, [])

        return {
            "discussion": discussion,
            "replies": sorted(replies, key=lambda r: r.created_at),
            "reply_count": len(replies)
        }

    def search_discussions(
        self,
        course_id: str,
        query: str
    ) -> List[Discussion]:
        """Search discussions in a course"""
        discussions = self.get_course_discussions(course_id)

        query_lower = query.lower()
        results = [
            d for d in discussions
            if (query_lower in d.title.lower()
                or query_lower in d.content.lower()
                or any(query_lower in tag.lower() for tag in d.tags))
        ]

        return results

    # Analytics

    def get_engagement_stats(self, student_id: str) -> Dict[str, Any]:
        """Get student engagement statistics"""
        # Count discussions and replies
        discussions_created = len([
            d for d in self.discussions.values()
            if d.author_id == student_id
        ])

        replies_posted = 0
        for replies in self.discussion_replies.values():
            replies_posted += len([r for r in replies if r.author_id == student_id])

        return {
            "discussions_created": discussions_created,
            "replies_posted": replies_posted,
            "total_posts": discussions_created + replies_posted,
            "unread_notifications": self.get_unread_count(student_id),
            "upcoming_events_count": len(self.get_upcoming_events(student_id, days=7))
        }


# Example usage
if __name__ == "__main__":
    manager = StudentPortalManager()

    student_id = "student_001"

    # Create notifications
    manager.create_notification(
        student_id=student_id,
        notification_type=NotificationType.ASSIGNMENT_DUE,
        title="Assignment Due Soon",
        message="Python Data Structures assignment is due in 2 days",
        priority=Priority.HIGH,
        action_url="/courses/course_001/assignments/assign_001",
        action_text="View Assignment"
    )

    # Create calendar event
    manager.create_event(
        student_id=student_id,
        title="Python Quiz",
        description="Chapter 3 Quiz",
        event_type="quiz",
        start_time=datetime.now() + timedelta(days=3),
        end_time=datetime.now() + timedelta(days=3, hours=1),
        course_id="course_001",
        reminders=[60, 1440]  # 1 hour and 1 day before
    )

    # Create discussion
    discussion = manager.create_discussion(
        course_id="course_001",
        title="Help with recursion",
        content="Can someone explain how recursion works in Python?",
        author_id=student_id,
        author_name="John Doe",
        category="questions"
    )

    # Add reply
    manager.add_reply(
        discussion.id,
        "Recursion is when a function calls itself...",
        "instructor_001",
        "Dr. Smith",
        is_instructor_reply=True
    )

    # Get dashboard
    dashboard = manager.get_student_dashboard(student_id)

    print(f"Unread notifications: {manager.get_unread_count(student_id)}")
    print(f"Upcoming events: {len(dashboard.upcoming_events)}")
