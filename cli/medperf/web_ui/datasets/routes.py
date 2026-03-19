import os
import logging
import threading
from typing import List, Optional

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, APIRouter, Depends, Form

from medperf import config
from medperf.account_management import get_medperf_user_data, get_medperf_user_object
from medperf.commands.mlcube.utils import check_access_to_container
from medperf.commands.dataset.associate import AssociateDataset
from medperf.commands.dataset.export_dataset import ExportDataset
from medperf.commands.dataset.import_dataset import ImportDataset
from medperf.commands.dataset.prepare import DataPreparation
from medperf.commands.dataset.set_operational import DatasetSetOperational
from medperf.commands.dataset.submit import DataCreation
from medperf.commands.execution.create import BenchmarkExecution
from medperf.commands.execution.submit import ResultSubmission
from medperf.commands.execution.utils import filter_latest_executions
from medperf.commands.cc.dataset_configure_for_cc import DatasetConfigureForCC
from medperf.commands.cc.dataset_update_cc_policy import DatasetUpdateCCPolicy
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.entities.training_exp import TrainingExp
from medperf.commands.association.utils import get_user_associations
from medperf.commands.dataset.associate_training import AssociateTrainingDataset
from medperf.commands.dataset.train import TrainingExecution
from medperf.web_ui.common import (
    templates,
    check_user_ui,
    check_user_api,
    initialize_state_task,
    reset_state_task,
)
from medperf.web_ui.utils import get_container_type

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
def datasets_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(check_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id
    datasets = Dataset.all(filters=filters)

    datasets = sorted(datasets, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    mine_datasets = [d for d in datasets if d.owner == my_user_id]
    other_datasets = [d for d in datasets if d.owner != my_user_id]
    datasets = mine_datasets + other_datasets
    return templates.TemplateResponse(
        "dataset/datasets.html",
        {
            "request": request,
            "datasets": datasets,
            "mine_only": mine_only,
        },
    )


@router.get("/ui/display/{dataset_id}", response_class=HTMLResponse)
def dataset_detail_ui(  # noqa
    request: Request,
    dataset_id: int,
    current_user: bool = Depends(check_user_ui),
):
    user_obj = get_medperf_user_object()

    dataset = Dataset.get(dataset_id)
    dataset.read_report()
    dataset.read_statistics()
    prep_cube = Cube.get(cube_uid=dataset.data_preparation_mlcube)

    my_user_id = user_obj.id
    is_owner = my_user_id == dataset.owner
    dataset_is_operational = dataset.is_operational()
    dataset_is_prepared = dataset.is_ready() or dataset_is_operational
    report_exists = os.path.exists(dataset.report_path)
    ui_mode = request.app.state.ui_mode

    cc_config_defaults = dataset.get_cc_config()
    cc_configured = dataset.is_cc_configured()
    cc_initialized = dataset.is_cc_initialized()
    cc_last_synced = dataset.get_last_synced()
    context = {
        "request": request,
        "dataset": dataset,
        "prep_cube": prep_cube,
        "dataset_is_prepared": dataset_is_prepared,
        "dataset_is_operational": dataset_is_operational,
        "is_owner": is_owner,
        "report_exists": report_exists,
        "cc_config_defaults": cc_config_defaults,
        "cc_configured": cc_configured,
        "cc_initialized": cc_initialized,
        "cc_last_synced": cc_last_synced,
    }

    if ui_mode == request.app.state.EVALUATION_MODE:
        benchmark_assocs = Dataset.get_benchmarks_associations(dataset_uid=dataset_id)
        benchmark_associations = {}
        for assoc in benchmark_assocs:
            benchmark_associations[assoc["benchmark"]] = assoc
        # benchmark_associations = sort_associations_display(benchmark_associations)

        # Get all relevant benchmarks for making an association
        benchmarks = Benchmark.all()
        valid_benchmarks = {
            b.id: b
            for b in benchmarks
            if b.data_preparation_mlcube == dataset.data_preparation_mlcube
        }
        for benchmark in valid_benchmarks:
            ref_model_id = valid_benchmarks[benchmark].reference_model
            valid_benchmarks[benchmark].reference_model = Model.get(ref_model_id)

        approved_benchmarks = [
            i
            for i in benchmark_associations
            if benchmark_associations[i]["approval_status"] == "APPROVED"
        ]
        # Get all results
        results = []
        if benchmark_assocs:
            user_id = user_obj.id
            results = Execution.all(filters={"owner": user_id})
            results = filter_latest_executions(results)

        # Fetch models associated with each benchmark
        benchmark_models = {}
        for assoc in benchmark_assocs:
            if assoc["approval_status"] != "APPROVED":
                continue  # if association is not approved we cannot list its models
            models_uids = Benchmark.get_models_uids(benchmark_uid=assoc["benchmark"])
            models = [Model.get(model_uid) for model_uid in models_uids]
            benchmark_models[assoc["benchmark"]] = models
            for model in models + [
                valid_benchmarks[assoc["benchmark"]].reference_model
            ]:
                model._encrypted = model.is_encrypted()
                model._requires_cc = model.requires_cc()
                if model._encrypted:
                    model.access_status = check_access_to_container(model.container.id)
                if model._requires_cc:
                    if not dataset.is_cc_initialized():
                        reason = "Your dataset is not configured for CC yet"
                        can_run = False
                    elif not model.is_cc_initialized():
                        reason = "Wait for model owner to configure their CC settings"
                        can_run = False
                    elif not user_obj.is_cc_initialized():
                        reason = "You haven't configured your workload run settings for CC yet"
                        can_run = False
                    else:
                        reason = ""
                        can_run = True
                    model.cc_run_status = {"can_run": can_run, "reason": reason}
                model.result = None
                for result in results:
                    if (
                        result.benchmark == assoc["benchmark"]
                        and result.dataset == dataset_id
                        and result.model == model.id
                    ):
                        model.result = result.todict()
                        model.result["results_exist"] = (
                            result.is_executed() or result.finalized
                        )
                        if model.result["results_exist"]:
                            model.result["results"] = result.read_results()

        context.update(
            {
                "benchmark_associations": benchmark_associations,
                "benchmarks": valid_benchmarks,
                "benchmark_models": benchmark_models,
                "approved_benchmarks": approved_benchmarks,
            }
        )

    else:
        training_associations = {}
        available_training_experiments = []
        try:
            user_training_assocs = get_user_associations(
                experiment_type="training_exp", component_type="dataset"
            )
            for a in user_training_assocs:
                if a.get("dataset") == dataset_id:
                    training_associations[a["training_exp"]] = a
            all_training = TrainingExp.all()
            available_training_experiments = [
                t
                for t in all_training
                if t.data_preparation_mlcube == dataset.data_preparation_mlcube
            ]
        except Exception as e:
            logger.warning("Could not load training associations: %s", e)

        experiments_by_id = {e.id: e for e in available_training_experiments}
        for exp_id in training_associations:
            if exp_id not in experiments_by_id:
                try:
                    experiments_by_id[exp_id] = TrainingExp.get(exp_id)
                except Exception:
                    pass
        context.update(
            {
                "training_associations": training_associations,
                "available_training_experiments": available_training_experiments,
                "experiments_by_id": experiments_by_id,
            }
        )

    return templates.TemplateResponse("dataset/dataset_detail.html", context)


@router.get("/register/ui", response_class=HTMLResponse)
def create_dataset_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    ui_mode = request.app.state.ui_mode
    context = {"request": request}

    if ui_mode == request.app.state.EVALUATION_MODE:
        benchmarks = Benchmark.all()
        context["benchmarks"] = benchmarks
    else:
        my_containers = Cube.all()
        containers = []
        for container in my_containers:
            container_obj = {
                "id": container.id,
                "name": container.name,
                "type": get_container_type(container),
            }
            containers.append(container_obj)
        data_prep_containers = [
            c for c in containers if c["type"] == "data-prep-container"
        ]
        context["data_prep_containers"] = data_prep_containers

    return templates.TemplateResponse("dataset/register_dataset.html", context)


@router.post("/register/", response_class=JSONResponse)
def register_dataset(
    request: Request,
    submit_as_prepared: bool = Form(False),
    benchmark: Optional[int] = Form(None),
    prep_cube_uid: Optional[int] = Form(None),
    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    data_path: str = Form(...),
    labels_path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="register_dataset")
    return_response = {"status": "", "entity_id": None, "error": ""}
    dataset_id = None
    try:
        dataset_id = DataCreation.run(
            benchmark_uid=benchmark,
            prep_cube_uid=prep_cube_uid,
            data_path=data_path,
            labels_path=labels_path,
            metadata_path=None,
            name=name,
            description=description,
            location=location,
            approved=False,
            submit_as_prepared=bool(submit_as_prepared),
        )
        return_response["status"] = "success"
        return_response["entity_id"] = dataset_id
        notification_message = "Dataset successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register dataset"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=(
            f"/datasets/ui/display/{dataset_id}"
            if dataset_id
            else "/datasets/register/ui"
        ),
    )
    return return_response


@router.post("/prepare", response_class=JSONResponse)
def prepare(
    request: Request,
    dataset_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="prepare")
    return_response = {"status": "", "dataset_id": None, "error": ""}

    try:
        dataset_id = DataPreparation.run(dataset_id)
        return_response["status"] = "success"
        return_response["dataset_id"] = dataset_id
        notification_message = "Dataset successfully prepared"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to prepare dataset"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{dataset_id}",
    )
    return return_response


