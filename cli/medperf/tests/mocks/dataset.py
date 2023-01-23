from medperf.enums import Status


def generate_dset(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "description": kwargs.get("description", "description"),
        "location": kwargs.get("location", "location"),
        "data_preparation_mlcube": kwargs.get("data_preparation_mlcube", 1),
        "input_data_hash": kwargs.get("input_data_hash", "input_data_hash"),
        "generated_uid": kwargs.get("generated_uid", "generated_uid"),
        "split_seed": kwargs.get("split_seed", "split_seed"),
        "generated_metadata": kwargs.get("generated_metadata", "generated_metadata"),
        "status": kwargs.get("status", Status.APPROVED.value),  # not in the server
        "state": kwargs.get("state", "PRODUCTION"),
        "separate_labels": kwargs.get("separate_labels", False),  # not in the server
        "is_valid": kwargs.get("is_valid", True),
        "user_metadata": kwargs.get("user_metadata", {}),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
        "owner": kwargs.get("owner", 1),
    }
