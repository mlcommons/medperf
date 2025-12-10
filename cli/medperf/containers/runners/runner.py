from abc import ABC, abstractmethod
from typing import Union, Dict


class Runner(ABC):
    @abstractmethod
    def download(
        self,
        expected_image_hash: Union[str, Dict[str, str]],
        download_timeout: int = None,
        get_hash_timeout: int = None,
    ) -> Union[str, Dict[str, str]]:
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
        container_decryption_key_file: str = None,
    ):
        pass

    @property
    def is_workflow(self):
        """Can be overriden for workflow runners"""
        return False
