from medperf.enums import Status


def generate_result(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "owner": kwargs.get("owner", 1),
        "benchmark": kwargs.get("benchmark", 1),
        "model": kwargs.get("model", 1),
        "dataset": kwargs.get("dataset", 1),
        "results": kwargs.get("results", {}),
        "metadata": kwargs.get("metadata", {}),
        "approval_status": kwargs.get("approval_status", Status.APPROVED.value),
        "approved_at": kwargs.get("approved_at", "approved_at"),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
    }
