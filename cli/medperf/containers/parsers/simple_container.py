from medperf.containers.parsers.parser import Parser
from medperf.exceptions import InvalidContainerSpec
from medperf.enums import ContainerTypes
import logging
import shlex

# Combined validation+statistics MedPerf task. It must start the in-container
# workflow at the sanity_check step (which then runs Statistics).
STATISTICS_TASK = "statistics"
SANITY_CHECK_START_ARG = "--start=sanity_check"


class SimpleContainerParser(Parser):
    def __init__(self, container_config: dict, allowed_runners: list):
        self.container_config = container_config
        self.allowed_runners = allowed_runners
        self.container_type = container_config["container_type"]

    def check_schema(self) -> str:
        if "image" not in self.container_config:
            raise InvalidContainerSpec("Container config should have an 'image' field.")

        if "tasks" not in self.container_config:
            raise InvalidContainerSpec("Container config should have a 'tasks' field.")

        for task in self.container_config["tasks"]:
            task_info = self.container_config["tasks"][task]
            volumes = {
                **task_info.get("input_volumes", {}),
                **task_info.get("output_volumes", {}),
            }
            for volume_label, volume in volumes.items():
                if "type" not in volume or "mount_path" not in volume:
                    raise InvalidContainerSpec(
                        "Container config task volumes should have a 'type' and 'mount_path' fields."
                    )
                if volume["type"] not in ["file", "directory"]:
                    logging.debug(f"Volume type for task {task}: {volume['type']}")
                    raise InvalidContainerSpec(
                        "Mount type should be either a file or a directory."
                    )

        self._check_data_preparator_constraints()

    def _check_data_preparator_constraints(self):
        tasks = self.container_config.get("tasks", {})
        if "prepare" not in tasks:
            return

        if STATISTICS_TASK not in tasks:
            raise InvalidContainerSpec(
                "Data preparator containers must define 'statistics' "
                "alongside 'prepare'."
            )

        if "sanity_check" in tasks:
            raise InvalidContainerSpec(
                "Data preparator containers must run sanity checks as part of "
                "'statistics' (via --start=sanity_check), not as a separate "
                "'sanity_check' task."
            )

        if "check_no_prepare" in tasks:
            raise InvalidContainerSpec(
                "Data preparator containers must use the 'statistics' task "
                "(not 'check_no_prepare') for sanity checks and statistics."
            )

        stats_task = tasks[STATISTICS_TASK]
        command = stats_task.get("run_args", {}).get("command", "")
        if SANITY_CHECK_START_ARG not in self._tokenize_command(command):
            raise InvalidContainerSpec(
                "Data preparator 'statistics' task command must include "
                f"'{SANITY_CHECK_START_ARG}'."
            )

        stats_outputs = stats_task.get("output_volumes", {})
        if "output_path" not in stats_outputs:
            raise InvalidContainerSpec(
                "Data preparator 'statistics' task must define an 'output_path' "
                "output volume for generated statistics."
            )

    @staticmethod
    def _tokenize_command(command) -> list:
        """Normalize a task command into tokens.

        Container commands may be given as a shell string or a pre-split list
        (both are accepted by the runners), so mirror that here instead of
        assuming a string.
        """
        if isinstance(command, str):
            return shlex.split(command)
        if isinstance(command, (list, tuple)):
            return [str(token) for token in command]
        raise InvalidContainerSpec(
            "Data preparator 'statistics' task 'command' must be a string " "or a list."
        )

    def check_task_schema(self, task: str) -> str:
        tasks = self.container_config["tasks"]
        logging.debug(f"Available tasks: {tasks}")
        if task not in tasks:
            raise InvalidContainerSpec(f"Task {task} is not found in container config.")

    def get_setup_args(self) -> str:
        return self.container_config["image"]

    def get_volumes(self, task: str, medperf_mounts: dict):
        task_info = self.container_config["tasks"][task]
        input_volumes = []
        output_volumes = []

        if "input_volumes" in task_info:
            logging.debug("Setting input volumes")
            for key in task_info["input_volumes"]:
                host_path = medperf_mounts[key]
                input_volumes.append(
                    {"host_path": host_path, **task_info["input_volumes"][key]}
                )

        if "output_volumes" in task_info:
            logging.debug("Setting output volumes")
            for key in task_info["output_volumes"]:
                host_path = medperf_mounts[key]
                output_volumes.append(
                    {"host_path": host_path, **task_info["output_volumes"][key]}
                )
        return input_volumes, output_volumes

    def get_run_args(self, task: str):
        task_info = self.container_config["tasks"][task]
        run_args = task_info.get("run_args", {})
        logging.debug(f"run args: {run_args}")
        return run_args

    def is_report_specified(self):
        try:
            return (
                "report_file"
                in self.container_config["tasks"]["prepare"]["output_volumes"]
            )
        except KeyError:
            return False

    def is_metadata_specified(self):
        try:
            return (
                "metadata_path"
                in self.container_config["tasks"]["prepare"]["output_volumes"]
            )
        except KeyError:
            return False

    def is_container_encrypted(self):
        encrypted_types = [
            ContainerTypes.ENCRYPTED_DOCKER_ARCHIVE.value,
            ContainerTypes.ENCRYPTED_SINGULARITY_FILE.value,
        ]
        return self.container_type in encrypted_types

    def is_docker_archive(self):
        file_types = [
            ContainerTypes.ENCRYPTED_DOCKER_ARCHIVE.value,
            ContainerTypes.DOCKER_ARCHIVE.value,
        ]
        return self.container_type in file_types

    def is_singularity_file(self):
        file_types = [
            ContainerTypes.ENCRYPTED_SINGULARITY_FILE.value,
            ContainerTypes.SINGULARITY_FILE.value,
        ]
        return self.container_type in file_types

    def is_docker_image(self):
        file_types = [
            ContainerTypes.DOCKER_IMAGE.value,
        ]
        return self.container_type in file_types

    def is_model_container(self):
        return "infer" in self.container_config["tasks"]

    def is_script_container(self):
        return "run_script" in self.container_config["tasks"]
