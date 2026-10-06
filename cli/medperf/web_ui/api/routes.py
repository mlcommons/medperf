# medperf/web_ui/api/routes.py
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Form, Depends, Query
from fastapi.responses import JSONResponse

import medperf.config as config
from medperf.exceptions import InvalidArgumentError
from medperf.web_ui.common import check_user_api
from medperf.web_ui.entity_search import search_entities
from medperf.utils import sanitize_path

router = APIRouter()


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


@router.get("/task_history", response_class=JSONResponse)
def get_task_history(current_user: bool = Depends(check_user_api)):
    """Return the most recent finished tasks with their logs, most recent first."""
    return {"tasks": config.ui.get_finished_tasks()}


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
