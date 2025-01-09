from fastapi import APIRouter, Depends, Form
from medperf.exceptions import CleanExit
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse

from medperf.commands.dataset.prepare import DataPreparation
from medperf.web_ui.common import get_current_user_api
import medperf.config as config

router = APIRouter()


@router.post("/prepare/prepare", response_class=JSONResponse)
def prepare(
    dataset_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        dataset_id = DataPreparation.run(dataset_id)
        return {"dataset_id": dataset_id}
    except CleanExit:
        return {"dataset_id": None}
    _drafts_prepare[dataset_id] = preparation

    preparation.get_dataset()  # prints nothing
    preparation.validate()  # may run Invalid Exception

    def run_preparation():
        with preparation.ui.proxy():
            run_in_threadpool(preparation.get_prep_cube)  # docker pull logs
            preparation.setup_parameters()  # Prints nothing

    _ = aio.create_task(run_preparation())

    def message_stream():
        for msg in preparation.ui.get_message_generator():
            yield msg + "\n"  # Yield each message as a chunk

    return StreamingResponse(message_stream(), media_type="text/plain")


@router.get("/events", response_class=JSONResponse)
def get_event(
    request: Request,
    current_user: bool = Depends(get_current_user_api),
):
    return config.ui.get_event()


@router.post("/events")
def respond(
    request: Request,
    is_approved: bool = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    config.ui.set_response({"value": is_approved})


# class ReportSendApprovalRequest(BaseModel):
#     dataset_id: int
#     ask_for_approval: bool
#     message_to_user: Optional[str]


# @router.get("/prepare/ask_send_approval", response_model=ReportSendApprovalRequest)
# def prepare_ask_approval(
#     dataset_id: int,
#     current_user: bool = Depends(get_current_user_api),
# ):
#     preparation = _drafts_prepare[dataset_id]
#     msg = None
#     ask_for_approval = preparation.should_prompt_for_report_sending_approval()
#     if ask_for_approval:
#         msg = preparation._report_sending_approval_msg()
#     return ReportSendApprovalRequest(
#         dataset_id=dataset_id, ask_for_approval=ask_for_approval, message_to_user=msg
#     )


# @router.get("/prepare/run", response_class=StreamingResponse)
# def prepare_run(
#     dataset_id: int,
#     approved_sending_reports: bool,
#     current_user: bool = Depends(get_current_user_api),
# ):
#     preparation = _drafts_prepare[dataset_id]
#     preparation.allow_sending_reports = approved_sending_reports

#     def run_preparation():
#         with preparation.ui.proxy():
#             if preparation.should_run_prepare():
#                 run_in_threadpool(preparation.run_prepare)  # Prints docker run logs

#             with preparation.ui.interactive():
#                 run_in_threadpool(
#                     preparation.run_sanity_check
#                 )  # Run a sanity-check task and prints docker run logs
#                 run_in_threadpool(
#                     preparation.run_statistics
#                 )  # Run a statistics task and prints docker run logs
#                 run_in_threadpool(preparation.mark_dataset_as_ready)

#     _ = aio.create_task(run_preparation())

#     def message_stream():
#         for msg in preparation.ui.get_message_generator():
#             yield msg + "\n"  # Yield each message as a chunk

#     return StreamingResponse(message_stream(), media_type="text/plain")
