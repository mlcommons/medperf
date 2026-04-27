import logging
import os
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

import medperf.config as config
from medperf.account_management import get_medperf_user_data
from medperf.commands.association.approval import Approval
from medperf.commands.association.utils import get_experiment_associations
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
    initialize_state_task,
    reset_state_task,
    sort_associations_display,
    templates,
)
from medperf.web_ui.utils import (
    get_container_type,
    build_listing_filters,
    build_pagination_context,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/register/ui", response_class=HTMLResponse)
def register_training_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    filters = {"owner": my_user_id}
    my_containers = Cube.all(filters=filters)
    containers = []
    for container in my_containers:
        container_obj = {
            "id": container.id,
            "name": container.name,
            "type": get_container_type(container),
        }
        containers.append(container_obj)
    data_prep_containers = [c for c in containers if c["type"] == "data-prep-container"]
    all_containers = [c for c in containers if c not in data_prep_containers]
    return templates.TemplateResponse(
        "training/register_training_experiment.html",
        {
            "request": request,
            "data_prep_containers": data_prep_containers,
            "all_containers": all_containers,
        },
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
    operational: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="register_training_experiment")
    return_response = {"status": "", "error": "", "entity_id": None}
    training_id = None
    try:
        training_exp_info = {
            "name": name,
            "description": description or "",
            "docs_url": (docs_url or "").strip() or None,
            "demo_dataset_tarball_url": "link",
            "demo_dataset_tarball_hash": "hash",
            "demo_dataset_generated_uid": "uid",
            "data_preparation_mlcube": int(data_preparation_container),
            "fl_mlcube": int(fl_container),
            "fl_admin_mlcube": int(fl_admin_container) if fl_admin_container else None,
            "state": (
                "OPERATION"
                if (operational and operational.lower() == "true")
                else "DEVELOPMENT"
            ),
        }
        training_id = SubmitTrainingExp.run(training_exp_info)
        return_response["status"] = "success"
        return_response["entity_id"] = training_id
        notification_message = "Training experiment successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register training experiment"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=(
            f"/training/ui/display/{training_id}"
            if training_id
            else "/training/register/ui"
        ),
    )
    return return_response


@router.get("/ui", response_class=HTMLResponse)
def training_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    current_user: bool = Depends(check_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]

    if mine_only:
        filters["owner"] = my_user_id

    total_count = TrainingExp.get_count(filters=filters)

    filters.update(
        build_listing_filters(page=page, page_size=page_size, ordering=ordering)
    )

    experiments = TrainingExp.all(filters=filters)

    pagination_context = build_pagination_context(
        page=page,
        page_size=page_size,
        ordering=ordering,
        total_count=total_count,
        page_items_count=len(experiments),
    )

    return templates.TemplateResponse(
        "training/training_experiments.html",
        {
            "request": request,
            "experiments": experiments,
            "mine_only": mine_only,
            **pagination_context,
        },
    )


@router.get("/ui/display/{training_id}", response_class=HTMLResponse)
def training_detail_ui(  # noqa
    request: Request,
    training_id: int,
    current_user: bool = Depends(check_user_ui),
):
    entity = TrainingExp.get(training_id)
    my_user_id = get_medperf_user_data()["id"]
    is_owner = entity.owner == my_user_id

    # Containers
    prep_cube = Cube.get(cube_uid=entity.data_preparation_mlcube)
    fl_cube = Cube.get(cube_uid=entity.fl_mlcube)
    fl_admin_cube = (
        Cube.get(cube_uid=entity.fl_admin_mlcube) if entity.fl_admin_mlcube else None
    )

    # Dataset associations (for owner: show pending and approved)
    dataset_associations = []
    datasets = {}
    dataset_assoc_pending = False
    try:
        dataset_associations = get_experiment_associations(
            experiment_id=training_id,
            experiment_type="training_exp",
            component_type="dataset",
        )
        dataset_associations = sort_associations_display(dataset_associations)
        dataset_assoc_pending = any(
            a.get("approval_status") == "PENDING" for a in dataset_associations
        )
        for a in dataset_associations:
            if a.get("dataset"):
                try:
                    datasets[a["dataset"]] = Dataset.get(a["dataset"])
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Could not load training dataset associations: %s", e)

    # Aggregator (one per experiment, from server)
    aggregator = None
    try:
        agg_meta = config.comms.get_experiment_aggregator(training_id)
        if agg_meta:
            aggregator = Aggregator(**agg_meta)
    except Exception:
        pass

    # Current event: show Start vs Close based on whether there's an active (non-finished) event
    has_active_event = False
    try:
        event_meta = config.comms.get_experiment_event(training_id)
        if event_meta and not event_meta.get("finished", True):
            has_active_event = True
    except Exception:
        pass

    # For owner: list of aggregators to choose from when adding aggregator
    available_aggregators = []
    if is_owner:
        try:
            available_aggregators = Aggregator.all()
            available_aggregators = sorted(
                available_aggregators,
                key=lambda a: (a.owner != my_user_id, a.name or ""),
            )
        except Exception:
            pass

    plan_exists = bool(entity.plan)

    return templates.TemplateResponse(
        "training/training_experiment_detail.html",
        {
            "request": request,
            "entity": entity,
            "prep_cube": prep_cube,
            "fl_cube": fl_cube,
            "fl_admin_cube": fl_admin_cube,
            "dataset_associations": dataset_associations,
            "datasets": datasets,
            "dataset_assoc_pending": dataset_assoc_pending,
            "aggregator": aggregator,
            "is_owner": is_owner,
            "has_active_event": has_active_event,
            "available_aggregators": available_aggregators,
            "plan_exists": plan_exists,
        },
    )


