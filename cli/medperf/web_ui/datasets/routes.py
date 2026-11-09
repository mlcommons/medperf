import os
import logging
from typing import List, Optional

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, APIRouter, Depends, Form

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
    UITask,
    templates,
    check_user_ui,
    check_user_api,
)
from medperf.web_ui.listing import fetch_listing_page

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
def datasets_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    search: Optional[str] = None,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    datasets, search_query, pagination_context = fetch_listing_page(
        Dataset,
        page=page,
        page_size=page_size,
        ordering=ordering,
        mine_only=mine_only,
        my_user_id=my_user_id,
        search=search,
    )

    return templates.TemplateResponse(
        "dataset/datasets.html",
        {
            "request": request,
            "datasets": datasets,
            "mine_only": mine_only,
            "search_query": search_query,
            **pagination_context,
        },
    )


def _dataset_page_context(dataset: Dataset) -> dict:
    """Context shared by the dataset pages (details, export): the dataset with
    its report/statistics loaded, its preparation container and its state."""
    dataset.read_report()
    dataset.read_statistics()
    dataset_is_operational = dataset.is_operational()
    return {
        "dataset": dataset,
        "prep_cube": Cube.get(cube_uid=dataset.data_preparation_mlcube),
        "dataset_is_prepared": dataset.is_ready() or dataset_is_operational,
        "dataset_is_operational": dataset_is_operational,
        "report_exists": os.path.exists(dataset.report_path),
    }


def _cc_run_status(model: Model, dataset: Dataset, user_obj) -> dict:
    """Whether a model requiring confidential computing can run on the dataset, and why not."""
    if not dataset.is_cc_initialized():
        reason = "Your dataset is not configured for CC yet"
    elif not model.is_cc_initialized():
        reason = "Wait for model owner to configure their CC settings"
    elif not user_obj.is_cc_initialized():
        reason = "You haven't configured your workload run settings for CC yet"
    else:
        reason = ""
    return {"can_run": not reason, "reason": reason}


def _attach_latest_result(
    model: Model, results: List[Execution], benchmark_id: int, dataset_id: int
):
    """Set `model.result` to the latest result of the model on the dataset in the benchmark."""
    model.result = None
    for result in results:
        if (
            result.benchmark == benchmark_id
            and result.dataset == dataset_id
            and result.model == model.id
        ):
            model.result = result.todict()
            model.result["results_exist"] = result.is_executed() or result.finalized
            if model.result["results_exist"]:
                model.result["results"] = result.read_results()


def _benchmark_models(
    benchmark_id: int, reference_model_id: int, dataset: Dataset, user_obj, results
) -> List[Model]:
    """Return the models of a benchmark the dataset can be run with, annotated
    for display (encryption/access, confidential computing status, latest result)."""
    models_uids = Benchmark.get_models_uids(benchmark_uid=benchmark_id)
    models_uids.insert(0, reference_model_id)
    models = [Model.get(model_uid) for model_uid in models_uids]
    # If any model requires confidential computing, the reference model is not listed
    if any(model.requires_cc() for model in models):
        models.pop(0)

    for model in models:
        model._encrypted = model.is_encrypted()
        model._requires_cc = model.requires_cc()
        if model._encrypted:
            model.access_status = check_access_to_container(model.container.id)
        if model._requires_cc:
            model.cc_run_status = _cc_run_status(model, dataset, user_obj)
        _attach_latest_result(model, results, benchmark_id, dataset.id)
    return models


