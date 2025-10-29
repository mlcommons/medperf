from typing import Optional
from medperf.exceptions import InvalidContainerSpec, MedperfException
from medperf import config
import os


def check_allowed_run_args(run_args):
    allowed_keys = {"shm_size", "gpus", "command", "entrypoint", "environment"}
    given_keys = set(run_args.keys())
    not_allowed_keys = given_keys.difference(allowed_keys)
    if not_allowed_keys:
        raise InvalidContainerSpec(
            f"Run args {', '.join(not_allowed_keys)} are not allowed."
        )


def add_medperf_run_args(run_args):
    run_args["user"] = f"{os.getuid()}:{os.getgid()}"
    run_args["remove_container"] = True


def add_user_defined_run_args(run_args):
    # shm_size
    if config.shm_size is not None:
        run_args["shm_size"] = config.shm_size

    # gpus
    gpus = run_args.get("gpus")
    if config.gpus is not None:
        gpus = config.gpus
    run_args["gpus"] = _normalize_gpu_arg(gpus)


def _normalize_gpu_arg(gpus: Optional[str]):
    if gpus is None or gpus == "":
        return

    if gpus == "all":
        return "all"

    if isinstance(gpus, int):
        if gpus == 0:
            return
        return gpus

    if isinstance(gpus, str):
        if gpus.isnumeric():
            if gpus == "0":
                return
            return int(gpus)
        if gpus.startswith("device="):
            gpus = gpus[len("device=") :]  # noqa
            if gpus:
                ids = gpus.split(",")
                return ids
    raise InvalidContainerSpec("Invalid gpus argument")


def add_medperf_environment_variables(run_args, medperf_env):
    env_dict: dict = run_args.get("environment", {})
    env_dict.update(medperf_env)
    run_args["environment"] = env_dict


def add_network_config(run_args, disable_network, ports):
    if disable_network and ports:
        raise MedperfException(
            "Internal error: ports is specified but disable_network is True"
        )
    if disable_network:
        run_args["network"] = "none"
        return

    for port in ports:
        if not isinstance(port, str) or port.count(":") != 2:
            raise MedperfException(
                "Internal error: Port should be in the format"
                " {interface}:{host_port}:{container_port}."
                f" Got {port}."
            )

    run_args["ports"] = ports


def add_medperf_tmp_folder(output_volumes, tmp_folder):
    output_volumes.append(
        {"host_path": tmp_folder, "mount_path": "/tmp", "type": "directory"}
    )


def check_docker_image_hash(
    computed_image_hash, expected_image_hash=None, alternative_image_hash=None
):
    if expected_image_hash and expected_image_hash != computed_image_hash:
        # try with digest if possible
        # This fixes an issue with newer docker versions where inspect returns
        # the digest instead of the image ID. The cleaner fix will require changing how
        # we define the image hash.
        if alternative_image_hash is None:
            raise InvalidContainerSpec(
                f"Hash mismatch. Expected {expected_image_hash}, found {computed_image_hash}."
            )
        if alternative_image_hash != computed_image_hash:
            raise InvalidContainerSpec(
                f"Hash mismatch. Expected {expected_image_hash} or"
                f" {alternative_image_hash}, found {computed_image_hash}."
            )
