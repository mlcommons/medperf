from .docker_runner import DockerRunner
from .singularity_runner import SingularityRunner
from .airflow_runner import AirflowRunner
from medperf import config
from medperf.exceptions import InvalidArgumentError
from medperf.containers.parsers.airflow_parser import AirflowParser


def load_runner(container_config_parser, container_files_base_path, container_name):
    if config.platform not in container_config_parser.allowed_runners:
        raise InvalidArgumentError(f"Cannot run this container using {config.platform}")

    if isinstance(container_config_parser, AirflowParser):
        return AirflowRunner(
            container_config_parser, container_files_base_path, container_name
        )
    if config.platform == "docker":
        return DockerRunner(container_config_parser)
    if config.platform == "singularity":
        return SingularityRunner(container_config_parser, container_files_base_path)

    # TODO: this check should happen at the beginning of any command
    raise InvalidArgumentError(f"Invalid container platform: {config.platform}")
