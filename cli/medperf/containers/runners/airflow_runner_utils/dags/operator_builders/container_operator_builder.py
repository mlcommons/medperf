from __future__ import annotations
from .operator_builder import OperatorBuilder
from abc import abstractmethod
import os
from medperf.exceptions import MedperfException


class MountInfo:

    def __init__(self, source: os.PathLike, target: os.PathLike, read_only: bool):
        self.source = source
        self.target = target
        self.read_only = read_only

    def __eq__(self, other):
        if not isinstance(other, MountInfo):
            return False
        return (
            self.source == other.source
            and self.target == other.target
            and self.read_only == other.read_only
        )

    def __hash__(self):
        return hash((self.source, self.target, self.read_only))


class ContainerOperatorBuilder(OperatorBuilder):

    def __init__(
        self,
        image: str,
        command: str | list[str],
        mounts: dict,
        host_mounts: dict,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.image = image
        if isinstance(command, str):
            self.base_command = command.split(" ")
        else:
            self.base_command = command

        self.mounts = self.build_mounts(mounts, host_mounts)

    def build_mounts(self, mounts, host_mounts):
        mount_infos = set()
        for mount_type, mount_info in mounts.items():
            read_only = mount_type == "input_volumes" and self.is_first
            for var_name, mount_details in mount_info.items():
                host_path = host_mounts[var_name]

                if host_path is None:
                    raise MedperfException(
                        f"Could not find definition for mount {var_name} in the Airflow environment!"
                    )
                mount_path = mount_details["mount_path"]

                mount_infos.add(
                    MountInfo(source=host_path, target=mount_path, read_only=read_only)
                )

                if mount_details.get("type") == "directory":
                    os.makedirs(host_path, exist_ok=True)
                elif mount_details.get("type") == "file" and not os.path.exists(
                    host_path
                ):
                    open(host_path, "x").close()
        container_mounts = [
            self._build_mount_item(mount_info) for mount_info in mount_infos
        ]
        return container_mounts

    @abstractmethod
    def _build_mount_item(self, mount_info: MountInfo):
        """Logic for building mounts in Docker or Singularity. Implemented in subclasses"""
        pass

    def _get_command(self):
        command = [*self.base_command]
        if self.partition:
            command = [*command, "--subject-subdir", self.partition]
        return command
