import time
from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from queue import Empty
import medperf.config as config
from medperf.web_ui.common import (
    check_user_api,
)
from medperf.web_ui.schemas import EventBase
import anyio

router = APIRouter()


@router.get("/notifications", response_class=JSONResponse)
def get_notifications(
    request: Request,
    current_user: bool = Depends(check_user_api),
):
    new_notifications = request.app.state.new_notifications.copy()
    request.app.state.notifications.extend(new_notifications)
    request.app.state.new_notifications.clear()

    return new_notifications


@router.post("/notifications/mark_read")
def read_notification(
    request: Request,
    notification_id: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    for notification in request.app.state.notifications:
        if notification.id == notification_id:
            notification.mark_read()
            return


@router.post("/notifications/delete")
def delete_notification(
    request: Request,
    notification_id: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    notifications = request.app.state.notifications

    for notification in notifications:
        if notification.id == notification_id:
            notifications.remove(notification)
            return


@router.get("/current_task", response_class=JSONResponse)
def get_task_id(request: Request, current_user: bool = Depends(check_user_api)):
    start_time = time.monotonic()
    while not config.ui.task_id:
        time.sleep(0.1)
        if time.monotonic() - start_time >= 2:
            break
    return {"task_id": config.ui.task_id}


def process_event(request: Request, event: EventBase):
    if request.app.state.task.running and event.task_id == request.app.state.task.id:
        request.app.state.task.add_log(event)
        return
    for task in request.app.state.old_tasks:
        if task.id == event.task_id:
            task.add_log(event)
            break


def sse_frame_event(event: EventBase):
    return f"id: {event.id}\ndata: {event.json()}\n\n"


def should_process_old(request: Request, stream_old: bool):
    if not stream_old:
        return
    for old_event in request.app.state.task.logs.copy():
        yield sse_frame_event(old_event)


def event_generator(request: Request, stream_old: bool):
    yield from should_process_old(request, stream_old)

    while True:
        event_processed = False
        event = None
        if anyio.from_thread.run(request.is_disconnected):
            break
        try:
            event = config.ui.get_event(timeout=1.0)
            if not event.task_id:
                continue

            process_event(request, event)
            event_processed = True
            yield sse_frame_event(event)

        except Empty:
            continue

        except (BrokenPipeError, ConnectionResetError, GeneratorExit):
            if event and not event_processed:
                process_event(request, event)
            break


@router.get("/events", response_class=StreamingResponse)
def stream_events(
    request: Request,
    stream_old: bool = False,
    current_user: bool = Depends(check_user_api),
):
    return StreamingResponse(
        event_generator(request, stream_old),
        media_type="text/event-stream; charset=utf-8",
    )


@router.post("/events")
def respond(
    request: Request,
    is_approved: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):
    config.ui.set_response({"value": is_approved})
    # Remove the prompt event after responding to the prompt
    for event in request.app.state.task.logs:
        if event.kind == "event" and event.type == "prompt":
            event.type = "prompt_done"
            event.approved = is_approved
            break
