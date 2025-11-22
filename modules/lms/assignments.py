"""
NEXUS LMS - Assignments Module
Handles assignment creation, submissions, file uploads, peer review, and grading.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class AssignmentType(Enum):
    TEXT = "text"
    FILE_UPLOAD = "file_upload"
    CODE_SUBMISSION = "code_submission"
    PEER_REVIEW = "peer_review"
    GROUP_PROJECT = "group_project"
    PRESENTATION = "presentation"


class SubmissionStatus(Enum):
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    RETURNED = "returned"


@dataclass
class Assignment:
    """Main assignment entity"""
    id: str
    course_id: str
    title: str
    description: str
    assignment_type: AssignmentType

    # Instructions and requirements
    instructions: str = ""
    requirements: List[str] = field(default_factory=list)
    rubric: Dict[str, Any] = field(default_factory=dict)

    # Scoring
    max_points: float = 100.0

    # Deadlines
    available_from: Optional[datetime] = None
    due_date: Optional[datetime] = None
    late_submission_allowed: bool = True
    late_penalty_percent: float = 10.0  # per day
    cutoff_date: Optional[datetime] = None  # absolute deadline

    # Submission settings
    allowed_file_types: List[str] = field(default_factory=list)
    max_file_size_mb: float = 10.0
    max_files: int = 5
    allow_resubmission: bool = True
    plagiarism_check: bool = False

    # Peer review settings (if applicable)
    peer_review_enabled: bool = False
    reviews_required: int = 3
    review_deadline: Optional[datetime] = None

    # Group settings
    is_group_assignment: bool = False
    max_group_size: int = 1

    # Feedback
    provide_feedback: bool = True
    auto_publish_grades: bool = False

    # Resources
    attachments: List[Dict[str, str]] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published: bool = False


@dataclass
class Submission:
    """Student's assignment submission"""
    id: str
    assignment_id: str
    student_id: str
    group_id: Optional[str] = None

    # Content
    text_content: str = ""
    files: List[Dict[str, str]] = field(default_factory=list)  # [{name, url, size}]
    code_submission: Dict[str, str] = field(default_factory=dict)  # {filename: code}
    links: List[str] = field(default_factory=list)

    # Status
    status: SubmissionStatus = SubmissionStatus.NOT_SUBMITTED
    is_late: bool = False
    days_late: int = 0

    # Grading
    score: Optional[float] = None
    feedback: str = ""
    rubric_scores: Dict[str, float] = field(default_factory=dict)
    graded_by: Optional[str] = None
    graded_at: Optional[datetime] = None

    # Peer reviews
    peer_reviews: List[str] = field(default_factory=list)  # review IDs

    # Plagiarism
    plagiarism_score: Optional[float] = None
    plagiarism_report: str = ""

    # Timestamps
    submitted_at: Optional[datetime] = None
    last_modified_at: datetime = field(default_factory=datetime.now)
    returned_at: Optional[datetime] = None

    # Attempt tracking
    attempt_number: int = 1
    previous_submissions: List[str] = field(default_factory=list)  # submission IDs


