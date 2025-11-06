from constants import (
    AIRFLOW_DATA_DIR,
    AIRFLOW_INPUT_DATA_DIR,
    AIRFLOW_WORKSPACE_DIR,
)


class PipelineState:
    # TODO properly define

    def __init__(self, running_subject: str = None, **airflow_kwargs):
        self.running_subject = running_subject
        self.airflow_kwargs = airflow_kwargs
        self.input_data_dir = AIRFLOW_INPUT_DATA_DIR
        self.data_dir = AIRFLOW_DATA_DIR
        self.workspace_dir = AIRFLOW_WORKSPACE_DIR
