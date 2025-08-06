from .singularity_runner import SingularityRunner
from .private_runner import PrivateRunner
from medperf.enums import ContainerTypes
from medperf.utils import remove_path
from .singularity_utils import convert_docker_image_to_sif
import os


class PrivateSingularityRunner(PrivateRunner, SingularityRunner):
    def __init__(self, container_config_parser, container_files_base_path):
        super().__init__(container_config_parser, container_files_base_path)
        self._decrypted_converted_image = None  # Used when converting Docker images

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
        try:
            decrypted_image = self._decrypt_image()
            if (
                self.parser.container_type
                == ContainerTypes.encrypted_docker_image.value
            ):
                decrypted_image = self._convert_decrypted_docker_image(decrypted_image)

            super().run(
                task=task,
                tmp_folder=tmp_folder,
                output_logs=output_logs,
                timeout=timeout,
                medperf_mounts=medperf_mounts,
                medperf_env=medperf_env,
                ports=ports,
                disable_network=disable_network,
                image=decrypted_image,
            )
        finally:
            self.clean_up(decrypted_image)

    def _convert_decrypted_docker_image(self, decrypted_image_path: str):
        sif_image_folder = os.path.dirname(decrypted_image_path)
        decrypted_image_name = os.path.basename(decrypted_image_path)
        decrypted_sif_name = os.path.splitext(decrypted_image_name)[0] + ".sif"

        self._decrypted_converted_image = os.path.join(
            sif_image_folder, decrypted_sif_name
        )

        convert_docker_image_to_sif(
            sif_image_folder=sif_image_folder,
            sif_image_file=self._decrypted_converted_image,
            singularity_executable=self.executable,
            docker_image=decrypted_image_path,
            protocol="docker-archive",
        )

        remove_path(decrypted_image_path)
        return self._decrypted_converted_image

    def clean_up(self, *args):
        self._safe_remove_file(self._decrypted_converted_image)
        super().clean_up(*args)
