import uuid
from typing import Optional
import asyncio as aio
import yaml
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse, HTMLResponse

from medperf import config
from medperf.commands.result.create import BenchmarkExecution
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.web_ui.common import templates, get_current_user_ui, get_current_user_api


class AssociationDraft(BaseModel):
    dataset: Dataset
    benchmark: Benchmark
    result: Optional[Result]


_draft_associate: dict[str, AssociationDraft] = {}

router = APIRouter()


@router.get("/associate_draft/ui", response_class=HTMLResponse)
async def associate_ui(
    request: Request,
    dataset_id: int,
    benchmark_id: int,
    current_user: bool = Depends(get_current_user_ui),
):
    """
    Serve the HTML page for associating a dataset with a benchmark.
    """
    dataset = Dataset.get(dataset_id)
    benchmark = Benchmark.get(benchmark_id)
    draft_id = str(uuid.uuid4())
    if benchmark.data_preparation_mlcube != dataset.data_preparation_mlcube:
        raise ValueError(
            f"Benchmark {benchmark_id} have prep_cube {benchmark.data_preparation_mlcube}, "
            f"while dataset {dataset_id} have prep_cube {dataset.data_preparation_mlcube}. Dataset cannot be "
            f"associated with this benchmark."
        )
    draft = AssociationDraft(dataset=dataset, benchmark=benchmark, result=None)
    _draft_associate[draft_id] = draft

    return templates.TemplateResponse(
        "dataset/dataset_associate.html",
        {
            "request": request,
            "draft_id": draft_id,
            "dataset": dataset,
            "benchmark": benchmark,
        },
    )


@router.post("/associate_draft/generate", response_class=StreamingResponse)
async def associate_generate(
    draft_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    draft = _draft_associate[draft_id]
    dataset = draft.dataset
    benchmark = draft.benchmark

    async def run_association():
        with config.ui.proxy():
            result = await run_in_threadpool(
                BenchmarkExecution.run,
                benchmark_uid=benchmark.id,
                data_uid=dataset.id,
                models_uids=[benchmark.reference_model_mlcube],
                no_cache=False,
            )  # docker pull logs
            result = result[0]
            _draft_associate[draft_id].result = result

    _ = aio.create_task(run_association())

    def message_stream():
        for msg in config.ui.get_message_generator():
            yield msg + "\n"  # Yield each message as a chunk

    return StreamingResponse(message_stream(), media_type="text/event-stream")


@router.get("/associate_draft/get_results", response_class=JSONResponse)
async def associate_get_results(
    draft_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    draft = _draft_associate[draft_id]
    return {
        "compatibility_results": yaml.dump(draft.get_result().results),
        "draft_id": draft_id,
    }


@router.post("/associate_draft/submit", response_class=JSONResponse)
async def associate_submit(
    draft_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    draft = _draft_associate[draft_id]
    try:
        metadata = {"test_result": draft.result.results}
        config.comms.associate_dset(draft.dataset.id, draft.benchmark.id, metadata)
        return {"draft_id": draft_id, "association_submitted": True}
    except Exception as e:
        return JSONResponse({"error": f"Error associating: {str(e)}"}, 400)


@router.get("/associate_draft/decline", response_class=JSONResponse)
async def associate_decline(
    draft_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    draft = _draft_associate.pop(draft_id)
    return {
        "dataset_id": draft.dataset.id,
        "draft_id": draft_id,
        "association_declined": True,
    }