@router.post("/set_operational", response_class=JSONResponse)
def set_operational(
    request: Request,
    dataset_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="dataset_set_operational")
    return_response = {"status": "", "dataset_id": None, "error": ""}

    try:
        dataset_id = DatasetSetOperational.run(dataset_id)
        return_response["status"] = "success"
        return_response["dataset_id"] = dataset_id
        notification_message = "Dataset successfully set to operational"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to set dataset to operational"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{dataset_id}",
    )
    return return_response


@router.post("/associate", response_class=JSONResponse)
def associate(
    request: Request,
    dataset_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="dataset_association")
    return_response = {"status": "", "error": ""}

    try:
        AssociateDataset.run(data_uid=dataset_id, benchmark_uid=benchmark_id)
        return_response["status"] = "success"
        notification_message = "Successfully requested dataset association"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to request dataset association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{dataset_id}",
    )
    return return_response


@router.post("/associate_training", response_class=JSONResponse)
def associate_training(
    request: Request,
    dataset_id: int = Form(...),
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="dataset_training_association")
    return_response = {"status": "", "error": ""}
    try:
        AssociateTrainingDataset.run(
            data_uid=dataset_id,
            training_exp_uid=training_exp_id,
            approved=True,
        )
        return_response["status"] = "success"
        notification_message = (
            "Successfully requested dataset association with training experiment"
        )
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to request association with training experiment"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{dataset_id}",
    )
    return return_response


