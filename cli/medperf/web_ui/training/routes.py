import logging
import os
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

import medperf.config as config
from medperf.account_management import get_medperf_user_data
from medperf.commands.association.approval import Approval
from medperf.commands.training.submit import SubmitTrainingExp
from medperf.commands.training.set_plan import SetPlan
from medperf.commands.training.start_event import StartEvent
from medperf.commands.training.get_experiment_status import GetExperimentStatus
from medperf.commands.training.update_plan import UpdatePlan
from medperf.commands.training.close_event import CloseEvent
from medperf.commands.training.set_aggregator import SetAggregator
from medperf.entities.training_exp import TrainingExp
from medperf.entities.aggregator import Aggregator
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.enums import Status
from medperf.web_ui.common import (
    check_user_api,
    check_user_ui,
    UITask,
    sort_associations_display,
    templates,
)
from medperf.web_ui.listing import fetch_listing_page

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/register/ui", response_class=HTMLResponse)
def register_training_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    return templates.TemplateResponse(
        "training/register_training_experiment.html",
        {"request": request},
    )


@router.post("/register", response_class=JSONResponse)
def register_training(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    docs_url: str = Form(""),
    data_preparation_container: str = Form(...),
    fl_container: str = Form(...),
    fl_admin_container: Optional[str] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    training_id = None
    with UITask(
        request, "register_training_experiment", response={"entity_id": None}
    ) as task:
        training_exp_info = {
            "name": name,
            "description": description or "",
            "docs_url": (docs_url or "").strip(),
            "demo_dataset_tarball_url": "link",
            "demo_dataset_tarball_hash": "hash",
            "demo_dataset_generated_uid": "uid",
            "data_preparation_mlcube": int(data_preparation_container),
            "fl_mlcube": int(fl_container),
            "fl_admin_mlcube": int(fl_admin_container) if fl_admin_container else None,
            "state": "DEVELOPMENT",
        }
        training_id = SubmitTrainingExp.run(training_exp_info)
        task.response["entity_id"] = training_id
    task.notify(
        success_message="Training experiment successfully registered",
        failure_message="Failed to register training experiment",
        url=(
            f"/training/ui/display/{training_id}"
            if training_id
            else "/training/register/ui"
        ),
    )
    return task.response


@router.get("/ui", response_class=HTMLResponse)
def training_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    search: Optional[str] = None,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    experiments, search_query, pagination_context = fetch_listing_page(
        TrainingExp,
        page=page,
        page_size=page_size,
        ordering=ordering,
        mine_only=mine_only,
        my_user_id=my_user_id,
        search=search,
    )

    return templates.TemplateResponse(
        "training/training_experiments.html",
        {
            "request": request,
            "experiments": experiments,
            "mine_only": mine_only,
            "search_query": search_query,
            **pagination_context,
        },
    )


def _datasets_associations_context(training_id: int) -> dict:
    """Dataset associations of a training experiment (shown to its owner),
    sorted for display, with the associated datasets."""
    context = {
        "datasets_associations": [],
        "datasets": {},
        "dataset_assoc_pending": False,
    }
    try:
        associations = TrainingExp.get_datasets_associations(
            training_exp_uid=training_id
        )
        context["dataset_assoc_pending"] = any(
            assoc["approval_status"] == "PENDING" for assoc in associations
        )
        associations = sort_associations_display(associations)
        context["datasets_associations"] = associations
        context["datasets"] = {
            assoc["dataset"]: Dataset.get(assoc["dataset"])
            for assoc in associations
            if assoc["dataset"]
        }
    except Exception as e:
        logger.warning("Could not load training dataset associations: %s", e)
    return context


def _experiment_aggregator(training_id: int) -> Optional[Aggregator]:
    """The aggregator set for a training experiment (one per experiment), if any."""
    try:
        agg_meta = config.comms.get_experiment_aggregator(training_id)
        if agg_meta:
            return Aggregator(**agg_meta)
    except Exception:
        pass
    return None


def _has_active_event(training_id: int) -> bool:
    """Whether the training experiment has an active (not finished) event,
    which decides between showing the Start and the Close event actions."""
    try:
        event_meta = config.comms.get_experiment_event(training_id)
        return bool(event_meta) and not event_meta.get("finished", True)
    except Exception:
        return False


@router.get("/ui/display/{training_id}", response_class=HTMLResponse)
def training_detail_ui(
    request: Request,
    training_id: int,
    current_user: bool = Depends(check_user_ui),
):
    entity = TrainingExp.get(training_id)
    is_owner = entity.owner == get_medperf_user_data()["id"]

    context = {
        "request": request,
        "entity": entity,
        "prep_cube": Cube.get(cube_uid=entity.data_preparation_mlcube),
        "fl_cube": Cube.get(cube_uid=entity.fl_mlcube),
        "fl_admin_cube": (
            Cube.get(cube_uid=entity.fl_admin_mlcube)
            if entity.fl_admin_mlcube
            else None
        ),
        "datasets_associations": [],
        "datasets": {},
        "dataset_assoc_pending": False,
        "aggregator": _experiment_aggregator(training_id),
        "is_owner": is_owner,
        "has_active_event": _has_active_event(training_id),
        "plan_exists": bool(entity.plan),
    }
    if is_owner:
        context.update(_datasets_associations_context(training_id))

    return templates.TemplateResponse(
        "training/training_experiment_detail.html", context
    )


@router.post("/set_plan", response_class=JSONResponse)
def set_plan(
    request: Request,
    training_exp_id: int = Form(...),
    path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "set_training_plan") as task:
        SetPlan.run(training_exp_id, path)
    task.notify(
        success_message="Training plan set successfully",
        failure_message="Failed to set training plan",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/add_aggregator", response_class=JSONResponse)
def add_aggregator(
    request: Request,
    training_exp_id: int = Form(...),
    aggregator_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "set_training_aggregator") as task:
        SetAggregator.run(training_exp_id, aggregator_id)
    task.notify(
        success_message="Aggregator set successfully",
        failure_message="Failed to set aggregator",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/start_event", response_class=JSONResponse)
def start_event(
    request: Request,
    training_exp_id: int = Form(...),
    event_name: str = Form(...),
    participants_list_file: Optional[str] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "start_training_event") as task:
        StartEvent.run(
            training_exp_id, event_name, participants_list_file=participants_list_file
        )
    task.notify(
        success_message="Training event started successfully",
        failure_message="Failed to start training event",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/get_experiment_status", response_class=JSONResponse)
def get_experiment_status(
    request: Request,
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(
        request, "get_training_status", response={"status_content": None}
    ) as task:
        GetExperimentStatus.run(training_exp_id, silent=True)
        exp = TrainingExp.get(training_exp_id)
        if exp.status_path and os.path.exists(exp.status_path):
            with open(exp.status_path) as f:
                task.response["status_content"] = yaml.safe_load(f)
    task.notify(
        success_message="Experiment status retrieved",
        failure_message="Failed to get experiment status",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/update_plan", response_class=JSONResponse)
def update_plan(
    request: Request,
    training_exp_id: int = Form(...),
    field_name: str = Form(...),
    field_value: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "update_training_plan") as task:
        UpdatePlan.run(training_exp_id, field_name, field_value)
    task.notify(
        success_message="Plan updated successfully",
        failure_message="Failed to update plan",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/close_event", response_class=JSONResponse)
def close_event(
    request: Request,
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "close_training_event") as task:
        CloseEvent.run(training_exp_id)
    task.notify(
        success_message="Event closed successfully",
        failure_message="Failed to close event",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/approve", response_class=JSONResponse)
def approve_association(
    request: Request,
    training_exp_id: int = Form(...),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "approve_training_dataset_association") as task:
        Approval.run(
            training_exp_uid=training_exp_id,
            approval_status=Status.APPROVED,
            dataset_uid=dataset_id,
        )
    task.notify(
        success_message="Association approved",
        failure_message="Failed to approve association",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response


@router.post("/reject", response_class=JSONResponse)
def reject_association(
    request: Request,
    training_exp_id: int = Form(...),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "reject_training_dataset_association") as task:
        Approval.run(
            training_exp_uid=training_exp_id,
            approval_status=Status.REJECTED,
            dataset_uid=dataset_id,
        )
    task.notify(
        success_message="Association rejected",
        failure_message="Failed to reject association",
        url=f"/training/ui/display/{training_exp_id}",
    )
    return task.response
