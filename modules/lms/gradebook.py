"""
NEXUS LMS - Gradebook Module
Handles grade calculation, weighted scoring, grade curves, transcripts, and analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import json


class GradeCategory(Enum):
    ASSIGNMENTS = "assignments"
    QUIZZES = "quizzes"
    EXAMS = "exams"
    PARTICIPATION = "participation"
    PROJECTS = "projects"
    FINAL_EXAM = "final_exam"


class GradingScale(Enum):
    LETTER = "letter"  # A, B, C, D, F
    PERCENTAGE = "percentage"  # 0-100
    POINTS = "points"
    PASS_FAIL = "pass_fail"
    GPA = "gpa"  # 0.0-4.0


@dataclass
class CategoryWeight:
    """Weight configuration for a grade category"""
    category: GradeCategory
    weight: float  # 0.0-1.0 (percentage of final grade)
    drop_lowest: int = 0  # number of lowest scores to drop
    extra_credit_allowed: bool = False


@dataclass
class GradeItem:
    """Individual gradeable item (assignment, quiz, etc.)"""
    id: str
    course_id: str
    title: str
    category: GradeCategory
    max_points: float
    weight: float = 1.0  # within category
    is_extra_credit: bool = False
    due_date: Optional[datetime] = None
    published: bool = False
    include_in_total: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StudentGrade:
    """A student's grade for a specific item"""
    student_id: str
    grade_item_id: str
    score: Optional[float] = None
    max_score: float = 0.0
    percentage: float = 0.0
    is_excused: bool = False
    is_late: bool = False
    late_penalty: float = 0.0
    notes: str = ""
    graded_at: Optional[datetime] = None
    entered_by: Optional[str] = None


@dataclass
class CourseGrade:
    """Overall course grade for a student"""
    student_id: str
    course_id: str

    # Category scores
    category_scores: Dict[str, float] = field(default_factory=dict)  # category: percentage
    category_weights: Dict[str, float] = field(default_factory=dict)

    # Final grades
    total_points: float = 0.0
    earned_points: float = 0.0
    percentage: float = 0.0
    letter_grade: str = ""
    gpa: float = 0.0

    # Status
    is_passing: bool = False
    is_complete: bool = False

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class GradingScheme:
    """Letter grade conversion scheme"""
    name: str
    scale: GradingScale
    thresholds: Dict[str, float] = field(default_factory=dict)  # grade: min_percentage

    def __post_init__(self):
        if not self.thresholds and self.scale == GradingScale.LETTER:
            # Default letter grade thresholds
            self.thresholds = {
                "A+": 97.0,
                "A": 93.0,
                "A-": 90.0,
                "B+": 87.0,
                "B": 83.0,
                "B-": 80.0,
                "C+": 77.0,
                "C": 73.0,
                "C-": 70.0,
                "D+": 67.0,
                "D": 63.0,
                "D-": 60.0,
                "F": 0.0
            }


@dataclass
class Transcript:
    """Student's academic transcript"""
    student_id: str
    courses: List[CourseGrade] = field(default_factory=list)
    cumulative_gpa: float = 0.0
    total_credits: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)


