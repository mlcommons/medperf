# medperf/web-ui/mlcubes/routes.py
import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request

from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.enums import Status
from medperf.web_ui.common import templates

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def mlcubes_ui(request: Request, local_only: bool = False, mine_only: bool = False):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    mlcubes = Cube.all(
        local_only=local_only,
        filters=filters,
    )
    mlcubes = sorted(mlcubes, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    mine_cubes = [c for c in mlcubes if c.owner == my_user_id]
    other_cubes = [c for c in mlcubes if c.owner != my_user_id]
    mlcubes = mine_cubes + other_cubes
    return templates.TemplateResponse("mlcubes.html", {"request": request, "mlcubes": mlcubes})


@router.get("/ui/{mlcube_id}", response_class=HTMLResponse)
def mlcube_detail_ui(request: Request, mlcube_id: int):
    mlcube = Cube.get(cube_uid=mlcube_id, valid_only=False)

    # Fetching associations and related benchmarks
    benchmarks_associations = Cube.get_benchmarks_associations(mlcube_uid=mlcube_id)

    approval_status_order = {
        Status.PENDING: 0,
        Status.APPROVED: 1,
        Status.REJECTED: 2,
    }

    def assoc_sorting_key(assoc):
        # lower status - first
        status_order = approval_status_order.get(assoc.approval_status, -1)
        # recent associations - first
        date_order = -(assoc.approved_at or assoc.created_at).timestamp()
        return status_order, date_order

    benchmarks_associations = sorted(benchmarks_associations, key=assoc_sorting_key)

    # Fetch benchmarks information
    benchmarks = {assoc.benchmark: Benchmark.get(assoc.benchmark) for assoc in benchmarks_associations if
                  assoc.benchmark}

    return templates.TemplateResponse(
        "mlcube_detail.html",
        {
            "request": request,
            "mlcube": mlcube,
            "benchmarks_associations": benchmarks_associations,
            "benchmarks": benchmarks
        }
    )
