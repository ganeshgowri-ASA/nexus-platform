"""
NEXUS HR - Performance Management Module
Performance reviews, goals, feedback, and development plans.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class ReviewCycle(Enum):
    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"
    PROBATION = "probation"


class ReviewStatus(Enum):
    NOT_STARTED = "not_started"
    SELF_REVIEW = "self_review"
    MANAGER_REVIEW = "manager_review"
    CALIBRATION = "calibration"
    COMPLETED = "completed"


class GoalStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class PerformanceReview:
    """Performance review"""
    id: str
    review_number: str
    employee_id: str
    employee_name: str
    reviewer_id: str
    reviewer_name: str

    # Period
    review_period_start: date
    review_period_end: date
    review_cycle: ReviewCycle

    # Ratings (1-5 scale)
    overall_rating: Optional[Decimal] = None
    competency_ratings: Dict[str, Decimal] = field(default_factory=dict)

    # Feedback
    strengths: str = ""
    areas_for_improvement: str = ""
    achievements: str = ""
    goals_next_period: str = ""

    # Self review
    self_review_completed: bool = False
    self_rating: Optional[Decimal] = None
    self_comments: str = ""

    # Status
    status: ReviewStatus = ReviewStatus.NOT_STARTED

    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Goal:
    """Employee goal/objective"""
    id: str
    employee_id: str
    title: str
    description: str

    # Timing
    start_date: date
    target_date: date
    completed_date: Optional[date] = None

    # Progress
    status: GoalStatus = GoalStatus.NOT_STARTED
    progress_percentage: int = 0

    # Measurement
    success_criteria: str = ""
    measurable_outcome: str = ""

    # Metadata
    category: str = ""  # "professional", "technical", "leadership"
    priority: str = "medium"  # "low", "medium", "high"

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Feedback:
    """Continuous feedback"""
    id: str
    employee_id: str
    from_user_id: str
    from_user_name: str

    # Content
    feedback_type: str  # "positive", "constructive", "general"
    content: str
    examples: str = ""

    # Visibility
    is_anonymous: bool = False
    is_visible_to_employee: bool = True

    created_at: datetime = field(default_factory=datetime.now)


class PerformanceManager:
    """Performance management"""

    def __init__(self):
        self.reviews: Dict[str, PerformanceReview] = {}
        self.goals: Dict[str, List[Goal]] = {}  # employee_id -> goals
        self.feedback: Dict[str, List[Feedback]] = {}  # employee_id -> feedback
        self.review_counter = 1000

    def create_review(
        self,
        employee_id: str,
        employee_name: str,
        reviewer_id: str,
        reviewer_name: str,
        review_cycle: ReviewCycle,
        period_start: date,
        period_end: date,
        **kwargs
    ) -> PerformanceReview:
        """Create performance review"""
        import uuid
        review_number = f"REV-{self.review_counter}"
        self.review_counter += 1

        review = PerformanceReview(
            id=str(uuid.uuid4()),
            review_number=review_number,
            employee_id=employee_id,
            employee_name=employee_name,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            review_cycle=review_cycle,
            review_period_start=period_start,
            review_period_end=period_end,
            **kwargs
        )

        self.reviews[review.id] = review
        return review

    def submit_self_review(
        self,
        review_id: str,
        self_rating: Decimal,
        comments: str
    ) -> bool:
        """Submit self review"""
        review = self.reviews.get(review_id)
        if not review:
            return False

        review.self_review_completed = True
        review.self_rating = self_rating
        review.self_comments = comments
        review.status = ReviewStatus.MANAGER_REVIEW

        return True

    def complete_review(
        self,
        review_id: str,
        overall_rating: Decimal,
        competency_ratings: Dict[str, Decimal],
        **kwargs
    ) -> bool:
        """Complete manager review"""
        review = self.reviews.get(review_id)
        if not review:
            return False

        review.overall_rating = overall_rating
        review.competency_ratings = competency_ratings

        for key, value in kwargs.items():
            if hasattr(review, key):
                setattr(review, key, value)

        review.status = ReviewStatus.COMPLETED
        review.completed_at = datetime.now()

        return True

    def create_goal(
        self,
        employee_id: str,
        title: str,
        description: str,
        target_date: date,
        **kwargs
    ) -> Goal:
        """Create employee goal"""
        import uuid
        goal = Goal(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            title=title,
            description=description,
            start_date=date.today(),
            target_date=target_date,
            **kwargs
        )

        if employee_id not in self.goals:
            self.goals[employee_id] = []

        self.goals[employee_id].append(goal)
        return goal

    def update_goal_progress(
        self,
        goal_id: str,
        progress_percentage: int,
        status: Optional[GoalStatus] = None
    ) -> Optional[Goal]:
        """Update goal progress"""
        for goals_list in self.goals.values():
            for goal in goals_list:
                if goal.id == goal_id:
                    goal.progress_percentage = min(100, max(0, progress_percentage))

                    if status:
                        goal.status = status

                    if progress_percentage >= 100:
                        goal.status = GoalStatus.COMPLETED
                        goal.completed_date = date.today()

                    goal.updated_at = datetime.now()
                    return goal

        return None

    def add_feedback(
        self,
        employee_id: str,
        from_user_id: str,
        from_user_name: str,
        feedback_type: str,
        content: str,
        **kwargs
    ) -> Feedback:
        """Add feedback"""
        import uuid
        feedback = Feedback(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            from_user_id=from_user_id,
            from_user_name=from_user_name,
            feedback_type=feedback_type,
            content=content,
            **kwargs
        )

        if employee_id not in self.feedback:
            self.feedback[employee_id] = []

        self.feedback[employee_id].append(feedback)
        return feedback

    def get_employee_goals(
        self,
        employee_id: str,
        active_only: bool = False
    ) -> List[Goal]:
        """Get employee goals"""
        goals = self.goals.get(employee_id, [])

        if active_only:
            goals = [
                g for g in goals
                if g.status in [GoalStatus.NOT_STARTED, GoalStatus.IN_PROGRESS]
            ]

        return goals

    def get_employee_feedback(self, employee_id: str) -> List[Feedback]:
        """Get employee feedback"""
        return self.feedback.get(employee_id, [])


if __name__ == "__main__":
    manager = PerformanceManager()

    # Create review
    review = manager.create_review(
        "employee_001",
        "John Doe",
        "manager_001",
        "Jane Smith",
        ReviewCycle.ANNUAL,
        date(2023, 1, 1),
        date(2023, 12, 31)
    )

    # Self review
    manager.submit_self_review(review.id, Decimal("4.0"), "Good year overall")

    # Complete review
    manager.complete_review(
        review.id,
        Decimal("4.5"),
        {"technical": Decimal("5.0"), "communication": Decimal("4.0")},
        strengths="Strong technical skills",
        areas_for_improvement="Leadership development"
    )

    # Create goal
    goal = manager.create_goal(
        "employee_001",
        "Complete AWS Certification",
        "Obtain AWS Solutions Architect certification",
        date(2024, 6, 30),
        category="professional"
    )

    manager.update_goal_progress(goal.id, 50, GoalStatus.IN_PROGRESS)

    print(f"Review: {review.review_number}, Rating: {review.overall_rating}")
    print(f"Goal: {goal.title}, Progress: {goal.progress_percentage}%")
