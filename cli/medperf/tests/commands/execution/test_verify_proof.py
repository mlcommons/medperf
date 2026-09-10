"""Which entity field is authoritative for each part of a proof.

This mapping is what decides whether a verification means anything: taking any
of it from the proof itself would establish nothing, so each expectation has to
come from MedPerf's own record of what should have run.
"""

import os

import pytest
import yaml

from medperf import config
from medperf.commands.execution.verify_proof import VerifyExecutionProof
from medperf.enums import BenchmarkTopology
from medperf.exceptions import InvalidArgumentError, MedperfException
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
from medperf.tests.mocks.model import TestAssetModel, TestContainerModel
from medperf_cc.attestation import GOOGLE
from medperf_cc.errors import AttestationError

PATCH_VERIFY = "medperf.commands.execution.verify_proof.{}"

SCRIPT_IMAGE = "sha256:scripthash"
DATA_UID = "the-generated-uid"
ASSET_HASH = "the-asset-hash"

PROOF = {"statement": {"version": 1}, "token": "from-the-server"}


@pytest.fixture()
def execution(mocker, fs):
    """A registered execution and the three entities it points at."""
    execution = TestExecution(benchmark=1, dataset=2, model=3)
    mocker.patch(PATCH_VERIFY.format("Execution.get"), return_value=execution)
    mocker.patch(
        PATCH_VERIFY.format("Benchmark.get"),
        return_value=TestBenchmark(
            topology=BenchmarkTopology.END_TO_END_SCRIPT.value,
            data_evaluator_mlcube=None,
            benchmark_script=7,
        ),
    )
    mocker.patch(
        PATCH_VERIFY.format("Dataset.get"),
        return_value=TestDataset(generated_uid=DATA_UID),
    )
    mocker.patch(
        PATCH_VERIFY.format("Model.get"),
        return_value=TestAssetModel(
            asset={
                "id": 5,
                "name": "asset",
                "asset_hash": ASSET_HASH,
                "asset_url": "https://test.com/asset.tar.gz",
                "state": "OPERATION",
                "is_valid": True,
            }
        ),
    )
    mocker.patch(
        "medperf.commands.execution.plan.Cube.get",
        return_value=TestCube(id=7, image_hash=SCRIPT_IMAGE),
    )
    return execution


@pytest.fixture()
def verify(mocker):
    """Captures what the verifier was asked to check, and against what."""
    return mocker.patch(PATCH_VERIFY.format("verify_proof"))


def test_expectations_come_from_medperf_not_from_the_proof(execution, verify):
    """A proof that only agreed with itself would establish nothing"""
    # Arrange
    execution.integrity_proof = PROOF

    # Act
    VerifyExecutionProof.run(execution.id)

    # Assert
    expectations = verify.call_args.args[1]
    assert expectations.script_image_hash == SCRIPT_IMAGE
    assert expectations.data_hash == DATA_UID
    assert expectations.model_hash == ASSET_HASH


def test_a_container_model_could_not_have_produced_this_proof(
    mocker, execution, verify
):
    """Only asset models are loaded into a confidential VM. There is no hash to
    pin for one that brings its own container, and rather than verifying
    against one expectation fewer, this says the record makes no sense"""
    # Arrange
    execution.integrity_proof = PROOF
    mocker.patch(PATCH_VERIFY.format("Model.get"), return_value=TestContainerModel())

    # Act & Assert
    with pytest.raises(MedperfException, match="not an asset"):
        VerifyExecutionProof.run(execution.id)
    verify.assert_not_called()


def test_the_reported_metrics_are_what_gets_checked(execution, verify):
    """What the server holds is what everyone downstream reads, and the only
    thing somebody who did not run the execution can check"""
    # Arrange
    execution.integrity_proof = PROOF
    execution.results = {"auc": 0.91}

    # Act
    VerifyExecutionProof.run(execution.id)

    # Assert
    assert verify.call_args.args[1].results == {"auc": 0.91}


def test_nothing_this_machine_happens_to_hold_is_an_expectation(fs, execution, verify):
    """Everything checked comes off the server, so a verification means the
    same for whoever ran the execution and for whoever only read the number"""
    # Arrange
    execution.integrity_proof = PROOF
    execution.results = {"auc": 0.91}
    runs = os.path.join(config.script_result_folder, str(execution.id))
    fs.create_file(os.path.join(runs, "1700000001_0", "results.yaml"))

    # Act
    VerifyExecutionProof.run(execution.id)

    # Assert
    expectations = verify.call_args.args[1]
    assert not any(
        isinstance(value, str) and runs in value
        for value in vars(expectations).values()
    )


def test_the_server_copy_of_the_proof_is_preferred(fs, execution, verify):
    """The local copy is what this machine happens to still hold; the server's
    is what everyone else would check"""
    # Arrange
    execution.integrity_proof = PROOF
    fs.create_file(
        execution.integrity_proof_path,
        contents=yaml.safe_dump({"statement": {}, "token": "from-this-machine"}),
    )

    # Act
    VerifyExecutionProof.run(execution.id)

    # Assert
    assert verify.call_args.args[0].token == "from-the-server"


def test_a_local_proof_is_used_when_the_server_has_none(fs, execution, verify):
    # Arrange
    execution.integrity_proof = {}
    fs.create_file(
        execution.integrity_proof_path,
        contents=yaml.safe_dump({"statement": {}, "token": "from-this-machine"}),
    )

    # Act
    VerifyExecutionProof.run(execution.id)

    # Assert
    assert verify.call_args.args[0].token == "from-this-machine"


def test_an_execution_with_no_proof_is_visibly_unverified(execution, verify):
    # Arrange
    execution.integrity_proof = {}

    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="no integrity proof"):
        VerifyExecutionProof.run(execution.id)


def test_the_client_names_an_authority_rather_than_supplying_a_trust_anchor(
    execution, verify
):
    """What to accept as proof that a token is genuine follows from who signed
    it, and is medperf_cc's business to work out"""
    # Arrange
    execution.integrity_proof = PROOF

    # Act
    VerifyExecutionProof.run(execution.id)

    # Assert
    assert verify.call_args.kwargs["authority"] == GOOGLE


def test_an_authority_that_cannot_be_reached_is_reported(mocker, execution):
    """Not a proof that failed -- a proof nobody was able to check"""
    # Arrange
    execution.integrity_proof = PROOF
    mocker.patch(
        PATCH_VERIFY.format("verify_proof"),
        side_effect=AttestationError("could not fetch the root certificate"),
    )

    # Act & Assert
    with pytest.raises(MedperfException, match="root certificate"):
        VerifyExecutionProof.run(execution.id)
