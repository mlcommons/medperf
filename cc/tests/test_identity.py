import pytest
from pydantic import ValidationError

from medperf_cc.errors import InternalError

from medperf_cc.identity import (
    TERM_CLAIMS,
    TERM_FIELDS,
    TERM_ORDER,
    AssetKind,
    WorkloadScope,
    WorkloadGrant,
    STORAGE_IDS,
    WorkloadIdentity,
)


@pytest.fixture()
def workload():
    return WorkloadIdentity(
        script_hash="scripthash",
        data_hash="datahash",
        model_hash="modelhash",
        result_collector_hash="collectorhash",
    )


@pytest.fixture()
def grant():
    """What an owner publishes: the same hashes, but able to leave some out."""
    return WorkloadGrant(
        script_hash="scripthash",
        data_hash="datahash",
        model_hash="modelhash",
        result_collector_hash="collectorhash",
    )


@pytest.fixture()
def run(workload):
    """The same workload, once it has been launched somewhere."""
    return workload.copy(
        update={"script_id": 1, "data_id": 2, "model_id": 3, "execution_id": 4}
    )


def test_every_term_has_a_claim_and_a_field():
    """The three tables are read together. A term missing from one of them
    would go unnoticed until an authorization silently stopped matching"""
    assert set(TERM_CLAIMS) == set(TERM_ORDER)
    assert set(TERM_FIELDS) == set(TERM_ORDER)


def test_a_scope_reads_the_terms_it_pins_in_order(grant):
    scope = WorkloadScope(terms=TERM_ORDER)

    assert scope.uid_of(grant) == "scripthash::datahash::modelhash::collectorhash"


def test_a_scope_leaves_out_what_it_does_not_pin(grant):
    scope = WorkloadScope(terms=["script", "model"])

    assert scope.uid_of(grant) == "scripthash::modelhash"
    assert not scope.pins("data")


def test_a_grant_may_omit_a_term_its_scope_does_not_pin():
    """The whole reason a grant is not an identity: one grant covers every
    model when its owner did not pin the model"""
    scope = WorkloadScope(terms=["script", "data", "collector"])
    grant = WorkloadGrant(script_hash="s", data_hash="d", result_collector_hash="c")

    assert scope.uid_of(grant) == "s::d::c"


def test_a_grant_that_omits_a_pinned_term_is_refused():
    """Joining the absent hash as "" would publish an authorization no workload
    could ever present"""
    scope = WorkloadScope(terms=TERM_ORDER)
    grant = WorkloadGrant(script_hash="s", data_hash="d", result_collector_hash="c")

    with pytest.raises(ValueError, match="has to name"):
        scope.uid_of(grant)


def test_an_identity_cannot_omit_anything():
    """A workload that ran, ran on something"""
    with pytest.raises(ValidationError):
        WorkloadIdentity(script_hash="s", result_collector_hash="c")


def test_an_asset_kind_knows_its_own_term_and_its_peer():
    assert AssetKind.DATA.own_term == AssetKind.MODEL.peer_term
    assert AssetKind.MODEL.own_term == AssetKind.DATA.peer_term


def test_storage_paths_are_derived_from_the_ids(run):
    assert run.results_path == "d2-m3-s1-e4/output"
    assert run.results_encryption_key_path == "d2-m3-s1-e4/encryption_key"


def test_each_execution_gets_storage_of_its_own(run):
    """Everything else about two runs of the same triple is identical, so
    without the execution the second would overwrite the first"""
    first = run.results_path
    run.execution_id = 9

    assert run.results_path != first
    assert run.results_path == "d2-m3-s1-e9/output"


@pytest.mark.parametrize("absent", STORAGE_IDS)
def test_a_workload_missing_any_id_has_no_storage_location(run, absent):
    """A launched workload that forgot one used to fall back to a shorter
    prefix, which another run would overwrite"""
    setattr(run, absent, None)

    with pytest.raises(InternalError, match=absent):
        run.results_path


def test_a_workload_that_was_never_launched_has_no_storage_location(workload):
    """What an owner authorizes is not a run, and has nowhere to put output"""
    with pytest.raises(InternalError):
        workload.storage_prefix
