import asyncio
import datetime as dt
import sys
from collections.abc import AsyncIterator


class _NoValue:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<NoValue>"

    __str__ = __repr__


NO_VALUE = _NoValue()


class MainEventLoop:
    """Singleton event loop holder for Python 3.14+."""

    _loop: asyncio.AbstractEventLoop | None = None

    @classmethod
    def get(cls) -> asyncio.AbstractEventLoop:
        """Get the main event loop, creating one if necessary."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            pass
        if cls._loop is None or cls._loop.is_closed():
            cls._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._loop)
        return cls._loop


main_event_loop = MainEventLoop()


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get asyncio event loop for Python 3.14+."""
    return main_event_loop.get()


def get_async_task_info():
    """Get information about current asyncio tasks for debugging (Python 3.14+)."""
    try:
        import asyncio
        current_task = asyncio.current_task()
        if current_task:
            return {
                'name': current_task.get_name(),
                'coro': current_task.get_coro().__name__ if hasattr(current_task.get_coro(), '__name__') else str(current_task.get_coro()),
                'state': 'done' if current_task.done() else 'running',
                'cancelled': current_task.cancelled()
            }
        return None
    except RuntimeError:
        return None


def get_event_loop_info():
    """Get information about the current event loop for debugging (Python 3.14+)."""
    try:
        loop = asyncio.get_running_loop()
        return {
            'running': loop.is_running(),
            'closed': loop.is_closed(),
            'debug': loop.get_debug(),
            'task_count': len(asyncio.all_tasks(loop)) if hasattr(asyncio, 'all_tasks') else 'unknown'
        }
    except RuntimeError:
        return None


def debug_async_state():
    """Comprehensive async debugging information (Python 3.14+)."""
    task_info = get_async_task_info()
    loop_info = get_event_loop_info()
    
    debug_info = {
        'task': task_info,
        'loop': loop_info,
        'python_version': sys.version_info
    }
    
    # Add Python 3.14+ specific introspection if available
    if sys.version_info >= (3, 14):
        try:
            # Try to use new asyncio introspection features
            import subprocess
            import os
            pid = os.getpid()
            # This would work with python -m asyncio ps {pid} command
            debug_info['introspection_available'] = True
        except Exception:
            debug_info['introspection_available'] = False
    
    return debug_info


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
