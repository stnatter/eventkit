"""Type definitions for eventkit."""

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .event import Event
    from .ops.combine import Fork

EventType: TypeAlias = "Event"
ForkType: TypeAlias = "Fork"
