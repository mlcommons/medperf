import json
from medperf.asset_management import gcp_utils


def create_service_account(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.create_service_account(config)


def allow_operator_to_use_service_account(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.add_service_account_iam_policy_binding(
        config,
        f"user:{config.account}",
        "roles/iam.serviceAccountUser",
    )


def grant_confidential_computing_workload_user(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.add_project_iam_policy_binding(
        config,
        f"serviceAccount:{config.service_account_email}",
        "roles/confidentialcomputing.workloadUser",
    )


def grant_logging_log_writer(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.add_project_iam_policy_binding(
        config,
        f"serviceAccount:{config.service_account_email}",
        "roles/logging.logWriter",
    )


def run_workload(
    config: gcp_utils.GCPOperatorConfig, docker_image: str, env_vars: dict
):
    # Build metadata string
    metadata_parts = [
        f"tee-image-reference={docker_image}",
        "tee-container-log-redirect=true",
    ]

    # Add environment variables
    for key, value in env_vars.items():
        metadata_parts.append(f"tee-env-{key}={value}")

    metadata = "^~^" + "~".join(metadata_parts)

    gcp_utils.run_workload(config, metadata)


def grant_bucket_public_read_access(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.add_bucket_iam_policy_binding(
        config, "allUsers", "roles/storage.objectViewer"
    )


def grant_bucket_write_access(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.add_bucket_iam_policy_binding(
        config,
        f"serviceAccount:{config.service_account_email}",
        "roles/storage.objectAdmin",
    )


class OperatorManager:
    def __init__(self, config: dict):
        self.config = gcp_utils.GCPOperatorConfig(**config)

    def setup(self):
        """Set up complete operator infrastructure"""
        create_service_account(self.config)
        allow_operator_to_use_service_account(self.config)
        grant_confidential_computing_workload_user(self.config)
        grant_logging_log_writer(self.config)
        grant_bucket_public_read_access(self.config)
        grant_bucket_write_access(self.config)

    def run_workload(
        self,
        docker_image: str,
        workload_dict: dict,
        dataset_cc_config: dict,
        model_cc_config: dict,
        dataset_hash: str,
        model_hash: str,
        result_collector_public_key: str,
    ):
        """Run workload using operator's service account"""
        workload_props = [
            workload_dict["image_digest"],
            workload_dict["EXPECTED_DATA_HASH"],
            workload_dict["EXPECTED_MODEL_HASH"],
            workload_dict["EXPECTED_RESULT_COLLECTOR_HASH"],
        ]

        workload_uid = "::".join(workload_props).replace(":", "_")
        results_config = {
            "bucket": self.config.bucket,
            "encrypted_result_bucket_file": f"{workload_uid}/output",
            "encrypted_key_bucket_file": f"{workload_uid}/encryption_key",
        }

        dataset_cc_config_str = json.dumps(dataset_cc_config)
        model_cc_config_str = json.dumps(model_cc_config)
        result_config_str = json.dumps(results_config)

        env_vars = {
            "DATA_CONFIG": dataset_cc_config_str,
            "MODEL_CONFIG": model_cc_config_str,
            "RESULT_CONFIG": result_config_str,
            "EXPECTED_DATA_HASH": dataset_hash,
            "EXPECTED_MODEL_HASH": model_hash,
            "RESULT_COLLECTOR": result_collector_public_key,
            "EXPECTED_RESULT_COLLECTOR_HASH": workload_dict[
                "EXPECTED_RESULT_COLLECTOR_HASH"
            ],
        }
        run_workload(self.config, docker_image, env_vars)
