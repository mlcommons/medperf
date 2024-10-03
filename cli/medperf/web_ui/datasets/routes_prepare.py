import asyncio as aio
from typing import Optional

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from medperf.commands.dataset.prepare import DataPreparation
from medperf.web_ui.common import templates

router = APIRouter()

_drafts_prepare: dict[int, DataPreparation] = {}


@router.get("/ui/prepare", response_class=HTMLResponse)
async def prepare_ui(dataset_id: int, request: Request):
    return templates.TemplateResponse("dataset_prepare.html", {"request": request, "dataset_id": dataset_id})


@router.get("/prepare_draft/generate", response_class=StreamingResponse)
async def prepare_generate(
        dataset_id: int
):
    preparation = DataPreparation(dataset_id, approve_sending_reports=False)
    _drafts_prepare[dataset_id] = preparation

    preparation.get_dataset()  # prints nothing
    preparation.validate()  # may run Invalid Exception

    async def run_preparation():
        with preparation.ui.proxy():
            await run_in_threadpool(preparation.get_prep_cube)  # docker pull logs
            preparation.setup_parameters()  # Prints nothing

    _ = aio.create_task(run_preparation())

    def message_stream():
        for msg in preparation.ui.get_message_generator():
            yield msg + "\n"  # Yield each message as a chunk

    return StreamingResponse(message_stream(), media_type="text/plain")


class ReportSendApprovalRequest(BaseModel):
    dataset_id: int
    ask_for_approval: bool
    message_to_user: Optional[str]


@router.get("/prepare_draft/ask_send_approval", response_model=ReportSendApprovalRequest)
async def prepare_ask_approval(
        dataset_id: int
):
    preparation = _drafts_prepare[dataset_id]
    msg = None
    ask_for_approval = preparation.should_prompt_for_report_sending_approval()
    if ask_for_approval:
        msg = preparation._report_sending_approval_msg()
    return ReportSendApprovalRequest(dataset_id=dataset_id,
                                     ask_for_approval=ask_for_approval,
                                     message_to_user=msg)


@router.get("/prepare_draft/run", response_class=StreamingResponse)
async def prepare_run(
        dataset_id: int,
        approved_sending_reports: bool
):
    preparation = _drafts_prepare[dataset_id]
    preparation.allow_sending_reports = approved_sending_reports

    async def run_preparation():
        with preparation.ui.proxy():
            if preparation.should_run_prepare():
                await run_in_threadpool(preparation.run_prepare)  # Prints docker run logs

            with preparation.ui.interactive():
                await run_in_threadpool(
                    preparation.run_sanity_check)  # Run a sanity-check task and prints docker run logs
                await run_in_threadpool(preparation.run_statistics)  # Run a statistics task and prints docker run logs
                await run_in_threadpool(preparation.mark_dataset_as_ready)

    _ = aio.create_task(run_preparation())

    def message_stream():
        for msg in preparation.ui.get_message_generator():
            yield msg + "\n"  # Yield each message as a chunk

    return StreamingResponse(message_stream(), media_type="text/plain")
