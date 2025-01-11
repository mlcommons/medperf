from medperf.exceptions import CleanExit
from fastapi import APIRouter, Depends, Form
from starlette.responses import JSONResponse

from medperf import config
from medperf.web_ui.common import get_current_user_api
from medperf.commands.dataset.associate import AssociateDataset


router = APIRouter()


@router.post("/associate/", response_class=JSONResponse)
def associate_generate(
    dataset_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        AssociateDataset.run(data_uid=dataset_id, benchmark_uid=benchmark_id)
        config.ui.set_success()
    except CleanExit:
        config.ui.set_error()
