import os

from medperf import config
from medperf.comms.factory import CommsFactory
from medperf.config_management import setup_config
from medperf.logging import setup_logging
from medperf.storage import (
    apply_configuration_migrations,
    init_storage,
    override_storage_config_paths,
)
from medperf.ui.factory import UIFactory


def initialize(for_webui=False, for_data_monitor=False):
    if not for_webui:
        log_file_name = config.log_file
        ui_class = config.ui
    else:
        log_file_name = config.webui_log_file
        ui_class = config.webui
    if for_data_monitor:
        log_file_name = config.data_monitor_log_file
    # Apply any required migration
    apply_configuration_migrations()

    # setup config
    setup_config()

    # Initialize storage
    override_storage_config_paths()
    init_storage()

    # Setup logging
    log_file = os.path.join(config.logs_storage, log_file_name)
    setup_logging(log_file, config.loglevel)

    # Setup UI, COMMS
    config.ui = UIFactory.create_ui(ui_class)
    config.comms = CommsFactory.create_comms(config.comms, config.server)

    # Setup auth class
    if config.auth_class == "Auth0":
        from .comms.auth import Auth0

        config.auth = Auth0()
    elif config.auth_class == "Local":
        from .comms.auth import Local

        config.auth = Local()
    else:
        raise ValueError(f"Unknown Auth class {config.auth_class}")