def _run_training_worker(
    request: Request, training_exp_id: int, dataset_id: int, task_id: str
):
    redirect_url = f"/datasets/ui/display/{dataset_id}"
    return_response = {"status": "", "error": ""}
    notification_message = "Training successfully finished"
    config.ui.set_task_id(task_id)
    try:
        TrainingExecution.run(training_exp_id=training_exp_id, data_uid=dataset_id)
        return_response["status"] = "success"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "An error occurred during training execution"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request, task_id)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=redirect_url,
    )


@router.post("/start_training", response_class=JSONResponse)
def start_training(
    request: Request,
    dataset_id: int = Form(...),
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    task_id = initialize_state_task(request, task_name="start_training")

    threading.Thread(
        target=_run_training_worker,
        args=(request, training_exp_id, dataset_id, task_id),
        daemon=True,
    ).start()

    return {"status": "started", "error": ""}


@router.post("/run", response_class=JSONResponse)
def run(
    request: Request,
    dataset_id: int = Form(...),
    benchmark_id: int = Form(...),
    model_ids: List[int] = Form(...),
    run_all: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="run_benchmark")
    return_response = {"status": "", "error": ""}

    try:
        BenchmarkExecution.run(
            benchmark_id,
            dataset_id,
            model_ids,
            no_cache=not run_all,
            rerun_finalized_executions=not run_all,
        )
        return_response["status"] = "success"
        notification_message = "Execution ran successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Error during execution"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{dataset_id}",
    )
    return return_response


