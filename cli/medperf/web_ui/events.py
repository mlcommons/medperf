from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import JSONResponse

import medperf.config as config
from medperf.web_ui.common import (
    get_current_user_api,
)

router = APIRouter()


@router.get("/notifications", response_class=JSONResponse)
def get_notifications(
    request: Request,
    current_user: bool = Depends(get_current_user_api),
):
    new_notifications = request.app.state.new_notifications.copy()
    for notification in new_notifications:
        request.app.state.notifications.append(notification)
        request.app.state.new_notifications.remove(notification)

    return new_notifications


@router.post("/notifications/mark_read")
def read_notification(
    request: Request,
    notification_id: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    for notification in request.app.state.notifications:
        if notification["id"] == notification_id:
            notification["read"] = True
            return

    for notification in request.app.state.new_notifications:
        if notification["id"] == notification_id:
            notification["read"] = True
            return


@router.post("/notifications/delete")
def delete_notification(
    request: Request,
    notification_id: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    notifications = request.app.state.notifications
    new_notifications = request.app.state.new_notifications

    for notification in notifications:
        if notification["id"] == notification_id:
            notifications.remove(notification)
            return

    for notification in new_notifications:
        if notification["id"] == notification_id:
            new_notifications.remove(notification)
            return


@router.get("/current_task", response_class=JSONResponse)
def get_task_id(request: Request, current_user: bool = Depends(get_current_user_api)):
    while not config.ui.task_id:
        pass
    return {"task_id": config.ui.task_id}


@router.get("/events", response_class=JSONResponse)
def get_event(
    request: Request,
    current_user: bool = Depends(get_current_user_api),
):
    event = config.ui.get_event()

    if event["task_id"] is None:
        return event
    # Add the event to task logs
    if request.app.state.task["running"]:
        if event["task_id"] == request.app.state.task["id"]:
            request.app.state.task["logs"].append(event)
        else:
            for task in request.app.state.old_tasks:
                if task["id"] == event["task_id"]:
                    task["logs"].append(event)
                    break
    else:
        for task in request.app.state.old_tasks:
            if task["id"] == event["task_id"]:
                task["logs"].append(event)
                break
    return event


@router.post("/events")
def respond(
    request: Request,
    is_approved: bool = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    config.ui.set_response({"value": is_approved})
    # Remove the prompt event after responding to the prompt
    for event in request.app.state.task["logs"]:
        if event["type"] == "prompt":
            event["type"] = "prompt_done"
            event["approved"] = is_approved
            break
