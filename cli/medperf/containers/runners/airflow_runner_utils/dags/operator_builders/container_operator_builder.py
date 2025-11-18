from __future__ import annotations
from .operator_builder import OperatorBuilder
from abc import abstractmethod
from typing import Optional


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

    @abstractmethod
    def build_mounts_and_command_args(self, base_inlet):
        pass

    def _get_command(self):
        command = [*self.base_command, *self.command_args]
        if self.partition:
            command = [*command, "--subject-subdir", self.partition]
        return command
