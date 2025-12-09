from datetime import datetime, timedelta
import os

ALWAYS_CONDITION = "ALWAYS"
YESTERDAY = datetime.today() - timedelta(days=1)
FINAL_ASSET = "medperf_airflow_completed_asset"
WORKFLOW_YAML_FILE = os.getenv("WORKFLOW_YAML_FILE")
