"""
Message queue and event bus system.

Handles async messaging, event routing, and dead letter queue management
for reliable integration processing.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import logging
import json
import asyncio
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Message:
    """Represents a queue message."""

    def __init__(
        self,
        id: str,
        topic: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        retry_count: int = 0,
        max_retries: int = 3,
        created_at: Optional[datetime] = None
    ):
        """
        Initialize message.

        Args:
            id: Unique message ID
            topic: Message topic/queue name
            payload: Message data
            priority: Message priority
            retry_count: Current retry count
            max_retries: Maximum retry attempts
            created_at: Creation timestamp
        """
        self.id = id
        self.topic = topic
        self.payload = payload
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'topic': self.topic,
            'payload': self.payload,
            'priority': self.priority.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            id=data['id'],
            topic=data['topic'],
            payload=data['payload'],
            priority=MessagePriority(data.get('priority', 'normal')),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else None
        )


class MessageQueue:
    """
    In-memory message queue with priority support.

    Provides reliable message queuing with retry logic and
    dead letter queue support.
    """

    def __init__(self, name: str):
        """
        Initialize message queue.

        Args:
            name: Queue name
        """
        self.name = name
        self._queues: Dict[MessagePriority, asyncio.Queue] = {
            MessagePriority.URGENT: asyncio.Queue(),
            MessagePriority.HIGH: asyncio.Queue(),
            MessagePriority.NORMAL: asyncio.Queue(),
            MessagePriority.LOW: asyncio.Queue()
        }
        self._processing: Dict[str, Message] = {}
        self._dlq: List[Message] = []  # Dead letter queue

    async def enqueue(self, message: Message) -> None:
        """
        Add message to queue.

        Args:
            message: Message to enqueue
        """
        priority = message.priority
        await self._queues[priority].put(message)
        logger.debug(f"Enqueued message {message.id} to {self.name} with priority {priority.value}")

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Get next message from queue (respecting priority).

        Args:
            timeout: Optional timeout in seconds

        Returns:
            Next message or None if timeout
        """
        # Try each priority queue in order
        for priority in [MessagePriority.URGENT, MessagePriority.HIGH, MessagePriority.NORMAL, MessagePriority.LOW]:
            queue = self._queues[priority]

            if not queue.empty():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=timeout or 0.1)
                    self._processing[message.id] = message
                    logger.debug(f"Dequeued message {message.id} from {self.name}")
                    return message
                except asyncio.TimeoutError:
                    continue

        return None

    async def ack(self, message_id: str) -> None:
        """
        Acknowledge message processing completion.

        Args:
            message_id: Message ID
        """
        if message_id in self._processing:
            del self._processing[message_id]
            logger.debug(f"Acknowledged message {message_id}")

    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """
        Negative acknowledge - message processing failed.

        Args:
            message_id: Message ID
            requeue: Whether to requeue the message
        """
        if message_id not in self._processing:
            return

        message = self._processing[message_id]
        del self._processing[message_id]

        if requeue and message.retry_count < message.max_retries:
            # Increment retry count and requeue
            message.retry_count += 1
            await self.enqueue(message)
            logger.info(f"Requeued message {message_id} (retry {message.retry_count}/{message.max_retries})")
        else:
            # Move to dead letter queue
            self._dlq.append(message)
            logger.warning(f"Moved message {message_id} to dead letter queue")

    def get_dlq_messages(self) -> List[Message]:
        """
        Get messages from dead letter queue.

        Returns:
            List of failed messages
        """
        return self._dlq.copy()

    def clear_dlq(self) -> None:
        """Clear dead letter queue."""
        self._dlq.clear()
        logger.info(f"Cleared dead letter queue for {self.name}")

    def size(self) -> int:
        """Get total queue size."""
        return sum(q.qsize() for q in self._queues.values())

    def processing_count(self) -> int:
        """Get number of messages being processed."""
        return len(self._processing)


