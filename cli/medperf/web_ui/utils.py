import uuid
from fastapi import Request
from medperf.entities.cube import Cube
from medperf.utils import sanitize_path
from medperf_dashboard.preparation_dashboard import build_app
from starlette.middleware.wsgi import WSGIMiddleware


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
