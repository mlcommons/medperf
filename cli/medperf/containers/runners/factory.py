from .docker_runner import DockerRunner
from .singularity_runner import SingularityRunner
from medperf import config
from medperf.exceptions import InvalidArgumentError
import logging


def load_runner(container_config_parser):
    if config.platform not in container_config_parser.allowed_runners:
        logging.debug(f"Allowed runners: {container_config_parser.allowed_runners}")
        raise InvalidArgumentError(f"Cannot run this container using {config.platform}")

    if config.launcher not in ("local", "slurm"):
        raise InvalidArgumentError(f"Invalid launcher: {config.launcher}")

    if config.launcher == "slurm" and config.platform != "singularity":
        # Docker containers are started by the Docker daemon, outside the Slurm
        # job's processes and cgroup, so Slurm could neither confine nor track them.
        raise InvalidArgumentError(
            "The slurm launcher requires '--platform singularity'."
        )

    if config.platform == "docker":
        return DockerRunner(container_config_parser)
    if config.platform == "singularity":
        return SingularityRunner(container_config_parser)

    # TODO: this check should happen at the beginning of any command
    raise InvalidArgumentError(f"Invalid container platform: {config.platform}")
