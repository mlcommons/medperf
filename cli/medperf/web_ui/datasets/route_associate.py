from typing import Any
import asyncio as aio
import yaml
from fastapi import APIRouter
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse, HTMLResponse

from medperf import config
from medperf.commands.result.create import BenchmarkExecution
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.web_ui.common import templates


class AssociationDraft(BaseModel):
    dataset: Dataset
    benchmark: Benchmark
    result: Any


_draft_associate: dict[int, AssociationDraft] = {}

router = APIRouter()


@router.get("/associate_draft/ui", response_class=HTMLResponse)
async def associate_ui(request: Request, dataset_id: int):
    """
    Serve the HTML page for associating a dataset with a benchmark.
    """
    dataset = Dataset.get(dataset_id)

    benchmarks = Benchmark.all(filters={"data_preparation_mlcube": dataset.data_preparation_mlcube})
    if benchmarks:
        benchmark = benchmarks[0]
    else:
        return HTMLResponse(
            "No compatible benchmark found for this dataset.",
            status_code=400,
        )

    return templates.TemplateResponse(
        "dataset_associate.html",
        {
            "request": request,
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "benchmark_id": benchmark.id,
            "benchmark_name": benchmark.name,
        },
    )


@router.post("/associate_draft/generate", response_class=StreamingResponse)
async def associate_generate(dataset_id: int):
    dataset = Dataset.get(dataset_id)
    benchmarks = Benchmark.all()
    benchmarks = [b for b in benchmarks if b.data_preparation_mlcube == dataset.data_preparation_mlcube]
    benchmark = benchmarks[0]

    async def run_preparation():
        with config.ui.proxy():
            result = await run_in_threadpool(
                BenchmarkExecution.run,
                benchmark_uid=benchmark.id,
                data_uid=dataset.id,
                models_uids=[benchmark.reference_model_mlcube],
                no_cache=False,
            )  # docker pull logs
            result = result[0]
            _draft_associate[dataset_id] = AssociationDraft(
                dataset=dataset,
                benchmark=benchmark,
                result=result
            )

    _ = aio.create_task(run_preparation())

    def message_stream():
        for msg in config.ui.get_message_generator():
            yield msg + "\n"  # Yield each message as a chunk

    return StreamingResponse(message_stream(), media_type="text/event-stream")


@router.get("/associate_draft/get_results", response_class=JSONResponse)
async def associate_get_results(dataset_id: int):
    draft = _draft_associate[dataset_id]
    return {
        "compatibility_results": yaml.dump(draft.result.results),
        "dataset_id": dataset_id,
        "dataset_name": draft.dataset.name,
        "benchmark_id": draft.benchmark.id,
        "benchmark_name": draft.benchmark.name
    }


@router.post("/associate_draft/submit", response_class=JSONResponse)
async def associate_submit(dataset_id: int):
    draft = _draft_associate[dataset_id]
    try:
        metadata = {"test_result": draft.result.results}
        config.comms.associate_dset(dataset_id, draft.benchmark.id, metadata)
        return {"dataset_id": dataset_id}
    except Exception as e:
        return JSONResponse({"error": f"Error associating: {str(e)}"}, 400)


@router.get("/associate_draft/decline", response_class=JSONResponse)
async def associate_decline(dataset_id: int):
    del _draft_associate[dataset_id]
    return {"dataset_id": dataset_id, "association_declined": True}
