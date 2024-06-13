import os
import shutil

from medperf import config
from medperf.config_management import read_config, write_config, ConfigManager

from .utils import full_folder_path


def override_storage_config_paths():
    for folder in config.storage:
        setattr(config, folder, full_folder_path(folder))


def init_storage():
    """Builds the general medperf folder structure."""
    for folder in config.storage:
        folder = getattr(config, folder)
        os.makedirs(folder, exist_ok=True)


def __apply_logs_migrations(config_p: ConfigManager):
    if "logs_folder" not in config_p.storage:
        return

    src_dir = os.path.join(config_p.storage["logs_folder"], "logs")
    tgt_dir = config.logs_storage

    shutil.move(src_dir, tgt_dir)

    del config_p.storage["logs_folder"]


def __apply_training_migrations(config_p: ConfigManager):

    for folder in [
        "aggregators_folder",
        "cas_folder",
        "training_events_folder",
        "training_folder",
    ]:
        if folder not in config_p.storage:
            # Assuming for now all folders are always moved together
            # I used here "benchmarks_folder" arbitrarily
            config_p.storage[folder] = config_p.storage["benchmarks_folder"]


def apply_configuration_migrations():
    if not os.path.exists(config.config_path):
        return

    config_p = read_config()
    __apply_logs_migrations(config_p)
    __apply_training_migrations(config_p)

    write_config(config_p)
