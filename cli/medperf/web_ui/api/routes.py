# medperf/web_ui/api/routes.py
import os
from fastapi import APIRouter, HTTPException, Form, Depends
from fastapi.responses import JSONResponse

from medperf.web_ui.common import check_user_api

router = APIRouter()

# Start listing folders at the /home/{username}
BASE_DIR = os.path.expanduser("~")
BASE_DIR = os.path.realpath(BASE_DIR)


# TODO: close with token and list in documentation
@router.post("/browse", response_class=JSONResponse)
def browse_directory(
    path: str = Form(...),
    with_files: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    # Ensure path is within the base directory
    if not os.path.commonpath([BASE_DIR, full_path]) == BASE_DIR:
        raise HTTPException(status_code=403, detail="Access denied")

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
    parent = os.path.dirname(full_path) if full_path != BASE_DIR else BASE_DIR
    have_parent = full_path != BASE_DIR

    return {
        "folders": folders,
        "parent": parent,
        "have_parent": have_parent,
        "current_folder": os.path.abspath(full_path),
    }
