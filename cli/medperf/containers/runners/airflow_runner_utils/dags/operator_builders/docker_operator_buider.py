from .container_operator_builder import ContainerOperatorBuilder
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
import os
from medperf.exceptions import MedperfException


class DockerOperatorBuilder(ContainerOperatorBuilder):

    def build_mounts_and_command_args(self, mounts, base_inlet):
        docker_mounts = []
        command_args = []
        try:
            for mount_type, mount_info in mounts.items():
                read_only = mount_type == "input_volumes"
                for var_name, mount_details in mount_info.items():
                    if var_name == "data_path" and base_inlet is not None:
                        env_name = "output_path"
                    elif var_name == "labels_path" and base_inlet is not None:
                        env_name = "output_labels_path"
                    elif var_name == "output_path" and self.raw_id == "statistics":
                        env_name = "statistics_file"
                    else:
                        env_name = var_name

                    host_path = os.getenv(f"host_{env_name}", None)

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
                    elif mount_details.get("type") == "file" and not os.path.exists(
                        host_path
                    ):
                        open(host_path, "x").close()
        except AttributeError:
            msg = "----------------------------------------------------------\n"
            msg += f"{self.image=}\n"
            msg += f"{self.base_command=}\n"
            msg += f"{mounts=}\n"
            msg += f"{base_inlet=}\n"
            msg += "----------------------------------------------------------"
            raise AttributeError(msg)
        return docker_mounts, command_args

    def _define_base_operator(self) -> DockerOperator:

        command = self._get_command()

        return DockerOperator(
            image=self.image,
            command=command,
            mounts=self.mounts,
            task_id=self.operator_id,
            task_display_name=self.display_name,
            # auto_remove="success",
            mount_tmp_dir=False,
            outlets=self.outlets,
        )
