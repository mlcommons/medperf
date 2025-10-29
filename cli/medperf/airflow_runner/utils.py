from enum import Enum


class DagRunState(str, Enum):
    """
    Duplicated from Airflow code so we do not need to install
    an explicit Airflow dependency in the MedPerf venv
    """

    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value
