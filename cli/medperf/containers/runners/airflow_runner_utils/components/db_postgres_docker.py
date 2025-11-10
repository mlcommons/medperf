from .db_component import DatabaseComponent
from .utils import validate_port, generate_random_password
from pydantic import SecretStr
from typing import Union

import os
import random
import string
import subprocess


class PostgresDBDocker(DatabaseComponent):

    POSTGRES_IMAGE = "postgres:14.19"
    START_PERIOD = 2
    INTERVAL = 5
    MAX_TRIES = 5
    TIMEOUT = 30

    def __init__(
        self,
        project_name: str,
        root_dir: os.PathLike,
        postgres_user: str = "postgres",
        postgres_password: SecretStr = None,
        postgres_db: str = "postgres",
        postgres_port: Union[str, int] = 5432,
        hostname: str = "localhost",
    ):
        super().__init__()
        self.user = postgres_user
        self.db = postgres_db
        self.password = postgres_password or generate_random_password()
        self.hostname = hostname
        self.port = validate_port(postgres_port)
        self.data_dir = os.path.join(root_dir, "postgres_data")
        self.logs_dir = os.path.join(root_dir, "logs")
        self.container_name = self.generate_container_name(project_name)
        self.container_id = None

    @property
    def component_name(self):
        return "PostgreSQL Database for Airflow"

    @property
    def logfile(self):
        return os.path.join(self.logs_dir, "postgres_db.log")

    @staticmethod
    def generate_container_name(project_name):
        all_characters = string.ascii_lowercase + string.digits
        num_digits = 4
        random_part = "".join(random.choice(all_characters) for _ in range(num_digits))
        complete_name = f"postgres_{project_name}_{random_part}"
        return complete_name

    async def start_logic(self):
        self.process = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                self.container_name,
                "-e",
                f"POSTGRES_USER={self.user}",
                "-e",
                f"POSTGRES_PASSWORD={self.password.get_secret_value()}",
                "-e",
                f"POSTGRES_DB={self.db}",
                "-v",
                f"{self.data_dir}:/var/lib/postgresql/data",
                "-p",
                f"{self.port}:{self.port}",
                f"{self.POSTGRES_IMAGE}",
            ],
            capture_output=True,
            text=True,
        )
        self.container_id = self.process.stdout
        await self.wait_for_start()

    def has_successfully_started(self):
        postgres_status: subprocess.CompletedProcess = subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                self.container_id,
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
            ["docker", "stop", self.container_id], capture_output=True, text=True
        )
        subprocess.run(
            ["docker", "rm", self.container_id], capture_output=True, text=True
        )

    def kill(self):
        subprocess.run(
            ["docker", "rm", "-f", self.container_id], capture_output=True, text=True
        )

    @property
    def connection_string(self):
        return f"postgresql+psycopg2://{self.user}:{self.password.get_secret_value()}@{self.hostname}:{self.port}/{self.db}"
