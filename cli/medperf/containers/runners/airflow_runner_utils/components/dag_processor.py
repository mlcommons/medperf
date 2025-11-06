from medperf.containers.runners.airflow_runner_utils.components.airflow_component import (
    AirflowComponentRunner,
)
import subprocess
import sys


class AirflowDagProcessor(AirflowComponentRunner):
    @property
    def logfile(self):
        return "processor.log"

    @property
    def initialize_command(self):
        return ["airflow", "dag-processor"]

    @property
    def component_name(self):
        return "Airflow DAG Processor"

    def has_successfully_started(self):
        has_dag_processor_jobs = subprocess.run(
            [
                self._python_exec,
                "-m",
                "airflow",
                "jobs",
                "check",
                "--job-type",
                "DagProcessorJob",
                "--local",
            ],
            capture_output=True,
        )
        return has_dag_processor_jobs.returncode == 0
