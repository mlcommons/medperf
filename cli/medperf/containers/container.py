from medperf.containers.runners import DockerRunner, SingularityRunner
from medperf import config
from medperf.exceptions import InvalidArgumentError


def load_runner(container_file_path: str):
    if config.platform == "docker":
        return DockerRunner(container_file_path)
    if config.platform == "singularity":
        return SingularityRunner(container_file_path)

    # TODO: this check should happen at the beginning of any command
    raise InvalidArgumentError(f"Invalid container platform: {config.platform}")
