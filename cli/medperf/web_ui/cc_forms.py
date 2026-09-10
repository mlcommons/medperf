"""Rendering and reading a confidential computing configuration form.

Which settings there are depends on the backend the user picked, and only
`medperf_cc` knows what any backend needs. The web UI asks it, offers what comes
back, and posts it as-is: adding a provider adds no code here.
"""

from typing import Optional

from medperf_cc.backends import service_config

BACKEND_FIELD = "backend"


def backend_settings_from_form(form, backends: dict, prefix: str = "") -> dict:
    """The configuration a submitted form describes.

    Fields are namespaced by backend, so switching the selector does not carry
    a half-filled form for another provider along with it."""
    backend = form.get(f"{prefix}{BACKEND_FIELD}")
    if not backend or backend not in backends:
        return {}

    settings = {BACKEND_FIELD: backend}
    for field in backends[backend]:
        value = form.get(f"{prefix}{backend}__{field['name']}")
        if value not in (None, ""):
            settings[field["name"]] = value
    return settings


def service_settings(cc_config: Optional[dict], service: str) -> dict:
    """What one service is currently configured with, shared level included."""
    return service_config(cc_config or {}, service)


def selected_backend(cc_config: Optional[dict], service: str = None) -> str:
    """Which backend a stored configuration is using, if any."""
    if service:
        return service_settings(cc_config, service).get(BACKEND_FIELD, "")
    return (cc_config or {}).get(BACKEND_FIELD, "")


def field_label(name: str) -> str:
    """A setting's name as a person would read it."""
    return name.replace("_", " ").capitalize()
