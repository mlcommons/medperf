from medperf.config_management import read_config, write_config
from medperf.exceptions import InvalidArgumentError
from medperf import config
import os
import re
import shutil


def full_folder_path(folder, new_base=None):
    server_path = config.server.split("//")[1]
    server_path = re.sub(r"[.:]", "_", server_path)

    if folder in config.root_folders:
        info = config.storage[folder]
        base = new_base or info["base"]
        full_path = os.path.join(base, info["name"])

    elif folder in config.server_folders:
        info = config.storage[folder]
        base = new_base or info["base"]
        full_path = os.path.join(base, info["name"], server_path)

    return full_path


def move_storage(target_base_path: str):
    config_p = read_config()

    target_base_path = os.path.abspath(target_base_path)
    target_base_path = os.path.normpath(target_base_path)
    if os.path.basename(target_base_path) != ".medperf":
        target_base_path = os.path.join(target_base_path, ".medperf")

    # TODO: We currently rely on the permissions of the base folder
    # It might be a better practice to recursively change permissions of its contents
    if os.path.exists(target_base_path):
        os.chmod(target_base_path, 0o700)
    else:
        os.makedirs(target_base_path, 0o700)

    for folder in config.storage:
        folder_path = os.path.join(
            config.storage[folder]["base"], config.storage[folder]["name"]
        )
        target_path = os.path.join(target_base_path, config.storage[folder]["name"])

        folder_path = os.path.normpath(folder_path)
        target_path = os.path.normpath(target_path)

        if folder_path == target_path:
            continue

        if os.path.exists(target_path):
            raise InvalidArgumentError(
                "Cannot move storage to the specified location. "
                f"This folder already exists: {target_path}"
            )

        shutil.move(folder_path, target_path)
        config_p.storage[folder] = target_base_path
        write_config(config_p)