class GradebookManager:
    """Manages gradebook, grade calculation, and reporting"""

    def __init__(self):
        self.grade_items: Dict[str, GradeItem] = {}
        self.student_grades: Dict[str, List[StudentGrade]] = {}  # key: student_id
        self.course_grades: Dict[str, CourseGrade] = {}  # key: f"{student_id}_{course_id}"
        self.category_weights: Dict[str, List[CategoryWeight]] = {}  # key: course_id
        self.grading_schemes: Dict[str, GradingScheme] = {}  # key: course_id

    # Grade item management

    def create_grade_item(
        self,
        course_id: str,
        title: str,
        category: GradeCategory,
        max_points: float,
        **kwargs
    ) -> GradeItem:
        """Create a new gradeable item"""
        import uuid
        item_id = kwargs.get('id', str(uuid.uuid4()))

        item = GradeItem(
            id=item_id,
            course_id=course_id,
            title=title,
            category=category,
            max_points=max_points,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.grade_items[item_id] = item
        return item

    def set_category_weights(
        self,
        course_id: str,
        weights: List[CategoryWeight]
    ) -> bool:
        """Set grade category weights for a course"""
        # Validate weights sum to 1.0
        total_weight = sum(w.weight for w in weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Category weights must sum to 1.0, got {total_weight}")

        self.category_weights[course_id] = weights
        return True

    def set_grading_scheme(
        self,
        course_id: str,
        scheme: GradingScheme
    ) -> bool:
        """Set the grading scheme for a course"""
        self.grading_schemes[course_id] = scheme
        return True

    # Grade entry

    def enter_grade(
        self,
        student_id: str,
        grade_item_id: str,
        score: float,
        **kwargs
    ) -> StudentGrade:
        """Enter a grade for a student"""
        if grade_item_id not in self.grade_items:
            raise ValueError("Grade item not found")

        item = self.grade_items[grade_item_id]

        # Validate score
        if score < 0:
            raise ValueError("Score cannot be negative")

        if not item.is_extra_credit and score > item.max_points:
            raise ValueError(f"Score cannot exceed {item.max_points}")

        # Calculate percentage
        percentage = (score / item.max_points * 100) if item.max_points > 0 else 0

        grade = StudentGrade(
            student_id=student_id,
            grade_item_id=grade_item_id,
            score=score,
            max_score=item.max_points,
            percentage=percentage,
            graded_at=datetime.now(),
            **kwargs
        )

        if student_id not in self.student_grades:
            self.student_grades[student_id] = []

        # Remove existing grade for this item if present
        self.student_grades[student_id] = [
            g for g in self.student_grades[student_id]
            if g.grade_item_id != grade_item_id
        ]

        self.student_grades[student_id].append(grade)

        # Recalculate course grade
        self._calculate_course_grade(student_id, item.course_id)

        return grade

    def excuse_grade(self, student_id: str, grade_item_id: str) -> bool:
        """Excuse a student from a grade item"""
        grade = self._find_student_grade(student_id, grade_item_id)

        if grade:
            grade.is_excused = True
        else:
            # Create excused grade entry
            item = self.grade_items[grade_item_id]
            grade = StudentGrade(
                student_id=student_id,
                grade_item_id=grade_item_id,
                max_score=item.max_points,
                is_excused=True
            )
            if student_id not in self.student_grades:
                self.student_grades[student_id] = []
            self.student_grades[student_id].append(grade)

        # Recalculate
        item = self.grade_items[grade_item_id]
        self._calculate_course_grade(student_id, item.course_id)

        return True

    def get_student_grade(
        self,
        student_id: str,
        grade_item_id: str
    ) -> Optional[StudentGrade]:
        """Get a student's grade for a specific item"""
        return self._find_student_grade(student_id, grade_item_id)

    def _find_student_grade(
        self,
        student_id: str,
        grade_item_id: str
    ) -> Optional[StudentGrade]:
        """Find a student's grade"""
        if student_id not in self.student_grades:
            return None

        for grade in self.student_grades[student_id]:
            if grade.grade_item_id == grade_item_id:
                return grade

        return None

    # Grade calculation

    def _calculate_course_grade(self, student_id: str, course_id: str) -> CourseGrade:
        """Calculate overall course grade for a student"""
        # Get all grade items for this course
        course_items = [
            item for item in self.grade_items.values()
            if item.course_id == course_id and item.published and item.include_in_total
        ]

        # Get category weights
        weights = self.category_weights.get(course_id, [])
        weight_dict = {w.category: w for w in weights}

        # Group items by category
        items_by_category: Dict[GradeCategory, List[GradeItem]] = {}
        for item in course_items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)

        # Calculate category scores
        category_scores = {}
        category_percentages = {}

        for category, items in items_by_category.items():
            score, max_score = self._calculate_category_score(
                student_id,
                items,
                weight_dict.get(category)
            )

            category_scores[category.value] = score
            category_percentages[category.value] = (
                (score / max_score * 100) if max_score > 0 else 0
            )

        # Calculate weighted final grade
        total_percentage = 0.0

        if weights:
            # Weighted calculation
            for category, weight_config in weight_dict.items():
                if category.value in category_percentages:
                    total_percentage += category_percentages[category.value] * weight_config.weight
        else:
            # Simple average if no weights configured
            if category_percentages:
                total_percentage = sum(category_percentages.values()) / len(category_percentages)

        # Get grading scheme
        scheme = self.grading_schemes.get(course_id, GradingScheme(
            name="Default",
            scale=GradingScale.LETTER
        ))

        # Convert to letter grade
        letter_grade = self._percentage_to_letter(total_percentage, scheme)
        gpa = self._letter_to_gpa(letter_grade)

        # Create/update course grade
        grade_key = f"{student_id}_{course_id}"
        course_grade = CourseGrade(
            student_id=student_id,
            course_id=course_id,
            category_scores=category_scores,
            category_weights={k.value: v.weight for k, v in weight_dict.items()},
            percentage=total_percentage,
            letter_grade=letter_grade,
            gpa=gpa,
            is_passing=total_percentage >= 60.0,
            last_updated=datetime.now()
        )

        self.course_grades[grade_key] = course_grade
        return course_grade

    def _calculate_category_score(
        self,
        student_id: str,
        items: List[GradeItem],
        weight_config: Optional[CategoryWeight]
    ) -> Tuple[float, float]:
        """Calculate score for a category"""
        scores: List[Tuple[float, float]] = []  # (earned, max)

        for item in items:
            grade = self._find_student_grade(student_id, item.id)

            if grade and grade.is_excused:
                continue  # Skip excused items

            if grade and grade.score is not None:
                earned = grade.score
                max_points = item.max_points
            else:
                # No grade yet - count as 0
                earned = 0.0
                max_points = item.max_points

            scores.append((earned, max_points))

        if not scores:
            return 0.0, 0.0

        # Drop lowest scores if configured
        if weight_config and weight_config.drop_lowest > 0:
            # Sort by percentage (ascending)
            scores.sort(key=lambda x: x[0] / x[1] if x[1] > 0 else 0)
            scores = scores[weight_config.drop_lowest:]

        # Sum up
        total_earned = sum(s[0] for s in scores)
        total_max = sum(s[1] for s in scores)

        return total_earned, total_max

    def _percentage_to_letter(
        self,
        percentage: float,
        scheme: GradingScheme
    ) -> str:
        """Convert percentage to letter grade"""
        if scheme.scale != GradingScale.LETTER:
            return f"{percentage:.1f}%"

        # Find appropriate letter grade
        for grade, threshold in sorted(
            scheme.thresholds.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if percentage >= threshold:
                return grade

        return "F"

    def _letter_to_gpa(self, letter: str) -> float:
        """Convert letter grade to GPA"""
        gpa_map = {
            "A+": 4.0, "A": 4.0, "A-": 3.7,
            "B+": 3.3, "B": 3.0, "B-": 2.7,
            "C+": 2.3, "C": 2.0, "C-": 1.7,
            "D+": 1.3, "D": 1.0, "D-": 0.7,
            "F": 0.0
        }
        return gpa_map.get(letter, 0.0)

    # Reporting and analytics

    def get_course_grade(self, student_id: str, course_id: str) -> Optional[CourseGrade]:
        """Get a student's overall grade for a course"""
        grade_key = f"{student_id}_{course_id}"
        return self.course_grades.get(grade_key)

    def get_student_gradebook(
        self,
        student_id: str,
        course_id: str
    ) -> Dict[str, Any]:
        """Get complete gradebook view for a student"""
        # Get all grades
        student_grades_list = self.student_grades.get(student_id, [])

        # Filter by course
        course_items = [
            item for item in self.grade_items.values()
            if item.course_id == course_id
        ]

        grade_details = []
        for item in course_items:
            grade = self._find_student_grade(student_id, item.id)

            grade_details.append({
                "item": item,
                "grade": grade,
                "percentage": grade.percentage if grade else None,
                "score": f"{grade.score}/{item.max_points}" if grade and grade.score is not None else "Not graded"
            })

        # Get overall grade
        course_grade = self.get_course_grade(student_id, course_id)

        return {
            "course_id": course_id,
            "student_id": student_id,
            "grades": grade_details,
            "overall_grade": course_grade,
            "category_breakdown": course_grade.category_scores if course_grade else {}
        }

    def get_course_gradebook(self, course_id: str) -> List[Dict[str, Any]]:
        """Get gradebook for all students in a course"""
        # Get all unique students who have grades in this course
        students = set()
        for item in self.grade_items.values():
            if item.course_id == course_id:
                for student_id, grades in self.student_grades.items():
                    if any(g.grade_item_id == item.id for g in grades):
                        students.add(student_id)

        # Get gradebook for each student
        gradebooks = []
        for student_id in students:
            gradebook = self.get_student_gradebook(student_id, course_id)
            gradebooks.append(gradebook)

        return gradebooks

    def generate_transcript(self, student_id: str) -> Transcript:
        """Generate academic transcript for a student"""
        # Get all course grades for student
        courses = []
        total_gpa_points = 0.0
        total_credits = 0.0

        for grade_key, course_grade in self.course_grades.items():
            if course_grade.student_id == student_id:
                courses.append(course_grade)
                # Assuming 3 credits per course (could be configurable)
                credits = 3.0
                total_gpa_points += course_grade.gpa * credits
                total_credits += credits

        cumulative_gpa = total_gpa_points / total_credits if total_credits > 0 else 0.0

        return Transcript(
            student_id=student_id,
            courses=courses,
            cumulative_gpa=cumulative_gpa,
            total_credits=total_credits
        )

    def get_grade_distribution(self, course_id: str) -> Dict[str, int]:
        """Get grade distribution for a course"""
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

        for grade_key, course_grade in self.course_grades.items():
            if course_grade.course_id == course_id:
                letter = course_grade.letter_grade[0] if course_grade.letter_grade else "F"
                if letter in distribution:
                    distribution[letter] += 1

        return distribution

    def apply_curve(
        self,
        course_id: str,
        target_average: float = 80.0
    ) -> bool:
        """Apply a curve to course grades"""
        # Get all course grades
        course_grades_list = [
            grade for grade in self.course_grades.values()
            if grade.course_id == course_id
        ]

        if not course_grades_list:
            return False

        # Calculate current average
        current_avg = sum(g.percentage for g in course_grades_list) / len(course_grades_list)

        # Calculate curve adjustment
        adjustment = target_average - current_avg

        # Apply to all students
        for course_grade in course_grades_list:
            course_grade.percentage = min(100.0, course_grade.percentage + adjustment)

            # Recalculate letter grade
            scheme = self.grading_schemes.get(course_id, GradingScheme(
                name="Default",
                scale=GradingScale.LETTER
            ))
            course_grade.letter_grade = self._percentage_to_letter(course_grade.percentage, scheme)
            course_grade.gpa = self._letter_to_gpa(course_grade.letter_grade)

        return True


# Example usage
if __name__ == "__main__":
    manager = GradebookManager()

    # Set up course grading
    course_id = "course_001"

    # Configure category weights
    manager.set_category_weights(course_id, [
        CategoryWeight(GradeCategory.ASSIGNMENTS, 0.30, drop_lowest=1),
        CategoryWeight(GradeCategory.QUIZZES, 0.20, drop_lowest=2),
        CategoryWeight(GradeCategory.EXAMS, 0.30),
        CategoryWeight(GradeCategory.FINAL_EXAM, 0.20)
    ])

    # Create grade items
    assignment1 = manager.create_grade_item(
        course_id, "Assignment 1", GradeCategory.ASSIGNMENTS, 100.0
    )
    quiz1 = manager.create_grade_item(
        course_id, "Quiz 1", GradeCategory.QUIZZES, 50.0
    )

    # Enter grades
    manager.enter_grade("student_001", assignment1.id, 95.0)
    manager.enter_grade("student_001", quiz1.id, 48.0)

    # Get course grade
    course_grade = manager.get_course_grade("student_001", course_id)
    if course_grade:
        print(f"Overall Grade: {course_grade.letter_grade} ({course_grade.percentage:.1f}%)")
        print(f"GPA: {course_grade.gpa}")
