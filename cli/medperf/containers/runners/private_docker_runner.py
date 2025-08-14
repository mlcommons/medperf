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
            # Define this early just in case we get an error before this is properly
            # defined, so clean up can run without issues
            repo_tags_list = []

            decrypted_image_archive = self._decrypt_image()

            repo_tags_list = self.get_repo_tags_from_archive(
                decrypted_image_archive
            )
            main_image_name = repo_tags_list[0]

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
                image=main_image_name,
            )
        finally:
            self.clean_up(*repo_tags_list)

    def get_repo_tags_from_archive(self, image_archive: str) -> list[str]:
        """
        Ideally we should find only a single entry in the digest with a single repo tag, but this method
        should hopefully generalize for manifests with multiple entries and/or multiple RepoTag values
        """
        manifest_file = "manifest.json"
        repo_tags_key = 'RepoTags'

        with tarfile.open(image_archive, "r") as tar:
            with tar.extractfile(manifest_file) as index_json_obj:
                manifests_list = json.load(index_json_obj)

        repo_tags_list = []
        for manifest in manifests_list:
            repo_tags_list.extend(manifest[repo_tags_key])

        return repo_tags_list

    def load_image(self, decrypted_image_archive):
        docker_load_cmd = ["docker", "load", "-i", decrypted_image_archive]
        run_command(docker_load_cmd)

    def clean_up(self, *args):
        for image_name in args:
            delete_docker_containers_and_image(image_name)

        super().clean_up()
