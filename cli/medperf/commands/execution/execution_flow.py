from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.benchmark import Benchmark
from medperf.enums import ModelType
from medperf.commands.execution.container_execution import ContainerExecution
from medperf.commands.execution.script_execution import ScriptExecution
from medperf.commands.execution.confidential_execution import ConfidentialExecution
from medperf.commands.execution.confidential_model_container_execution import (
    ConfidentialModelContainerExecution,
)
from medperf.account_management import get_medperf_user_data, is_user_logged_in
from medperf.exceptions import ExecutionError


class ExecutionFlow:
    @classmethod
    def run(
        cls,
        benchmark_id: int,
        dataset: Dataset,
        model: Model,
        evaluator: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        user_is_model_owner = (
            is_user_logged_in() and model.owner == get_medperf_user_data()["id"]
        )

        if (
            evaluator.is_script()
            and model.type == ModelType.ASSET.value
            and model.requires_cc()
            and not user_is_model_owner
        ):
            return ConfidentialExecution.run(
                benchmark_id, dataset, model, evaluator, execution, ignore_model_errors
            )
        elif (
            model.type == ModelType.ASSET.value
            and model.requires_cc()
            and not user_is_model_owner
        ):
            benchmark = Benchmark.get(benchmark_id)
            ref_model = Model.get(benchmark.reference_model)
            script = ref_model.container_obj
            return ConfidentialModelContainerExecution.run(
                benchmark_id,
                dataset,
                model,
                script,
                evaluator,
                execution,
                ignore_model_errors,
            )
        elif model.type == ModelType.ASSET.value:
            if not evaluator.is_script():
                raise ExecutionError(
                    "Running a model container with another asset model is not supported yet."
                )
            asset = model.asset_obj
            asset.prepare_asset_files()
            return ScriptExecution.run(
                dataset, asset, evaluator, execution, ignore_model_errors
            )
        else:
            container = model.container_obj
            container.download_run_files()
            return ContainerExecution.run(
                dataset, container, evaluator, execution, ignore_model_errors
            )
