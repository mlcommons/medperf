import yaml
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from medperf import config
from medperf.commands.dataset.set_operational import DatasetSetOperational
from medperf.web_ui.common import get_current_user_api

_drafts_operational: dict[int, DatasetSetOperational] = {}

router = APIRouter()


@router.post("/operational_draft/generate", response_class=JSONResponse)
def set_operational(
    dataset_id: int,
    current_user: bool = Depends(get_current_user_api),
):
    preparation = DatasetSetOperational(dataset_id, approved=False)
    _drafts_operational[dataset_id] = preparation
    preparation.validate()
    preparation.generate_uids()
    preparation.set_statistics()
    preparation.set_operational()
    body = preparation.todict()
    statistics = {k: v for (k, v) in body.items() if v is not None}
    return {"yaml_statistics": yaml.dump(statistics)}


@router.post("/operational_draft/submit", response_class=JSONResponse)
def submit_operational(
    dataset_id: int,
    current_user: bool = Depends(get_current_user_api),
):
    preparation = _drafts_operational[dataset_id]
    try:
        preparation.approved = True
        body = preparation.todict()
        config.comms.update_dataset(preparation.dataset.id, body)
        preparation.write()
        return {"dataset_id": dataset_id}
    except Exception as e:
        return JSONResponse(
            {"error": f"Error moving to operational state: {str(e)}"}, 400
        )


@router.get("/operational_draft/decline", response_class=JSONResponse)
def decline_operational(
    dataset_id: int,
    current_user: bool = Depends(get_current_user_api),
):
    del _drafts_operational[dataset_id]
    return {"dataset_id": dataset_id, "op_declined": True}
