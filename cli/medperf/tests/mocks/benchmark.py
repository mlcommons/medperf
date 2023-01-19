from medperf.enums import Status


class Benchmark:
    def __init__(self):
        self.name = "MockedBenchmark"
        self.data_preparation = 1


def generate_benchmark(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "description": kwargs.get("description", "description"),
        "docs_url": kwargs.get("docs_url", ""),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
        "approved_at": kwargs.get("approved_at", "approved_at"),
        "owner": kwargs.get("owner", 1),
        "demo_dataset_tarball_url": kwargs.get(
            "demo_dataset_tarball_url", "demo_dataset_tarball_url"
        ),
        "demo_dataset_tarball_hash": kwargs.get(
            "demo_dataset_tarball_hash", "demo_dataset_tarball_hash"
        ),
        "demo_dataset_generated_uid": kwargs.get(
            "demo_dataset_generated_uid", "demo_dataset_generated_uid"
        ),
        "data_preparation_mlcube": kwargs.get("data_preparation_mlcube", 1),
        "reference_model_mlcube": kwargs.get("reference_model_mlcube", 2),
        "models": kwargs.get("models", [2]),
        "data_evaluator_mlcube": kwargs.get("data_evaluator_mlcube", 3),
        "state": kwargs.get("state", "PRODUCTION"),
        "is_valid": kwargs.get("is_valid", True),
        "is_active": kwargs.get("is_active", True),
        "approval_status": kwargs.get("approval_status", Status.APPROVED.value),
        "metadata": kwargs.get("metadata", {}),
        "user_metadata": kwargs.get("user_metadata", {}),
    }
