from __future__ import annotations
from .operator_builder import OperatorBuilder
from abc import abstractmethod
from typing import Optional
import os
from medperf.exceptions import MedperfException


class ContainerOperatorBuilder(OperatorBuilder):

    def __init__(
        self,
        image: str,
        command: str | list[str],
        mounts: dict,
        base_inlet: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.image = image
        if isinstance(command, str):
            self.base_command = command.split(" ")
        else:
            self.base_command = command

        self.mounts, self.command_args = self.build_mounts_and_command_args(
            mounts, base_inlet
        )

    def build_mounts_and_command_args(self, mounts, base_inlet):
        container_mounts = []
        command_args = []

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
                mount_path = mount_details["mount_path"]
                mount_item = self._build_mount_item(host_path, mount_path, read_only)

                container_mounts.append(mount_item)
                command_args.extend([f"--{var_name}", mount_path])
                if mount_details.get("type") == "directory":
                    os.makedirs(host_path, exist_ok=True)
                elif mount_details.get("type") == "file" and not os.path.exists(
                    host_path
                ):
                    open(host_path, "x").close()

        return container_mounts, command_args

    @abstractmethod
    def _build_mount_item(self, host_path, mount_path, read_only):
        """Logic for building mounts in Docker or Singularity. Implemented in subclasses"""
        pass

    def _get_command(self):
        command = [*self.base_command, *self.command_args]
        if self.partition:
            command = [*command, "--subject-subdir", self.partition]
        return command
