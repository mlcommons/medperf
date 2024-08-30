import os

from medperf import settings
from medperf.comms.factory import CommsFactory
from medperf.config_management import setup_config
from medperf.logging import setup_logging
from medperf.storage import (
    apply_configuration_migrations,
    init_storage,
    override_storage_config_paths,
)
from medperf.ui.factory import UIFactory


def initialize():
    # Apply any required migration
    apply_configuration_migrations()

    # setup config
    setup_config()

    # Initialize storage
    override_storage_config_paths()
    init_storage()

    # Setup logging
    log_file = os.path.join(settings.logs_storage, settings.log_file)
    setup_logging(log_file, settings.loglevel)

    # Setup UI, COMMS
    settings.ui = UIFactory.create_ui(settings.ui)
    settings.comms = CommsFactory.create_comms(settings.comms, settings.server)

    # Setup auth class
    if settings.auth_class == "Auth0":
        from .comms.auth import Auth0

        settings.auth = Auth0()
    elif settings.auth_class == "Local":
        from .comms.auth import Local

        settings.auth = Local()
    else:
        raise ValueError(f"Unknown Auth class {settings.auth_class}")
