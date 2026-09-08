"""How a configuration selects what answers.

A caller never names a backend. What it hands over is what an asset owner or an
operator wrote down, so everything below is about reading that correctly --
including refusing to guess.
"""

import pytest

from medperf_cc.backends import backend_of, service_config, settings_of
from medperf_cc.errors import ConfigurationError
from medperf_cc.runner import RUNNERS, get_runner
from medperf_cc.storage import STORAGES, get_storage
from medperf_cc.storage.gcp import GCPStorage
from medperf_cc.vault import VAULTS, get_vault
from medperf_cc.vault.mock import MockVault
from medperf_cc.identity import AssetKind
from tests.conftest import any_policy

SHARED = {"backend": "gcp", "project_id": "p", "project_number": "42", "bucket": "b"}


def test_one_backend_at_the_top_level_serves_every_service():
    """The common case: one provider, configured once"""
    assert service_config(SHARED, "storage")["backend"] == "gcp"
    assert service_config(SHARED, "vault")["backend"] == "gcp"


def test_a_service_section_overrides_the_shared_level():
    config = {**SHARED, "vault": {"backend": "mock", "root": "/tmp/x"}}

    assert service_config(config, "storage")["backend"] == "gcp"
    assert service_config(config, "vault")["backend"] == "mock"


def test_a_section_still_sees_the_shared_settings():
    """A provider usually wants the same account for everything it does"""
    config = {**SHARED, "vault": {"keyring_name": "ring"}}

    assert service_config(config, "vault")["project_id"] == "p"
    assert service_config(config, "vault")["keyring_name"] == "ring"


def test_no_service_section_leaks_into_a_backend():
    config = {**SHARED, "vault": {"backend": "mock"}}

    assert "vault" not in service_config(config, "storage")


@pytest.mark.parametrize(
    "registry,service", [(STORAGES, "storage"), (VAULTS, "vault"), (RUNNERS, "runner")]
)
def test_an_unnamed_backend_is_refused_rather_than_guessed(registry, service):
    """Falling back to a default would send an asset somewhere its owner never
    chose, and `mock` protects nothing at all"""
    with pytest.raises(ConfigurationError, match="No .* backend selected"):
        backend_of({}, registry, service)


@pytest.mark.parametrize(
    "registry,service", [(STORAGES, "storage"), (VAULTS, "vault"), (RUNNERS, "runner")]
)
def test_an_unknown_backend_is_refused(registry, service):
    with pytest.raises(ConfigurationError, match="Unknown"):
        backend_of({"backend": "typo"}, registry, service)


def test_the_name_that_chose_a_backend_is_not_passed_on_to_it():
    assert settings_of({"backend": "mock", "root": "/tmp/x"}) == {"root": "/tmp/x"}


def test_each_service_resolves_on_its_own():
    """An asset's two halves need not be with the same provider"""
    storage = get_storage(
        {**SHARED, "wip": "pool", "wip_provider": "provider"}, "dataset1"
    )
    vault = get_vault(
        {"backend": "mock", "root": "/tmp/x"},
        "dataset1",
        any_policy().scope(AssetKind.DATA),
        any_policy(),
    )

    assert isinstance(storage, GCPStorage)
    assert isinstance(vault, MockVault)


def test_a_runner_resolves_the_same_way():
    assert get_runner({"backend": "mock", "root": "/tmp/x"}).backend == "mock"
