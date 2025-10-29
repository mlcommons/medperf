from .container_operator_builder import ContainerOperatorBuilder
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


class DockerOperatorBuilder(ContainerOperatorBuilder):

    def build_mounts(self, mounts):
        docker_mounts = []
        for mount in mounts:
            host_path, docker_path = mount.rsplit(":", maxsplit=1)
            docker_mounts.append(
                Mount(source=host_path, target=docker_path, type="bind")
            )
        return docker_mounts

    def _define_base_operator(self) -> DockerOperator:

        command = self._get_command()

        return DockerOperator(
            image=self.image,
            command=command,
            mounts=self.mounts,
            task_id=self.operator_id,
            task_display_name=self.display_name,
            auto_remove="success",
            mount_tmp_dir=False,
            outlets=self.outlets,
        )
