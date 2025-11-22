from abc import ABC, abstractmethod


class Runner(ABC):
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
        container_decryption_key_file: str = None,
    ):
        pass
