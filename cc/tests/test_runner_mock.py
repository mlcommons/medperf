"""The mock runner: what it asks the container runtime for.

Starting a real container belongs to the integration tests. What matters here
is that a workload would receive exactly what a confidential VM gives it. Where
its output goes is the collector's, and is tested in `test_result_store_mock.py`.
"""

import json

import pytest

from medperf_cc import WorkloadIdentity, get_runner, store_config
from medperf_cc.errors import OperationError

IMAGE = "ghcr.io/example/benchmark-script@sha256:scripthash"


@pytest.fixture()
def runner(tmp_path):
    return get_runner({"backend": "mock", "root": str(tmp_path / "cc")})


@pytest.fixture()
def workload():
    return WorkloadIdentity(
        script_hash="scripthash",
        data_hash="datahash",
        model_hash="modelhash",
        result_collector_hash="collectorhash",
        script_id=1,
        data_id=2,
        model_id=3,
        execution_id=4,
    )


@pytest.fixture()
def address(tmp_path, workload):
    """Where the collector wants the output.

    Worked out from the settings they published; under the mock that is the
    same directory, but the runner is told rather than asked either way."""
    return store_config(
        {"backend": "mock", "root": str(tmp_path / "cc")}, workload
    )


@pytest.fixture()
def start(runner, workload, address):
    """Starting the workload with everything its caller has to supply."""

    def _start(collector_key="key"):
        runner.start(workload, IMAGE, {}, {}, address, collector_key)

    return _start


@pytest.fixture()
def started(mocker):
    """Captures the command the runner would have run."""
    run = mocker.patch(
        "medperf_cc.runner.mock.subprocess.run",
        return_value=mocker.Mock(returncode=0, stderr=""),
    )
    return run


def command_of(started):
    return started.call_args.args[0]


def test_the_workload_receives_the_environment_a_vm_would(start, started):
    """`EXPECTED_*` is what a real backend matches an attestation against, so
    the workload has to see it exactly as the operator set it"""
    start(collector_key="the-collector-key")

    command = command_of(started)
    assert "EXPECTED_DATA_HASH=datahash" in command
    assert "EXPECTED_MODEL_HASH=modelhash" in command
    assert "RESULT_COLLECTOR=the-collector-key" in command
    assert command[-1] == IMAGE


def test_the_workload_is_told_where_the_collector_wants_its_output(
    start, started, address
):
    """The destination is the collector's, so it reaches the VM exactly as the
    caller supplied it -- the runner neither chooses it nor rewrites it"""
    start()

    result_config = json.loads(
        [c for c in command_of(started) if c.startswith("RESULT_CONFIG=")][0].split(
            "=", 1
        )[1]
    )
    assert result_config == address


def test_the_workload_sees_the_paths_the_parties_exchanged(runner, start, started):
    """Mounted at the same path inside, or nothing the owner published would
    mean the same thing to the workload"""
    start()

    root = runner.mock.root
    assert f"{root}:{root}" in command_of(started)


def test_each_workload_gets_a_container_of_its_own(workload, start, started):
    start()

    assert workload.storage_prefix in " ".join(command_of(started))


def test_a_runtime_that_refuses_is_reported(start, mocker):
    mocker.patch(
        "medperf_cc.runner.mock.subprocess.run",
        return_value=mocker.Mock(returncode=1, stderr="no such image"),
    )

    with pytest.raises(OperationError, match="no such image"):
        start()
