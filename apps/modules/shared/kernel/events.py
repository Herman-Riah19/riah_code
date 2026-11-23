# apps/modules/shared/kernel/events.py
"""Domain events system for decoupled communication"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from collections import defaultdict


@dataclass
class DomainEvent:
    """Base domain event"""
    eventType: str
    aggregateId: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


class EventBus:
    """Simple in-memory event bus for domain events"""
    
    def __init__(self):
        self._handlers: dict[str, list[callable]] = defaultdict(list)
    
    def subscribe(self, eventType: str, handler: callable) -> None:
        self._handlers[eventType].append(handler)
    
    def unsubscribe(self, eventType: str, handler: callable) -> None:
        if handler in self._handlers[eventType]:
            self._handlers[eventType].remove(handler)
    
    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.eventType, []):
            try:
                handler(event)
            except Exception:
                # Log but don't fail - events shouldn't break the flow
                pass
    
    def publishAsync(self, event: DomainEvent) -> None:
        # In production, use proper async (asyncio, thread pool, message queue)
        import threading
        threading.Thread(target=self.publish, args=(event,), daemon=True).start()


# Global event bus instance
eventBus = EventBus()

# Standard event types
class EventTypes:
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"
    CHECKPOINT_SAVED = "checkpoint.saved"
    MODEL_LOADED = "model.loaded"
    TRAINING_STEP = "training.step"
    CORPUS_SCRAPED = "corpus.scraped"
    CORPUS_ENCODED = "corpus.encoded"
    TOKENIZER_TRAINED = "tokenizer.trained"
    CHAT_SESSION_CREATED = "chat.session.created"
    CHAT_MESSAGE_SENT = "chat.message.sent"