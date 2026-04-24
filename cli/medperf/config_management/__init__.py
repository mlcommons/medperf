from .config_management import ConfigManager, read_config, write_config  # noqa
from medperf import config
import os


def _init_config():
    """builds the initial configuration file"""

    default_profile = {
        param: getattr(config, param) for param in config.configurable_parameters
    }
    config_p = ConfigManager()

    # default profile
    config_p[config.default_profile_name] = default_profile

    # testauth profile
    config_p[config.testauth_profile_name] = {
        **default_profile,
        "server": config.local_server,
        "certificate": config.local_certificate,
        "auth_audience": config.auth_dev_audience,
        "auth_domain": config.auth_dev_domain,
        "auth_jwks_url": config.auth_dev_jwks_url,
        "auth_idtoken_issuer": config.auth_dev_idtoken_issuer,
        "auth_client_id": config.auth_dev_client_id,
        "certificate_authority_id": config.dev_certificate_authority_id,
        "certificate_authority_fingerprint": config.dev_certificate_authority_fingerprint,
    }

    # local profile
    config_p[config.test_profile_name] = {
        **default_profile,
        "server": config.local_server,
        "certificate": config.local_certificate,
        "auth_class": "Local",
        "auth_audience": "N/A",
        "auth_domain": "N/A",
        "auth_jwks_url": "N/A",
        "auth_idtoken_issuer": "N/A",
        "auth_client_id": "N/A",
        "certificate_authority_id": config.dev_certificate_authority_id,
        "certificate_authority_fingerprint": config.dev_certificate_authority_fingerprint,
    }

    # storage
    config_p.storage = {
        folder: config.storage[folder]["base"] for folder in config.storage
    }

    config_p.activate(config.default_profile_name)

    os.makedirs(config.config_storage, exist_ok=True)
    write_config(config_p)


def setup_config():
    if not os.path.exists(config.config_path):
        _init_config()

    # Set current active profile parameters
    config_p = read_config()
    for param in config_p.active_profile:
        setattr(config, param, config_p.active_profile[param])

    # Set storage parameters
    for folder in config_p.storage:
        config.storage[folder]["base"] = config_p.storage[folder]
