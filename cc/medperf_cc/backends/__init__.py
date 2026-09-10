"""Choosing which backend provides a service, from configuration alone.

A caller never names a backend. It hands over the configuration an asset or an
operator carries, and the service it wants -- storage, vault or runner -- and
what answers is whatever that configuration selected.

Configuration is read in two layers. Keys at the top level are shared by every
service, because one provider usually wants the same account and project for
all of them, and a section named after a service adds to or overrides them --
including the backend itself, so an asset's two halves need not be with the
same provider:

    {"backend": "gcp", "project_id": "p", "bucket": "b", ...}

    {"backend": "gcp", "project_id": "p", "bucket": "b",
     "vault": {"keyring_name": "medperf", "key_location": "us-west1"}}
"""

from typing import Dict

from medperf_cc.errors import ConfigurationError

# The services an asset's own configuration can carve out a section for. The
# runner is not among them: it is the operator's, configured separately, and
# has nothing to share a top level with.
ASSET_SERVICES = ("storage", "vault")


def service_config(config: dict, service: str) -> dict:
    """The configuration one service sees: the shared level, then its own."""
    shared = {
        key: value
        for key, value in (config or {}).items()
        if key not in ASSET_SERVICES
    }
    return {**shared, **((config or {}).get(service) or {})}


def backend_of(config: dict, registry: Dict[str, type], service: str) -> str:
    """The backend a configuration names for a service.

    An unnamed one is refused rather than guessed: guessing would send an asset
    somewhere its owner never chose, and one of the choices protects nothing at
    all. An unknown one is refused for the same reason."""
    backend = (config or {}).get("backend")
    if backend is None:
        raise ConfigurationError(
            f"No {service} backend selected."
            f" Set \"backend\" to one of: {', '.join(sorted(registry))}"
        )
    if backend not in registry:
        raise ConfigurationError(
            f"Unknown {service} backend {backend!r}."
            f" Supported: {', '.join(sorted(registry))}"
        )
    return backend


def settings_of(config: dict) -> dict:
    """The configuration a backend receives, without the name that chose it."""
    return {key: value for key, value in (config or {}).items() if key != "backend"}


def describe(registry: Dict[str, type]) -> Dict[str, list]:
    """The settings each backend in a registry takes.

    So a user interface can offer them without knowing what any of them are.
    Each entry is `{"name": ..., "required": ...}`; a backend that grows a
    setting grows it here too, with nothing outside this package to change."""
    return {
        backend: [
            {"name": name, "required": field.required}
            for name, field in implementation.SETTINGS.__fields__.items()
        ]
        for backend, implementation in registry.items()
    }
