import logging
import os
import threading

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

import medperf.config as config
from medperf.account_management import get_medperf_user_data
from medperf.commands.aggregator.submit import SubmitAggregator
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.commands.aggregator.run import StartAggregator
from medperf.entities.aggregator import Aggregator
from medperf.entities.ca import CA
from medperf.entities.cube import Cube
from medperf.utils import get_pki_assets_path
from medperf.web_ui.common import (
    check_user_api,
    check_user_ui,
    initialize_state_task,
    reset_state_task,
    templates,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/register/ui", response_class=HTMLResponse)
def register_aggregator_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    containers = Cube.all()
    containers = [{"id": c.id, "name": c.name} for c in containers]
    return templates.TemplateResponse(
        "aggregators/register_aggregator.html",
        {"request": request, "containers": containers},
    )


@router.post("/register", response_class=JSONResponse)
def register_aggregator(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    port: int = Form(...),
    aggregation_mlcube: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="register_aggregator")
    return_response = {"status": "", "error": "", "entity_id": None}
    aggregator_id = None
    try:
        aggregator_id = SubmitAggregator.run(
            name=name,
            address=address.strip(),
            port=port,
            aggregation_mlcube=aggregation_mlcube,
        )
        return_response["status"] = "success"
        return_response["entity_id"] = aggregator_id
        notification_message = "Aggregator successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register aggregator"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = (
        f"/aggregators/ui/display/{aggregator_id}"
        if aggregator_id
        else "/aggregators/register/ui"
    )
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


@router.get("/ui", response_class=HTMLResponse)
def aggregators_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(check_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    aggregators = Aggregator.all(filters=filters)
    aggregators = sorted(aggregators, key=lambda x: x.created_at or "", reverse=True)
    mine_aggs = [a for a in aggregators if a.owner == my_user_id]
    other_aggs = [a for a in aggregators if a.owner != my_user_id]
    aggregators = mine_aggs + other_aggs

    return templates.TemplateResponse(
        "aggregators/aggregators.html",
        {"request": request, "aggregators": aggregators, "mine_only": mine_only},
    )


@router.get("/ui/display/{aggregator_id}", response_class=HTMLResponse)
def aggregator_detail_ui(
    request: Request,
    aggregator_id: int,
    current_user: bool = Depends(check_user_ui),
):
    certificate_exists = False
    experiments_using_aggregator = []

    my_user_id = get_medperf_user_data()["id"]
    entity = Aggregator.get(aggregator_id)
    owner = entity.owner == my_user_id

    if owner:
        ca_id = config.certificate_authority_id
        if ca_id:
            try:
                ca = CA.get(ca_id)
                aggregator = Aggregator.get(aggregator_id)
                address = aggregator.address
                output_path = get_pki_assets_path(address, ca.id)
                certificate_exists = os.path.exists(output_path)
            except Exception as exp:
                logger.warning(
                    f"Failed to check server certificate for aggregator {aggregator_id}: {exp}"
                )

        experiments_using_aggregator = entity.get_training_experiments()

    return templates.TemplateResponse(
        "aggregators/aggregator_detail.html",
        {
            "request": request,
            "entity": entity,
            "experiments_using_aggregator": experiments_using_aggregator,
            "owner": owner,
            "certificate_exists": certificate_exists,
        },
    )


@router.post("/get_server_certificate", response_class=JSONResponse)
def get_server_certificate(
    request: Request,
    aggregator_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="aggregator_get_server_cert")
    return_response = {"status": "", "error": ""}
    try:
        GetServerCertificate.run(aggregator_id=aggregator_id)
        return_response["status"] = "success"
        notification_message = "Server certificate retrieved successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to get server certificate"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    redirect_url = f"/aggregators/ui/display/{aggregator_id}"
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )
    return return_response


def _run_aggregator_worker(
    request: Request,
    training_exp_id: int,
    aggregator_id: int,
    publish_on: str,
    task_id: str,
):
    redirect_url = f"/aggregators/ui/display/{aggregator_id}"
    return_response = {"status": "", "error": ""}
    notification_message = "Aggregator run started successfully"
    config.ui.set_task_id(task_id)
    try:
        StartAggregator.run(training_exp_id=training_exp_id, publish_on=publish_on)
        return_response["status"] = "success"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "An error occurred while running the aggregator"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request, task_id)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )


@router.post("/run", response_class=JSONResponse)
def run_aggregator(
    request: Request,
    aggregator_id: int = Form(...),
    training_exp_id: int = Form(...),
    publish_on: str = Form("127.0.0.1"),
    current_user: bool = Depends(check_user_api),
):
    agg_meta = config.comms.get_experiment_aggregator(training_exp_id)
    if not agg_meta or agg_meta.get("id") != aggregator_id:
        raise ValueError("Selected training experiment does not use this aggregator")

    task_id = initialize_state_task(request, task_name="start_aggregator")

    threading.Thread(
        target=_run_aggregator_worker,
        args=(request, training_exp_id, aggregator_id, publish_on, task_id),
        daemon=True,
    ).start()

    return {"status": "started", "error": ""}
