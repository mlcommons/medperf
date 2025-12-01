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
    def get_run_args(self, task: str):
        pass

    @abstractmethod
    def is_report_specified(self):
        pass

    @abstractmethod
    def is_metadata_specified(self):
        pass

    @abstractmethod
    def is_container_encrypted(self):
        pass

    @abstractmethod
    def is_docker_archive(self):
        pass

    @abstractmethod
    def is_singularity_file(self):
        pass

    @abstractmethod
    def is_docker_image(self):
        pass
