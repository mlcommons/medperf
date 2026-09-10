"""Operating a confidential workload: start it and watch it.

Only the launching half. What the workload produced is picked up from the
store it was written to -- see `medperf.cc.results`.
"""

from colorama import Fore, Style

import medperf.config as medperf_config
from medperf.cc.config import asset_for, runner_for
from medperf.cc.errors import as_medperf_error
from medperf.entities.user import User
from medperf.exceptions import ExecutionError
from medperf_cc import AssetKind, WorkloadIdentity, WorkloadRunner


def workload_configs(dataset, model):
    """What the workload is told about where to fetch each asset from.

    Never the stored configuration: this travels to the VM as environment the
    operator can read, so a key broker's admin token must not go with it."""
    return (
        asset_for(dataset, AssetKind.DATA).workload_config(),
        asset_for(model, AssetKind.MODEL).workload_config(),
    )


@as_medperf_error()
def setup_operator(user: User):
    if not user.cc_operator.configured:
        return

    runner_for(user).verify()


@as_medperf_error(ExecutionError)
def run_workload(
    runner: WorkloadRunner,
    docker_image: str,
    workload: WorkloadIdentity,
    dataset_cc_config: dict,
    model_cc_config: dict,
    result_config: dict,
    result_collector_public_key: str,
):
    runner.start(
        workload,
        docker_image,
        dataset_cc_config,
        model_cc_config,
        result_config,
        result_collector_public_key,
    )


@as_medperf_error(ExecutionError)
def wait_for_workload(runner: WorkloadRunner, workload: WorkloadIdentity):
    for output in runner.wait(workload):
        medperf_config.ui.print_subprocess_logs(
            f"{Fore.WHITE}{Style.DIM}{output}{Style.RESET_ALL}"
        )
