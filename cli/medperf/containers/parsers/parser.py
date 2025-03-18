from abc import ABC, abstractmethod


class Parser(ABC):
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
