# apps/modules/shared/kernel/events.py
"""Domain events system for decoupled communication."""

from __future__ import annotations

import contextlib
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

EventHandler = Callable[["DomainEvent"], None]


@dataclass
class DomainEvent:
    """Base domain event."""

    eventType: str
    aggregateId: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1


class EventBus:
    """Simple in-memory event bus for domain events."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, eventType: str, handler: EventHandler) -> None:
        """Register a handler for one event type."""
        self._handlers[eventType].append(handler)

    def unsubscribe(self, eventType: str, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        if handler in self._handlers[eventType]:
            self._handlers[eventType].remove(handler)

    def publish(self, event: DomainEvent) -> None:
        """Notify every handler; a failing handler never breaks the flow."""
        for handler in self._handlers.get(event.eventType, []):
            with contextlib.suppress(Exception):
                handler(event)

    def publishAsync(self, event: DomainEvent) -> None:
        """Publish through a short-lived daemon thread."""
        import threading  # noqa: PLC0415 - only needed for async publishing

        threading.Thread(target=self.publish, args=(event,), daemon=True).start()


# Global event bus instance
eventBus = EventBus()


class EventTypes:
    """Standard event type identifiers."""

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
