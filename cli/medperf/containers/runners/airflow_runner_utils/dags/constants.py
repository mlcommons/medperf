from datetime import datetime, timedelta
import os

SUMMARIZER_ID = "pipeline_summarizer"
SUMMARIZER_TAG = "Pipeline Summarizer"
ALWAYS_CONDITION = "ALWAYS"
YESTERDAY = datetime.today() - timedelta(days=1)
FINAL_ASSET = "medperf_airflow_completed_asset"
WORKFLOW_YAML_FILE = os.getenv("WORKFLOW_YAML_FILE")
