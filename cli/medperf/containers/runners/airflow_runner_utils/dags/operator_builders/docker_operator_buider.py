from .container_operator_builder import ContainerOperatorBuilder
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
import os
from medperf.exceptions import MedperfException


class DockerOperatorBuilder(ContainerOperatorBuilder):

    def build_mounts_and_command_args(self, mounts):
        docker_mounts = []
        command_args = []
        for mount_type, mount_info in mounts.items():
            read_only = mount_type == "input_volumes"
            for var_name, mount_details in mount_info.items():
                host_path = os.getenv(f"host_{var_name}", None)
                if host_path is None:
                    raise MedperfException(
                        f"Could not find definition for mount {var_name} in the Airflow environment!"
                    )
                docker_path = mount_details["mount_path"]
                docker_mounts.append(
                    Mount(
                        source=host_path,
                        target=docker_path,
                        type="bind",
                        read_only=read_only,
                    )
                )
                command_args.extend([f"--{var_name}", docker_path])
                if mount_details.get("type") == "directory":
                    os.makedirs(host_path, exist_ok=True)
        return docker_mounts, command_args

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
