from .container_operator_builder import ContainerOperatorBuilder
from airflow.providers.singularity.operators.singularity import SingularityOperator
import os
from medperf.exceptions import MedperfException


class SingularityOperatorBuilder(ContainerOperatorBuilder):
    """
    Currently untested!!
    """

    def build_mounts_and_command_args(self, mounts: dict):
        """Singularity operator uses raw mount strings as they are, /path/in/host:/path/in/container"""
        singularity_mounts = []
        command_args = []
        for mount_type, mount_info in mounts.items():
            read_only = mount_type == "input_volumes"
            for var_name, mount_details in mount_info.items():
                host_path = os.getenv(f"host_{var_name}", None)
                if host_path is None:
                    raise MedperfException(
                        f"Could not find definition for mount {var_name} in the Airflow environment!"
                    )
                singularity_path = mount_details["mount_path"]
                mount_suffix = "ro" if read_only else "rw"
                mount_str = f"{host_path}:{singularity_path}:{mount_suffix}"
                singularity_mounts.append(mount_str)
                command_args.extend([f"--{var_name}", singularity_path])

                if mount_details.get("type") == "directory":
                    os.makedirs(host_path, exist_ok=True)
        return singularity_mounts, command_args

    def _define_base_operator(self) -> SingularityOperator:
        command = self._get_command()
        return SingularityOperator(
            image=self.image,
            command=command,
            volumes=self.mounts,
            task_id=self.operator_id,
            task_display_name=self.display_name,
            auto_remove=True,
            outlets=self.outlets,
        )
