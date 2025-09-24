"""Type definitions for eventkit."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event
    from .ops.combine import Fork

type EventType = "Event"
type ForkType = "Fork"
