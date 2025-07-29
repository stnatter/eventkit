import asyncio
import itertools
import time

from ..event import Event
from ..util import NO_VALUE, get_event_loop, timerange
from .op import Op


class Wait(Event):
    __slots__ = ("_task",)

    def __init__(self, future, name="wait"):
        Event.__init__(self, name)
        if future.done():
            self._task = None
            self.set_done()
        else:
            # For futures, we don't need to create a task - just use the future directly
            self._task = future
            future.add_done_callback(self._on_task_done)

    def _on_task_done(self, task):
        try:
            result = task.result()
        except Exception as error:
            result = NO_VALUE
            if self.error_event is not None:
                self.error_event.emit(self, error)
        self.emit(result)
        self._task = None
        self.set_done()

    def __del__(self):
        if hasattr(self, "_task") and self._task:
            self._task.cancel()


class Aiterate(Event):
    __slots__ = ("_task",)

    def __init__(self, ait):
        Event.__init__(self, ait.__qualname__)
        # Use the original working approach: always create the task
        try:
            self._task = asyncio.create_task(self._looper(ait))
        except RuntimeError:
            # No running loop - get/create one and use it
            # Note: This may generate a "coroutine never awaited" warning
            # but the task will be properly executed when run() is called
            loop = get_event_loop()
            self._task = loop.create_task(self._looper(ait))

    async def _looper(self, ait):
        try:
            async for args in ait:
                self.emit(args)
        except Exception as error:
            if self.error_event is not None:
                self.error_event.emit(self, error)
        self._task = None
        self.set_done()

    def __del__(self):
        if hasattr(self, "_task") and self._task:
            self._task.cancel()


class Sequence(Aiterate):
    __slots__ = ()

    def __init__(self, values, interval=0, times=None):
        async def sequence():
            t0 = time.time()
            if times is not None:
                for t, value in zip(times, values, strict=False):
                    delay = max(0, time.time() + t - t0)
                    await asyncio.sleep(delay)
                    yield value
            else:
                for i, value in enumerate(values):
                    delay = max(0, i * interval + t0 - time.time())
                    await asyncio.sleep(delay)
                    yield value

        Aiterate.__init__(self, sequence())


class Repeat(Sequence):
    __slots__ = ()

    def __init__(self, value, count, interval=0, times=None):
        Sequence.__init__(self, itertools.repeat(count), interval, times)


class Range(Sequence):
    __slots__ = ()

    def __init__(self, *args, interval=0, times=None):
        Sequence.__init__(self, range(*args), interval, times)


class Timerange(Aiterate):
    __slots__ = ()

    def __init__(self, start=0, end=None, step=1):
        Aiterate.__init__(self, timerange(start, end, step))


class Timer(Aiterate):
    __slots__ = ()

    def __init__(self, interval, count=None):
        async def timer():
            t0 = time.time()
            i = 0
            while count is None or i < count:
                i += 1
                delay = i * interval + t0 - time.time()
                await asyncio.sleep(delay)
                yield i * interval

        Aiterate.__init__(self, timer())


class Marble(Op):
    __slots__ = ()

    def __init__(self, s, interval=0, times=None):
        s = s.replace("_", "")
        source = (
            Event.sequence(s, interval, times)
            .filter(lambda c: c not in "- ")
            .takewhile(lambda c: c != "|")
        )
        Op.__init__(self, source)
