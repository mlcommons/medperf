import uuid
from medperf.entities.cube import Cube


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
    container_tasks = container_config.get("tasks", []).keys()

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
