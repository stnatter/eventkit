import asyncio
import datetime as dt
from collections.abc import AsyncIterator


class _NoValue:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<NoValue>"

    __str__ = __repr__


NO_VALUE = _NoValue()


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get asyncio event loop for Python 3.13+."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - create and set a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# Lazy initialization - create main loop when needed
class MainEventLoop:
    """Lazy event loop holder."""

    _loop: asyncio.AbstractEventLoop | None = None

    @classmethod
    def get(cls) -> asyncio.AbstractEventLoop:
        if cls._loop is None:
            cls._loop = get_event_loop()
        return cls._loop


main_event_loop = MainEventLoop()


async def timerange(
    start: int | float | dt.datetime | dt.time = 0,
    end: int | float | dt.datetime | dt.time | None = None,
    step: float | dt.timedelta = 1,
) -> AsyncIterator[dt.datetime]:
    """
    Iterator that waits periodically until certain time points are
    reached while yielding those time points.

    Args:
        start: Start time, can be specified as:

            * ``datetime.datetime``.
            * ``datetime.time``: Today is used as date.
            * ``int`` or ``float``: Number of seconds relative to now.
              Values will be quantized to the given step.
        end: End time, can be specified as:

            * ``datetime.datetime``.
            * ``datetime.time``: Today is used as date.
            * ``None``: No end limit.
        step: Number of seconds, or ``datetime.timedelta``,
            to space between values.
    """
    tz = getattr(start, "tzinfo", None)
    now = dt.datetime.now(tz)
    if isinstance(step, dt.timedelta):
        delta = step
        step = delta.total_seconds()
    else:
        delta = dt.timedelta(seconds=step)
    if start == 0 or isinstance(start, int | float):
        seconds_val = float(start) if isinstance(start, int | float) else 0.0
        t = now + dt.timedelta(seconds=seconds_val)
        # quantize to step
        t = dt.datetime.fromtimestamp(step * int(t.timestamp() / step))
    elif isinstance(start, dt.time):
        t = dt.datetime.combine(now.today(), start)
    else:
        # start must be dt.datetime at this point
        t = start

    if t < now:
        # t += delta
        t -= ((t - now) // delta) * delta

    if isinstance(end, dt.time):
        end = dt.datetime.combine(now.today(), end)
    elif isinstance(end, int | float):
        end = now + dt.timedelta(seconds=end)

    while end is None or t <= end:
        now = dt.datetime.now(tz)
        secs = (t - now).total_seconds()
        await asyncio.sleep(secs)
        yield t
        t += delta
