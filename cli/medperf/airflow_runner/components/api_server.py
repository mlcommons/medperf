from __future__ import annotations
from medperf.airflow_runner.components.airflow_component import AirflowComponentRunner
from medperf.airflow_runner.components.utils import validate_port
from typing import Union
from .utils import run_healthcheck


class AirflowApiServer(AirflowComponentRunner):
    def __init__(self, port: Union[str, int], **kwargs):
        self.port = validate_port(port)
        super().__init__(**kwargs)

    @property
    def component_name(self):
        return "Airflow API Server"

    @property
    def logfile(self):
        return "apiserver.log"

    @property
    def initialize_command(self):
        return ["airflow", "api-server", "--port", self.port]

    def has_successfully_started(self):
        return run_healthcheck("http://localhost:8080/api/v2/version")
