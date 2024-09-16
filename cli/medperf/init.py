import os

from medperf import settings
from medperf.config_management import setup_config
from medperf.logging import setup_logging
from medperf.storage import (
    apply_configuration_migrations,
    init_storage,
    override_storage_config_paths,
)


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
