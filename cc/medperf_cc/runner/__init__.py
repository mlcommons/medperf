"""Starting a confidential workload and collecting what it produced."""

from medperf_cc.backends import backend_of, describe, settings_of
from medperf_cc.backends.mock import MOCK
from medperf_cc.runner.base import WorkloadRunner
from medperf_cc.runner.gcp import GCP_RUNNER, ConfidentialSpaceRunner
from medperf_cc.runner.mock import MockRunner

RUNNERS = {
    GCP_RUNNER: ConfidentialSpaceRunner,
    MOCK: MockRunner,
}


def runner_backends() -> dict:
    """What an operator may choose to run workloads with, and what each choice
    needs from them."""
    return describe(RUNNERS)


def get_runner(config: dict) -> WorkloadRunner:
    backend = backend_of(config, RUNNERS, "runner")
    return RUNNERS[backend](settings_of(config))


__all__ = ["RUNNERS", "WorkloadRunner", "get_runner", "runner_backends"]
