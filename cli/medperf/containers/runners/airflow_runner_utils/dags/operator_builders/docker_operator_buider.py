from .container_operator_builder import ContainerOperatorBuilder, MountInfo
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


class DockerOperatorBuilder(ContainerOperatorBuilder):

    def _build_mount_item(self, mount_info: MountInfo):
        return Mount(
            source=mount_info.source,
            target=mount_info.target,
            type="bind",
            read_only=mount_info.read_only,
        )

    def _define_base_operator(self) -> DockerOperator:

        command = self._get_command()

        # TODO when adding device requests, it should be similar to what is defined below
        # from docker.types import eviceRequest
        # device_request = DeviceRequest(device_ids=["0", "2"], capabilities=[["gpu"]])
        return DockerOperator(
            image=self.image,
            command=command,
            mounts=self.mounts,
            task_id=self.operator_id,
            task_display_name=self.display_name,
            # auto_remove="success",
            mount_tmp_dir=False,
            outlets=self.outlets,
            # TODO add medperf arguments: shm_size, user, network, ports, entrypoint, gpus
            shm_size=None,
            user=None,
            network_mode=None,
            port_bindings=None,
            device_requests=None,  # gpus
        )
