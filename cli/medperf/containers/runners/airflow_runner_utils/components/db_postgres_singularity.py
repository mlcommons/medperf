from .db_postgres_component import PostgresDatabaseComponent
import subprocess
from medperf import config
from medperf import config
from medperf.containers.runners.singularity_utils import (
    get_singularity_executable_props,
)


class PostgresDBSingularity(PostgresDatabaseComponent):
    """Note: currently untested!"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        executable, runtime, version = get_singularity_executable_props()
        self.executable = executable
        self.runtime = runtime
        self.version = version

    @property
    def instance_name(self):
        return f"instance://{self.container_name}"

    async def start_logic(self):
        """Notes:
        - singularity instance start runs detached (similar to docker run -d)
        """
        run_env = {
            "SINGULARITYENV_POSTGRES_USER": self.user,
            "SINGULARITYENV_POSTGRES_PASSWORD": self.password.get_secret_value(),
            "SINGULARITYENV_POSTGRES_DB": self.db,
        }
        self.process = subprocess.run(
            [
                self.executable,
                "instance",
                "start",
                "-eC",
                "--bind",
                f"{self.data_dir}:/var/lib/postgresql/data:rw",
                f"docker://{config.airflow_postgres_image}",
                self.container_name,
            ],
            capture_output=True,
            text=True,
            env=run_env,
        )
        await self.wait_for_start()

    def has_successfully_started(self):
        postgres_status: subprocess.CompletedProcess = subprocess.run(
            [
                self.executable,
                "exec",
                self.instance_name,
                "pg_isready",
                "-U",
                self.user,
                "-d",
                self.db,
            ],
            capture_output=True,
            text=True,
        )
        return postgres_status.returncode == 0

    def terminate(self):
        subprocess.run(
            [self.executable, "stop", self.instance_name],
            capture_output=True,
            text=True,
        )

    def kill(self):
        subprocess.run(
            [self.executable, "stop", "-F", self.instance_name],
            capture_output=True,
            text=True,
        )
