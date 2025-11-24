from .container_operator_builder import ContainerOperatorBuilder, MountInfo
from airflow.providers.singularity.operators.singularity import SingularityOperator


class SingularityOperatorBuilder(ContainerOperatorBuilder):
    """
    Currently untested!!
    """

    def _build_mount_item(
        self, host_path, mount_path, read_only, mount_info: MountInfo
    ):
        mount_suffix = "ro" if mount_info.read_only else "rw"
        mount_str = f"{mount_info.source}:{mount_info.target}:{mount_suffix}"
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
