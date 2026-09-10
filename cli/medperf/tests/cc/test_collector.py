"""Working out who the results of one execution are for.

Both asset owners name the roles they release results to. The results are
encrypted for a single key and written to a single place, so it has to be one
party both of them named -- and which one is not a choice MedPerf can make on
anybody's behalf.
"""

import pytest

from medperf.cc.collector import collector_role, resolve_collector
from medperf.exceptions import ExecutionError
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.model import TestAssetModel
from medperf_cc import AssetPolicy, Party

PATCH_COLLECTOR = "medperf.cc.collector.{}"

BENCHMARK_OWNER_ID = 10
DATA_OWNER_ID = 20
MODEL_OWNER_ID = 30

THEIR_STORE = {"backend": "mock", "root": "/tmp/theirs"}


@pytest.fixture()
def entities():
    return {
        "benchmark": TestBenchmark(owner=BENCHMARK_OWNER_ID),
        "dataset": TestDataset(owner=DATA_OWNER_ID),
        "model": TestAssetModel(owner=MODEL_OWNER_ID),
    }


@pytest.fixture(autouse=True)
def somebody_else(mocker):
    """Nobody is logged in, so every party is read the way a peer reads them:
    their certificate from the benchmark listing, their store from what the
    server publishes about them."""
    mocker.patch(PATCH_COLLECTOR.format("is_current_user"), return_value=False)
    certificate = mocker.MagicMock()
    certificate.public_key.return_value = b"their-key"
    mocker.patch(PATCH_COLLECTOR.format("certificate_of"), return_value=certificate)
    comms = mocker.patch(PATCH_COLLECTOR.format("medperf_config")).comms
    comms.get_user_metadata.return_value = {"cc": {"collector": THEIR_STORE}}
    return comms


def set_policies(mocker, data_roles, model_roles):
    policies = {
        TestDataset: AssetPolicy(allowed_result_collectors=data_roles),
        TestAssetModel: AssetPolicy(allowed_result_collectors=model_roles),
    }
    mocker.patch(
        PATCH_COLLECTOR.format("policy_of"),
        side_effect=lambda entity: policies[type(entity)],
    )


def resolve(entities):
    return resolve_collector(
        entities["benchmark"], entities["dataset"], entities["model"]
    )


def test_the_one_party_both_owners_named_collects(mocker, entities):
    """One key, one destination, so it has to be a role they both named"""
    # Arrange
    set_policies(
        mocker, [Party.MODEL_OWNER], [Party.MODEL_OWNER, Party.DATA_OWNER]
    )

    # Act
    collector = resolve(entities)

    # Assert
    assert collector.user_id == MODEL_OWNER_ID
    assert collector.party is Party.MODEL_OWNER
    assert collector.settings == THEIR_STORE


def test_owners_who_agree_on_nobody_are_refused(mocker, entities):
    # Arrange
    set_policies(mocker, [Party.DATA_OWNER], [Party.MODEL_OWNER])

    # Act & Assert
    with pytest.raises(ExecutionError, match="have not agreed"):
        resolve(entities)


def test_owners_who_agree_on_two_parties_are_refused(mocker, entities):
    """Not a choice this can make on anybody's behalf"""
    # Arrange
    both = [Party.DATA_OWNER, Party.MODEL_OWNER]
    set_policies(mocker, both, both)

    # Act & Assert
    with pytest.raises(ExecutionError, match="more than one party"):
        resolve(entities)


def test_two_roles_held_by_one_person_are_one_candidate(mocker, entities):
    """A model owner who also owns the dataset is not two collectors"""
    # Arrange
    entities["dataset"].owner = MODEL_OWNER_ID
    both = [Party.DATA_OWNER, Party.MODEL_OWNER]
    set_policies(mocker, both, both)

    # Act
    collector = resolve(entities)

    # Assert
    assert collector.user_id == MODEL_OWNER_ID


def test_a_collector_with_nowhere_to_receive_results_is_refused(
    mocker, entities, somebody_else
):
    """The workload has to be told where to write, and only they can say"""
    # Arrange
    set_policies(mocker, [Party.MODEL_OWNER], [Party.MODEL_OWNER])
    somebody_else.get_user_metadata.return_value = {}

    # Act & Assert
    with pytest.raises(ExecutionError, match="not configured anywhere"):
        resolve(entities)


def test_the_role_alone_costs_no_certificate_or_settings_lookup(mocker, entities):
    """Whoever only needs to know *who* collects -- to refuse reporting
    results that are not theirs, say -- should not pay for the key and the
    store as well"""
    # Arrange
    set_policies(mocker, [Party.MODEL_OWNER], [Party.MODEL_OWNER])
    certificate = mocker.patch(PATCH_COLLECTOR.format("certificate_of"))

    # Act
    user_id, party = collector_role(
        entities["benchmark"], entities["dataset"], entities["model"]
    )

    # Assert
    assert (user_id, party) == (MODEL_OWNER_ID, Party.MODEL_OWNER)
    certificate.assert_not_called()
