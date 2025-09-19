from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import time
from typing_extensions import Literal
from medperf import config


class Notification(BaseModel):
    id: str
    message: str
    type: Literal["success", "failed", "info"]
    read: bool = False
    timestamp: float = Field(default_factory=time.time)
    url: Optional[str] = None

    def mark_read(self):
        self.read = True

    def to_json(self):
        return self.dict()


class EventBase(BaseModel):
    id: Optional[int] = None
    task_id: Optional[str] = None

    def to_json(self):
        return self.dict()


class Event(EventBase):
    kind: str = "event"
    type: str
    message: str
    interactive: bool
    end: bool
    response: Optional[dict] = None
    approved: Optional[bool] = None


class EventChunk(EventBase):
    kind: str = "chunk"
    events: List[Event] = Field(default_factory=list)
    length: int
    size_bytes: int


class WebUITask(BaseModel):
    id: str = ""
    name: str = ""
    running: bool = False
    logs: List[EventBase] = Field(default_factory=list)
    formData: Dict = Field(default_factory=dict)
    last_event_id: int = 0
    log_events_count: int = 0
    max_log_events: int = config.MAXLOGMESSAGES

    def _set_event_id(self, log: EventBase):
        self.last_event_id += 1
        log.id = self.last_event_id

    def _is_log_event(self, log: EventBase):
        return log.interactive and log.type == "print"

    def _remove_excess_logs(self):
        if self.log_events_count <= self.max_log_events:
            return

        for event in self.logs.copy():
            if self.log_events_count <= self.max_log_events:
                break
            if event.kind == "event":
                if self._is_log_event(event):
                    self.logs.remove(event)
                    self.log_events_count -= 1
            else:
                diff = self.log_events_count - self.max_log_events
                chunk_length = event.length
                if chunk_length <= diff:
                    self.logs.remove(event)
                    self.log_events_count -= chunk_length
                else:
                    event.events = event.events[diff - 1:]
                    self.log_events_count -= diff

    def _process_events_count(self, log: EventBase):
        if log.kind == "event":
            if self._is_log_event(log):
                self.log_events_count += 1
        else:
            self.log_events_count += len(log.events)

    def add_log(self, log: EventBase):
        self._set_event_id(log)
        self._process_events_count(log)
        self._remove_excess_logs()
        self.logs.append(log)

    def set_running(self, running: bool):
        self.running = running

    def to_json(self):
        return self.dict()
