import os
import shutil
import time

from medperf import settings
from medperf.config_management import config

from .utils import full_folder_path


def override_storage_config_paths():
    for folder in settings.storage:
        setattr(settings, folder, full_folder_path(folder))


def init_storage():
    """Builds the general medperf folder structure."""
    for folder in settings.storage:
        folder = getattr(settings, folder)
        os.makedirs(folder, exist_ok=True)


def apply_configuration_migrations():
    if not os.path.exists(settings.config_path):
        return

    config_p = config.read_config()

    # Migration for moving the logs folder to a new location
    if "logs_folder" not in config_p.storage:
        return

    src_dir = os.path.join(config_p.storage["logs_folder"], "logs")
    tgt_dir = settings.logs_storage

    shutil.move(src_dir, tgt_dir)

    del config_p.storage["logs_folder"]

    # Migration for tracking the login timestamp (i.e., refresh token issuance timestamp)
    if settings.credentials_keyword in config_p.active_profile:
        # So the user is logged in
        if "logged_in_at" not in config_p.active_profile[settings.credentials_keyword]:
            # Apply migration. We will set it to the current time, since this
            # will make sure they will not be logged out before the actual refresh
            # token expiration (for a better user experience). However, currently logged
            # in users will still face a confusing error when the refresh token expires.
            config_p.active_profile[settings.credentials_keyword][
                "logged_in_at"
            ] = time.time()

    config_p.write_config()
