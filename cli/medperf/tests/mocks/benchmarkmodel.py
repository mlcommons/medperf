from medperf.enums import Status
from datetime import datetime

mock_datetime = str(datetime.now())


def generate_benchmarkmodel(**kwargs):
    dict_ = {
        "model_mlcube": 1,
        "benchmark": 1,
        "initiated_by": 1,
        "metadata": {},
        "approval_status": Status.APPROVED.value,
        "approved_at": mock_datetime,
        "created_at": mock_datetime,
        "modified_at": mock_datetime,
        "priority": 0,
    }
    dict_.update(kwargs)
    return dict_
