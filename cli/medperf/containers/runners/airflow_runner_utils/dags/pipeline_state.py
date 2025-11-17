class PipelineState:
    # TODO properly define

    def __init__(self, running_subject: str = None, **airflow_kwargs):
        self.running_subject = running_subject
        self.airflow_kwargs = airflow_kwargs
