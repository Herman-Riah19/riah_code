# tests/unit/test_shared/test_events.py
"""Tests for the in-memory domain event bus."""

from __future__ import annotations

import threading

from apps.modules.shared.kernel.events import DomainEvent, EventBus, EventTypes


def makeEvent(eventType: str = EventTypes.JOB_STARTED) -> DomainEvent:
    """Build a minimal event for the bus tests."""
    return DomainEvent(eventType=eventType, aggregateId="job-1", payload={"step": 1})


class TestDomainEvent:
    """Event payload defaults."""

    def test_timestamp_is_timezone_aware(self) -> None:
        event = makeEvent()

        assert event.timestamp.tzinfo is not None
        assert event.version == 1


class TestEventBus:
    """Subscribe, publish and unsubscribe behaviour."""

    def test_publish_calls_matching_handlers(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []
        bus.subscribe(EventTypes.JOB_STARTED, received.append)

        bus.publish(makeEvent())

        assert [event.aggregateId for event in received] == ["job-1"]

    def test_publish_ignores_other_event_types(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []
        bus.subscribe(EventTypes.JOB_STARTED, received.append)

        bus.publish(makeEvent(EventTypes.JOB_FAILED))

        assert received == []

    def test_unsubscribe_stops_delivery(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []
        bus.subscribe(EventTypes.JOB_STARTED, received.append)
        bus.unsubscribe(EventTypes.JOB_STARTED, received.append)

        bus.publish(makeEvent())

        assert received == []

    def test_unsubscribe_unknown_handler_is_a_noop(self) -> None:
        bus = EventBus()

        bus.unsubscribe(EventTypes.JOB_STARTED, lambda event: None)

    def test_failing_handler_does_not_block_others(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        def failing(event: DomainEvent) -> None:
            raise RuntimeError("handler failure")

        bus.subscribe(EventTypes.JOB_STARTED, failing)
        bus.subscribe(EventTypes.JOB_STARTED, received.append)

        bus.publish(makeEvent())

        assert len(received) == 1

    def test_publish_async_delivers_event(self) -> None:
        bus = EventBus()
        delivered = threading.Event()

        def handler(event: DomainEvent) -> None:
            delivered.set()

        bus.subscribe(EventTypes.MODEL_LOADED, handler)

        bus.publishAsync(makeEvent(EventTypes.MODEL_LOADED))

        assert delivered.wait(timeout=5.0) is True
