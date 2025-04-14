from medperf.exceptions import MedperfException, InvalidContainerSpec
from .parser import Parser
import os
import yaml
from .mlcube import MLCubeParser
from .simple_container import SimpleContainerParser


def _is_mlcube_yaml_file(container_config: dict):
    # new container files have "container_type" key
    # otherwise, it's an mlcube definition file
    return "container_type" not in container_config and (
        "docker" in container_config or "singularity" in container_config
    )


def load_parser(container_config_path: str) -> Parser:
    if not os.path.exists(container_config_path):
        # Internal error
        raise MedperfException(f"{container_config_path} hasn't been downloaded yet.")

    with open(container_config_path) as f:
        container_config = yaml.safe_load(f)

    if container_config is None:
        raise InvalidContainerSpec(
            f"Empty container config file: {container_config_path}"
        )

    if _is_mlcube_yaml_file(container_config):
        # add workspace_path to the container configuration dict
        # this is necessary given how mlcube used to parse the file
        workspace_path = os.path.join(
            os.path.dirname(container_config_path), "workspace"
        )
        container_config["workspace_path"] = workspace_path
        parser = MLCubeParser(
            container_config, allowed_runners=["docker", "singularity"]
        )
        parser.check_schema()
        return parser

    if "container_type" not in container_config:
        raise InvalidContainerSpec(
            "Container config file should contain a 'container_type' field."
        )

    container_type = container_config["container_type"]
    if container_type == "DockerImage":
        parser = SimpleContainerParser(
            container_config, allowed_runners=["docker", "singularity"]
        )
        parser.check_schema()
        return parser

    if container_type == "SingularityFile":
        parser = SimpleContainerParser(
            container_config, allowed_runners=["singularity"]
        )
        parser.check_schema()
        return parser

    raise InvalidContainerSpec(f"Invalid container type: {container_type}.")
