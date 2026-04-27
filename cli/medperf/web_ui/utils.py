import uuid
from medperf.entities.cube import Cube


def get_ui_ordering(ordering: str) -> str:
    ordering_map = {
        "created_at_asc": "created_at",
        "name_asc": "name",
        "name_desc": "-name",
    }
    return ordering_map.get(ordering, "-created_at")


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
