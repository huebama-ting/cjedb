from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Database(_message.Message):
    __slots__ = ["events"]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[Event]
    def __init__(self, events: _Optional[_Iterable[_Union[Event, _Mapping]]] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ["story_id", "story_name", "choices"]
    class Choice(_message.Message):
        __slots__ = ["title", "text"]
        TITLE_FIELD_NUMBER: _ClassVar[int]
        TEXT_FIELD_NUMBER: _ClassVar[int]
        title: str
        text: str
        def __init__(self, title: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...
    STORY_ID_FIELD_NUMBER: _ClassVar[int]
    STORY_NAME_FIELD_NUMBER: _ClassVar[int]
    CHOICES_FIELD_NUMBER: _ClassVar[int]
    story_id: int
    story_name: str
    choices: _containers.RepeatedCompositeFieldContainer[Event.Choice]
    def __init__(self, story_id: _Optional[int] = ..., story_name: _Optional[str] = ..., choices: _Optional[_Iterable[_Union[Event.Choice, _Mapping]]] = ...) -> None: ...
