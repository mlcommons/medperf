from abc import ABC, abstractmethod
from medperf.containers.parsers.parser import Parser


class Runner(ABC):
    def __init__(self, container_config_parser: Parser, container_files_base_path: str):
        self.parser = container_config_parser
        self.container_files_base_path = container_files_base_path

    @abstractmethod
    def download(
        self,
        expected_image_hash: str,
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        pass

    @abstractmethod
    def run(
        self,
        task: str,
        tmp_folder: str,
        output_logs: str = None,
        timeout: int = None,
        medperf_mounts: dict[str, str] = {},
        medperf_env: dict[str, str] = {},
        ports: list = [],
        disable_network: bool = True,
        image: str = None,
    ):
        pass
