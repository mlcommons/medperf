import asyncio as aio
from concurrent.futures import ThreadPoolExecutor
import json
from enum import Enum
from threading import Thread
from typing import Optional, Dict, List, Union
from queue import Queue
from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from starlette.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel

from medperf.commands.benchmark.benchmark import BenchmarkExecution
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.web_ui.common import templates
from medperf.web_ui.results import results

router = APIRouter()


class DraftStatus(Enum):
    pending = "pending"
    running = "running"
    failed = "failed"
    executed = "executed"
    submitted = "submitted"
    n_a = "n/a"


# Draft model to store running benchmark executions
class RunDraft(BaseModel):
    benchmark_id: int
    dataset_id: int
    model_id: int
    result_id: str  # formatted as b{benchmark_id}m{model_id}d{dataset_id}
    status: DraftStatus
    logs: Optional[List[str]]

    def get_result(self) -> Optional[Result]:
        return results.get(self.result_id)


class RunStatus(BaseModel):
    model_id: int
    status: DraftStatus
    result: Optional[Result]


_drafts: Dict[str, RunDraft] = {}
_task_queue: Queue = Queue()


@router.get("/run_draft/ui/{result_id}", response_class=HTMLResponse)
async def run_draft_ui(result_id: str, request: Request):
    # Fetch relevant details like dataset_id, benchmark_id, and model_id from result_id
    # result_id is in the format "b{benchmark_id}m{model_id}d{dataset_id}"
    parts = result_id[1:].split('m')
    benchmark_id = int(parts[0])
    benchmark = Benchmark.get(benchmark_id)
    dataset_part = parts[1].split('d')
    model_id = int(dataset_part[0])
    dataset_id = int(dataset_part[1])
    model = Cube.get(model_id)
    dataset = Dataset.get(dataset_id)

    return templates.TemplateResponse(
        "dataset_run.html",
        {
            "request": request,
            "dataset": dataset,
            "benchmark": benchmark,
            "model": model,
            "result_id": result_id,
        }
    )


# Worker thread to process tasks in the background
def worker_thread():
    while True:
        benchmark_id, dataset_id, model_id = _task_queue.get()
        result_id = f"b{benchmark_id}m{model_id}d{dataset_id}"
        draft = _drafts[result_id]
        try:
            # Run the benchmark execution for each model
            execution = BenchmarkExecution(
                benchmark_uid=benchmark_id,
                data_uid=dataset_id,
                models_uids=[model_id],
                ignore_model_errors=True,
                ignore_failed_experiments=False,
            )
            draft.logs = []
            draft.status = DraftStatus.running

            def run_with_logs():
                try:
                    with execution.ui.proxy():
                        execution.prepare()
                        execution.validate()
                        execution.prepare_models()
                        results: List[Result] = execution.run_experiments()
                    return results[0], DraftStatus.executed
                except Exception as e:
                    execution.ui.print_error(f"Execution failed: {str(e)}")
                    return None, DraftStatus.failed

            # Run the execution in a separate thread to extract logs in realtime
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_with_logs)

                for log in execution.ui.get_message_generator():
                    draft.logs.append(log)
                result, status = future.result()
                draft.status = status
                results[result.local_id] = result
        finally:
            _task_queue.task_done()


# Start the worker thread
worker = Thread(target=worker_thread, daemon=True)
worker.start()


@router.post("/run_draft/run", response_model=RunStatus)
async def run_benchmark(dataset_id: int, benchmark_id: int, model_id: int):
    result_id = f"b{benchmark_id}m{model_id}d{dataset_id}"
    if result_id in _drafts:
        raise HTTPException(status_code=400, detail="Run draft already exists")

    # Create a new draft and add to queue
    draft = RunDraft(
        benchmark_id=benchmark_id,
        dataset_id=dataset_id,
        model_id=model_id,
        result_id=result_id,
        status=DraftStatus.pending,
        logs=[]
    )
    _drafts[result_id] = draft
    _task_queue.put((benchmark_id, dataset_id, model_id))

    return RunStatus(
        model_id=draft.model_id,
        status=draft.status,
        result=draft.get_result()
    )


@router.get("/run_draft/status", response_model=RunStatus)
async def get_run_status(dataset_id: int, benchmark_id: int, model_id: int):
    result_id = f"b{benchmark_id}m{model_id}d{dataset_id}"
    draft = _drafts.get(result_id)

    result = _load_result_if_exists(result_id)
    if result:
        if str(result.id).isdigit():
            status = DraftStatus.submitted
        else:
            status = DraftStatus.executed
        return RunStatus(
            model_id=model_id,
            status=status,
            result=result
        )
    elif draft:
        return RunStatus(
            model_id=draft.model_id,
            status=draft.status,
            result=draft.get_result()
        )
    else:
        return RunStatus(
            model_id=model_id,
            status=DraftStatus.n_a,
            result=None
            )


@router.get("/run_draft/logs", response_class=StreamingResponse)
async def get_run_logs(dataset_id: int, benchmark_id: int, model_id: int):
    result_id = f"b{benchmark_id}m{model_id}d{dataset_id}"
    draft = _drafts.get(result_id)

    async def log_stream():
        if not draft:
            yield json.dumps({"type": "print", "message": "No logs available"}) + "\n"
            return

        line_id = 0
        while True:
            await aio.sleep(1)  # Simulate real-time log fetching
            while line_id < len(draft.logs):
                yield draft.logs[line_id] + "\n"
                line_id += 1
            if draft.status not in {DraftStatus.pending, DraftStatus.running} and line_id >= len(draft.logs):
                break

    return StreamingResponse(log_stream(), media_type="text/event-stream")


def _load_result_if_exists(result_id: str) -> Optional[Result]:
    # Implement logic to load a result from disk if it exists
    if result_id in results:
        result = results[result_id]
        return result
    else:
        return None