class EventBus:
    """
    Pub/sub event bus for integration events.

    Provides event-driven communication between components.
    """

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_log: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle events
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from event type.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.info(f"Unsubscribed handler from event type: {event_type}")

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish event to subscribers.

        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional metadata
        """
        event = {
            'id': self._generate_event_id(event_type, data),
            'type': event_type,
            'data': data,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }

        # Log event
        self._event_log.append(event)

        # Notify subscribers
        handlers = self._subscribers.get(event_type, [])
        if handlers:
            logger.info(f"Publishing event {event_type} to {len(handlers)} subscribers")

            # Execute handlers concurrently
            tasks = [handler(event) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.debug(f"No subscribers for event type: {event_type}")

    def _generate_event_id(self, event_type: str, data: Dict[str, Any]) -> str:
        """Generate unique event ID."""
        content = f"{event_type}:{json.dumps(data, sort_keys=True)}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_event_log(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get event log.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events

        Returns:
            List of events
        """
        events = self._event_log

        if event_type:
            events = [e for e in events if e['type'] == event_type]

        return events[-limit:]


class DeadLetterQueue:
    """
    Manages failed messages that couldn't be processed.

    Provides inspection, retry, and cleanup capabilities for
    failed messages.
    """

    def __init__(self):
        """Initialize dead letter queue."""
        self._messages: List[Message] = []

    def add(self, message: Message, error: str) -> None:
        """
        Add message to DLQ.

        Args:
            message: Failed message
            error: Error description
        """
        # Add error info to payload
        message.payload['_dlq_error'] = error
        message.payload['_dlq_timestamp'] = datetime.now().isoformat()

        self._messages.append(message)
        logger.warning(f"Added message {message.id} to DLQ: {error}")

    def get_messages(
        self,
        topic: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from DLQ.

        Args:
            topic: Optional filter by topic
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        messages = self._messages

        if topic:
            messages = [m for m in messages if m.topic == topic]

        if limit:
            messages = messages[:limit]

        return messages

    def remove(self, message_id: str) -> bool:
        """
        Remove message from DLQ.

        Args:
            message_id: Message ID

        Returns:
            True if removed
        """
        for i, msg in enumerate(self._messages):
            if msg.id == message_id:
                del self._messages[i]
                logger.info(f"Removed message {message_id} from DLQ")
                return True

        return False

    def retry(self, message_id: str, queue: MessageQueue) -> bool:
        """
        Retry message from DLQ.

        Args:
            message_id: Message ID
            queue: Queue to retry message in

        Returns:
            True if retried
        """
        for i, msg in enumerate(self._messages):
            if msg.id == message_id:
                # Reset retry count
                msg.retry_count = 0

                # Remove DLQ metadata
                msg.payload.pop('_dlq_error', None)
                msg.payload.pop('_dlq_timestamp', None)

                # Requeue
                asyncio.create_task(queue.enqueue(msg))

                del self._messages[i]
                logger.info(f"Retrying message {message_id} from DLQ")
                return True

        return False

    def clear(self, topic: Optional[str] = None) -> int:
        """
        Clear DLQ messages.

        Args:
            topic: Optional filter by topic

        Returns:
            Number of messages cleared
        """
        if topic:
            original_count = len(self._messages)
            self._messages = [m for m in self._messages if m.topic != topic]
            cleared = original_count - len(self._messages)
        else:
            cleared = len(self._messages)
            self._messages.clear()

        logger.info(f"Cleared {cleared} messages from DLQ")
        return cleared

    def size(self) -> int:
        """Get DLQ size."""
        return len(self._messages)


# Global instances
_queues: Dict[str, MessageQueue] = {}
_event_bus = EventBus()
_dlq = DeadLetterQueue()


def get_queue(name: str) -> MessageQueue:
    """
    Get or create a message queue.

    Args:
        name: Queue name

    Returns:
        MessageQueue instance
    """
    if name not in _queues:
        _queues[name] = MessageQueue(name)

    return _queues[name]


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    return _event_bus


def get_dlq() -> DeadLetterQueue:
    """Get global dead letter queue instance."""
    return _dlq
