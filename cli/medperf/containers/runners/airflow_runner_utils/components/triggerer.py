from medperf.containers.runners.airflow_runner_utils.components.airflow_component import (
    AirflowComponentRunner,
)
import subprocess
import sys


class AirflowTriggerer(AirflowComponentRunner):
    @property
    def logfile(self):
        return "triggerer.log"

    @property
    def component_name(self):
        return "Airflow Triggerer"

    @property
    def initialize_command(self):
        return ["airflow", "triggerer"]

    def has_successfully_started(self):
        has_triggerer_jobs = subprocess.run(
            [
                self._python_exec,
                "-m",
                "airflow",
                "jobs",
                "check",
                "--job-type",
                "TriggererJob",
                "--local",
            ],
            capture_output=True,
            env=self._run_env,
        )
        return has_triggerer_jobs.returncode == 0
