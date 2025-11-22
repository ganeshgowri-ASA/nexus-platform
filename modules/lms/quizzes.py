"""
NEXUS LMS - Quizzes Module
Handles quiz creation, question banks, automatic grading, and assessment analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    CODE = "code"


class QuizType(Enum):
    PRACTICE = "practice"
    GRADED = "graded"
    EXAM = "exam"
    SURVEY = "survey"


@dataclass
class QuizQuestion:
    """Base quiz question"""
    id: str
    question_type: QuestionType
    question_text: str
    points: float = 1.0
    explanation: str = ""
    tags: List[str] = field(default_factory=list)

    # Multiple choice / True-False
    options: List[str] = field(default_factory=list)
    correct_answers: List[int] = field(default_factory=list)  # indices

    # Short answer / Fill blank
    correct_text_answers: List[str] = field(default_factory=list)
    case_sensitive: bool = False

    # Essay
    sample_answer: str = ""
    rubric: str = ""

    # Matching
    matching_pairs: Dict[str, str] = field(default_factory=dict)

    # Code question
    code_template: str = ""
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    language: str = "python"

    # Settings
    randomize_options: bool = False
    allow_partial_credit: bool = False

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Quiz:
    """Main quiz entity"""
    id: str
    course_id: str
    title: str
    description: str
    quiz_type: QuizType

    # Questions
    questions: List[QuizQuestion] = field(default_factory=list)
    question_bank_id: Optional[str] = None
    randomize_questions: bool = False
    questions_per_attempt: Optional[int] = None  # None = all questions

    # Scoring
    total_points: float = 0.0
    passing_score: float = 70.0
    show_correct_answers: bool = True
    show_answers_after: str = "submission"  # "submission", "deadline", "never"

    # Timing
    time_limit_minutes: Optional[int] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    # Attempt settings
    max_attempts: int = 1
    keep_best_score: bool = True
    allow_review: bool = True
    shuffle_questions: bool = False

    # Access control
    require_password: bool = False
    password: Optional[str] = None
    ip_restrictions: List[str] = field(default_factory=list)

    # Proctoring
    require_webcam: bool = False
    lockdown_browser: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published: bool = False


@dataclass
class QuizAttempt:
    """Student's quiz attempt"""
    id: str
    quiz_id: str
    student_id: str
    attempt_number: int

    # Answers
    answers: Dict[str, Any] = field(default_factory=dict)  # question_id: answer
    question_order: List[str] = field(default_factory=list)

    # Scoring
    score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    passed: bool = False

    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    time_spent_seconds: int = 0

    # Status
    is_completed: bool = False
    is_graded: bool = False
    requires_manual_grading: bool = False

    # Question scores
    question_scores: Dict[str, float] = field(default_factory=dict)  # question_id: score
    feedback: Dict[str, str] = field(default_factory=dict)  # question_id: feedback


