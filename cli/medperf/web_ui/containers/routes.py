# medperf/web-ui/containers/routes.py
import logging

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request

from medperf.commands.mlcube.associate import AssociateCube
from medperf.commands.mlcube.submit import SubmitCube
import medperf.config as config
from medperf.account_management import get_medperf_user_data
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.exceptions import MedperfException
from medperf.web_ui.common import (
    get_current_user_api,
    templates,
    get_current_user_ui,
)
from medperf.commands.compatibility_test.run import CompatibilityTestExecution

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def containers_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(get_current_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    containers = Cube.all(
        filters=filters,
    )
    containers = sorted(containers, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    mine_containers = [c for c in containers if c.owner == my_user_id]
    other_containers = [c for c in containers if c.owner != my_user_id]
    containers = mine_containers + other_containers
    return templates.TemplateResponse(
        "container/containers.html",
        {"request": request, "containers": containers, "mine_only": mine_only},
    )


@router.get("/ui/display/{container_id}", response_class=HTMLResponse)
def container_detail_ui(
    request: Request,
    container_id: int,
    current_user: bool = Depends(get_current_user_ui),
):
    container = Cube.get(cube_uid=container_id, valid_only=False)

    benchmark_assocs = Cube.get_benchmarks_associations(mlcube_uid=container_id)

    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc.benchmark] = assoc

    benchmarks = Benchmark.all()
    benchmarks = {b.id: b for b in benchmarks}
    # benchmarks_associations = sort_associations_display(benchmarks_associations)
    is_owner = container.owner == get_medperf_user_data()["id"]

    return templates.TemplateResponse(
        "container/container_detail.html",
        {
            "request": request,
            "entity": container,
            "entity_name": container.name,
            "is_owner": is_owner,
            "benchmarks_associations": benchmark_associations,
            "benchmarks": benchmarks,
        },
    )


@router.get("/register/ui", response_class=HTMLResponse)
def create_container_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "container/register_container.html",
        {"request": request, "benchmarks": benchmarks},
    )


@router.get("/register/compatibility_test", response_class=HTMLResponse)
def compatibilty_test_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "container/compatibility_test.html",
        {"request": request, "benchmarks": benchmarks},
    )


@router.post("/register", response_class=JSONResponse)
def register_container(
    name: str = Form(...),
    container_file: str = Form(...),
    parameters_file: str = Form(""),
    additional_file: str = Form(""),
    current_user: bool = Depends(get_current_user_api),
):
    container_info = {
        "name": name,
        "git_mlcube_url": container_file,
        "git_mlcube_hash": "",
        "git_parameters_url": parameters_file,
        "parameters_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": "",
        "state": "OPERATION",
    }
    try:
        container_id = SubmitCube.run(container_info)
        config.ui.set_success()
        return {"status": "success", "container_id": container_id, "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "container_id": None, "error": str(exp)}


@router.post("/test", response_class=JSONResponse)
def test_container(
    benchmark: int = Form(...),
    container_path: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        _, results = CompatibilityTestExecution.run(
            benchmark=benchmark, model=container_path
        )
        config.ui.set_success()
        return {"status": "success", "error": "", "results": results}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "error": str(exp), "results": ""}


@router.post("/associate", response_class=JSONResponse)
def associate(
    container_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        AssociateCube.run(cube_uid=container_id, benchmark_uid=benchmark_id)
        config.ui.set_success()
        return {"status": "success", "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "error": str(exp)}
