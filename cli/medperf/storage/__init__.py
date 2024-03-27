import os
import shutil

from medperf import config
from medperf.config_management import read_config, write_config

from .utils import full_folder_path


def override_storage_config_paths():
    for folder in config.storage:
        setattr(config, folder, full_folder_path(folder))


def init_storage():
    """Builds the general medperf folder structure."""
    for folder in config.storage:
        folder = getattr(config, folder)
        os.makedirs(folder, exist_ok=True)


def apply_configuration_migrations():
    if not os.path.exists(config.config_path):
        return

    config_p = read_config()

    if "logs_folder" not in config_p.storage:
        return

    src_dir = os.path.join(config_p.storage["logs_folder"], "logs")
    tgt_dir = config.logs_storage

    old_logs = os.listdir(src_dir)
    for old_log in old_logs:
        old_log_path = os.path.join(src_dir, old_log)
        shutil.move(old_log_path, tgt_dir)

    del config_p.storage["logs_folder"]

    write_config(config_p)
