from medperf.containers.parsers.parser import Parser
from medperf.exceptions import InvalidContainerSpec


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
                    raise InvalidContainerSpec(
                        "Mount type should be either a file or a directory."
                    )

    def check_task_schema(self, task: str) -> str:
        tasks = self.container_config["tasks"]
        if task not in tasks:
            raise InvalidContainerSpec(f"Task {task} is not found in container config.")

    def get_setup_args(self) -> str:
        return self.container_config["image"]

    def get_volumes(self, task: str, medperf_mounts: dict):
        task_info = self.container_config["tasks"][task]
        input_volumes = []
        output_volumes = []

        if "input_volumes" in task_info:
            for key in task_info["input_volumes"]:
                host_path = medperf_mounts[key]
                input_volumes.append(
                    {"host_path": host_path, **task_info["input_volumes"][key]}
                )

        if "output_volumes" in task_info:
            for key in task_info["output_volumes"]:
                host_path = medperf_mounts[key]
                output_volumes.append(
                    {"host_path": host_path, **task_info["output_volumes"][key]}
                )
        return input_volumes, output_volumes

    def get_run_args(self, task: str, medperf_mounts: dict):
        task_info = self.container_config["tasks"][task]
        return task_info.get("run_args", {})

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
