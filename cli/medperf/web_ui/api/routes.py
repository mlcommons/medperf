# medperf/web_ui/api/routes.py
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Form, Depends, Request, Query, Body
from fastapi.responses import JSONResponse

import medperf.config as config
from medperf.exceptions import (
    EditableInstallUpdateError,
    InvalidArgumentError,
    UpdateNotNeededError,
)
from medperf.web_ui.common import check_user_api
from medperf.web_ui.entity_search import search_entities
from medperf.update_manager import UpdateManager
from medperf.utils import sanitize_path

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/update_status", response_class=JSONResponse, include_in_schema=False)
def update_status(request: Request, current_user: bool = Depends(check_user_api)):
    # Polled by waitForRestart() (update_banner.js) across the restart; the
    # session token is carried over, so the cookie stays valid throughout.
    updater = UpdateManager()
    payload = {
        "status": "ok",
        "version": updater.get_installed_version(),
    }

    if getattr(request.app.state, "update_in_progress", False):
        payload["update_in_progress"] = True

    update_error = getattr(request.app.state, "update_error", None)
    if update_error:
        payload["status"] = "update_failed"
        payload["error"] = update_error
        # Reported once, so a past failure doesn't mask later healthy polls
        request.app.state.update_error = None
    return payload


@router.get("/update_check", response_class=JSONResponse)
def update_check(
    request: Request,
    refresh: bool = Query(False),
    current_user: bool = Depends(check_user_api),
):
    updater = UpdateManager()
    info = updater.get_update_info(force_refresh=refresh)
    request.app.state.update_check = info
    message = updater.format_update_check_message(info)
    return {**info, "message": message}


@router.post("/update", response_class=JSONResponse)
def update_medperf(
    request: Request,
    body: dict = Body(default_factory=dict),
    current_user: bool = Depends(check_user_api),
):
    if request.app.state.task_running:
        raise HTTPException(
            status_code=400,
            detail="A task is currently running. Wait for it to finish before updating.",
        )

    if config.running_containers:
        raise HTTPException(
            status_code=400,
            detail="Containers are still running. Stop them before updating.",
        )

    if getattr(request.app.state, "update_in_progress", False):
        raise HTTPException(status_code=409, detail="Update already in progress.")

    updater = UpdateManager()
    try:
        installed_version = updater.validate_update(
            latest_version=body.get("latest_version"),
            current_version=body.get("current_version"),
        )
    except (UpdateNotNeededError, EditableInstallUpdateError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    host_props = getattr(request.app.state, "host_props", None) or {}
    port = host_props.get("port", 8100)
    request.app.state.update_in_progress = True
    request.app.state.update_error = None

    updater.schedule_webui_update(port, request.app.state)
    logger.info("Scheduled MedPerf update (installed %s) via PyPI", installed_version)

    return JSONResponse(status_code=202, content={"status": "started"})


@router.get("/entity_search", response_class=JSONResponse)
def entity_search(
    entity_type: str = Query(...),
    q: Optional[str] = Query(None),
    mine_only: bool = Query(False),
    container_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    selected_id: Optional[int] = Query(None),
    ids: Optional[str] = Query(
        None, description="Comma-separated entity IDs to restrict results"
    ),
    current_user: bool = Depends(check_user_api),
):
    allowed_ids = None
    if ids:
        try:
            allowed_ids = [int(item.strip()) for item in ids.split(",") if item.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ids parameter")

    return search_entities(
        entity_type,
        q=q,
        mine_only=mine_only,
        container_type=container_type,
        limit=limit,
        selected_id=selected_id,
        allowed_ids=allowed_ids,
    )


@router.get("/running_tasks", response_class=JSONResponse)
def get_running_tasks(current_user: bool = Depends(check_user_api)):
    tasks = list(config.running_containers.keys())
    return {"tasks": tasks}


@router.post("/stop_task", response_class=JSONResponse)
def stop_task(
    task_name: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    wrapper = config.running_containers.get(task_name)
    if wrapper is None:
        raise HTTPException(
            status_code=404, detail=f"No running task named '{task_name}'"
        )
    try:
        wrapper.killpg()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


# TODO: close with token and list in documentation
@router.post("/browse", response_class=JSONResponse)
def browse_directory(
    path: str = Form(""),
    with_files: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):
    path = path or str(Path.home())
    base_dir = "/"  # Allow user to put any path
    try:
        full_path = sanitize_path(os.path.join(base_dir, path))
    except InvalidArgumentError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    # List directories inside the path and sort them
    sorted_folders = []
    sorted_files = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            sorted_folders.append(item)
        else:
            if with_files:
                sorted_files.append(item)

    sorted_folders.sort(key=lambda x: (x.startswith("."), x.lower()))
    sorted_files.sort(key=lambda x: (x.startswith("."), x.lower()))

    sorted_items = sorted_folders + sorted_files

    folders = []
    for item in sorted_items:
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            folders.append({"name": item, "path": item_path, "type": "dir"})
        else:
            folders.append({"name": item, "path": item_path, "type": "file"})

    # Add the parent directory
    parent = os.path.dirname(full_path) if full_path != base_dir else base_dir
    have_parent = full_path != base_dir

    return {
        "folders": folders,
        "parent": parent,
        "have_parent": have_parent,
        "current_folder": os.path.abspath(full_path),
    }
