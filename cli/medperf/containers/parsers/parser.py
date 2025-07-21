from abc import ABC, abstractmethod


class Parser(ABC):

    def __init__(self, container_config: dict, allowed_runners: list):
        self.container_config = container_config
        self.allowed_runners = allowed_runners

    @property
    @abstractmethod
    def container_type(self):
        pass
    
    @abstractmethod
    def check_schema(self):
        pass

    @abstractmethod
    def check_task_schema(self, task: str):
        pass

    @abstractmethod
    def get_setup_args(self):
        pass

    @abstractmethod
    def get_volumes(self, task: str, medperf_mounts: dict):
        pass

    @abstractmethod
    def get_run_args(self, task: str, medperf_mounts: dict):
        pass

    @abstractmethod
    def is_report_specified(self):
        pass

    @abstractmethod
    def is_metadata_specified(self):
        pass
