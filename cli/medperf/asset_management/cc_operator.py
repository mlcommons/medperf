import json
from medperf.asset_management import gcp_utils


def create_service_account(service_account_name):
    gcp_utils.create_service_account(service_account_name)


def allow_operator_to_use_service_account(service_account_email, operator_account):
    gcp_utils.add_service_account_iam_policy_binding(
        service_account_email,
        f"user:{operator_account}",
        "roles/iam.serviceAccountUser",
    )


def grant_confidential_computing_workload_user(
    service_account_email, operator_project_id
):
    gcp_utils.add_project_iam_policy_binding(
        operator_project_id,
        f"serviceAccount:{service_account_email}",
        "roles/confidentialcomputing.workloadUser",
    )


def grant_logging_log_writer(service_account_email, operator_project_id):
    gcp_utils.add_project_iam_policy_binding(
        operator_project_id,
        f"serviceAccount:{service_account_email}",
        "roles/logging.logWriter",
    )


def run_workload(
    service_account_email: str, docker_image: str, vm_name: str, env_vars: dict
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

    gcp_utils.run_workload(vm_name, service_account_email, metadata)


def grant_bucket_public_read_access(bucket_name):
    gcp_utils.add_bucket_iam_policy_binding(
        bucket_name, "allUsers", "roles/storage.objectViewer"
    )


def grant_bucket_write_access(bucket_name, service_account_email):
    gcp_utils.add_bucket_iam_policy_binding(
        bucket_name,
        f"serviceAccount:{service_account_email}",
        "roles/storage.objectAdmin",
    )


class OperatorManager:
    def __init__(self, config: dict):
        operator_config = gcp_utils.GCPOperatorConfig(**config)
        self.operator_project_id = operator_config.project_id
        self.service_account_name = operator_config.service_account_name
        self.operator_account = operator_config.account
        self.vm_name = operator_config.vm_name
        self.service_account_email = operator_config.service_account_email
        self.bucket = operator_config.bucket

    def setup(self):
        """Set up complete operator infrastructure"""
        create_service_account(self.service_account_name)
        allow_operator_to_use_service_account(
            self.service_account_email,
            self.operator_account,
        )
        grant_confidential_computing_workload_user(
            self.service_account_email,
            self.operator_project_id,
        )
        grant_logging_log_writer(
            self.service_account_email,
            self.operator_project_id,
        )
        grant_bucket_public_read_access(self.bucket)
        grant_bucket_write_access(self.bucket, self.service_account_email)

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
            "bucket_name": self.bucket,
            "output_result_path": f"{workload_uid}/output",
            "results_encryption_key_path": f"{workload_uid}/encryption_key",
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
        }
        run_workload(self.service_account_email, docker_image, self.vm_name, env_vars)
