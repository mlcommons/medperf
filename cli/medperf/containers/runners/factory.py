from .docker_runner import DockerRunner
from .singularity_runner import SingularityRunner
from .private_docker_runner import PrivateDockerRunner
from .private_singularity_runner import PrivateSingularityRunner
from medperf import config
from medperf.exceptions import InvalidArgumentError
from medperf.containers.parsers.parser import Parser
from medperf.enums import ContainerTypes


def load_runner(container_config_parser: Parser, container_files_base_path: str):
    if config.platform not in container_config_parser.allowed_runners:
        raise InvalidArgumentError(f"Cannot run this container using {config.platform}")

    if config.platform == "docker":
        if (
            container_config_parser.container_type
            == ContainerTypes.encrypted_docker_image.value
        ):
            return PrivateDockerRunner(
                container_config_parser, container_files_base_path
            )
        else:
            return DockerRunner(container_config_parser, container_files_base_path)
    if config.platform == "singularity":
        if (
            container_config_parser.container_type
            == ContainerTypes.encrypted_singularity_file.value
        ):
            return PrivateSingularityRunner(
                container_config_parser, container_files_base_path
            )
        else:
            return SingularityRunner(container_config_parser, container_files_base_path)

    # TODO: this check should happen at the beginning of any command
    raise InvalidArgumentError(f"Invalid container platform: {config.platform}")
