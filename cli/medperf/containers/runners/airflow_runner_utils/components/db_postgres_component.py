from .component import ComponentRunner
from .utils import validate_port, generate_random_password
from pydantic import SecretStr
from typing import Union

import os
import random
import string
from abc import abstractmethod


class PostgresDatabaseComponent(ComponentRunner):

    START_PERIOD = 2
    INTERVAL = 5
    MAX_TRIES = 12
    TIMEOUT = 60

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

    @property
    def connection_string(self):
        return f"postgresql+psycopg2://{self.user}:{self.password.get_secret_value()}@{self.hostname}:{self.port}/{self.db}"

    @abstractmethod
    async def start_logic(self):
        """Logic to start the Postgres container goes here"""
        pass

    @abstractmethod
    def has_successfully_started(self):
        """Logic to check if Postgres container has succesfully started goes here"""

    @abstractmethod
    def terminate(self):
        """Logic to gracefully terminate Postgres container goes here"""

    @abstractmethod
    def kill(self):
        """ "Logic to forcefully stop Postgres container goes here"""
