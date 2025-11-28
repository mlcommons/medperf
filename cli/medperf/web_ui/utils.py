import uuid
from medperf.entities.cube import Cube
import yaml


def get_container_type(container: Cube):
    with open(container.cube_path, "r") as f:
        yaml_data = yaml.safe_load(f.read())
    container_tasks = yaml_data.get("tasks", []).keys()
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
