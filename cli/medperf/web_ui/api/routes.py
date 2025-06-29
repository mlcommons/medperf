# medperf/web_ui/api/routes.py
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Form, Depends
from fastapi.responses import JSONResponse

from medperf.exceptions import InvalidArgumentError
from medperf.web_ui.common import check_user_api
from medperf.utils import sanitize_path

router = APIRouter()


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
