import json
from medperf.asset_management import gcp_utils
from medperf.utils import generate_tmp_path, untar
from medperf.encryption import SymmetricEncryption, AsymmetricEncryption


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
    config: gcp_utils.GCPOperatorConfig,
    docker_image: str,
    env_vars: dict,
    workload: gcp_utils.CCWorkloadID,
):
    # Build metadata string
    metadata_parts = [
        f"tee-image-reference={docker_image}",
        "tee-container-log-redirect=true",
    ]

    # Add environment variables
    for key, value in env_vars.items():
        metadata_parts.append(f"tee-env-{key}={value}")

    if config.gpu:
        metadata_parts.append("tee-install-gpu-driver=true")

    metadata = "^~^" + "~".join(metadata_parts)

    if config.gpu:
        gcp_utils.run_gpu_workload(config, workload, metadata)
    else:
        gcp_utils.run_workload(config, workload, metadata)


def grant_bucket_read_access(config: gcp_utils.GCPOperatorConfig):
    gcp_utils.add_bucket_iam_policy_binding(
        config, f"user:{config.account}", "roles/storage.objectViewer"
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
        grant_bucket_read_access(self.config)
        grant_bucket_write_access(self.config)

    def run_workload(
        self,
        docker_image: str,
        workload: gcp_utils.CCWorkloadID,
        dataset_cc_config: dict,
        model_cc_config: dict,
        result_collector_public_key: str,
    ):
        """Run workload using operator's service account"""

        results_config = {
            "bucket": self.config.bucket,
            "encrypted_result_bucket_file": workload.results_path,
            "encrypted_key_bucket_file": workload.results_encryption_key_path,
        }

        dataset_cc_config_str = json.dumps(dataset_cc_config)
        model_cc_config_str = json.dumps(model_cc_config)
        result_config_str = json.dumps(results_config)

        env_vars = {
            "DATA_CONFIG": dataset_cc_config_str,
            "MODEL_CONFIG": model_cc_config_str,
            "RESULT_CONFIG": result_config_str,
            "EXPECTED_DATA_HASH": workload.data_hash,
            "EXPECTED_MODEL_HASH": workload.model_hash,
            "RESULT_COLLECTOR": result_collector_public_key,
            "EXPECTED_RESULT_COLLECTOR_HASH": workload.result_collector_hash,
        }
        run_workload(self.config, docker_image, env_vars, workload)

    def wait_for_workload_completion(self, workload: gcp_utils.CCWorkloadID):
        gcp_utils.wait_for_workload_completion(self.config, workload)

    def download_results(
        self,
        workload: gcp_utils.CCWorkloadID,
        private_key_bytes: bytes,
        results_path: str,
    ):

        encrypted_results_path = generate_tmp_path()
        key_path = generate_tmp_path()

        gcp_utils.download_file_from_gcs(
            self.config,
            f"gs://{self.config.bucket}/{workload.results_path}",
            encrypted_results_path,
        )
        gcp_utils.download_file_from_gcs(
            self.config,
            f"gs://{self.config.bucket}/{workload.results_encryption_key_path}",
            key_path,
        )

        with open(key_path, "rb") as key_file:
            encrypted_key = key_file.read()

        decryption_key = AsymmetricEncryption().decrypt(
            private_key_bytes, encrypted_key
        )

        tmp_key_path = generate_tmp_path()
        with open(tmp_key_path, "wb") as tmp_key_file:
            tmp_key_file.write(decryption_key)

        results_archive_path = generate_tmp_path()
        SymmetricEncryption().decrypt_file(
            encrypted_results_path, tmp_key_path, results_archive_path
        )

        # Extract results
        untar(results_archive_path, remove=True, extract_to=results_path)
