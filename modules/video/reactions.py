"""
NEXUS Reactions Module - Hand Raise, Emojis, Polls, Q&A
Interactive features for participant engagement
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Set
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ReactionType(Enum):
    """Types of reactions"""
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"
    CLAP = "👏"
    HEART = "❤️"
    LAUGH = "😂"
    SURPRISED = "😮"
    THINKING = "🤔"
    CELEBRATE = "🎉"
    RAISE_HAND = "✋"


class PollStatus(Enum):
    """Poll status"""
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class QuestionStatus(Enum):
    """Q&A question status"""
    PENDING = "pending"
    ANSWERED = "answered"
    DISMISSED = "dismissed"


@dataclass
class Reaction:
    """Represents a participant reaction"""
    id: str = field(default_factory=lambda: str(uuid4()))
    participant_id: str = ""
    participant_name: str = ""
    reaction_type: ReactionType = ReactionType.THUMBS_UP
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 5.0  # How long reaction is displayed

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "participant_id": self.participant_id,
            "participant_name": self.participant_name,
            "reaction": self.reaction_type.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PollOption:
    """A poll option"""
    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    votes: Set[str] = field(default_factory=set)  # Set of participant IDs

    def vote_count(self) -> int:
        """Get vote count"""
        return len(self.votes)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "text": self.text,
            "votes": self.vote_count(),
        }


@dataclass
class Poll:
    """Represents a poll"""
    id: str = field(default_factory=lambda: str(uuid4()))
    question: str = ""
    options: List[PollOption] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    status: PollStatus = PollStatus.DRAFT
    allow_multiple_choices: bool = False
    anonymous: bool = False
    voters: Set[str] = field(default_factory=set)  # Track who voted
    ended_at: Optional[datetime] = None

    def add_option(self, text: str) -> PollOption:
        """Add a poll option"""
        option = PollOption(text=text)
        self.options.append(option)
        return option

    def vote(self, participant_id: str, option_id: str) -> bool:
        """Cast a vote"""
        if self.status != PollStatus.ACTIVE:
            return False

        # Find option
        option = None
        for opt in self.options:
            if opt.id == option_id:
                option = opt
                break

        if not option:
            return False

        # Check if already voted (if not allowing multiple choices)
        if not self.allow_multiple_choices and participant_id in self.voters:
            # Remove previous votes
            for opt in self.options:
                opt.votes.discard(participant_id)

        # Add vote
        option.votes.add(participant_id)
        self.voters.add(participant_id)

        return True

    def get_results(self) -> Dict:
        """Get poll results"""
        total_votes = len(self.voters)

        results = []
        for option in self.options:
            vote_count = option.vote_count()
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0

            results.append({
                "option_id": option.id,
                "text": option.text,
                "votes": vote_count,
                "percentage": round(percentage, 1),
            })

        return {
            "poll_id": self.id,
            "question": self.question,
            "total_voters": total_votes,
            "results": results,
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question": self.question,
            "options": [opt.to_dict() for opt in self.options],
            "status": self.status.value,
            "allow_multiple_choices": self.allow_multiple_choices,
            "anonymous": self.anonymous,
            "total_voters": len(self.voters),
            "created_at": self.created_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


@dataclass
class Question:
    """Represents a Q&A question"""
    id: str = field(default_factory=lambda: str(uuid4()))
    asked_by: str = ""
    asker_name: str = ""
    question: str = ""
    asked_at: datetime = field(default_factory=datetime.now)
    status: QuestionStatus = QuestionStatus.PENDING
    upvotes: Set[str] = field(default_factory=set)  # Participant IDs who upvoted
    answer: str = ""
    answered_by: Optional[str] = None
    answered_at: Optional[datetime] = None
    is_live: bool = False  # Being answered live

    def upvote(self, participant_id: str) -> bool:
        """Upvote a question"""
        if participant_id in self.upvotes:
            return False

        self.upvotes.add(participant_id)
        return True

    def remove_upvote(self, participant_id: str) -> bool:
        """Remove upvote"""
        if participant_id not in self.upvotes:
            return False

        self.upvotes.remove(participant_id)
        return True

    def get_upvote_count(self) -> int:
        """Get upvote count"""
        return len(self.upvotes)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "asked_by": self.asker_name,
            "question": self.question,
            "status": self.status.value,
            "upvotes": self.get_upvote_count(),
            "answer": self.answer,
            "is_live": self.is_live,
            "asked_at": self.asked_at.isoformat(),
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }


class ReactionManager:
    """
    Manages reactions for a conference
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.recent_reactions: List[Reaction] = []
        self.reaction_history: List[Reaction] = []
        self.max_recent_reactions = 50

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "reaction_sent": [],
        }

        logger.info(f"ReactionManager initialized for conference: {conference_id}")

    def send_reaction(
        self,
        participant_id: str,
        participant_name: str,
        reaction_type: ReactionType,
    ) -> Reaction:
        """Send a reaction"""
        reaction = Reaction(
            participant_id=participant_id,
            participant_name=participant_name,
            reaction_type=reaction_type,
        )

        self.recent_reactions.append(reaction)
        self.reaction_history.append(reaction)

        # Keep only recent reactions
        if len(self.recent_reactions) > self.max_recent_reactions:
            self.recent_reactions.pop(0)

        self._trigger_event("reaction_sent", reaction.to_dict())

        logger.debug(f"Reaction sent by {participant_name}: {reaction_type.value}")
        return reaction

    def get_recent_reactions(self, limit: int = 20) -> List[Reaction]:
        """Get recent reactions"""
        return self.recent_reactions[-limit:]

    def get_reaction_stats(self) -> Dict:
        """Get reaction statistics"""
        stats: Dict[str, int] = {}

        for reaction in self.reaction_history:
            reaction_name = reaction.reaction_type.value
            stats[reaction_name] = stats.get(reaction_name, 0) + 1

        return {
            "total_reactions": len(self.reaction_history),
            "by_type": stats,
        }

    def on_event(self, event_name: str, callback: Callable) -> None:
        """Register an event handler"""
        if event_name in self.event_handlers:
            self.event_handlers[event_name].append(callback)

    def _trigger_event(self, event_name: str, data: Dict) -> None:
        """Trigger an event"""
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_name}: {e}")


