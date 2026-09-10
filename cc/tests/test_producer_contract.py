"""The producing side of a proof, checked against the verifying side.

The confidential base image builds separately with minimal dependencies and
cannot install this package, so it copies in `medperf_cc/statement.py` and
imports it as `statement`. That is what makes the encoding and the hashing one
implementation rather than two, and it is what is stubbed in below: the producer
is loaded from source with `statement` bound to the real module, exactly as the
image runs it.

What is left to check is what the producer decides on its own -- which keys go
in a statement, where the measurements come from, and what a workload that
produced no metrics attests to.
"""

import importlib.util
import json
import os
import sys
import types

import pytest
import yaml

from medperf_cc import proof as verifier
from medperf_cc import statement as contract

PRODUCER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "examples",
    "cc",
    "base_image",
    "src",
    "integrity_proof.py",
)


def load_producer():
    """Loads the base image's module, with the contract it is built against.

    The launcher client does not exist outside the VM, so it is stubbed with
    what the producer uses. `statement` is not stubbed -- it is the real
    `medperf_cc.statement`, which is what the image gets a copy of."""
    attestation = types.ModuleType("assets.attestation")
    attestation.AttestationUnavailable = type(
        "AttestationUnavailable", (Exception,), {}
    )
    attestation.request_token = lambda **kwargs: ""

    assets = types.ModuleType("assets")
    assets.attestation = attestation

    stubs = {
        "assets": assets,
        "assets.attestation": attestation,
        "statement": contract,
    }
    saved = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        spec = importlib.util.spec_from_file_location(
            "base_image_integrity_proof", PRODUCER_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous in saved.items():
            if previous is None:
                del sys.modules[name]
            else:
                sys.modules[name] = previous


@pytest.fixture(scope="module")
def producer():
    return load_producer()


@pytest.fixture()
def results(tmp_path):
    directory = tmp_path / "results"
    (directory / "nested").mkdir(parents=True)
    (directory / "results.yaml").write_text("auc: 0.91\n")
    (directory / "nested" / "predictions.csv").write_text("1,2,3\n")
    return str(directory)


def test_the_producer_takes_the_contract_from_this_package(producer):
    """If it ever stopped, the two sides could disagree again"""
    assert producer.STATEMENT_FILE is contract.STATEMENT_FILE
    assert producer.PROOF_AUDIENCE is contract.PROOF_AUDIENCE
    assert producer.statement_hash is contract.statement_hash
    assert producer.canonical_hash is contract.canonical_hash


def test_the_version_it_writes_is_one_the_verifier_supports():
    assert contract.STATEMENT_VERSION in contract.SUPPORTED_STATEMENT_VERSIONS


def test_the_statement_carries_everything_the_verifier_checks(
    producer, results, monkeypatch, tmp_path
):
    """A key the producer never writes is a check that can never pass"""
    # Arrange
    monkeypatch.setenv("TMP_FILES", str(tmp_path))

    # Act
    statement = producer.build_statement(results)

    # Assert
    assert set(statement) == {
        "version",
        "results_sha256",
        "data_sha256",
        "model_sha256",
    }


def test_the_metrics_it_attests_to_are_the_ones_the_server_will_hold(producer, results):
    """The producer reads a YAML file, the verifier is handed a dict off the
    server. They have to arrive at the same number or nobody can check a
    reported metric"""
    # Arrange
    metrics = {"auc": 0.91, "accuracy": 0.8, "nested": {"b": 2, "a": [1, 2]}}
    with open(os.path.join(results, contract.RESULTS_FILE), "w") as f:
        yaml.safe_dump(metrics, f)

    # Act
    attested = producer.results_hash(results)

    # Assert
    assert attested == verifier.results_hash(json.loads(json.dumps(metrics)))


def test_the_metrics_hash_ignores_how_the_yaml_was_written(producer, results):
    """Key order and formatting are not part of what was computed"""
    # Arrange
    path = os.path.join(results, contract.RESULTS_FILE)
    with open(path, "w") as f:
        f.write("auc: 0.91\naccuracy: 0.8\n")
    one_way = producer.results_hash(results)

    # Act
    with open(path, "w") as f:
        f.write("accuracy:   0.8\n\nauc: 0.91\n")

    # Assert
    assert producer.results_hash(results) == one_way


def test_an_undefined_metric_is_attested_to_as_the_null_it_becomes(producer, results):
    """`AUC: .nan` is a real output -- an AUC is undefined when the labels hold
    one class. Python spells it `NaN`, which no other JSON reader accepts, so
    what a strict store holds after the round trip is null"""
    # Arrange
    with open(os.path.join(results, contract.RESULTS_FILE), "w") as f:
        f.write("AUC: .nan\nAccuracy: 0.93\n")

    # Act
    attested = producer.results_hash(results)

    # Assert
    assert attested == verifier.results_hash({"AUC": None, "Accuracy": 0.93})


def test_a_workload_producing_no_metrics_attests_to_none(producer, tmp_path):
    """An inference_script workload returns predictions, not a score"""
    # Arrange
    predictions_only = tmp_path / "predictions"
    predictions_only.mkdir()
    (predictions_only / "preds.csv").write_text("1,2,3\n")

    # Act
    attested = producer.results_hash(str(predictions_only))

    # Assert
    assert attested is None


def test_the_statement_the_producer_writes_is_the_one_it_committed_to(
    producer, results, monkeypatch, tmp_path
):
    """Serialization must not change the hash: the verifier recomputes it from
    the parsed JSON, not from the bytes on disk"""
    # Arrange
    monkeypatch.setenv("TMP_FILES", str(tmp_path))
    statement = producer.build_statement(results)

    # Act
    with open(os.path.join(results, contract.STATEMENT_FILE), "w") as f:
        json.dump(statement, f, sort_keys=True, separators=(",", ":"))
    with open(os.path.join(results, contract.STATEMENT_FILE)) as f:
        parsed = json.load(f)

    # Assert
    assert verifier.statement_hash(parsed) == contract.statement_hash(statement)


def test_the_producer_reports_what_the_workload_measured(
    producer, results, monkeypatch, tmp_path
):
    # Arrange
    monkeypatch.setenv("TMP_FILES", str(tmp_path))
    with open(tmp_path / producer.MEASURED_HASHES_FILE, "w") as f:
        json.dump({"data_sha256": "measured-data", "model_sha256": "measured-model"}, f)

    # Act
    statement = producer.build_statement(results)

    # Assert
    assert statement["data_sha256"] == "measured-data"
    assert statement["model_sha256"] == "measured-model"


def test_the_script_is_deliberately_not_in_the_statement(
    producer, results, monkeypatch, tmp_path
):
    """It comes from the token's attested image digest. A workload
    self-reporting its own image would be worth nothing"""
    # Arrange
    monkeypatch.setenv("TMP_FILES", str(tmp_path))

    # Act
    statement = producer.build_statement(results)

    # Assert
    assert "script" not in json.dumps(statement)