def _evaluation_context(dataset: Dataset, user_obj) -> dict:
    """Context of the dataset page in evaluation mode: benchmark associations,
    benchmarks the dataset can be associated with, and their models and results."""
    benchmark_assocs = Dataset.get_benchmarks_associations(dataset_uid=dataset.id)
    benchmark_associations = {assoc["benchmark"]: assoc for assoc in benchmark_assocs}

    # Benchmarks the dataset can be associated with (same data preparation container)
    valid_benchmarks = {
        b.id: b
        for b in Benchmark.all()
        if b.data_preparation_mlcube == dataset.data_preparation_mlcube
    }
    approved_benchmarks = [
        benchmark_id
        for benchmark_id, assoc in benchmark_associations.items()
        if assoc["approval_status"] == "APPROVED"
    ]

    results = []
    if benchmark_assocs:
        results = Execution.all(filters={"owner": user_obj.id})
        results = filter_latest_executions(results)

    # Models can only be listed for approved associations
    benchmark_models = {
        benchmark_id: _benchmark_models(
            benchmark_id,
            valid_benchmarks[benchmark_id].reference_model,
            dataset,
            user_obj,
            results,
        )
        for benchmark_id in approved_benchmarks
    }

    return {
        "benchmark_associations": benchmark_associations,
        "benchmarks": valid_benchmarks,
        "benchmark_models": benchmark_models,
        "approved_benchmarks": approved_benchmarks,
    }


def _training_context(dataset: Dataset) -> dict:
    """Context of the dataset page in training mode: training experiment
    associations and the experiments the dataset can be associated with."""
    training_associations = {}
    available_training_experiments = []
    try:
        user_training_assocs = get_user_associations(
            experiment_type="training_exp", component_type="dataset"
        )
        for assoc in user_training_assocs:
            if assoc.get("dataset") == dataset.id:
                training_associations[assoc["training_exp"]] = assoc
        available_training_experiments = [
            exp
            for exp in TrainingExp.all()
            if exp.data_preparation_mlcube == dataset.data_preparation_mlcube
        ]
    except Exception as e:
        logger.warning("Could not load training associations: %s", e)

    experiments_by_id = {exp.id: exp for exp in available_training_experiments}
    for exp_id in training_associations:
        if exp_id not in experiments_by_id:
            try:
                experiments_by_id[exp_id] = TrainingExp.get(exp_id)
            except Exception:
                pass

    return {
        "training_associations": training_associations,
        "available_training_experiments": available_training_experiments,
        "experiments_by_id": experiments_by_id,
    }


@router.get("/ui/display/{dataset_id}", response_class=HTMLResponse)
def dataset_detail_ui(
    request: Request,
    dataset_id: int,
    current_user: bool = Depends(check_user_ui),
):
    user_obj = get_medperf_user_object()
    dataset = Dataset.get(dataset_id)

    context = {
        "request": request,
        **_dataset_page_context(dataset),
        "is_owner": user_obj.id == dataset.owner,
        "cc_config_defaults": dataset.get_cc_config(),
        "cc_configured": dataset.is_cc_configured(),
        "cc_initialized": dataset.is_cc_initialized(),
        "cc_last_synced": dataset.get_last_synced(),
    }
    if request.app.state.ui_mode == request.app.state.EVALUATION_MODE:
        context.update(_evaluation_context(dataset, user_obj))
    else:
        context.update(_training_context(dataset))

    return templates.TemplateResponse("dataset/dataset_detail.html", context)


