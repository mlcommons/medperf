"""The mock result store: where a workload's output lands, and getting it back.

The collector's own storage, which under the mock is a directory every party
shares -- which is what lets an operator and a collector who are different
people find each other without a cloud account between them.
"""

import os

import pytest

from medperf_cc import WorkloadIdentity, get_result_store, store_config
from medperf_cc.result_store.mock import RESULTS_FILE, RESULTS_KEY_FILE

SETTINGS = {"backend": "mock"}


@pytest.fixture()
def settings(tmp_path):
    return {**SETTINGS, "root": str(tmp_path / "cc")}


@pytest.fixture()
def result_store(settings):
    return get_result_store(settings)


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


def test_the_workload_is_told_where_to_write(result_store, workload):
    config = result_store.store_config(workload)

    assert config["backend"] == "mock"
    assert config["results_name"] == workload.storage_prefix


def test_what_travels_to_the_vm_is_an_address_and_nothing_else(result_store, workload):
    """The operator can read it, and it belongs to somebody else"""
    assert set(result_store.store_config(workload)) == {
        "backend",
        "root",
        "results_name",
    }


def test_an_operator_can_work_out_the_address_without_holding_a_store(
    settings, workload, result_store
):
    """The whole of what an operator needs from somebody else's store: a
    function of their published settings, reaching nothing and holding nothing"""
    assert store_config(settings, workload) == result_store.store_config(workload)


def test_results_are_not_ready_before_a_workload_has_run(result_store, workload):
    assert not result_store.results_ready(workload)


def test_half_written_results_are_not_ready(result_store, workload):
    """Both the output and the key it is wrapped with, or there is nothing to
    open"""
    __write_result(result_store, workload, RESULTS_FILE, b"encrypted results")

    assert not result_store.results_ready(workload)


def test_what_the_workload_wrote_comes_back(result_store, workload, tmp_path):
    __write_result(result_store, workload, RESULTS_FILE, b"encrypted results")
    __write_result(result_store, workload, RESULTS_KEY_FILE, b"wrapped key")

    destination = str(tmp_path / "fetched.enc")
    wrapped = result_store.fetch(workload, destination)

    assert result_store.results_ready(workload)
    assert open(destination, "rb").read() == b"encrypted results"
    assert wrapped == b"wrapped key"


def __write_result(result_store, workload, filename, content):
    directory = os.path.join(result_store.mock.root, workload.storage_prefix)
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, filename), "wb") as f:
        f.write(content)