@dataclass
class PeerReview:
    """Peer review of a submission"""
    id: str
    submission_id: str
    reviewer_id: str
    assignment_id: str

    # Review content
    overall_rating: Optional[float] = None
    criterion_ratings: Dict[str, float] = field(default_factory=dict)
    comments: str = ""
    strengths: str = ""
    improvements: str = ""

    # Status
    is_completed: bool = False
    is_helpful: Optional[bool] = None  # rated by submission owner

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Group:
    """Group for group assignments"""
    id: str
    assignment_id: str
    name: str
    members: List[str] = field(default_factory=list)  # student IDs
    leader_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class AssignmentManager:
    """Manages assignments, submissions, and grading"""

    def __init__(self):
        self.assignments: Dict[str, Assignment] = {}
        self.submissions: Dict[str, List[Submission]] = {}  # key: assignment_id
        self.peer_reviews: Dict[str, List[PeerReview]] = {}  # key: submission_id
        self.groups: Dict[str, Group] = {}

    # Assignment management

    def create_assignment(
        self,
        course_id: str,
        title: str,
        description: str,
        assignment_type: AssignmentType,
        **kwargs
    ) -> Assignment:
        """Create a new assignment"""
        import uuid
        assignment_id = kwargs.get('id', str(uuid.uuid4()))

        assignment = Assignment(
            id=assignment_id,
            course_id=course_id,
            title=title,
            description=description,
            assignment_type=assignment_type,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.assignments[assignment_id] = assignment
        return assignment

    def update_assignment(self, assignment_id: str, **updates) -> Optional[Assignment]:
        """Update assignment details"""
        if assignment_id not in self.assignments:
            return None

        assignment = self.assignments[assignment_id]
        for key, value in updates.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)

        assignment.updated_at = datetime.now()
        return assignment

    def publish_assignment(self, assignment_id: str) -> bool:
        """Publish an assignment"""
        if assignment_id not in self.assignments:
            return False

        assignment = self.assignments[assignment_id]

        if not assignment.due_date:
            raise ValueError("Assignment must have a due date")

        assignment.published = True
        assignment.updated_at = datetime.now()
        return True

    def get_assignment(self, assignment_id: str) -> Optional[Assignment]:
        """Get an assignment by ID"""
        return self.assignments.get(assignment_id)

    def get_course_assignments(self, course_id: str) -> List[Assignment]:
        """Get all assignments for a course"""
        return [
            assignment for assignment in self.assignments.values()
            if assignment.course_id == course_id
        ]

    # Submission management

    def submit_assignment(
        self,
        assignment_id: str,
        student_id: str,
        **content
    ) -> Submission:
        """Submit an assignment"""
        if assignment_id not in self.assignments:
            raise ValueError("Assignment not found")

        assignment = self.assignments[assignment_id]

        # Check if assignment is available
        now = datetime.now()
        if assignment.available_from and now < assignment.available_from:
            raise ValueError("Assignment not yet available")

        # Check for existing submission
        existing = self.get_student_submission(assignment_id, student_id)

        if existing:
            if not assignment.allow_resubmission:
                raise ValueError("Resubmission not allowed")
            # Archive previous submission
            existing.previous_submissions.append(existing.id)

        # Check deadline and late status
        is_late = False
        days_late = 0

        if assignment.due_date:
            if now > assignment.due_date:
                is_late = True
                days_late = (now - assignment.due_date).days

                if assignment.cutoff_date and now > assignment.cutoff_date:
                    raise ValueError("Assignment deadline has passed")

                if not assignment.late_submission_allowed:
                    raise ValueError("Late submissions not allowed")

        # Create submission
        import uuid
        submission = Submission(
            id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            student_id=student_id,
            status=SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED,
            is_late=is_late,
            days_late=days_late,
            submitted_at=now,
            **content
        )

        if existing:
            submission.attempt_number = existing.attempt_number + 1

        if assignment_id not in self.submissions:
            self.submissions[assignment_id] = []

        # Remove old submission if exists
        if existing:
            self.submissions[assignment_id] = [
                s for s in self.submissions[assignment_id]
                if s.student_id != student_id
            ]

        self.submissions[assignment_id].append(submission)

        # Trigger peer review assignment if enabled
        if assignment.peer_review_enabled:
            self._assign_peer_reviews(assignment_id, submission.id)

        return submission

    def grade_submission(
        self,
        submission_id: str,
        score: float,
        feedback: str = "",
        graded_by: str = "",
        rubric_scores: Optional[Dict[str, float]] = None
    ) -> bool:
        """Grade a submission"""
        submission = self._find_submission(submission_id)
        if not submission:
            return False

        assignment = self.assignments[submission.assignment_id]

        # Validate score
        if score < 0 or score > assignment.max_points:
            raise ValueError(f"Score must be between 0 and {assignment.max_points}")

        # Apply late penalty if applicable
        final_score = score
        if submission.is_late and assignment.late_penalty_percent > 0:
            penalty = (assignment.late_penalty_percent / 100) * score * submission.days_late
            final_score = max(0, score - penalty)

        submission.score = final_score
        submission.feedback = feedback
        submission.graded_by = graded_by
        submission.graded_at = datetime.now()
        submission.status = SubmissionStatus.GRADED

        if rubric_scores:
            submission.rubric_scores = rubric_scores

        # Auto-publish if enabled
        if assignment.auto_publish_grades:
            submission.status = SubmissionStatus.RETURNED
            submission.returned_at = datetime.now()

        return True

    def return_submission(self, submission_id: str) -> bool:
        """Return graded submission to student"""
        submission = self._find_submission(submission_id)
        if not submission:
            return False

        if submission.status != SubmissionStatus.GRADED:
            raise ValueError("Submission must be graded first")

        submission.status = SubmissionStatus.RETURNED
        submission.returned_at = datetime.now()
        return True

    def get_student_submission(
        self,
        assignment_id: str,
        student_id: str
    ) -> Optional[Submission]:
        """Get a student's submission for an assignment"""
        if assignment_id not in self.submissions:
            return None

        submissions = [
            s for s in self.submissions[assignment_id]
            if s.student_id == student_id
        ]

        return submissions[0] if submissions else None

    def get_assignment_submissions(self, assignment_id: str) -> List[Submission]:
        """Get all submissions for an assignment"""
        return self.submissions.get(assignment_id, [])

    def get_student_assignments(
        self,
        course_id: str,
        student_id: str
    ) -> List[Dict[str, Any]]:
        """Get all assignments and their submission status for a student"""
        assignments = self.get_course_assignments(course_id)
        result = []

        for assignment in assignments:
            if not assignment.published:
                continue

            submission = self.get_student_submission(assignment.id, student_id)

            result.append({
                "assignment": assignment,
                "submission": submission,
                "is_overdue": (
                    datetime.now() > assignment.due_date
                    if assignment.due_date and not submission
                    else False
                )
            })

        return result

    def _find_submission(self, submission_id: str) -> Optional[Submission]:
        """Find a submission by ID"""
        for submissions_list in self.submissions.values():
            for submission in submissions_list:
                if submission.id == submission_id:
                    return submission
        return None

    # Peer review

    def _assign_peer_reviews(self, assignment_id: str, submission_id: str) -> None:
        """Automatically assign peer reviews for a submission"""
        assignment = self.assignments[assignment_id]
        all_submissions = self.get_assignment_submissions(assignment_id)

        if len(all_submissions) < assignment.reviews_required:
            return  # Not enough submissions yet

        # Simple round-robin assignment
        import random
        other_submissions = [s for s in all_submissions if s.id != submission_id]
        reviewers = random.sample(
            other_submissions,
            min(assignment.reviews_required, len(other_submissions))
        )

        for reviewer_submission in reviewers:
            self.create_peer_review(
                submission_id,
                reviewer_submission.student_id,
                assignment_id
            )

    def create_peer_review(
        self,
        submission_id: str,
        reviewer_id: str,
        assignment_id: str
    ) -> PeerReview:
        """Create a peer review assignment"""
        import uuid
        review = PeerReview(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            reviewer_id=reviewer_id,
            assignment_id=assignment_id
        )

        if submission_id not in self.peer_reviews:
            self.peer_reviews[submission_id] = []

        self.peer_reviews[submission_id].append(review)
        return review

    def submit_peer_review(
        self,
        review_id: str,
        overall_rating: float,
        comments: str,
        **kwargs
    ) -> bool:
        """Submit a peer review"""
        review = self._find_peer_review(review_id)
        if not review:
            return False

        review.overall_rating = overall_rating
        review.comments = comments
        review.is_completed = True
        review.completed_at = datetime.now()

        for key, value in kwargs.items():
            if hasattr(review, key):
                setattr(review, key, value)

        return True

    def get_submission_reviews(self, submission_id: str) -> List[PeerReview]:
        """Get all peer reviews for a submission"""
        return self.peer_reviews.get(submission_id, [])

    def _find_peer_review(self, review_id: str) -> Optional[PeerReview]:
        """Find a peer review by ID"""
        for reviews_list in self.peer_reviews.values():
            for review in reviews_list:
                if review.id == review_id:
                    return review
        return None

    # Group assignments

    def create_group(
        self,
        assignment_id: str,
        name: str,
        members: List[str],
        leader_id: Optional[str] = None
    ) -> Group:
        """Create a group for a group assignment"""
        assignment = self.assignments[assignment_id]

        if not assignment.is_group_assignment:
            raise ValueError("Not a group assignment")

        if len(members) > assignment.max_group_size:
            raise ValueError(f"Group size exceeds maximum of {assignment.max_group_size}")

        import uuid
        group = Group(
            id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            name=name,
            members=members,
            leader_id=leader_id or members[0]
        )

        self.groups[group.id] = group
        return group

    # Analytics

    def get_assignment_analytics(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for an assignment"""
        if assignment_id not in self.assignments:
            return None

        assignment = self.assignments[assignment_id]
        submissions = self.get_assignment_submissions(assignment_id)

        submitted = [s for s in submissions if s.status != SubmissionStatus.NOT_SUBMITTED]
        graded = [s for s in submissions if s.status == SubmissionStatus.GRADED or s.status == SubmissionStatus.RETURNED]
        late = [s for s in submissions if s.is_late]

        scores = [s.score for s in graded if s.score is not None]

        return {
            "assignment_id": assignment_id,
            "title": assignment.title,
            "total_submissions": len(submitted),
            "graded_submissions": len(graded),
            "late_submissions": len(late),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "pending_grading": len(submitted) - len(graded)
        }


# Example usage
if __name__ == "__main__":
    manager = AssignmentManager()

    # Create an assignment
    assignment = manager.create_assignment(
        course_id="course_001",
        title="Python Data Structures Assignment",
        description="Implement various data structures",
        assignment_type=AssignmentType.CODE_SUBMISSION,
        max_points=100.0,
        due_date=datetime.now() + timedelta(days=7),
        instructions="Implement Stack, Queue, and LinkedList classes",
        allowed_file_types=[".py"],
        plagiarism_check=True
    )

    # Publish assignment
    manager.publish_assignment(assignment.id)

    # Student submits
    submission = manager.submit_assignment(
        assignment.id,
        "student_001",
        text_content="See attached Python file",
        files=[{"name": "data_structures.py", "url": "...", "size": "5KB"}]
    )

    # Grade submission
    manager.grade_submission(
        submission.id,
        score=95.0,
        feedback="Excellent work! Clean implementation.",
        graded_by="instructor_001",
        rubric_scores={"correctness": 45, "style": 25, "documentation": 25}
    )

    # Return to student
    manager.return_submission(submission.id)

    print(f"Assignment: {assignment.title}")
    print(f"Submission score: {submission.score}/{assignment.max_points}")
