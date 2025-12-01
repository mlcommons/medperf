from .docker_runner import DockerRunner
from .singularity_runner import SingularityRunner
from medperf import config
from medperf.exceptions import InvalidArgumentError
import logging


def load_runner(container_config_parser):
    if config.platform not in container_config_parser.allowed_runners:
        logging.debug(f"Allowed runners: {container_config_parser.allowed_runners}")
        raise InvalidArgumentError(f"Cannot run this container using {config.platform}")

    if config.platform == "docker":
        return DockerRunner(container_config_parser)
    if config.platform == "singularity":
        return SingularityRunner(container_config_parser)

    # TODO: this check should happen at the beginning of any command
    raise InvalidArgumentError(f"Invalid container platform: {config.platform}")