@router.get("/register/ui", response_class=HTMLResponse)
def create_dataset_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    return templates.TemplateResponse(
        "dataset/register_dataset.html",
        {"request": request},
    )


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
    entity_id = None
    with UITask(request, "register_dataset", response={"entity_id": None}) as task:
        entity_id = DataCreation.run(
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
        task.response["entity_id"] = entity_id
    task.notify(
        success_message="Dataset successfully registered",
        failure_message="Failed to register dataset",
        url=(
            f"/datasets/ui/display/{entity_id}"
            if entity_id
            else "/datasets/register/ui"
        ),
    )
    return task.response


@router.post("/prepare", response_class=JSONResponse)
def prepare(
    request: Request,
    entity_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "prepare", response={"entity_id": None}) as task:
        entity_id = DataPreparation.run(entity_id)
        task.response["entity_id"] = entity_id
    task.notify(
        success_message="Dataset successfully prepared",
        failure_message="Failed to prepare dataset",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/set_operational", response_class=JSONResponse)
def set_operational(
    request: Request,
    entity_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(
        request, "dataset_set_operational", response={"entity_id": None}
    ) as task:
        entity_id = DatasetSetOperational.run(entity_id)
        task.response["entity_id"] = entity_id
    task.notify(
        success_message="Dataset successfully set to operational",
        failure_message="Failed to set dataset to operational",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/associate", response_class=JSONResponse)
def associate(
    request: Request,
    entity_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "dataset_association") as task:
        AssociateDataset.run(data_uid=entity_id, benchmark_uid=benchmark_id)
    task.notify(
        success_message="Successfully requested dataset association",
        failure_message="Failed to request dataset association",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/associate_training", response_class=JSONResponse)
def associate_training(
    request: Request,
    entity_id: int = Form(...),
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "dataset_training_association") as task:
        AssociateTrainingDataset.run(
            data_uid=entity_id,
            training_exp_uid=training_exp_id,
            approved=True,
        )
    task.notify(
        success_message="Successfully requested dataset association with training experiment",
        failure_message="Failed to request association with training experiment",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/start_training", response_class=JSONResponse)
def start_training(
    request: Request,
    entity_id: int = Form(...),
    training_exp_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "start_training") as task:
        TrainingExecution.run(training_exp_id=training_exp_id, data_uid=entity_id)
    task.notify(
        success_message="Training successfully finished",
        failure_message="An error occurred during training execution",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/run", response_class=JSONResponse)
def run(
    request: Request,
    entity_id: int = Form(...),
    benchmark_id: int = Form(...),
    model_ids: List[int] = Form(...),
    run_all: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "run_benchmark") as task:
        BenchmarkExecution.run(
            benchmark_id,
            entity_id,
            model_ids,
            no_cache=not run_all,
            rerun_finalized_executions=not run_all,
        )
    task.notify(
        success_message="Execution ran successfully",
        failure_message="Error during execution",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/submit_result", response_class=JSONResponse)
def submit_result(
    request: Request,
    result_id: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "submit_result") as task:
        ResultSubmission.run(result_id)
    task.notify(
        success_message="Result successfully submitted",
        failure_message="Failed to submit results",
    )
    return task.response


@router.post("/export/ui", response_class=HTMLResponse)
def export_dataset_ui(
    request: Request,
    submit: str = Form(...),
    entity_id: int = Form(...),
    current_user: bool = Depends(check_user_ui),
):
    dataset = Dataset.get(entity_id)
    return templates.TemplateResponse(
        "dataset/export_dataset.html",
        {"request": request, **_dataset_page_context(dataset)},
    )


@router.post("/export", response_class=JSONResponse)
def export_dataset(
    request: Request,
    entity_id: int = Form(...),
    output_path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):

    with UITask(request, "export_dataset", response={"entity_id": entity_id}) as task:
        ExportDataset.run(entity_id, output_path)
    task.notify(
        success_message="Dataset successfully exported",
        failure_message="Failed to export dataset",
    )
    return task.response


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
    entity_id: int = Form(...),
    input_path: str = Form(...),
    raw_dataset_path: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "import_dataset", response={"entity_id": entity_id}) as task:
        ImportDataset.run(entity_id, input_path, raw_dataset_path)
    task.notify(
        success_message="Dataset successfully imported",
        failure_message="Failed to import dataset",
        url=f"/datasets/ui/display/{entity_id}" if task.succeeded else "",
    )
    return task.response


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
    with UITask(request, "data_update_cc_config") as task:
        DatasetConfigureForCC.run(entity_id, args, {})
    task.notify(
        success_message="Successfully updated dataset CC config!",
        failure_message="Failed to update dataset CC config",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response


@router.post("/sync_cc_policy", response_class=JSONResponse)
def sync_cc_policy(
    request: Request,
    entity_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "data_update_cc_policy") as task:
        DatasetUpdateCCPolicy.run(entity_id)
    task.notify(
        success_message="Successfully updated dataset CC policy!",
        failure_message="Failed to update dataset CC policy",
        url=f"/datasets/ui/display/{entity_id}",
    )
    return task.response
