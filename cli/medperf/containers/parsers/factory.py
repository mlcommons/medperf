from medperf.exceptions import InvalidContainerSpec
from .parser import Parser
from .simple_container import SimpleContainerParser
from medperf.enums import ContainerTypes
import logging

DOCKER_TYPES = [
    ContainerTypes.DOCKER_IMAGE.value,
    ContainerTypes.DOCKER_ARCHIVE.value,
    ContainerTypes.ENCRYPTED_DOCKER_ARCHIVE.value,
]
SINGULARITY_TYPES = [
    ContainerTypes.SINGULARITY_FILE.value,
    ContainerTypes.ENCRYPTED_SINGULARITY_FILE.value,
]


def load_parser(container_config: dict) -> Parser:
    if container_config is None:
        raise InvalidContainerSpec("Empty container configuration")

    if "container_type" not in container_config:
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
