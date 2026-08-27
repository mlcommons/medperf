import uuid
from typing import Optional, Tuple

from fastapi import Request
from starlette.middleware.wsgi import WSGIMiddleware

from medperf.dashboard.preparation_dashboard import build_app
from medperf.entities.cube import Cube
from medperf.utils import sanitize_path

MIN_SEARCH_LENGTH = 2
SEARCH_DEBOUNCE_MS = 300


def normalize_search_query(search: Optional[str]) -> str:
    return (search or "").strip()


def apply_listing_search(filters: dict, search: Optional[str]) -> Tuple[dict, str]:
    query = normalize_search_query(search)
    if len(query) >= MIN_SEARCH_LENGTH:
        filters["search"] = query
    return filters, query


def get_ui_ordering(ordering: str) -> str:
    ordering_map = {
        "created_at_asc": "created_at",
        "name_asc": "name",
        "name_desc": "-name",
    }
    return ordering_map.get(ordering, "-created_at")


def build_listing_filters(page: int, page_size: int, ordering: str) -> dict:
    offset = (page - 1) * page_size
    return {
        "limit": page_size,
        "offset": offset,
        "ordering": get_ui_ordering(ordering),
    }


def build_pagination_context(
    page: int,
    page_size: int,
    ordering: str,
    total_count: int,
    page_items_count: int,
) -> dict:
    offset = (page - 1) * page_size
    total_pages = (total_count + page_size - 1) // page_size
    start_index = 0
    end_index = 0
    if total_count != 0:
        start_index = offset + 1
        end_index = min(offset + page_items_count, total_count)
    return {
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "ordering": ordering,
        "total_count": total_count,
        "start_index": start_index,
        "end_index": end_index,
    }


def get_container_type(container: Cube):
    # todo: use container parser.
    container_config = container.container_config
    container_tasks = container_config.get("tasks", {}).keys()

    if "prepare" in container_tasks and "sanity_check" in container_tasks:
        return "data-prep-container"
    elif "infer" in container_tasks:
        return "reference-container"
    elif "evaluate" in container_tasks or "run_script" in container_tasks:
        return "metrics-container"
    else:
        return "unknown-container"


def generate_uuid():
    return str(uuid.uuid4())


def mount_dashboard(
    request: Request, benchmark_id, stages_path, institutions_path, force_update
):
    dashboards = request.app.state.dashboards
    stages_path = sanitize_path(stages_path)
    institutions_path = sanitize_path(institutions_path)

    dashboard_built = benchmark_id in dashboards

    stages_changed = False
    institutions_changed = False
    if dashboard_built:
        stages_changed = stages_path != dashboards[benchmark_id]["stages_path"]
        institutions_changed = (
            institutions_path != dashboards[benchmark_id]["institutions_path"]
        )

    must_build = (
        not dashboard_built or stages_changed or institutions_changed or force_update
    )

    if not must_build:
        return

    dashbaord_app = build_app(
        benchmark_id,
        stages_path,
        institutions_path,
        prefix=f"/ui/display/{benchmark_id}/dashboard/app/",
    )
    request.app.state.dashboards[benchmark_id] = {
        "stages_path": stages_path,
        "institutions_path": institutions_path,
    }
    request.app.mount(
        f"/ui/display/{benchmark_id}/dashboard/app",
        WSGIMiddleware(dashbaord_app.server),
    )
