from typing import Any as AnyType, Optional
from .op import Op
from ..event import Event


class Errors(Event):
    __slots__ = ('_source',)

    def __init__(self, source: Optional[AnyType] = None):
        Event.__init__(self)
        self._source = source
        if source is not None:
            if source.done():
                self.set_done()
            elif hasattr(source, 'error_event') and source.error_event is not None:
                source.error_event += self.emit


class EndOnError(Op):
    __slots__ = ()

    def __init__(self, source: Optional[AnyType] = None):
        Op.__init__(self, source)

    def on_source_error(self, source: AnyType, error: AnyType) -> None:
        if self._source is not None:
            self._disconnect_from(self._source)
        if self.error_event is not None:
            self.error_event.emit(error)
        self.set_done()
