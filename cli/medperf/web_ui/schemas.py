import json
from queue import Queue
import threading
from medperf.web_ui.utils import generate_uuid
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

    def _remove_excess_logs(self):
        if self.log_events_count <= self.max_log_events:
            return

        for event in self.logs.copy():
            if self.log_events_count <= self.max_log_events:
                break
            if event.kind == "event":
                if event.is_chunkable:
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
            if log.is_chunkable:
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


class GlobalEventsManager:
    def __init__(self):
        self.events_counter = 0
        self.notifications: List[Notification] = list()
        self.new_notifications: List[Notification] = list()
        self.events: List[Event] = list()
        self.waiting_ack: List[Event] = list()
        self._lock = threading.Lock()
        self._notifs_lock = threading.Lock()

    def add_event(self, event: Event) -> None:
        """Add an event into the events list.

        Args:
            event (Event): The event to be added.
        """

        with self._lock:
            self.events_counter += 1
            event.id = self.events_counter
            self.events.append(event)

    def get_event(self) -> Optional[Event]:
        """Return the next event from the list."""

        with self._lock:
            if self.events:
                event = self.events.pop(0)
                self.waiting_ack.append(event)
                return event

    def get_all_events(self) -> List:
        """Combine the two lists (events and waiting_ack) into the waiting_ack list and return it."""

        with self._lock:
            if self.events or self.waiting_ack:
                self.waiting_ack.extend(self.events)
                self.events.clear()
                return self.waiting_ack

        return []

    def acknowledge_event(self, event_id: int) -> None:
        """Remove an event from waiting_ack.

        Args:
            event_id (int): id of the event to be removed.

        """

        with self._lock:
            for event in self.waiting_ack:
                if event.id == event_id:
                    self.waiting_ack.remove(event)
                    return

    def reset_waiting_events(self) -> None:
        """Combine both lists (events and waiting_ack) into the events list"""

        with self._lock:
            self.events.extend(self.waiting_ack)
            self.waiting_ack.clear()

    def add_notification(self, message: str, return_response: dict, url: str) -> None:
        if return_response["status"] == "failed":
            message += f": {return_response['error']}"

        notification = Notification(
            id=generate_uuid(),
            message=message,
            type=return_response["status"],
            url=url,
        )

        with self._notifs_lock:
            self.new_notifications.append(notification)

    def clear_notifications(self) -> None:
        with self._notifs_lock:
            self.notifications.clear()

    def clear_new_notifications(self) -> None:
        with self._notifs_lock:
            self.new_notifications.clear()

    def get_new_notification(self) -> Optional[Notification]:
        with self._notifs_lock:
            if not self.new_notifications:
                return

            oldest_notification = self.new_notifications[0]
            self.new_notifications.remove(oldest_notification)
            self.notifications.append(oldest_notification)

            return oldest_notification

    def get_all_notifications(self) -> List[Notification]:
        with self._notifs_lock:
            if self.new_notifications:
                self.notifications.extend(self.new_notifications)
                self.new_notifications.clear()

        return self.notifications

    def get_unread_count(self) -> int:
        with self._notifs_lock:
            return len([i for i in self.notifications if not i.read])

    def delete_notification(self, notification_id: str) -> None:
        with self._notifs_lock:
            for notification in self.notifications:
                if notification.id == notification_id:
                    self.notifications.remove(notification)
                    return

    def mark_notification_as_read(self, notification_id) -> None:
        with self._notifs_lock:
            for notification in self.notifications:
                if notification.id == notification_id:
                    notification.read = True
                    return


def _buffer_key(task_id: Optional[str]) -> str:
    """Key for per-task buffer; chunks must not mix events from different tasks."""
    return task_id if task_id else "_"


