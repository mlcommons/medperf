from medperf.exceptions import InvalidContainerSpec
from .parser import Parser
import os
from .mlcube import MLCubeParser
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


def _is_mlcube_yaml_file(container_config: dict):
    # new container files have "container_type" key
    # otherwise, it's an mlcube definition file
    return "container_type" not in container_config and (
        "docker" in container_config or "singularity" in container_config
    )


def load_parser(container_config: dict, container_files_base_path: os.PathLike) -> Parser:
    if container_config is None:
        raise InvalidContainerSpec(
            f"Empty container config file: {container_config}"
        )

    if _is_mlcube_yaml_file(container_config):
        # add workspace_path to the container configuration dict
        # this is necessary given how mlcube used to parse the file
        workspace_path = os.path.join(
            container_files_base_path, "workspace"
        )
        container_config["workspace_path"] = workspace_path
        parser = MLCubeParser(
            container_config, allowed_runners=["docker", "singularity"]
        )
        parser.check_schema()
        return parser

    if "container_type" not in container_config:
        raise InvalidContainerSpec(
            f"Container config file should contain a 'container_type' field.\n{container_config}"
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
