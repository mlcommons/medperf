import os
import subprocess
from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio
import async_timeout
import logging

logger = logging.getLogger(__name__)


class ComponentRunner(ABC):

    START_PERIOD = 5
    INTERVAL = 10
    TIMEOUT = 60
    MAX_TRIES = 5

    def __init__(self):
        self.process = None

    @property
    @abstractmethod
    def logfile(self) -> str:
        pass

    @property
    @abstractmethod
    def has_successfully_started(self) -> bool:
        pass

    @property
    def component_name(self):
        """Can be overriden to customize name"""
        return self.__class__.__name__

    @property
    def starting_message(self):
        return f"Starting component {self.component_name}"

    @property
    def finished_message(self):
        return f"Component {self.component_name} started succesfully"

    @property
    def fail_message(self):
        return f"Failed to start up component {self.component_name}"

    def run_command_with_logging(
        self, command: List[str], logfile_path: os.PathLike, env: Dict = None
    ):
        with open(logfile_path, "a") as f:
            self.process = subprocess.Popen(command, env=env, stdout=f, stderr=f)

    async def start(self):
        logger.debug(self.starting_message)
        await self.start_logic()
        logger.debug(self.finished_message)

    @abstractmethod
    async def start_logic(self):
        pass

    async def wait_for_start(self):
        try:
            async with async_timeout.timeout(self.TIMEOUT):
                await self._sync_wait_for_start()
        except asyncio.TimeoutError:
            raise TimeoutError(self.fail_message)

    async def _sync_wait_for_start(self):
        current_try = 1
        while current_try < self.MAX_TRIES:
            if self.has_successfully_started():
                return
            await asyncio.sleep(self.INTERVAL)
            current_try += 1
        raise ValueError(
            f"Component {self.component_name} exceeded maximum number of checks to start."
        )

    def terminate(self):
        if self.process is not None:
            self.process.terminate()

    def kill(self):
        if self.process is not None:
            self.process.kill()

    def __enter__(self):
        self.start_logic()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.terminate()

        else:
            self.kill()

        return False  # Propagate exception, if any