class PollManager:
    """
    Manages polls for a conference
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.polls: Dict[str, Poll] = {}
        self.active_poll: Optional[Poll] = None

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "poll_created": [],
            "poll_started": [],
            "poll_ended": [],
            "vote_cast": [],
        }

        logger.info(f"PollManager initialized for conference: {conference_id}")

    def create_poll(
        self,
        question: str,
        options: List[str],
        created_by: str,
        allow_multiple_choices: bool = False,
        anonymous: bool = False,
    ) -> Poll:
        """Create a new poll"""
        poll = Poll(
            question=question,
            created_by=created_by,
            allow_multiple_choices=allow_multiple_choices,
            anonymous=anonymous,
        )

        for option_text in options:
            poll.add_option(option_text)

        self.polls[poll.id] = poll

        self._trigger_event("poll_created", poll.to_dict())

        logger.info(f"Poll created: {question}")
        return poll

    def start_poll(self, poll_id: str) -> bool:
        """Start a poll"""
        poll = self.polls.get(poll_id)
        if not poll or poll.status != PollStatus.DRAFT:
            return False

        poll.status = PollStatus.ACTIVE
        self.active_poll = poll

        self._trigger_event("poll_started", poll.to_dict())

        logger.info(f"Poll started: {poll.question}")
        return True

    def end_poll(self, poll_id: str) -> bool:
        """End a poll"""
        poll = self.polls.get(poll_id)
        if not poll or poll.status != PollStatus.ACTIVE:
            return False

        poll.status = PollStatus.CLOSED
        poll.ended_at = datetime.now()

        if self.active_poll and self.active_poll.id == poll_id:
            self.active_poll = None

        self._trigger_event("poll_ended", {
            **poll.to_dict(),
            "results": poll.get_results(),
        })

        logger.info(f"Poll ended: {poll.question}")
        return True

    def vote(self, poll_id: str, participant_id: str, option_id: str) -> bool:
        """Cast a vote on a poll"""
        poll = self.polls.get(poll_id)
        if not poll:
            return False

        if poll.vote(participant_id, option_id):
            self._trigger_event("vote_cast", {
                "poll_id": poll_id,
                "participant_id": participant_id,
                "option_id": option_id,
            })

            logger.debug(f"Vote cast on poll: {poll_id}")
            return True

        return False

    def get_poll(self, poll_id: str) -> Optional[Poll]:
        """Get a poll"""
        return self.polls.get(poll_id)

    def get_all_polls(self) -> List[Poll]:
        """Get all polls"""
        return list(self.polls.values())

    def get_active_poll(self) -> Optional[Poll]:
        """Get the active poll"""
        return self.active_poll

    def on_event(self, event_name: str, callback: Callable) -> None:
        """Register an event handler"""
        if event_name in self.event_handlers:
            self.event_handlers[event_name].append(callback)

    def _trigger_event(self, event_name: str, data: Dict) -> None:
        """Trigger an event"""
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_name}: {e}")


class QAManager:
    """
    Manages Q&A for a conference
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.questions: Dict[str, Question] = {}
        self.enabled = False

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "question_asked": [],
            "question_answered": [],
            "question_upvoted": [],
            "question_live": [],
        }

        logger.info(f"QAManager initialized for conference: {conference_id}")

    def enable(self) -> None:
        """Enable Q&A"""
        self.enabled = True
        logger.info("Q&A enabled")

    def disable(self) -> None:
        """Disable Q&A"""
        self.enabled = False
        logger.info("Q&A disabled")

    def ask_question(
        self,
        participant_id: str,
        participant_name: str,
        question_text: str,
    ) -> Optional[Question]:
        """Ask a question"""
        if not self.enabled:
            return None

        question = Question(
            asked_by=participant_id,
            asker_name=participant_name,
            question=question_text,
        )

        self.questions[question.id] = question

        self._trigger_event("question_asked", question.to_dict())

        logger.info(f"Question asked by {participant_name}: {question_text[:50]}...")
        return question

    def answer_question(
        self,
        question_id: str,
        answer_text: str,
        answered_by: str,
    ) -> bool:
        """Answer a question"""
        question = self.questions.get(question_id)
        if not question:
            return False

        question.answer = answer_text
        question.answered_by = answered_by
        question.answered_at = datetime.now()
        question.status = QuestionStatus.ANSWERED

        self._trigger_event("question_answered", question.to_dict())

        logger.info(f"Question answered: {question_id}")
        return True

    def mark_question_live(self, question_id: str) -> bool:
        """Mark a question as being answered live"""
        question = self.questions.get(question_id)
        if not question:
            return False

        question.is_live = True

        self._trigger_event("question_live", question.to_dict())

        logger.info(f"Question marked as live: {question_id}")
        return True

    def dismiss_question(self, question_id: str) -> bool:
        """Dismiss a question"""
        question = self.questions.get(question_id)
        if not question:
            return False

        question.status = QuestionStatus.DISMISSED
        logger.info(f"Question dismissed: {question_id}")
        return True

    def upvote_question(
        self,
        question_id: str,
        participant_id: str,
    ) -> bool:
        """Upvote a question"""
        question = self.questions.get(question_id)
        if not question:
            return False

        if question.upvote(participant_id):
            self._trigger_event("question_upvoted", {
                "question_id": question_id,
                "upvotes": question.get_upvote_count(),
            })

            logger.debug(f"Question upvoted: {question_id}")
            return True

        return False

    def get_questions(
        self,
        status: Optional[QuestionStatus] = None,
        sort_by_upvotes: bool = True,
    ) -> List[Question]:
        """Get questions, optionally filtered by status"""
        questions = list(self.questions.values())

        if status:
            questions = [q for q in questions if q.status == status]

        if sort_by_upvotes:
            questions.sort(key=lambda q: q.get_upvote_count(), reverse=True)

        return questions

    def get_pending_questions(self) -> List[Question]:
        """Get pending questions sorted by upvotes"""
        return self.get_questions(status=QuestionStatus.PENDING, sort_by_upvotes=True)

    def get_answered_questions(self) -> List[Question]:
        """Get answered questions"""
        return self.get_questions(status=QuestionStatus.ANSWERED, sort_by_upvotes=False)

    def get_stats(self) -> Dict:
        """Get Q&A statistics"""
        return {
            "total_questions": len(self.questions),
            "pending": len([q for q in self.questions.values() if q.status == QuestionStatus.PENDING]),
            "answered": len([q for q in self.questions.values() if q.status == QuestionStatus.ANSWERED]),
            "dismissed": len([q for q in self.questions.values() if q.status == QuestionStatus.DISMISSED]),
        }

    def on_event(self, event_name: str, callback: Callable) -> None:
        """Register an event handler"""
        if event_name in self.event_handlers:
            self.event_handlers[event_name].append(callback)

    def _trigger_event(self, event_name: str, data: Dict) -> None:
        """Trigger an event"""
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_name}: {e}")
