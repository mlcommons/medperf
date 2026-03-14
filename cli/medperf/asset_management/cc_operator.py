import json
from medperf.asset_management.gcp_utils import (
    GCPOperatorConfig,
    CCWorkloadID,
    download_file_from_gcs,
    check_gcs_file_exists,
    run_workload,
    wait_for_workload_completion,
)
from medperf.asset_management.operator_check import verify_operator_setup
from medperf.exceptions import MedperfException, ExecutionError
from medperf.utils import generate_tmp_path, untar
from medperf.encryption import SymmetricEncryption, AsymmetricEncryption


class OperatorManager:
    def __init__(self, config: dict):
        self.config = GCPOperatorConfig(**config)

    def setup(self):
        """Set up complete operator infrastructure"""
        success, message = verify_operator_setup(
            self.config.service_account_email, self.config.bucket
        )

        if not success:
            raise MedperfException(f"Operator setup verification failed: {message}")

    def run_workload(
        self,
        docker_image: str,
        workload: CCWorkloadID,
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
        metadata = {}
        metadata["tee-image-reference"] = docker_image
        metadata["tee-container-log-redirect"] = "true"

        # Add environment variables
        for key, value in env_vars.items():
            metadata[f"tee-env-{key}"] = value

        try:
            run_workload(self.config, metadata)
        except Exception:
            raise ExecutionError(
                "Failed to run workload: User lacks permissions or VM does not exist"
            )

    def wait_for_workload_completion(self, workload: CCWorkloadID):
        wait_for_workload_completion(self.config, workload)

    def results_exist(self, workload: CCWorkloadID):
        results_exist = check_gcs_file_exists(self.config, workload.results_path)
        if not results_exist:
            return False
        decryption_key_exists = check_gcs_file_exists(
            self.config, workload.results_encryption_key_path
        )
        return decryption_key_exists

    def download_results(
        self,
        workload: CCWorkloadID,
        private_key_bytes: bytes,
        results_path: str,
    ):

        encrypted_results_path = generate_tmp_path()
        key_path = generate_tmp_path()

        download_file_from_gcs(
            self.config,
            f"gs://{self.config.bucket}/{workload.results_path}",
            encrypted_results_path,
        )
        download_file_from_gcs(
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
