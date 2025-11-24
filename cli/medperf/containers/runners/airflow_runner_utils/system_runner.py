from __future__ import annotations
import subprocess
import os
from .api_client.client import AirflowAPIClient
from .components.api_server import AirflowApiServer
from .components.airflow_component import AirflowComponentRunner
from .components.dag_processor import AirflowDagProcessor
from .components.db_postgres_docker import PostgresDBDocker
from .components.scheduler import AirflowScheduler
from .components.triggerer import AirflowTriggerer
from .components.utils import validate_port
from .monitor.yaml_dag_monitor import Summarizer
from .yaml_partial_parser import YamlPartialParser
from airflow.utils.state import DagRunState
import configparser
from typing import Union, List
import secrets
from pydantic import SecretStr
import json
import logging
import asyncio
from medperf.containers.runners.airflow_runner_utils.dags.constants import (
    FINAL_ASSET,
    SUMMARIZER_ID,
)
from medperf import config
import sys


class AirflowSystemRunner:
    def __init__(
        self,
        airflow_home: os.PathLike,
        user: str,
        dags_folder: os.PathLike,
        mounts: dict[str, os.PathLike],
        yaml_dags_dir: os.PathLike,
        project_name: str,
        port: Union[str, int] = 8080,
        postgres_port: Union[str, int] = 5432,
        airflow_python_executable: os.PathLike = None,
        **extra_airflow_configs: dict,
    ):
        self.airflow_home = airflow_home
        self._python_exec = airflow_python_executable or sys.executable
        # TODO windows
        self.port = validate_port(port)
        self.dags_folder = dags_folder
        self.extra_configs = extra_airflow_configs
        self.mounts = mounts
        self.yaml_parser = YamlPartialParser(yaml_file_dir=yaml_dags_dir)
        self.user = user
        self._password = SecretStr(secrets.token_urlsafe(16))
        self.airflow_config_file = os.path.join(self.airflow_home, "airflow.cfg")
        self.project_name = project_name
        self._postgres_password = SecretStr(secrets.token_urlsafe(16))
        self._postgres_user = self._postgres_db = "airflow"
        self.postgres_port = postgres_port
        self.scheduler = self.api_server = self.dag_processor = self.db = (
            self.triggerer
        ) = None
        self.host = "localhost"

    @property
    def _complete_link(self):
        return f"http://{self.host}:{self.port}"

    @property
    def _airflow_components(self) -> List[AirflowComponentRunner]:
        return [
            self.scheduler,
            self.api_server,
            self.dag_processor,
            self.db,
            self.triggerer,
        ]

    def _initial_setup(self):
        logging.debug("Creating initial Airflow configuration")
        config_create_process = subprocess.run(
            [self._python_exec, "-m", "airflow", "config", "list"],
            capture_output=True,
            env=self._run_env,
        )
        airflow_config = configparser.ConfigParser()
        logging.debug(
            f"Airflow process creation stdout:\n{config_create_process.stdout}"
        )
        with open(self.airflow_config_file, "r") as f:
            airflow_config.read_file(f)
        airflow_config["core"].update(
            {
                "dags_folder": self.dags_folder,
                "executor": "LocalExecutor",
                "auth_manager": "airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager",
                "load_examples": "false",
            }
        )
        airflow_config["database"].update(
            {"sql_alchemy_conn": self.db.connection_string}
        )
        airflow_config["scheduler"].update({"enable_health_check": "true"})

        logging.debug(f"Saving Airflow configuration to {self.airflow_config_file}")
        with open(self.airflow_config_file, "w") as f:
            airflow_config.write(f)

    def init_airflow(self, force_venv_creation: bool = False):
        # create_airflow_venv_if_not_exists(force_creation=force_venv_creation)
        os.makedirs(os.path.join(self.airflow_home, "logs"), exist_ok=True)
        self._initialize_components()

        config.ui.print("Starting Airflow components")
        asyncio.run(self.db.start())
        if not os.path.exists(self.airflow_config_file):
            self._initial_setup()

        self._start_airflow_db()
        self._create_admin_user()
        self._create_pools()
        asyncio.run(self._start_non_db_components())
        config.ui.print("Airflow components successfully started")

    @property
    def _run_env(self):
        sys_env = os.environ.copy()
        sys_env["AIRFLOW_HOME"] = self.airflow_home
        return sys_env

    def _initialize_components(self):
        common_args = {
            "python_executable": self._python_exec,
            "airflow_home": self.airflow_home,
            "container_type": config.platform,
            "yaml_dags_dir": self.yaml_parser.yaml_dir_path,
            "dags_folder": self.dags_folder,
        }

        self.db = PostgresDBDocker(
            project_name=self.project_name,  # TODO Check platform to instantiate singularity version
            root_dir=self.airflow_home,
            postgres_user="airflow",
            postgres_db="airflow",
            hostname=self.host,
        )
        self.api_server = AirflowApiServer(**common_args, port=self.port)
        self.scheduler = AirflowScheduler(
            **common_args, user=self.user, password=self._password, mounts=self.mounts
        )
        self.dag_processor = AirflowDagProcessor(**common_args, mounts=self.mounts)
        self.triggerer = AirflowTriggerer(**common_args)

    def _start_airflow_db(self):
        logging.debug("Migrating Airflow DB")
        init_db_logs = os.path.join(self.airflow_home, "logs", "init_db.log")
        with open(init_db_logs, "a") as f:
            db_migrate = subprocess.run(
                [self._python_exec, "-m", "airflow", "db", "migrate"],
                stdout=f,
                stderr=f,
                env=self._run_env,
            )

        if db_migrate.returncode != 0:
            raise ValueError("Failed Airflow Database migration")

    async def _start_non_db_components(self):
        await asyncio.gather(
            self.api_server.start(),
            self.scheduler.start(),
            self.dag_processor.start(),
            self.triggerer.start(),
        )

    def _create_admin_user(self):
        """First attempts to delete user by email, so that it can be generated again with a new password"""
        admin_email = "admin@admin.com"

        logging.debug("Deleting existing admin user, if any")
        delete_previous_user = subprocess.run(
            [
                self._python_exec,
                "-m",
                "airflow",
                "users",
                "delete",
                "--email",
                admin_email,
            ],
            capture_output=True,
            text=True,
            env=self._run_env,
        )
        logging.debug(f"User deletion stdout:\n{delete_previous_user.stdout}")
        logging.debug("Creating new admin user")
        create_new_user = subprocess.run(
            [
                self._python_exec,
                "-m",
                "airflow",
                "users",
                "create",
                "--username",
                self.user,
                "--role",
                "Admin",
                "--password",
                self._password.get_secret_value(),
                "--firstname",
                "admin",
                "--lastname",
                "admin",
                "--email",
                "admin@admin.com",
            ],
            capture_output=True,
            text=True,
            env=self._run_env,
        )
        logging.debug(f"Admin creation stdout:\n{create_new_user.stdout}")

    def _create_pools(self):
        logging.debug("Creating pools")
        if self.yaml_parser.pools is None:
            logging.debug("No pool definitions found")
            return

        pools_json = os.path.join(self.airflow_home, "pools.json")

        logging.debug(f"Writing pools to {pools_json}")
        with open(pools_json, "w") as f:
            json.dump(self.yaml_parser.pools, f, indent=4)

        logging.debug("Running pool creation command in Airflow")
        create_pools = subprocess.run(
            [self._python_exec, "-m", "airflow", "pools", "import", pools_json],
            capture_output=True,
            text=True,
            env=self._run_env,
        )

        if create_pools.stderr:
            raise ValueError(
                f"Error when attempting to create pools:\n{create_pools.stderr}"
            )

    def wait_for_dag(self):
        asyncio.run(self._async_wait_for_dag())

    async def _async_wait_for_dag(self):
        msg = [
            f"MedPerf has started executing the Data Pipeline {self.project_name} via Airflow."
        ]
        msg.append("Execution will continue until the pipeline successfully completes.")
        msg.append(
            f"The Airflow UI is available at the following link: {self._complete_link}."
        )
        msg.append(
            "Please use the following credentials for interacting with the Airflow WebUI"
        )
        msg.append("-------------------------------------------------------")
        msg.append(f"User: {self.user}")
        msg.append(f"Password: {self._password.get_secret_value()}")
        msg.append("-------------------------------------------------------")
        msg.append(
            "Note that the password value will change every time Airflow is restarted via MedPerf."
        )
        msg.append(
            "If this process must be stopped prematurely, please use the Ctrl+C command!"
        )

        wait_interval = 10  # seconds
        for line in msg:
            config.ui.print(line)
        api_url = f"{self._complete_link}/api/v2"
        with AirflowAPIClient(
            username=self.user, password=self._password, api_url=api_url
        ) as airflow_client:
            try:
                summarizer = Summarizer(
                    yaml_parser=self.yaml_parser,
                    report_file=self.mounts.get("report_file"),
                )
                summarizer_task = asyncio.create_task(
                    summarizer.summarize_every_x_seconds(
                        interval_seconds=1, airflow_client=airflow_client
                    )
                )
                while True:
                    await asyncio.sleep(wait_interval)
                    if self._check_completed_asset(airflow_client):
                        break

            except KeyboardInterrupt:
                config.ui.print("Interrupting Airflow Execution. Please wait...")
                raise

            finally:
                summarizer_task.cancel()
                summarizer.summarize(airflow_client)

        config.ui.print(
            "Pipeline Execution finished. Airflow will now be closed and MedPerf will proceed."
        )

    def _check_completed_asset(self, airflow_client: AirflowAPIClient) -> bool:
        """Checks if the final asset that marks pipeline completion has been updated"""
        try:
            asset_events = airflow_client.assets.get_asset_events()["asset_events"]
        except json.JSONDecodeError:
            config.ui.print(
                "Error checking completion of the pipeline. Please use the Airflow WebUI to verify execution status."
            )
            asset_events = []

        if not asset_events:
            return False

        final_asset = [event for event in asset_events if event["uri"] == FINAL_ASSET]
        return bool(final_asset)

    def _check_ran_summarizer(self, airflow_client: AirflowAPIClient) -> bool:
        """Checks if the summarizer has finished running. It is triggered by the final asset."""
        last_summarizer_run = airflow_client.dag_runs.get_most_recent_dag_run(
            dag_id=SUMMARIZER_ID
        )["dag_runs"]
        if not last_summarizer_run:
            return False

        last_summarizer_run = last_summarizer_run[0]
        run_state = last_summarizer_run["state"]

        if run_state == DagRunState.FAILED:
            raise ValueError("Final summarizer run failed!")

        return last_summarizer_run["state"] == DagRunState.SUCCESS

    def _stop_airflow(self):
        logging.debug("Stopping Airflow execution")
        for component in self._airflow_components:
            if component is not None and component.process:
                logging.debug(f"Stopping component {component.component_name}")
                component.terminate()

    def _kill_airflow(self):
        logging.debug("Forcefully terminating Airflow execution")
        for component in self._airflow_components:
            if component is not None:
                logging.debug(f"Killing component {component.component_name}")
                component.kill()

    def __enter__(self):
        logging.debug("Entering Airflow context manager")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logging.debug("Exiting Airflow context manager")
        if exc_type is None:
            self._stop_airflow()

        else:
            self._kill_airflow()
