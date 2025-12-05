import os


class PipelineState:
    # TODO properly define

    def __init__(self, running_subject: str = None, **airflow_kwargs):
        self.running_subject = running_subject
        self.airflow_kwargs = airflow_kwargs
        self.host_input_data_path = os.getenv("host_data_path")
        self.host_output_data_path = os.getenv("host_output_path")
        self.host_labels_path = os.getenv("host_labels_path")
        self.host_output_labels_path = os.getenv("host_output_labels_path")
