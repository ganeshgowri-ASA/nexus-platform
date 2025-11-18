"""
NEXUS Breakout Rooms Module - Auto/Manual Assignment with Timer
Supports breakout room creation, assignment, and management
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Set
from uuid import uuid4
import asyncio
import random
import logging

logger = logging.getLogger(__name__)


class AssignmentMethod(Enum):
    """Methods for assigning participants to breakout rooms"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    PARTICIPANT_CHOICE = "participant_choice"


class RoomStatus(Enum):
    """Breakout room status"""
    CREATED = "created"
    OPEN = "open"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class BreakoutRoomSettings:
    """Settings for breakout rooms"""
    assignment_method: AssignmentMethod = AssignmentMethod.AUTOMATIC
    allow_participants_to_choose: bool = False
    allow_participants_to_return: bool = True
    auto_move_participants: bool = True
    auto_close_rooms: bool = True
    duration_minutes: Optional[int] = None
    warning_minutes: int = 1  # Warn before auto-close
    enable_recording: bool = False
    enable_chat: bool = True
    allow_host_to_join_any_room: bool = True


class BreakoutRoom:
    """
    Represents a single breakout room
    """

    def __init__(
        self,
        room_number: int,
        name: Optional[str] = None,
        capacity: int = 50,
    ):
        self.id = str(uuid4())
        self.room_number = room_number
        self.name = name or f"Breakout Room {room_number}"
        self.capacity = capacity

        # Participants
        self.participants: Set[str] = set()
        self.host_id: Optional[str] = None

        # Room state
        self.status = RoomStatus.CREATED
        self.created_at = datetime.now()
        self.opened_at: Optional[datetime] = None
        self.closed_at: Optional[datetime] = None

        # Timer
        self.duration: Optional[timedelta] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.time_remaining: Optional[timedelta] = None

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "participant_joined": [],
            "participant_left": [],
            "room_opened": [],
            "room_closed": [],
            "timer_warning": [],
            "timer_expired": [],
        }

        logger.info(f"BreakoutRoom created: {self.name}")

    def add_participant(self, participant_id: str) -> bool:
        """Add a participant to the room"""
        if len(self.participants) >= self.capacity:
            logger.warning(f"Room {self.name} at capacity")
            return False

        if participant_id in self.participants:
            return False

        self.participants.add(participant_id)
        self._trigger_event("participant_joined", {
            "room_id": self.id,
            "participant_id": participant_id,
        })

        logger.debug(f"Participant {participant_id} added to {self.name}")
        return True

    def remove_participant(self, participant_id: str) -> bool:
        """Remove a participant from the room"""
        if participant_id not in self.participants:
            return False

        self.participants.remove(participant_id)
        self._trigger_event("participant_left", {
            "room_id": self.id,
            "participant_id": participant_id,
        })

        logger.debug(f"Participant {participant_id} removed from {self.name}")
        return True

    def set_host(self, participant_id: str) -> bool:
        """Set a participant as the room host"""
        if participant_id not in self.participants:
            return False

        self.host_id = participant_id
        logger.info(f"Host set for {self.name}: {participant_id}")
        return True

    def open(self) -> bool:
        """Open the room for participants to join"""
        if self.status != RoomStatus.CREATED:
            return False

        self.status = RoomStatus.OPEN
        self.opened_at = datetime.now()

        self._trigger_event("room_opened", {"room_id": self.id})

        logger.info(f"Room opened: {self.name}")
        return True

    def activate(self) -> bool:
        """Activate the room (participants are in it)"""
        if self.status != RoomStatus.OPEN:
            return False

        self.status = RoomStatus.ACTIVE
        logger.info(f"Room activated: {self.name}")
        return True

    def close(self) -> bool:
        """Close the room"""
        if self.status == RoomStatus.CLOSED:
            return False

        self.status = RoomStatus.CLOSING

        # Cancel timer if active
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()

        # Move participants back to main room
        participant_ids = list(self.participants)
        for participant_id in participant_ids:
            self.remove_participant(participant_id)

        self.status = RoomStatus.CLOSED
        self.closed_at = datetime.now()

        self._trigger_event("room_closed", {"room_id": self.id})

        logger.info(f"Room closed: {self.name}")
        return True

    async def start_timer(
        self,
        duration_minutes: int,
        warning_minutes: int = 1,
    ) -> None:
        """Start a timer for the room"""
        self.duration = timedelta(minutes=duration_minutes)
        self.time_remaining = self.duration

        logger.info(f"Timer started for {self.name}: {duration_minutes} minutes")

        # Calculate warning time
        warning_time = duration_minutes - warning_minutes
        if warning_time > 0:
            await asyncio.sleep(warning_time * 60)
            self._trigger_event("timer_warning", {
                "room_id": self.id,
                "minutes_remaining": warning_minutes,
            })
            logger.info(f"Timer warning for {self.name}: {warning_minutes} minutes remaining")

        # Wait for remaining time
        await asyncio.sleep(warning_minutes * 60)

        # Timer expired
        self.time_remaining = timedelta(0)
        self._trigger_event("timer_expired", {"room_id": self.id})
        logger.info(f"Timer expired for {self.name}")

        # Auto-close room
        self.close()

    def get_info(self) -> Dict:
        """Get room information"""
        return {
            "id": self.id,
            "room_number": self.room_number,
            "name": self.name,
            "status": self.status.value,
            "participant_count": len(self.participants),
            "capacity": self.capacity,
            "host_id": self.host_id,
            "created_at": self.created_at.isoformat(),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "participants": list(self.participants),
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


class BreakoutRoomManager:
    """
    Manages breakout rooms for a conference
    """

    def __init__(
        self,
        conference_id: str,
        settings: Optional[BreakoutRoomSettings] = None,
    ):
        self.conference_id = conference_id
        self.settings = settings or BreakoutRoomSettings()

        self.rooms: Dict[str, BreakoutRoom] = {}
        self.participant_room_map: Dict[str, str] = {}  # participant_id -> room_id
        self.main_room_participants: Set[str] = set()

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "rooms_created": [],
            "rooms_opened": [],
            "rooms_closed": [],
            "participant_moved": [],
        }

        logger.info(f"BreakoutRoomManager initialized for conference: {conference_id}")

    def create_rooms(
        self,
        num_rooms: int,
        room_names: Optional[List[str]] = None,
        capacity_per_room: int = 50,
    ) -> List[BreakoutRoom]:
        """Create breakout rooms"""
        rooms = []

        for i in range(num_rooms):
            room_number = i + 1
            name = room_names[i] if room_names and i < len(room_names) else None
            room = BreakoutRoom(room_number, name, capacity_per_room)

            self.rooms[room.id] = room
            rooms.append(room)

        self._trigger_event("rooms_created", {
            "num_rooms": num_rooms,
            "room_ids": [r.id for r in rooms],
        })

        logger.info(f"Created {num_rooms} breakout rooms")
        return rooms

    def assign_participants(
        self,
        participant_ids: List[str],
        method: Optional[AssignmentMethod] = None,
        assignments: Optional[Dict[str, str]] = None,  # participant_id -> room_id
    ) -> Dict[str, List[str]]:
        """Assign participants to breakout rooms"""
        assignment_method = method or self.settings.assignment_method
        result: Dict[str, List[str]] = {}

        if assignment_method == AssignmentMethod.MANUAL and assignments:
            # Manual assignment
            for participant_id, room_id in assignments.items():
                if room_id in self.rooms:
                    room = self.rooms[room_id]
                    if room.add_participant(participant_id):
                        self.participant_room_map[participant_id] = room_id
                        if room_id not in result:
                            result[room_id] = []
                        result[room_id].append(participant_id)

        elif assignment_method == AssignmentMethod.AUTOMATIC:
            # Automatic round-robin assignment
            room_list = list(self.rooms.values())
            if not room_list:
                logger.warning("No rooms available for assignment")
                return result

            for i, participant_id in enumerate(participant_ids):
                room = room_list[i % len(room_list)]
                if room.add_participant(participant_id):
                    self.participant_room_map[participant_id] = room.id
                    if room.id not in result:
                        result[room.id] = []
                    result[room.id].append(participant_id)

        logger.info(f"Assigned {len(participant_ids)} participants using {assignment_method.value}")
        return result

    def assign_participants_randomly(
        self,
        participant_ids: List[str],
        num_rooms: Optional[int] = None,
    ) -> Dict[str, List[str]]:
        """Randomly assign participants to breakout rooms"""
        shuffled = participant_ids.copy()
        random.shuffle(shuffled)

        room_count = num_rooms or len(self.rooms)
        room_list = list(self.rooms.values())[:room_count]

        result: Dict[str, List[str]] = {}

        for i, participant_id in enumerate(shuffled):
            room = room_list[i % len(room_list)]
            if room.add_participant(participant_id):
                self.participant_room_map[participant_id] = room.id
                if room.id not in result:
                    result[room.id] = []
                result[room.id].append(participant_id)

        logger.info(f"Randomly assigned {len(participant_ids)} participants")
        return result

    def move_participant(
        self,
        participant_id: str,
        to_room_id: Optional[str],
    ) -> bool:
        """Move a participant to a different room (or main room if None)"""

        # Remove from current room
        if participant_id in self.participant_room_map:
            current_room_id = self.participant_room_map[participant_id]
            current_room = self.rooms.get(current_room_id)
            if current_room:
                current_room.remove_participant(participant_id)
            del self.participant_room_map[participant_id]

        # Move to main room
        if to_room_id is None:
            self.main_room_participants.add(participant_id)
            logger.info(f"Participant {participant_id} moved to main room")
            return True

        # Move to breakout room
        if to_room_id in self.rooms:
            room = self.rooms[to_room_id]
            if room.add_participant(participant_id):
                self.participant_room_map[participant_id] = to_room_id
                self.main_room_participants.discard(participant_id)

                self._trigger_event("participant_moved", {
                    "participant_id": participant_id,
                    "room_id": to_room_id,
                })

                logger.info(f"Participant {participant_id} moved to room {room.name}")
                return True

        return False

    def open_all_rooms(self) -> bool:
        """Open all breakout rooms"""
        for room in self.rooms.values():
            if room.status == RoomStatus.CREATED:
                room.open()

        self._trigger_event("rooms_opened", {
            "num_rooms": len(self.rooms),
        })

        logger.info(f"Opened all {len(self.rooms)} breakout rooms")
        return True

    async def start_rooms_with_timer(
        self,
        duration_minutes: int,
        warning_minutes: int = 1,
    ) -> None:
        """Start all rooms with a timer"""
        self.open_all_rooms()

        # Start timer for each room
        timer_tasks = []
        for room in self.rooms.values():
            if room.status == RoomStatus.OPEN:
                room.activate()
                task = asyncio.create_task(
                    room.start_timer(duration_minutes, warning_minutes)
                )
                room.timer_task = task
                timer_tasks.append(task)

        logger.info(f"Started {len(timer_tasks)} rooms with {duration_minutes} minute timer")

        # Wait for all timers
        if timer_tasks:
            await asyncio.gather(*timer_tasks, return_exceptions=True)

    def close_all_rooms(self) -> bool:
        """Close all breakout rooms and return participants to main room"""
        for room in self.rooms.values():
            if room.status != RoomStatus.CLOSED:
                # Get participants before closing
                participants = list(room.participants)

                # Close room
                room.close()

                # Move participants to main room
                for participant_id in participants:
                    if participant_id in self.participant_room_map:
                        del self.participant_room_map[participant_id]
                    self.main_room_participants.add(participant_id)

        self._trigger_event("rooms_closed", {
            "num_rooms": len(self.rooms),
        })

        logger.info(f"Closed all {len(self.rooms)} breakout rooms")
        return True

    def get_room(self, room_id: str) -> Optional[BreakoutRoom]:
        """Get a breakout room by ID"""
        return self.rooms.get(room_id)

    def get_all_rooms(self) -> List[BreakoutRoom]:
        """Get all breakout rooms"""
        return list(self.rooms.values())

    def get_participant_room(self, participant_id: str) -> Optional[BreakoutRoom]:
        """Get the room a participant is currently in"""
        room_id = self.participant_room_map.get(participant_id)
        if room_id:
            return self.rooms.get(room_id)
        return None

    def is_in_main_room(self, participant_id: str) -> bool:
        """Check if participant is in main room"""
        return participant_id in self.main_room_participants

    def broadcast_message_to_all_rooms(self, message: str) -> int:
        """Broadcast a message to all breakout rooms"""
        count = 0
        for room in self.rooms.values():
            if room.status in [RoomStatus.OPEN, RoomStatus.ACTIVE]:
                # In a full implementation, would send message to room
                logger.info(f"Broadcasting to {room.name}: {message}")
                count += 1

        return count

    def get_stats(self) -> Dict:
        """Get breakout room statistics"""
        return {
            "conference_id": self.conference_id,
            "total_rooms": len(self.rooms),
            "active_rooms": len([r for r in self.rooms.values() if r.status == RoomStatus.ACTIVE]),
            "total_participants_in_breakout": len(self.participant_room_map),
            "participants_in_main_room": len(self.main_room_participants),
            "rooms": [r.get_info() for r in self.rooms.values()],
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
