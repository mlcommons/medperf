from .container_operator_builder import ContainerOperatorBuilder
from airflow.providers.singularity.operators.singularity import SingularityOperator
import os
from medperf.exceptions import MedperfException


class SingularityOperatorBuilder(ContainerOperatorBuilder):
    """
    Currently untested!!
    """

    def _build_mount_item(self, host_path, mount_path, read_only):
        mount_suffix = "ro" if read_only else "rw"
        mount_str = f"{host_path}:{mount_path}:{mount_suffix}"
        return mount_str

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
