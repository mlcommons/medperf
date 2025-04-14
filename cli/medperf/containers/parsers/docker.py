from medperf.containers.parsers.parser import Parser
from medperf.exceptions import InvalidContainerSpec


class DockerParser(Parser):
    def __init__(self, container_config: dict):
        self.container_config = container_config

    def check_schema(self) -> str:
        if "image" not in self.container_config:
            raise InvalidContainerSpec("Container config should have an 'image' field.")

        if "tasks" not in self.container_config:
            raise InvalidContainerSpec("Container config should have a 'tasks' field.")

    def check_task_schema(self, task: str) -> str:
        tasks = self.container_config["tasks"]
        if task not in tasks:
            raise InvalidContainerSpec(f"Task {task} is not found in container config.")

    def get_setup_args(self) -> str:
        return self.container_config["image"]

    def get_volumes(self, task: str, medperf_mounts: dict):
        task_info = self.container_config["tasks"][task]
        input_volumes = {}
        output_volumes = {}

        if "input_volumes" in task_info:
            for key in task_info["input_volumes"]:
                host_path = medperf_mounts[key]
                bind_path = task_info["input_volumes"][key]
                input_volumes[host_path] = bind_path

        if "output_volumes" in task_info:
            for key in task_info["output_volumes"]:
                host_path = medperf_mounts[key]
                bind_path = task_info["output_volumes"][key]
                output_volumes[host_path] = bind_path

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
