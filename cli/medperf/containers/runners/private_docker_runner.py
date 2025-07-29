from .docker_runner import DockerRunner
from .private_runner import PrivateRunner
from medperf.utils import remove_path
import tarfile
import json
from .utils import run_command, delete_docker_containers_and_image


class PrivateDockerRunner(PrivateRunner, DockerRunner):
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
            image_digests_list = []
            decrypted_image_archive = self.decrypt_image()

            # Usually there will be only one digest, but this should be somewhat robust if there are more
            image_digests_list = self.get_image_digests_from_archive(
                decrypted_image_archive
            )
            main_image_digest = image_digests_list[0]

            self.load_image(decrypted_image_archive)
            remove_path(decrypted_image_archive)

            super().run(
                task=task,
                tmp_folder=tmp_folder,
                output_logs=output_logs,
                timeout=timeout,
                medperf_mounts=medperf_mounts,
                medperf_env=medperf_env,
                ports=ports,
                disable_network=disable_network,
                image=main_image_digest,
            )
        finally:
            self.clean_up(*image_digests_list)

    def get_image_digests_from_archive(self, image_archive: str) -> list[str]:
        """
        Ideally we should find only digest from a single entry in the archive's index, but this method
        should hopefully generalize for manifests with multiple entries and/or multiple RepoTag values
        """
        index_file = "index.json"
        manifests_key = "manifests"
        digest_key = "digest"

        with tarfile.open(image_archive, "r") as tar:
            with tar.extractfile(index_file) as index_json_obj:
                index = json.load(index_json_obj)

        manifests_list = index[manifests_key]
        digests_list = []
        for manifest in manifests_list:
            digests_list.append(manifest[digest_key])

        return digests_list

    def load_image(self, decrypted_image_archive):
        docker_load_cmd = ["docker", "load", "-i", decrypted_image_archive]
        run_command(docker_load_cmd)

    def clean_up(self, *args):
        for image_name in args:
            delete_docker_containers_and_image(image_name)

        super().clean_up()
