from medperf import config
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.enums import ModelType
from medperf.commands.execution.container_execution import ContainerExecution
from medperf.commands.execution.script_execution import ScriptExecution
from medperf.commands.execution.confidential_execution import ConfidentialExecution
from medperf.account_management import get_medperf_user_data, is_user_logged_in


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
            model.type == ModelType.ASSET.value
            and model.is_cc_mode()
            and not user_is_model_owner
        ):
            return ConfidentialExecution.run(
                benchmark_id, dataset, model, evaluator, execution, ignore_model_errors
            )
        elif model.type == ModelType.ASSET.value:
            asset = model.asset_obj
            asset.prepare_asset_files()
            return ScriptExecution.run(
                dataset, asset, evaluator, execution, ignore_model_errors
            )
        else:
            container = model.container_obj
            with config.ui.interactive():
                container.download_run_files()
            return ContainerExecution.run(
                dataset, container, evaluator, execution, ignore_model_errors
            )
