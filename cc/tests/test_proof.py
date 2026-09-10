import json
import os

import pytest

from medperf_cc.proof import (
    IntegrityProof,
    ProofExpectations,
    results_hash,
    verify_proof,
)
from medperf_cc.statement import (
    PROOF_AUDIENCE,
    RESULTS_FILE,
    STATEMENT_FILE,
    TOKEN_FILE,
    statement_hash,
)
from medperf_cc.attestation import TrustAnchor
from medperf_cc.testing import FakeAttestationAuthority, confidential_space_claims

# `verify_proof` resolves what to trust from the name of an authority, and
# fetches its root. Standing in a throwaway one is how these tests get a proof
# that verifies without reaching Google.
TEST_AUTHORITY = "test-authority"

SCRIPT_IMAGE = "sha256:scripthash"
DATA_HASH = "datahash"
MODEL_HASH = "modelhash"


@pytest.fixture()
def authority():
    return FakeAttestationAuthority()


@pytest.fixture(autouse=True)
def anchor(mocker, authority):
    return mocker.patch(
        "medperf_cc.proof.trust_anchor",
        return_value=TrustAnchor(pki_root_pem=authority.root_pem),
    )


METRICS = {"auc": 0.91}


@pytest.fixture()
def results(tmp_path):
    directory = tmp_path / "results"
    directory.mkdir()
    (directory / RESULTS_FILE).write_text("auc: 0.91\n")
    (directory / "extra.txt").write_text("something else\n")
    return directory


def statement(**overrides):
    body = {
        "version": 2,
        "results_sha256": results_hash(METRICS),
        "data_sha256": DATA_HASH,
        "model_sha256": MODEL_HASH,
    }
    body.update(overrides)
    return body


def proof_for(authority, body, **claim_overrides):
    claims = confidential_space_claims(
        aud=PROOF_AUDIENCE, eat_nonce=statement_hash(body), **claim_overrides
    )
    return IntegrityProof(statement=body, token=authority.mint(claims))


def expectations(**overrides):
    fields = {
        "script_image_hash": SCRIPT_IMAGE,
        "data_hash": DATA_HASH,
        "model_hash": MODEL_HASH,
        "results": METRICS,
    }
    fields.update(overrides)
    return ProofExpectations(**fields)


def test_a_proof_of_this_run_verifies(authority):
    proof = proof_for(authority, statement())

    verdict = verify_proof(proof, expectations())

    assert verdict.verified, verdict.failures
    assert (
        "Reported metrics are exactly the ones the workload computed" in verdict.checks
    )


def test_editing_the_statement_afterwards_is_caught(authority):
    """The statement's hash is the token's nonce, so changing one word of it
    detaches it from the attestation"""
    proof = proof_for(authority, statement())
    proof.statement["results_sha256"] = "something-more-convenient"

    verdict = verify_proof(proof, expectations())

    assert not verdict.verified
    assert any("nonce" in failure for failure in verdict.failures)


def test_a_proof_from_another_authority_is_refused():
    proof = proof_for(FakeAttestationAuthority(), statement())

    verdict = verify_proof(proof, expectations())

    assert not verdict.verified


def test_a_different_script_is_caught(authority):
    """Which code ran comes from the attested image digest, so a workload
    cannot claim to have been the benchmark's script"""
    proof = proof_for(authority, statement())

    verdict = verify_proof(
        proof, expectations(script_image_hash="sha256:otherscript")
    )

    assert not verdict.verified
    assert any("produced by image" in failure for failure in verdict.failures)


def test_a_different_dataset_is_caught(authority):
    proof = proof_for(authority, statement())

    verdict = verify_proof(proof, expectations(data_hash="a-different-dataset"))

    assert not verdict.verified
    assert any("different data" in failure for failure in verdict.failures)


