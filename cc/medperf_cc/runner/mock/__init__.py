"""Running the workload as a plain container on this machine.

The same image a confidential VM would run, given the same environment, writing
its output to the same mock storage every other party is using. What is missing
is the VM: nothing is measured, nothing is attested, and the workload could be
anything. Selecting `mock` is selecting "no protection at all".
"""

import logging
import os
import subprocess
from typing import Iterator

from medperf_cc.backends.mock import MOCK, MockConfig
from medperf_cc.errors import OperationError
from medperf_cc.identity import WorkloadIdentity
from medperf_cc.runner.base import WorkloadRunner

# What a Confidential Space launcher would attest to, handed over instead. The
# workload cannot measure its own image, so without this it could not name the
# identity it is running as, and the mock vault would have nothing to check.
# Supplying it is exactly the protection the mock does not provide: a real
# workload proves this, it does not assert it.
ATTESTED_SCRIPT_ENV = "MEDPERF_MOCK_ATTESTED_SCRIPT"


class MockRunner(WorkloadRunner):
    SETTINGS = MockConfig

    def __init__(self, config: dict):
        super().__init__(config)
        self.mock = MockConfig(**config)

    @property
    def backend(self) -> str:
        return MOCK

    def verify(self) -> None:
        try:
            subprocess.run(
                ["docker", "version"],
                capture_output=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as e:
            raise OperationError(
                f"The mock runner needs docker to start a workload: {e}"
            )
        os.makedirs(self.mock.root, exist_ok=True)

    def launch(self, workload: WorkloadIdentity, image: str, env: dict) -> None:
        env = {**env, ATTESTED_SCRIPT_ENV: workload.script_hash}
        name = self.__container_name(workload)
        os.makedirs(self.mock.root, exist_ok=True)
        self.__remove_container(name)

        command = [
            "docker",
            "run",
            "--detach",
            "--name",
            name,
            # Mounted at the same path inside, so every path the parties
            # exchanged means the same thing on both sides.
            "--volume",
            f"{self.mock.root}:{self.mock.root}",
            # gnupg wants somewhere to put its keyring
            "--env",
            "HOME=/tmp",
            # The workload writes as whoever the image says. Running it as this
            # user keeps the results readable once they are back on the host.
            "--user",
            f"{os.getuid()}:{os.getgid()}",
        ]
        for key, value in env.items():
            command += ["--env", f"{key}={value}"]
        command.append(image)

        started = subprocess.run(command, capture_output=True, text=True)
        if started.returncode != 0:
            raise OperationError(f"Failed to start the workload: {started.stderr}")

    def wait(self, workload: WorkloadIdentity) -> Iterator[str]:
        name = self.__container_name(workload)
        logs = subprocess.Popen(
            ["docker", "logs", "--follow", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in logs.stdout:
            yield line.rstrip()
        logs.wait()

        exit_code = self.__exit_code(name)
        if exit_code not in (0, None):
            logging.error(f"The workload exited with status {exit_code}")

    def __container_name(self, workload: WorkloadIdentity) -> str:
        return f"medperf-cc-mock-{workload.storage_prefix}"

    def __remove_container(self, name: str) -> None:
        subprocess.run(
            ["docker", "rm", "--force", name], capture_output=True
        )

    def __exit_code(self, name: str):
        inspected = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.ExitCode}}",
                name,
            ],
            capture_output=True,
            text=True,
        )
        if inspected.returncode != 0:
            return None
        try:
            return int(inspected.stdout.strip())
        except ValueError:
            return None
