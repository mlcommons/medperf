"""An asset's whole lifecycle, on the backend that needs no cloud account.

The mock backends exist so this can run anywhere, and so that the abstraction
has a second implementation keeping it honest: anything these tests reach for
that only Google Cloud could provide is a leak.
"""

import io
import json
import os

import pytest

from medperf_cc import AssetKind, ConfidentialAsset, Party, WorkloadGrant
from medperf_cc.backends.mock import MOCK, PERMITTED_FILE
from medperf_cc.storage.mock import ASSET_FILE
from medperf_cc.vault.mock import KEY_FILE

from tests.conftest import any_policy

CIPHERTEXT = b"not really encrypted, but the vault never looks"
KEY = b"0123456789abcdef0123456789abcdef"


@pytest.fixture()
def config(tmp_path):
    return {"backend": MOCK, "root": str(tmp_path / "cc")}


def workload(data_hash="datahash", collector_hash="collectorhash"):
    return WorkloadGrant(
        script_hash="scripthash",
        model_hash="modelhash",
        data_hash=data_hash,
        result_collector_hash=collector_hash,
    )


def published(config, kind=AssetKind.DATA, policy=None):
    asset = ConfidentialAsset(config, "dataset3", kind, policy or any_policy())
    asset.verify()
    asset.publish(KEY, io.BytesIO(CIPHERTEXT))
    return asset


def test_the_key_and_the_ciphertext_are_published_apart(config):
    asset = published(config)

    assert asset.storage.store.read(ASSET_FILE) == CIPHERTEXT
    assert asset.vault.store.read(KEY_FILE) == KEY


def test_both_halves_are_told_who_may_open_the_asset(config):
    """Reading the ciphertext and holding the key are two grants, even where
    one provider happens to give both"""
    asset = published(config)

    asset.set_permitted([workload()])

    assert asset.storage.store.permitted() == asset.vault.store.permitted()
    assert asset.storage.store.permitted() == [asset.scope.uid_of(workload())]


def test_repeated_identities_collapse(config):
    asset = published(config)

    asset.set_permitted([workload(), workload(), workload()])

    assert len(asset.vault.store.permitted()) == 1


def test_not_pinning_the_peer_collapses_what_it_no_longer_distinguishes(config):
    """Two workloads differing only in data are one grant to an owner who chose
    not to pin the data"""
    policy = any_policy(bind_peer_asset=False)
    asset = ConfidentialAsset(config, "model4", AssetKind.MODEL, policy)

    asset.set_permitted([workload(), workload(data_hash="other")])

    assert asset.vault.store.permitted() == ["scripthash::modelhash::collectorhash"]


def test_pinning_the_peer_keeps_them_apart(config):
    """Which is what an unconfigured policy does, for either kind of asset"""
    asset = ConfidentialAsset(config, "dataset3", AssetKind.DATA, any_policy())

    asset.set_permitted([workload(), workload(data_hash="other")])

    assert len(asset.vault.store.permitted()) == 2


def test_a_sync_that_leaves_an_identity_out_takes_it_away(config):
    """The whole of how a grant is revoked"""
    asset = published(config)
    asset.set_permitted([workload()])

    asset.set_permitted([])

    assert asset.vault.store.permitted() == []


def test_the_workload_is_told_where_both_halves_are(config):
    asset = published(config)

    told = asset.workload_config()

    assert told["storage"]["backend"] == MOCK
    assert told["vault"]["backend"] == MOCK
    assert told["storage"]["asset_name"] == "dataset3"


def test_the_workload_is_told_which_terms_its_grant_is_written_over(config):
    """It has to project its own identity the same way the owner did, or the
    key it presents an identity for could never match one that was granted"""
    asset = published(
        config, kind=AssetKind.MODEL, policy=any_policy(bind_peer_asset=False)
    )

    told = asset.workload_config()

    assert told["vault"]["terms"] == ["script", "model", "collector"]


def test_a_mixed_configuration_tells_the_workload_about_both(tmp_path):
    """A dataset can live in one provider and have its key released by another,
    and the workload has to be able to reach each of them"""
    config = {
        "backend": MOCK,
        "root": str(tmp_path / "cc"),
        "vault": {
            "backend": "gcp",
            "project_id": "p",
            "project_number": "42",
            "bucket": "b",
            "keyring_name": "ring",
            "key_name": "key",
            "key_location": "us-west1",
            "wip": "pool",
            "wip_provider": "provider",
        },
    }

    told = ConfidentialAsset(
        config, "dataset3", AssetKind.DATA, any_policy()
    ).workload_config()

    assert told["storage"]["backend"] == MOCK
    assert told["vault"]["backend"] == "gcp"


def test_nothing_the_owner_configured_reaches_the_workload_unasked(tmp_path):
    """What the workload is told travels to the VM as environment the operator
    can read, so each backend names the fields it hands over rather than
    passing on whatever happens to be in the owner's configuration"""
    config = {
        "backend": MOCK,
        "root": str(tmp_path / "cc"),
        "admin_token": "the-admin-token",
    }

    told = ConfidentialAsset(config, "dataset3", AssetKind.DATA, any_policy())

    assert "the-admin-token" not in json.dumps(told.workload_config())


def test_the_policy_decides_what_the_grant_pins(config):
    narrow = ConfidentialAsset(
        config,
        "model4",
        AssetKind.MODEL,
        any_policy(bind_peer_asset=True, allowed_result_collectors=[Party.DATA_OWNER]),
    )

    narrow.set_permitted([workload()])

    assert narrow.vault.store.permitted() == [
        "scripthash::datahash::modelhash::collectorhash"
    ]


def test_publishing_twice_replaces_rather_than_accumulates(config):
    """An asset's name is derived from the entity, so a republish overwrites"""
    published(config)
    published(config)

    directory = os.path.join(config["root"], "dataset3")

    assert sorted(os.listdir(directory)) == [ASSET_FILE]


def test_permitted_identities_are_recorded_where_a_workload_could_check(config):
    asset = published(config)

    asset.set_permitted([workload()])

    assert os.path.exists(os.path.join(asset.vault.store.directory, PERMITTED_FILE))
