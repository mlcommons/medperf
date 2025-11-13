import json
from queue import Queue
import threading
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

    @property
    def is_chunkable(self) -> bool:
        """Return True if the event should be combined into a print chunk.

        Chunking applies only to interactive print lines.

        Returns:
            bool: True if this event is an interactive print - False otherwise.
        """

        return self.interactive and self.type == "print"

    def get_size_bytes(self) -> int:
        event_string = json.dumps(
            self.to_json(), ensure_ascii=False, separators=(",", ":")
        )
        return len(event_string.encode("utf-8"))


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
    max_log_events: int = config.webui_max_log_messages

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


class EventsManager:
    def __init__(self):
        self.events: Queue[EventBase] = Queue()
        self.buffer: List[Event] = []
        self.size = 0  # For bytes check
        self.created_at = 0  # For age check - will be time.monotonic()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.max_chunk_length = config.webui_max_chunk_length
        self.max_chunk_age = config.webui_max_chunk_age
        self.max_chunk_size = config.webui_max_chunk_size

    def add_event(self, event: Event):
        """Append an event to the chunk buffer and update its size.

        If the buffer is empty, set its created_at timestamp (monotonic) to now.

        Args:
            event (Event): The event to buffer (typically an interactive print line).
        """

        if not self.buffer:
            self.created_at = time.monotonic()
        self.buffer.append(event)
        self.size += event.get_size_bytes()

    def process_event(self, event: Event):
        """
        Process a single event: buffer chunkable events, flush if needed,
        or immediately enqueue non-chunkable events.
        """

        if event.is_chunkable:
            with self.lock:
                self.add_event(event)
                self.flush_by_size()
            return

        with self.lock:
            self.flush_buffer()

        self.enqueue_event(event)

    def enqueue_event(self, event: EventBase):
        """Enqueue an event (chunked or single) into the events queue.

        Args:
            event (EventBase): The event or chunk to enqueue.
        """
        self.events.put_nowait(event)

    def dequeue_event(self, timeout: Optional[float]) -> Optional[EventBase]:
        """
        Return the next event or chunk from the queue.

        Args:
            timeout (float | None): Seconds to wait for an event.
        """

        return self.events.get(block=True, timeout=timeout)

    def _build_chunk(self, events: List[Event], size: int) -> EventChunk:
        """Build an EventChunk object from a list of events."""

        for i, ev in enumerate(events, 1):
            ev.id = i

        return EventChunk(
            task_id=events[0].task_id,
            events=events,
            length=len(events),
            size_bytes=size,
        )

    def flush_buffer(self):
        """
        Flush the event buffer: if it contains multiple events, emit them as
        an EventChunk; otherwise enqueue the single event. The buffer is then reset.
        """
        if not self.buffer:
            return
        buffer = list(self.buffer)
        size = self.size
        self.buffer.clear()
        self.size = 0
        self.created_at = 0

        if len(buffer) != 1:
            chunk = self._build_chunk(buffer, size)
            self.events.put_nowait(chunk)
            return

        self.events.put_nowait(buffer[0])

    def flush_by_size(self):
        """Flush the buffer if it exceeds the max event count or max byte size."""

        length_exceeded = len(self.buffer) >= self.max_chunk_length
        size_bytes_exceeded = self.size >= self.max_chunk_size

        if self.buffer and (length_exceeded or size_bytes_exceeded):
            self.flush_buffer()

    def flush_by_age(self):
        """Flush the buffer if the oldest event exceeds the max age."""

        time_exceeded = (time.monotonic() - self.created_at) >= self.max_chunk_age
        if self.buffer and time_exceeded:
            self.flush_buffer()

    def flush_by_age_worker(self):
        """
        Background loop that periodically flushes the buffer if it exceeds max age.

        Runs until 'stop_event' is set.
        """

        while not self.stop_event.is_set():
            with self.lock:
                self.flush_by_age()
            time.sleep(0.2)

    def start_buffering(self):
        """Start the age-based flushing worker thread."""

        self.stop_event.clear()

        # worker for age-flushing
        age_worker = threading.Thread(target=self.flush_by_age_worker, daemon=True)
        age_worker.start()

    def stop_buffering(self):
        """Stop the age-flushing worker and flush any remaining buffered events."""

        self.stop_event.set()
        with self.lock:
            self.flush_buffer()
