from medperf.entities.asset import Asset
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.enums import ModelType
from medperf.commands.execution.container_execution import ContainerExecution
from medperf.commands.execution.script_execution import ScriptExecution


class ExecutionFlow:
    @classmethod
    def run(
        cls,
        dataset: Dataset,
        model: Model,
        evaluator: Cube,
        execution: Execution = None,
        ignore_model_errors=False,
        local_model=False,
    ):
        if model.type == ModelType.ASSET.value:
            asset = Asset.get(model.asset)
            if not local_model:
                asset.prepare_asset_files()
            return ScriptExecution.run(
                dataset, asset, evaluator, execution, ignore_model_errors
            )
        else:
            container = Cube.get(model.container)
            if not local_model:
                container.download_run_files()
            return ContainerExecution.run(
                dataset, container, evaluator, execution, ignore_model_errors
            )
