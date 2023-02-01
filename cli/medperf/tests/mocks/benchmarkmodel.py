from medperf.enums import Status


def generate_benchmarkmodel(**kwargs):
    dict_ = {
        "model_mlcube": 1,
        "benchmark": 1,
        "initiated_by": 1,
        "metadata": {},
        "approval_status": Status.APPROVED.value,
        "approved_at": "approved_at",
        "created_at": "created_at",
        "modified_at": "modified_at",
        "priority": 0,
    }
    dict_.update(kwargs)
    return dict_
