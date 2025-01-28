# medperf/web-ui/mlcubes/routes.py
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
from medperf.exceptions import CleanExit
from medperf.web_ui.common import (  # noqa
    get_current_user_api,
    templates,
    sort_associations_display,
    get_current_user_ui,
)
from medperf.commands.compatibility_test.run import CompatibilityTestExecution

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def mlcubes_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(get_current_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    mlcubes = Cube.all(
        filters=filters,
    )
    mlcubes = sorted(mlcubes, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    mine_cubes = [c for c in mlcubes if c.owner == my_user_id]
    other_cubes = [c for c in mlcubes if c.owner != my_user_id]
    mlcubes = mine_cubes + other_cubes
    return templates.TemplateResponse(
        "mlcube/mlcubes.html",
        {"request": request, "mlcubes": mlcubes, "mine_only": mine_only},
    )


@router.get("/ui/display/{mlcube_id}", response_class=HTMLResponse)
def mlcube_detail_ui(
    request: Request,
    mlcube_id: int,
    current_user: bool = Depends(get_current_user_ui),
):
    mlcube = Cube.get(cube_uid=mlcube_id, valid_only=False)

    benchmark_assocs = Cube.get_benchmarks_associations(mlcube_uid=mlcube_id)

    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc.benchmark] = assoc

    benchmarks = Benchmark.all()
    benchmarks = {b.id: b for b in benchmarks}
    # benchmarks_associations = sort_associations_display(benchmarks_associations)
    is_owner = mlcube.owner == get_medperf_user_data()["id"]

    return templates.TemplateResponse(
        "mlcube/mlcube_detail.html",
        {
            "request": request,
            "entity": mlcube,
            "entity_name": mlcube.name,
            "is_owner": is_owner,
            "benchmarks_associations": benchmark_associations,
            "benchmarks": benchmarks,
        },
    )


@router.get("/submit/ui", response_class=HTMLResponse)
def create_mlcube_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "mlcube/mlcube_submit.html", {"request": request, "benchmarks": benchmarks}
    )


@router.get("/submit/compatibility_test", response_class=HTMLResponse)
def compatibilty_test_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "mlcube/compatibility_test.html", {"request": request, "benchmarks": benchmarks}
    )


@router.post("/submit", response_class=JSONResponse)
def submit_mlcube(
    name: str = Form(...),
    mlcube_file: str = Form(...),
    parameters_file: str = Form(...),
    additional_file: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    mlcube_info = {
        "name": name,
        "git_mlcube_url": mlcube_file,
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
        mlcube_id = SubmitCube.run(mlcube_info)
        config.ui.set_success()
        return {"mlcube_id": mlcube_id}
    except CleanExit:
        config.ui.set_error()
        return {"mlcube_id": None}


@router.post("/test", response_class=JSONResponse)
def test_mlcube(
    benchmark: int = Form(...),
    model_path: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        CompatibilityTestExecution.run(benchmark=benchmark, model=model_path)
        return config.ui.set_success()
    except CleanExit:
        return config.ui.set_error()


@router.post("/associate", response_class=JSONResponse)
def associate(
    mlcube_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        AssociateCube.run(cube_uid=mlcube_id, benchmark_uid=benchmark_id)
        return config.ui.set_success()
    except CleanExit:
        return config.ui.set_error()