@router.post("/set_plan", response_class=JSONResponse)
def set_plan(
    request: Request,
    training_exp_id: int = Form(...),
    path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="set_training_plan")
    return_response = {"status": "", "error": ""}
    try:
        SetPlan.run(training_exp_id, path)
        return_response["status"] = "success"
        notification_message = "Training plan set successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to set training plan"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/training/ui/display/{training_exp_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.post("/add_aggregator", response_class=JSONResponse)
def add_aggregator(
    request: Request,
    training_exp_id: int = Form(...),
    aggregator_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="set_training_aggregator")
    return_response = {"status": "", "error": ""}
    try:
        SetAggregator.run(training_exp_id, aggregator_id)
        return_response["status"] = "success"
        notification_message = "Aggregator set successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to set aggregator"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/training/ui/display/{training_exp_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.post("/start_event", response_class=JSONResponse)
def start_event(
    request: Request,
    training_exp_id: int = Form(...),
    event_name: str = Form(...),
    participants_list_file: Optional[str] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="start_training_event")
    return_response = {"status": "", "error": ""}
    try:
        StartEvent.run(
            training_exp_id, event_name, participants_list_file=participants_list_file
        )
        return_response["status"] = "success"
        notification_message = "Training event started successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to start training event"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/training/ui/display/{training_exp_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.post("/get_experiment_status", response_class=JSONResponse)
def get_experiment_status(
    request: Request,
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="get_training_status")
    return_response = {"status": "", "error": "", "status_content": None}
    try:
        GetExperimentStatus.run(training_exp_id, silent=True)
        exp = TrainingExp.get(training_exp_id)
        if exp.status_path and os.path.exists(exp.status_path):
            with open(exp.status_path) as f:
                return_response["status_content"] = yaml.safe_load(f)
        return_response["status"] = "success"
        notification_message = "Experiment status retrieved"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to get experiment status"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/training/ui/display/{training_exp_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.post("/update_plan", response_class=JSONResponse)
def update_plan(
    request: Request,
    training_exp_id: int = Form(...),
    field_name: str = Form(...),
    field_value: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="update_training_plan")
    return_response = {"status": "", "error": ""}
    try:
        UpdatePlan.run(training_exp_id, field_name, field_value)
        return_response["status"] = "success"
        notification_message = "Plan updated successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to update plan"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/training/ui/display/{training_exp_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.post("/close_event", response_class=JSONResponse)
def close_event(
    request: Request,
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="close_training_event")
    return_response = {"status": "", "error": ""}
    try:
        CloseEvent.run(training_exp_id)
        return_response["status"] = "success"
        notification_message = "Event closed successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to close event"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/training/ui/display/{training_exp_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.post("/approve", response_class=JSONResponse)
def approve_association(
    request: Request,
    training_exp_id: int = Form(...),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="approve_training_dataset_association")
    return_response = {"status": "", "error": ""}
    try:
        Approval.run(
            training_exp_uid=training_exp_id,
            approval_status=Status.APPROVED,
            dataset_uid=dataset_id,
        )
        return_response["status"] = "success"
        notification_message = "Association approved"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to approve association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/training/ui/display/{training_exp_id}",
    )
    return return_response


@router.post("/reject", response_class=JSONResponse)
def reject_association(
    request: Request,
    training_exp_id: int = Form(...),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="reject_training_dataset_association")
    return_response = {"status": "", "error": ""}
    try:
        Approval.run(
            training_exp_uid=training_exp_id,
            approval_status=Status.REJECTED,
            dataset_uid=dataset_id,
        )
        return_response["status"] = "success"
        notification_message = "Association rejected"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to reject association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/training/ui/display/{training_exp_id}",
    )
    return return_response
