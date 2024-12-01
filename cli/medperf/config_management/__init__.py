from .config_management import config, Auth0Settings  # noqa
from medperf import settings
import os


def _init_config():
    """builds the initial configuration file"""

    default_profile = settings.default_profile.copy()
    # default_profile["ui"] = settings.default_ui

    config_p = config

    # default profile
    config_p[settings.default_profile_name] = default_profile

    # testauth profile
    config_p[settings.testauth_profile_name] = {
        **default_profile,
        "server": settings.local_server,
        "certificate": settings.local_certificate,
        "auth_audience": settings.auth_dev_audience,
        "auth_domain": settings.auth_dev_domain,
        "auth_jwks_url": settings.auth_dev_jwks_url,
        "auth_idtoken_issuer": settings.auth_dev_idtoken_issuer,
        "auth_client_id": settings.auth_dev_client_id,
    }

    # local profile
    config_p[settings.test_profile_name] = {
        **default_profile,
        "server": settings.local_server,
        "certificate": settings.local_certificate,
        "auth_class": "Local",
        "auth_audience": "N/A",
        "auth_domain": "N/A",
        "auth_jwks_url": "N/A",
        "auth_idtoken_issuer": "N/A",
        "auth_client_id": "N/A",
    }

    # storage
    config_p.storage = {
        folder: settings.storage[folder]["base"] for folder in settings.storage
    }

    config_p.activate(settings.default_profile_name)

    os.makedirs(settings.config_storage, exist_ok=True)
    config_p.write_config()


def setup_config():
    if not os.path.exists(settings.config_path):
        _init_config()

    # Set current active profile parameters
    config.read_config()
    # for param in config_p.active_profile:
    #     setattr(settings, param, config_p.active_profile[param])

    # Set storage parameters
    for folder in config.storage:
        settings.storage[folder]["base"] = config.storage[folder]