@dataclass
class QuestionBank:
    """Reusable question bank"""
    id: str
    name: str
    description: str
    category: str
    questions: List[QuizQuestion] = field(default_factory=list)
    created_by: str = ""
    is_shared: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class QuizManager:
    """Manages quizzes, question banks, and grading"""

    def __init__(self):
        self.quizzes: Dict[str, Quiz] = {}
        self.attempts: Dict[str, List[QuizAttempt]] = {}  # key: quiz_id
        self.question_banks: Dict[str, QuestionBank] = {}

    # Quiz management

    def create_quiz(
        self,
        course_id: str,
        title: str,
        description: str,
        quiz_type: QuizType,
        **kwargs
    ) -> Quiz:
        """Create a new quiz"""
        import uuid
        quiz_id = kwargs.get('id', str(uuid.uuid4()))

        quiz = Quiz(
            id=quiz_id,
            course_id=course_id,
            title=title,
            description=description,
            quiz_type=quiz_type,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.quizzes[quiz_id] = quiz
        return quiz

    def add_question(self, quiz_id: str, question: QuizQuestion) -> bool:
        """Add a question to a quiz"""
        if quiz_id not in self.quizzes:
            return False

        quiz = self.quizzes[quiz_id]
        quiz.questions.append(question)
        quiz.total_points += question.points
        quiz.updated_at = datetime.now()

        return True

    def create_multiple_choice_question(
        self,
        question_text: str,
        options: List[str],
        correct_indices: List[int],
        points: float = 1.0,
        **kwargs
    ) -> QuizQuestion:
        """Create a multiple choice question"""
        import uuid
        return QuizQuestion(
            id=str(uuid.uuid4()),
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text=question_text,
            options=options,
            correct_answers=correct_indices,
            points=points,
            **kwargs
        )

    def create_true_false_question(
        self,
        question_text: str,
        is_true: bool,
        points: float = 1.0,
        **kwargs
    ) -> QuizQuestion:
        """Create a true/false question"""
        import uuid
        return QuizQuestion(
            id=str(uuid.uuid4()),
            question_type=QuestionType.TRUE_FALSE,
            question_text=question_text,
            options=["True", "False"],
            correct_answers=[0 if is_true else 1],
            points=points,
            **kwargs
        )

    def create_short_answer_question(
        self,
        question_text: str,
        correct_answers: List[str],
        points: float = 1.0,
        case_sensitive: bool = False,
        **kwargs
    ) -> QuizQuestion:
        """Create a short answer question"""
        import uuid
        return QuizQuestion(
            id=str(uuid.uuid4()),
            question_type=QuestionType.SHORT_ANSWER,
            question_text=question_text,
            correct_text_answers=correct_answers,
            case_sensitive=case_sensitive,
            points=points,
            **kwargs
        )

    def update_quiz(self, quiz_id: str, **updates) -> Optional[Quiz]:
        """Update quiz settings"""
        if quiz_id not in self.quizzes:
            return None

        quiz = self.quizzes[quiz_id]
        for key, value in updates.items():
            if hasattr(quiz, key):
                setattr(quiz, key, value)

        quiz.updated_at = datetime.now()
        return quiz

    def publish_quiz(self, quiz_id: str) -> bool:
        """Publish a quiz"""
        if quiz_id not in self.quizzes:
            return False

        quiz = self.quizzes[quiz_id]

        if not quiz.questions:
            raise ValueError("Cannot publish quiz without questions")

        quiz.published = True
        quiz.updated_at = datetime.now()
        return True

    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get a quiz by ID"""
        return self.quizzes.get(quiz_id)

    def get_course_quizzes(self, course_id: str) -> List[Quiz]:
        """Get all quizzes for a course"""
        return [
            quiz for quiz in self.quizzes.values()
            if quiz.course_id == course_id
        ]

    # Quiz attempts

    def start_quiz_attempt(self, quiz_id: str, student_id: str) -> QuizAttempt:
        """Start a new quiz attempt"""
        if quiz_id not in self.quizzes:
            raise ValueError("Quiz not found")

        quiz = self.quizzes[quiz_id]

        # Check if quiz is available
        now = datetime.now()
        if quiz.available_from and now < quiz.available_from:
            raise ValueError("Quiz not yet available")
        if quiz.available_until and now > quiz.available_until:
            raise ValueError("Quiz deadline has passed")

        # Check attempt limits
        student_attempts = self.get_student_attempts(quiz_id, student_id)
        if len(student_attempts) >= quiz.max_attempts:
            raise ValueError("Maximum attempts reached")

        # Create attempt
        import uuid
        attempt = QuizAttempt(
            id=str(uuid.uuid4()),
            quiz_id=quiz_id,
            student_id=student_id,
            attempt_number=len(student_attempts) + 1,
            max_score=quiz.total_points
        )

        # Determine question order
        if quiz.shuffle_questions:
            import random
            attempt.question_order = [q.id for q in quiz.questions]
            random.shuffle(attempt.question_order)
        else:
            attempt.question_order = [q.id for q in quiz.questions]

        if quiz_id not in self.attempts:
            self.attempts[quiz_id] = []

        self.attempts[quiz_id].append(attempt)
        return attempt

    def submit_answer(
        self,
        attempt_id: str,
        question_id: str,
        answer: Any
    ) -> bool:
        """Submit an answer for a question"""
        attempt = self._find_attempt(attempt_id)
        if not attempt:
            return False

        if attempt.is_completed:
            raise ValueError("Quiz already submitted")

        attempt.answers[question_id] = answer
        return True

    def submit_quiz(self, attempt_id: str) -> QuizAttempt:
        """Submit a quiz attempt for grading"""
        attempt = self._find_attempt(attempt_id)
        if not attempt:
            raise ValueError("Attempt not found")

        if attempt.is_completed:
            raise ValueError("Quiz already submitted")

        quiz = self.quizzes[attempt.quiz_id]

        attempt.submitted_at = datetime.now()
        attempt.is_completed = True
        attempt.time_spent_seconds = int(
            (attempt.submitted_at - attempt.started_at).total_seconds()
        )

        # Auto-grade
        self._grade_attempt(attempt, quiz)

        return attempt

    def _grade_attempt(self, attempt: QuizAttempt, quiz: Quiz) -> None:
        """Grade a quiz attempt"""
        total_score = 0.0
        requires_manual = False

        # Create question lookup
        questions_dict = {q.id: q for q in quiz.questions}

        for question_id, answer in attempt.answers.items():
            question = questions_dict.get(question_id)
            if not question:
                continue

            score = self._grade_question(question, answer)

            # Check if manual grading needed
            if question.question_type in [QuestionType.ESSAY, QuestionType.CODE]:
                requires_manual = True
                score = 0.0  # Will be graded manually

            attempt.question_scores[question_id] = score
            total_score += score

        attempt.score = total_score
        attempt.percentage = (total_score / quiz.total_points * 100) if quiz.total_points > 0 else 0
        attempt.passed = attempt.percentage >= quiz.passing_score
        attempt.requires_manual_grading = requires_manual
        attempt.is_graded = not requires_manual

    def _grade_question(self, question: QuizQuestion, answer: Any) -> float:
        """Grade a single question"""
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            if isinstance(answer, list):
                # Multiple select
                correct_set = set(question.correct_answers)
                answer_set = set(answer)

                if correct_set == answer_set:
                    return question.points

                if question.allow_partial_credit:
                    correct_selected = len(correct_set & answer_set)
                    incorrect_selected = len(answer_set - correct_set)
                    total_correct = len(correct_set)
                    return max(0, (correct_selected - incorrect_selected) / total_correct * question.points)

            else:
                # Single select
                if answer in question.correct_answers:
                    return question.points

        elif question.question_type == QuestionType.TRUE_FALSE:
            if answer in question.correct_answers:
                return question.points

        elif question.question_type == QuestionType.SHORT_ANSWER:
            answer_str = str(answer).strip()
            for correct in question.correct_text_answers:
                if question.case_sensitive:
                    if answer_str == correct:
                        return question.points
                else:
                    if answer_str.lower() == correct.lower():
                        return question.points

        elif question.question_type == QuestionType.FILL_BLANK:
            # Similar to short answer
            return self._grade_question(
                QuizQuestion(
                    id=question.id,
                    question_type=QuestionType.SHORT_ANSWER,
                    question_text=question.question_text,
                    correct_text_answers=question.correct_text_answers,
                    case_sensitive=question.case_sensitive,
                    points=question.points
                ),
                answer
            )

        return 0.0

    def manual_grade_question(
        self,
        attempt_id: str,
        question_id: str,
        score: float,
        feedback: str = ""
    ) -> bool:
        """Manually grade a question (for essays, code, etc.)"""
        attempt = self._find_attempt(attempt_id)
        if not attempt:
            return False

        quiz = self.quizzes[attempt.quiz_id]
        question = next((q for q in quiz.questions if q.id == question_id), None)

        if not question:
            return False

        # Validate score
        if score < 0 or score > question.points:
            raise ValueError(f"Score must be between 0 and {question.points}")

        # Update scores
        old_score = attempt.question_scores.get(question_id, 0.0)
        attempt.question_scores[question_id] = score
        attempt.feedback[question_id] = feedback

        # Recalculate total
        attempt.score = sum(attempt.question_scores.values())
        attempt.percentage = (attempt.score / quiz.total_points * 100) if quiz.total_points > 0 else 0
        attempt.passed = attempt.percentage >= quiz.passing_score

        # Check if all manual grading is done
        manual_questions = [
            q for q in quiz.questions
            if q.question_type in [QuestionType.ESSAY, QuestionType.CODE]
        ]
        all_graded = all(q.id in attempt.question_scores for q in manual_questions)

        if all_graded:
            attempt.is_graded = True
            attempt.requires_manual_grading = False

        return True

    def get_student_attempts(self, quiz_id: str, student_id: str) -> List[QuizAttempt]:
        """Get all attempts by a student for a quiz"""
        if quiz_id not in self.attempts:
            return []

        return [
            attempt for attempt in self.attempts[quiz_id]
            if attempt.student_id == student_id
        ]

    def get_best_attempt(self, quiz_id: str, student_id: str) -> Optional[QuizAttempt]:
        """Get student's best attempt"""
        attempts = self.get_student_attempts(quiz_id, student_id)
        completed = [a for a in attempts if a.is_completed]

        if not completed:
            return None

        return max(completed, key=lambda a: a.score)

    def _find_attempt(self, attempt_id: str) -> Optional[QuizAttempt]:
        """Find an attempt by ID"""
        for attempts_list in self.attempts.values():
            for attempt in attempts_list:
                if attempt.id == attempt_id:
                    return attempt
        return None

    # Question banks

    def create_question_bank(
        self,
        name: str,
        description: str,
        category: str,
        created_by: str
    ) -> QuestionBank:
        """Create a question bank"""
        import uuid
        bank_id = str(uuid.uuid4())

        bank = QuestionBank(
            id=bank_id,
            name=name,
            description=description,
            category=category,
            created_by=created_by
        )

        self.question_banks[bank_id] = bank
        return bank

    def add_question_to_bank(self, bank_id: str, question: QuizQuestion) -> bool:
        """Add a question to a question bank"""
        if bank_id not in self.question_banks:
            return False

        self.question_banks[bank_id].questions.append(question)
        return True

    # Analytics

    def get_quiz_analytics(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a quiz"""
        if quiz_id not in self.quizzes:
            return None

        quiz = self.quizzes[quiz_id]
        attempts = self.attempts.get(quiz_id, [])
        completed = [a for a in attempts if a.is_completed]

        if not completed:
            return {
                "quiz_id": quiz_id,
                "title": quiz.title,
                "total_attempts": 0,
                "average_score": 0,
                "pass_rate": 0,
                "average_time": 0
            }

        scores = [a.percentage for a in completed]
        times = [a.time_spent_seconds for a in completed]

        return {
            "quiz_id": quiz_id,
            "title": quiz.title,
            "total_attempts": len(completed),
            "average_score": sum(scores) / len(scores),
            "pass_rate": sum(1 for a in completed if a.passed) / len(completed) * 100,
            "average_time": sum(times) // len(times),
            "highest_score": max(scores),
            "lowest_score": min(scores)
        }


# Example usage
if __name__ == "__main__":
    manager = QuizManager()

    # Create a quiz
    quiz = manager.create_quiz(
        course_id="course_001",
        title="Python Basics Quiz",
        description="Test your Python knowledge",
        quiz_type=QuizType.GRADED,
        time_limit_minutes=30,
        max_attempts=3
    )

    # Add questions
    q1 = manager.create_multiple_choice_question(
        question_text="Which of the following is a mutable data type in Python?",
        options=["Tuple", "String", "List", "Integer"],
        correct_indices=[2],
        points=2.0,
        explanation="Lists are mutable in Python"
    )
    manager.add_question(quiz.id, q1)

    q2 = manager.create_true_false_question(
        question_text="Python is a statically-typed language",
        is_true=False,
        points=1.0,
        explanation="Python is dynamically-typed"
    )
    manager.add_question(quiz.id, q2)

    # Publish quiz
    manager.publish_quiz(quiz.id)

    # Student takes quiz
    attempt = manager.start_quiz_attempt(quiz.id, "student_001")
    manager.submit_answer(attempt.id, q1.id, [2])
    manager.submit_answer(attempt.id, q2.id, [1])
    manager.submit_quiz(attempt.id)

    print(f"Quiz: {quiz.title}")
    print(f"Score: {attempt.percentage:.1f}%")
    print(f"Passed: {attempt.passed}")