@router.post("/submit_result", response_class=JSONResponse)
def submit_result(
    request: Request,
    result_id: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="submit_result")
    return_response = {"status": "", "error": ""}

    try:
        ResultSubmission.run(result_id)
        return_response["status"] = "success"
        notification_message = "Result successfully submitted"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to submit results"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
    )
    return return_response


@router.post("/export/ui", response_class=HTMLResponse)
def export_dataset_ui(
    request: Request,
    submit: str = Form(...),
    dataset_id: int = Form(...),
    current_user: bool = Depends(check_user_ui),
):
    dataset = Dataset.get(dataset_id)
    dataset.read_report()
    dataset.read_statistics()
    prep_cube = Cube.get(cube_uid=dataset.data_preparation_mlcube)
    dataset_is_operational = dataset.state == "OPERATION"
    dataset_is_prepared = dataset.is_ready() or dataset_is_operational
    report_exists = os.path.exists(dataset.report_path)

    return templates.TemplateResponse(
        "dataset/export_dataset.html",
        {
            "request": request,
            "dataset": dataset,
            "prep_cube": prep_cube,
            "dataset_is_prepared": dataset_is_prepared,
            "dataset_is_operational": dataset_is_operational,
            "report_exists": report_exists,
        },
    )


@router.post("/export", response_class=JSONResponse)
def export_dataset(
    request: Request,
    dataset_id: int = Form(...),
    output_path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):

    initialize_state_task(request, task_name="export_dataset")
    return_response = {"status": "", "error": "", "dataset_id": dataset_id}

    try:
        ExportDataset.run(dataset_id, output_path)
        return_response["status"] = "success"
        notification_message = "Dataset successfully exported"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to export dataset"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
    )

    return return_response


@router.get("/import/ui", response_class=HTMLResponse)
def import_dataset_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):

    return templates.TemplateResponse(
        "dataset/import_dataset.html",
        {"request": request},
    )


@router.post("/import", response_class=JSONResponse)
def import_dataset(
    request: Request,
    dataset_id: int = Form(...),
    input_path: str = Form(...),
    raw_dataset_path: str = Form(None),
    current_user: bool = Depends(check_user_api),
):

    initialize_state_task(request, task_name="import_dataset")
    return_response = {"status": "", "error": "", "dataset_id": dataset_id}

    try:
        ImportDataset.run(dataset_id, input_path, raw_dataset_path)
        return_response["status"] = "success"
        notification_message = "Dataset successfully imported"
    except Exception as exp:
        dataset_id = None
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to import dataset"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{dataset_id}" if dataset_id else "",
    )

    return return_response


@router.post("/edit_cc_config", response_class=JSONResponse)
def edit_cc_config(
    request: Request,
    entity_id: int = Form(...),
    configure_cc: bool = Form(False),
    project_id: str = Form(""),
    project_number: str = Form(""),
    bucket: str = Form(""),
    keyring_name: str = Form(""),
    key_name: str = Form(""),
    key_location: str = Form(""),
    wip: str = Form(""),
    wip_provider: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    args = {
        "project_id": project_id,
        "project_number": project_number,
        "bucket": bucket,
        "keyring_name": keyring_name,
        "key_name": key_name,
        "key_location": key_location,
        "wip": wip,
        "wip_provider": wip_provider,
    }
    if not configure_cc:
        args = {}
    initialize_state_task(request, task_name="data_update_cc_config")
    return_response = {"status": "", "error": ""}
    try:
        DatasetConfigureForCC.run(entity_id, args, {})
        return_response["status"] = "success"
        notification_message = "Successfully updated dataset CC config!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to update dataset CC config"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/datasets/ui/display/{entity_id}",
    )
    return return_response


@router.post("/sync_cc_policy", response_class=JSONResponse)
def sync_cc_policy(
    entity_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    try:
        DatasetUpdateCCPolicy.run(entity_id)
        return {"status": "success", "error": ""}
    except Exception as exp:
        logger.exception(exp)
        return {"status": "failed", "error": str(exp)}