class EventsManager:
    """
    Buffers chunkable events (interactive prints) per task_id, flushes by size/age or
    when a non-chunkable event arrives. Events are enqueued to a per-task queue so
    each SSE stream (one per task) only receives that task's events.

    flush_all_buffers: before enqueueing a non-chunkable event we flush every task's
    buffer so chunkable events are sent first. Also used when a task ends.
    """

    def __init__(self):
        self._event_queues: Dict[str, Queue] = {}  # _buffer_key(task_id) -> Queue[EventBase]
        self._queues_lock = threading.Lock()
        self._buffers: Dict[str, Dict] = {}  # _buffer_key(task_id) -> {"events", "size", "created_at"}
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._age_worker_started = False
        self.max_chunk_length = config.webui_max_chunk_length
        self.max_chunk_age = config.webui_max_chunk_age
        self.max_chunk_size = config.webui_max_chunk_size

    def _queue_for(self, task_id: Optional[str]) -> Queue:
        key = _buffer_key(task_id)
        with self._queues_lock:
            if key not in self._event_queues:
                self._event_queues[key] = Queue()
            return self._event_queues[key]

    def _get_or_create_buffer(self, key: str) -> Dict:
        if key not in self._buffers:
            self._buffers[key] = {"events": [], "size": 0, "created_at": 0.0}
        return self._buffers[key]

    def add_event(self, event: Event):
        """Append an event to the chunk buffer for its task_id."""

        key = _buffer_key(event.task_id)
        buf = self._get_or_create_buffer(key)
        if not buf["events"]:
            buf["created_at"] = time.monotonic()
        buf["events"].append(event)
        buf["size"] += event.get_size_bytes()

    def process_event(self, event: Event):
        """
        Process a single event: buffer chunkable events per task_id, flush if needed,
        or immediately enqueue non-chunkable events.
        """

        if event.is_chunkable:
            with self.lock:
                self.add_event(event)
                self.flush_by_size()
            return

        with self.lock:
            self.flush_all_buffers()

        self.enqueue_event(event)

    def enqueue_event(self, event: EventBase):
        """Enqueue an event into the queue for its task_id so only that task's SSE receives it."""
        self._queue_for(event.task_id).put_nowait(event)

    def dequeue_event(self, task_id: Optional[str], timeout: Optional[float]) -> Optional[EventBase]:
        """Return the next event or chunk for the given task_id (used by SSE stream)."""
        return self._queue_for(task_id).get(block=True, timeout=timeout)

    def _build_chunk(self, events: List[Event], size: int) -> EventChunk:
        """Build an EventChunk from events (all same task_id)."""

        for i, ev in enumerate(events, 1):
            ev.id = i

        return EventChunk(
            task_id=events[0].task_id,
            events=events,
            length=len(events),
            size_bytes=size,
        )

    def _flush_one_buffer(self, key: str) -> None:
        """Flush a single task's buffer: emit chunk or single event, then clear it."""
        buf = self._buffers.get(key)
        if not buf or not buf["events"]:
            return
        events = list(buf["events"])
        size = buf["size"]
        buf["events"].clear()
        buf["size"] = 0
        buf["created_at"] = 0.0
        self._buffers.pop(key, None)  # remove empty buffer

        task_id = events[0].task_id
        if len(events) != 1:
            self._queue_for(task_id).put_nowait(self._build_chunk(events, size))
        else:
            self._queue_for(task_id).put_nowait(events[0])

    def flush_all_buffers(self) -> None:
        """Flush every task's buffer (e.g. before a non-chunkable event)."""
        for key in list(self._buffers.keys()):
            self._flush_one_buffer(key)

    def flush_by_size(self) -> None:
        """Flush any task's buffer that exceeds max length or byte size."""
        for key in list(self._buffers.keys()):
            buf = self._buffers.get(key)
            if not buf or not buf["events"]:
                continue
            length_ok = len(buf["events"]) >= self.max_chunk_length
            size_ok = buf["size"] >= self.max_chunk_size
            if length_ok or size_ok:
                self._flush_one_buffer(key)

    def flush_by_age(self) -> None:
        """Flush any task's buffer whose oldest event exceeds max age."""
        now = time.monotonic()
        for key in list(self._buffers.keys()):
            buf = self._buffers.get(key)
            if not buf or not buf["events"]:
                continue
            if (now - buf["created_at"]) >= self.max_chunk_age:
                self._flush_one_buffer(key)

    def _flush_by_age_worker(self) -> None:
        """Background loop: periodically flush buffers that exceed max age."""
        while not self._stop_event.is_set():
            with self.lock:
                self.flush_by_age()
            time.sleep(0.2)

    def start_buffering(self) -> None:
        """Start the age-based flushing worker (idempotent; one worker for all tasks)."""
        with self.lock:
            if self._age_worker_started:
                return
            self._age_worker_started = True
            self._stop_event.clear()
        t = threading.Thread(target=self._flush_by_age_worker, daemon=True)
        t.start()

    def stop_buffering(self) -> None:
        """Flush all task buffers (e.g. when a task ends). Does not stop the age worker."""
        with self.lock:
            self.flush_all_buffers()
