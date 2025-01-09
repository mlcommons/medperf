from pathlib import Path
from typing import Dict

import yaml
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse
from medperf.commands.result.submit import ResultSubmission
from medperf.entities.result import Result
from medperf.web_ui.common import get_current_user_api
from medperf.web_ui.results import results

_drafts_result_submit: dict[str, ResultSubmission] = {}

router = APIRouter()


@router.post("/result_submit_draft/generate/", response_class=JSONResponse)
def get_submission(
    result_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    submission = ResultSubmission(result_id, approved=False)
    _drafts_result_submit[result_id] = submission
    submission.get_result()
    return {"results": yaml.dump(submission.result.results)}


@router.post("/result_submit_draft/submit/", response_class=JSONResponse)
def submit_result(
    result_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    submission = _drafts_result_submit[result_id]
    try:
        submission.approved = True
        updated_result_dict = submission.result.upload()
        # real result id is modified after submission, thus updating it
        submission.to_permanent_path(updated_result_dict)
        result = Result(**updated_result_dict)
        results[result_id] = result
        submission.write(updated_result_dict)
        return {"result_id": result_id}
    except Exception as e:
        return JSONResponse(
            {"error": f"Error moving to operational state: {str(e)}"}, 400
        )


@router.get("/result_submit_draft/decline", response_class=JSONResponse)
def decline_result_submit(
    result_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    del _drafts_result_submit[result_id]
    return {"result_id": result_id, "op_declined": True}
