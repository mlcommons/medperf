from medperf.exceptions import InvalidContainerSpec
from .parser import Parser
from .simple_container import SimpleContainerParser
from medperf.enums import ContainerTypes
import logging
from .airflow_parser import AirflowParser

DOCKER_TYPES = [
    ContainerTypes.DOCKER_IMAGE.value,
    ContainerTypes.DOCKER_ARCHIVE.value,
    ContainerTypes.ENCRYPTED_DOCKER_ARCHIVE.value,
]
SINGULARITY_TYPES = [
    ContainerTypes.SINGULARITY_FILE.value,
    ContainerTypes.ENCRYPTED_SINGULARITY_FILE.value,
]


def _is_airflow_yaml_file(airflow_config: dict):
    return "container_type" not in airflow_config and "steps" in airflow_config


def load_parser(container_config: dict, container_files_base_path: str) -> Parser:

    if _is_airflow_yaml_file(container_config):
        # TODO add modifications to use container hashes rather than tags for download
        parser = AirflowParser(
            airflow_config=container_config,
            allowed_runners=["docker", "singularity"],
            container_files_base_path=container_files_base_path,
        )
        parser.check_schema()
        return parser

    elif container_config is None:
        raise InvalidContainerSpec("Empty container configuration")

    elif "container_type" not in container_config:
        raise InvalidContainerSpec(
            "Container configuration should contain a 'container_type' field."
        )

    container_type = container_config["container_type"]
    logging.debug(f"Container type: {container_type}")
    if container_type in DOCKER_TYPES:
        logging.debug("Found a docker type")
        parser = SimpleContainerParser(
            container_config, allowed_runners=["docker", "singularity"]
        )
        parser.check_schema()
        return parser

    if container_type in SINGULARITY_TYPES:
        logging.debug("Found a singularity type")
        parser = SimpleContainerParser(
            container_config, allowed_runners=["singularity"]
        )
        parser.check_schema()
        return parser

    expected = ", ".join([c.value for c in ContainerTypes])
    raise InvalidContainerSpec(
        f"Invalid container type: {container_type}. Expected: {expected}"
    )
