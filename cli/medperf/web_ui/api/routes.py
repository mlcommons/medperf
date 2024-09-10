# medperf/web_ui/api/routes.py
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter()

BASE_DIR = os.getcwd()  # Restrict access to this base directory


@router.get("/browse")
def browse_directory(path: str = Query(...)):
    full_path = os.path.join(BASE_DIR, path)
    os.path.join(BASE_DIR, path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    # Ensure path is within the base directory
    if not os.path.commonpath([BASE_DIR, full_path]).startswith(BASE_DIR):
        raise HTTPException(status_code=403, detail="Access denied")

    # List directories inside the path
    folders = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            folders.append({"name": item, "path": os.path.relpath(item_path, BASE_DIR)})

    # Add the parent directory if not at the root
    parent = os.path.dirname(full_path) if full_path != BASE_DIR else None

    return JSONResponse({"folders": folders, "parent": parent})
