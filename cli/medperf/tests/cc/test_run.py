"""The identity one confidential execution runs under.

Derived, never stored: the operator works it out to launch the workload, and
the collector works out the same one afterwards to find what was written for
them. Nothing is handed between them, so the two derivations have to agree --
and when they do not, nothing fails loudly. The rebuilt identity just names a
place nothing was ever written to.
"""

import pytest

from medperf.cc.run import ConfidentialRun

PATCH_RUN = "medperf.cc.run.{}"

COLLECTOR_KEY_HASH = "hash-of-the-collector-key"


@pytest.fixture(autouse=True)
def a_store(mocker):
    return mocker.patch(PATCH_RUN.format("result_store_for"))


@pytest.fixture()
def collector(mocker):
    return mocker.MagicMock(
        user_id=20,
        public_key=b"collector-key",
        key_hash=COLLECTOR_KEY_HASH,
        settings={"backend": "mock", "root": "/tmp/theirs"},
    )


@pytest.fixture()
def parts(mocker):
    return {
        "plan": mocker.MagicMock(script_hash="scripthash", script_id=7),
        "dataset": mocker.MagicMock(id=1, generated_uid="datahash"),
        "model": mocker.MagicMock(
            id=2, asset_obj=mocker.MagicMock(asset_hash="modelhash")
        ),
        "execution": mocker.MagicMock(id=42),
    }


def resolve(parts, collector):
    return ConfidentialRun.resolve(
        parts["plan"],
        parts["dataset"],
        parts["model"],
        parts["execution"],
        collector,
    )


def test_the_identity_is_built_from_what_the_server_already_holds(parts, collector):
    """Every term of it is recorded, which is what lets it be derived twice
    rather than stored once"""
    # Act
    run = resolve(parts, collector)

    # Assert
    assert run.workload.data_hash == "datahash"
    assert run.workload.model_hash == "modelhash"
    assert run.workload.script_hash == "scripthash"
    assert run.workload.result_collector_hash == COLLECTOR_KEY_HASH


def test_a_launched_workload_says_which_execution_it_is(parts, collector):
    """Its storage prefix is built from this. Without it, two runs of the same
    dataset, model and script write to the same place and the second overwrites
    the first"""
    # Act
    run = resolve(parts, collector)

    # Assert
    assert run.workload.execution_id == 42
    assert str(42) in run.workload.storage_prefix


def test_the_collector_rebuilds_the_identity_the_operator_launched(parts, collector):
    """The operator stores nothing for them. If these ever drifted apart the
    collector would look in a place nothing was written to, and the results
    would simply appear not to exist"""
    # Act
    operators = resolve(parts, collector)
    collectors = resolve(parts, collector)

    # Assert
    assert operators.workload.storage_prefix == collectors.workload.storage_prefix


def test_what_reaches_the_vm_comes_from_the_collectors_store(parts, collector, a_store):
    # Act
    run = resolve(parts, collector)

    # Assert
    a_store.assert_called_once_with(collector.settings)
    assert run.store_config is a_store.return_value.store_config.return_value


def test_the_key_reaches_the_workload_as_text(parts, collector):
    """It travels as VM metadata, which carries strings"""
    # Act & Assert
    assert resolve(parts, collector).collector_public_key == "collector-key"
