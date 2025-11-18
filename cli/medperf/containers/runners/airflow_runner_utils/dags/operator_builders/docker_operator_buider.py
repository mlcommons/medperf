from .container_operator_builder import ContainerOperatorBuilder
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
import os
from medperf.exceptions import MedperfException


class DockerOperatorBuilder(ContainerOperatorBuilder):

    def _build_mount_item(self, host_path, mount_path, read_only):
        return Mount(
            source=host_path,
            target=mount_path,
            type="bind",
            read_only=read_only,
        )

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
