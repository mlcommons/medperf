from .db_postgres_component import PostgresDatabaseComponent
import subprocess
from medperf import config
import logging


class PostgresDBDocker(PostgresDatabaseComponent):

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
                f"{self.data_dir}:/var/lib/postgresql/data:rw",
                "-p",
                f"{self.port}:5432",
                f"{config.airflow_postgres_image}",
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
        has_started = postgres_status.returncode == 0

        if not has_started:
            config.ui.print("Postgres DB not started yet")
            config.ui.print(f"stdout=\n{postgres_status.stdout}")
            config.ui.print(f"stderr=\n{postgres_status.stderr}")

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