def test_a_workload_that_read_something_else_than_it_declared_is_caught(authority):
    """The declaration is operator-supplied; the measurement was taken inside
    the VM. Only their agreement makes the declaration worth anything"""
    proof = proof_for(authority, statement(data_sha256="what-was-actually-read"))

    verdict = verify_proof(proof, expectations())

    assert not verdict.verified
    assert any("measured" in failure for failure in verdict.failures)


def test_an_unknown_statement_version_is_refused(authority):
    proof = proof_for(authority, statement(version=99))

    verdict = verify_proof(proof, expectations())

    assert not verdict.verified


def test_a_proof_outlives_the_token_that_carries_it(authority):
    """A proof records a run that already happened. A one-hour token that had
    to still be current would make every proof self-destruct"""
    import time

    past = int(time.time()) - 90 * 24 * 3600
    proof = proof_for(authority, statement(), iat=past, exp=past + 3600)

    verdict = verify_proof(proof, expectations())

    assert verdict.verified, verdict.failures


def test_a_proof_is_checked_without_holding_the_output_files(authority):
    """The whole of what a verifier needs is the metrics off the server. Only
    whoever ran the workload keeps the files, so nothing may depend on them"""
    proof = proof_for(authority, statement())

    verdict = verify_proof(proof, expectations())

    assert verdict.verified, verdict.failures
    assert any("Reported metrics" in check for check in verdict.checks)


def test_a_verification_with_nothing_to_compare_against_cannot_be_asked_for():
    """The fail-open case: a check has nothing to compare against, passes on
    the absence, and the results are reported as backed by a valid proof. There
    is no such thing as an incomplete expectation to hand `verify_proof`."""
    with pytest.raises(TypeError):
        ProofExpectations()


@pytest.mark.parametrize(
    "missing", ["script_image_hash", "data_hash", "model_hash", "results"]
)
def test_a_single_missing_expectation_is_refused(missing):
    with pytest.raises(ValueError, match=missing.replace("_", " ")):
        expectations(**{missing: None})


def test_a_reported_metric_that_was_edited_is_caught(authority):
    """The whole point: the number on the server is the number computed"""
    proof = proof_for(authority, statement())

    verdict = verify_proof(proof, expectations(results={"auc": 0.99}))

    assert not verdict.verified
    assert any("Reported metrics do not match" in f for f in verdict.failures)


def test_metrics_check_the_same_however_the_dict_was_ordered(authority):
    """It arrives as JSON off a database, not as the file that was written"""
    metrics = {"b": 2, "a": 1}
    proof = proof_for(authority, statement(results_sha256=results_hash(metrics)))

    verdict = verify_proof(proof, expectations(results={"a": 1, "b": 2}))

    assert verdict.verified, verdict.failures


def test_metrics_reported_for_a_workload_that_attested_to_none(authority):
    """A predictions-only workload cannot vouch for a metric somebody reports"""
    proof = proof_for(authority, statement(results_sha256=None))

    verdict = verify_proof(proof, expectations())

    assert not verdict.verified
    assert any("attested to no metrics" in f for f in verdict.failures)


def test_every_failure_is_reported_not_just_the_first(authority):
    """Which part is wrong is the useful output"""
    proof = proof_for(authority, statement())

    verdict = verify_proof(
        proof,
        expectations(
            script_image_hash="sha256:otherscript", data_hash="a-different-dataset"
        ),
    )

    assert len(verdict.failures) == 2


def test_a_proof_round_trips_through_a_results_directory(authority, results):
    proof = proof_for(authority, statement())
    (results / STATEMENT_FILE).write_text(json.dumps(proof.statement))
    (results / TOKEN_FILE).write_text(proof.token)

    read_back = IntegrityProof.from_results_dir(str(results))

    assert read_back.statement == proof.statement
    assert read_back.token == proof.token


def test_no_proof_where_the_workload_wrote_none(results):
    assert IntegrityProof.from_results_dir(str(results)) is None
    assert IntegrityProof.from_results_dir(os.path.join(str(results), "nope")) is None
