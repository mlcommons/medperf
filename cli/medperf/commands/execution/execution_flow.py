from medperf import config
from medperf.entities.model import Model
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.enums import BenchmarkTopology, ExecutionMedium
from medperf.commands.execution.container_execution import ContainerExecution
from medperf.commands.execution.script_execution import ScriptExecution
from medperf.commands.execution.confidential_execution import ConfidentialExecution
from medperf.commands.execution.confidential_model_container_execution import (
    ConfidentialModelContainerExecution,
)
from medperf.commands.execution.plan import BenchmarkPlan, resolve_execution_medium
from medperf.exceptions import ExecutionError


def _run_container_model(plan, dataset, model, execution, ignore_model_errors):
    container = model.container_obj
    with config.ui.interactive():
        container.download_run_files()
    return ContainerExecution.run(
        dataset, container, plan.evaluator, execution, ignore_model_errors
    )


def _run_asset_model_script(plan, dataset, model, execution, ignore_model_errors):
    asset = model.asset_obj
    asset.prepare_asset_files()
    return ScriptExecution.run(
        dataset, asset, plan.script, execution, ignore_model_errors
    )


# Topology decides what runs; medium decides where. Every supported combination
# gets an entry here, so an unsupported one is a missing key rather than a
# branch that silently falls through.
EXECUTORS = {
    (BenchmarkTopology.BYO_INFERENCE_SCRIPT, ExecutionMedium.LOCAL): (
        _run_container_model
    ),
    (BenchmarkTopology.END_TO_END_SCRIPT, ExecutionMedium.LOCAL): (
        _run_asset_model_script
    ),
    (BenchmarkTopology.END_TO_END_SCRIPT, ExecutionMedium.CONFIDENTIAL): (
        ConfidentialExecution.run
    ),
    (BenchmarkTopology.INFERENCE_SCRIPT, ExecutionMedium.CONFIDENTIAL): (
        ConfidentialModelContainerExecution.run
    ),
}

UNSUPPORTED_REASONS = {
    (BenchmarkTopology.BYO_INFERENCE_SCRIPT, ExecutionMedium.CONFIDENTIAL): (
        "Confidential execution requires an asset model, but a"
        " byo_inference_script benchmark runs container models. Container"
        " models are protected with container encryption instead."
    ),
    (BenchmarkTopology.INFERENCE_SCRIPT, ExecutionMedium.LOCAL): (
        "Running an inference_script benchmark locally is not supported yet."
        " Configure the model for confidential computing, or use an"
        " end_to_end_script benchmark."
    ),
}


class ExecutionFlow:
    @classmethod
    def run(
        cls,
        plan: BenchmarkPlan,
        dataset: Dataset,
        model: Model,
        execution: Execution = None,
        ignore_model_errors=False,
    ):
        """Runs a single (model, dataset) experiment of a benchmark.

        Args:
            plan (BenchmarkPlan): the benchmark's resolved components
            dataset (Dataset): the dataset to run against
            model (Model): the model to execute
        """
        cls.validate_model(plan, model)
        medium = resolve_execution_medium(model, dataset)
        cls.validate_execution(medium, execution)
        executor = EXECUTORS.get((plan.topology, medium))
        if executor is None:
            reason = UNSUPPORTED_REASONS.get(
                (plan.topology, medium),
                f"Executing a {plan.topology.value} benchmark on the"
                f" {medium.value} medium is not supported.",
            )
            raise ExecutionError(reason)

        return executor(plan, dataset, model, execution, ignore_model_errors)

    @staticmethod
    def validate_execution(medium: ExecutionMedium, execution: Execution):
        """A confidential run needs a registered execution to belong to.

        Its identity, the storage its output goes to, and the status it reports
        back are all keyed by the execution. A compatibility test has none --
        it assembles components ad hoc, without registering anything -- so it
        cannot be run confidentially, and saying so here is cheaper than
        failing once a confidential VM is already running."""
        if medium is ExecutionMedium.CONFIDENTIAL and execution is None:
            raise ExecutionError(
                "A confidential execution cannot be run as a compatibility"
                " test. Associate the model with a benchmark and run it"
                " through that benchmark instead."
            )

    @staticmethod
    def validate_model(plan: BenchmarkPlan, model: Model):
        """Checks the model is of the kind the topology expects.

        The server enforces this when an association is created; this catches
        the ad-hoc combinations a local compatibility test can put together."""
        if plan.topology.uses_asset_models and not model.is_asset():
            raise ExecutionError(
                f"A {plan.topology.value} benchmark expects asset models,"
                f" but model {model.identifier} is a container."
            )
        if not plan.topology.uses_asset_models and not model.is_container():
            raise ExecutionError(
                f"A {plan.topology.value} benchmark expects container models,"
                f" but model {model.identifier} is an asset."
            )
