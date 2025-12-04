import uuid
from medperf.entities.cube import Cube


def get_container_type(container: Cube):
    container_config = container.container_config
    container_tasks = container_config.get("tasks", []).keys()

    if "prepare" in container_tasks and "sanity_check" in container_tasks:
        return "data-prep-container"
    elif "infer" in container_tasks:
        return "reference-container"
    elif "evaluate" in container_tasks:
        return "metrics-container"
    else:
        return "unknown-container"


def generate_uuid():
    return str(uuid.uuid4())
