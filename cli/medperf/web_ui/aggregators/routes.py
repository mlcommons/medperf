import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

import medperf.config as config
from medperf.account_management import get_medperf_user_data
from medperf.commands.aggregator.submit import SubmitAggregator
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.commands.aggregator.run import StartAggregator
from medperf.entities.aggregator import Aggregator
from medperf.entities.ca import CA
from medperf.utils import get_pki_assets_path
from medperf.web_ui.common import (
    check_user_api,
    check_user_ui,
    UITask,
    templates,
)
from medperf.enums import CryptoKeyType
from medperf.web_ui.listing import fetch_listing_page

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/register/ui", response_class=HTMLResponse)
def register_aggregator_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    return templates.TemplateResponse(
        "aggregators/register_aggregator.html",
        {"request": request},
    )


@router.post("/register", response_class=JSONResponse)
def register_aggregator(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    port: int = Form(...),
    admin_port: int = Form(...),
    aggregation_mlcube: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    aggregator_id = None
    with UITask(request, "register_aggregator", response={"entity_id": None}) as task:
        aggregator_id = SubmitAggregator.run(
            name=name,
            address=address.strip(),
            port=port,
            admin_port=admin_port,
            aggregation_mlcube=aggregation_mlcube,
        )
        task.response["entity_id"] = aggregator_id
    task.notify(
        success_message="Aggregator successfully registered",
        failure_message="Failed to register aggregator",
        url=(
            f"/aggregators/ui/display/{aggregator_id}"
            if aggregator_id
            else "/aggregators/register/ui"
        ),
    )
    return task.response


@router.get("/ui", response_class=HTMLResponse)
def aggregators_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    search: Optional[str] = None,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    aggregators, search_query, pagination_context = fetch_listing_page(
        Aggregator,
        page=page,
        page_size=page_size,
        ordering=ordering,
        mine_only=mine_only,
        my_user_id=my_user_id,
        search=search,
    )

    return templates.TemplateResponse(
        "aggregators/aggregators.html",
        {
            "request": request,
            "aggregators": aggregators,
            "mine_only": mine_only,
            "search_query": search_query,
            **pagination_context,
        },
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
                output_path = get_pki_assets_path(address, ca.id, CryptoKeyType.RSA)
                certificate_exists = os.path.exists(output_path)
            except Exception as exp:
                logger.warning(
                    f"Failed to check server certificate for aggregator {aggregator_id}: {exp}"
                )

        experiments_using_aggregator = entity.get_training_experiments()

    training_allowed_ids = ",".join(str(exp.id) for exp in experiments_using_aggregator)

    return templates.TemplateResponse(
        "aggregators/aggregator_detail.html",
        {
            "request": request,
            "entity": entity,
            "experiments_using_aggregator": experiments_using_aggregator,
            "training_allowed_ids": training_allowed_ids,
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
    with UITask(request, "aggregator_get_server_cert") as task:
        GetServerCertificate.run(aggregator_id=aggregator_id)
    task.notify(
        success_message="Server certificate retrieved successfully",
        failure_message="Failed to get server certificate",
        url=f"/aggregators/ui/display/{aggregator_id}",
    )
    return task.response


@router.post("/run", response_class=JSONResponse)
def run_aggregator(
    request: Request,
    aggregator_id: int = Form(...),
    training_exp_id: int = Form(...),
    publish_on: str = Form("127.0.0.1"),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "start_aggregator") as task:
        StartAggregator.run(training_exp_id=training_exp_id, publish_on=publish_on)
    task.notify(
        success_message="Aggregator run started successfully",
        failure_message="An error occurred while running the aggregator",
        url=f"/aggregators/ui/display/{aggregator_id}",
    )
    return task.response
