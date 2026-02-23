from medperf.utils import generate_tmp_path
from medperf.asset_management import gcp_utils


class AssetPolicyManager:
    def __init__(self, config: dict, encryption_key_file: str):
        self.config = gcp_utils.GCPAssetConfig(**config)
        self.encryption_key_file = encryption_key_file

    def __create_keyring(self):
        gcp_utils.create_keyring(self.config)

    def __create_key(self):
        gcp_utils.create_kms_key(self.config)

    def __add_key_iam_binding(self):
        gcp_utils.add_kms_key_iam_policy_binding(
            self.config,
            f"user:{self.config.account}",
            "roles/cloudkms.cryptoKeyEncrypter",
        )

    def __create_workload_identity_pool(self):
        gcp_utils.create_workload_identity_pool(self.config)

    def __encrypt_key(self):
        tmp_encrypted_key_path = generate_tmp_path()

        gcp_utils.encrypt_with_kms_key(
            self.config, self.encryption_key_file, tmp_encrypted_key_path
        )
        return tmp_encrypted_key_path

    def __upload_encrypted_key(self, tmp_encrypted_key_path):
        gcp_utils.upload_file_to_gcs(
            self.config,
            tmp_encrypted_key_path,
            f"gs://{self.config.bucket}/{self.config.encrypted_key_bucket_file}",
        )

    def __create_wip_oidc_provider(self, policy: dict[str, str]):
        # IMPORTANT: https://docs.cloud.google.com/confidential-computing/
        # confidential-space/docs/create-grant-access-confidential-resources#attestation-assertions
        google_subject_attr = (
            'google.subject="gcpcs::"'
            '+assertion.submods.container.image_digest+"::"'
            '+assertion.submods.gce.project_number+"::"'
            "+assertion.submods.gce.instance_id"
        )
        workload_uid_attr = (
            "attribute.workload_uid="
            'assertion.submods.container.image_digest+"::"+'
            'assertion.submods.container.env_override.EXPECTED_DATA_HASH+"::"+'
            'assertion.submods.container.env_override.EXPECTED_MODEL_HASH+"::"+'
            "assertion.submods.container.env_override.EXPECTED_RESULT_COLLECTOR_HASH"
        )

        attribute_mapping = google_subject_attr + "," + workload_uid_attr
        attribute_condition = 'assertion.swname == "CONFIDENTIAL_SPACE"'

        if "location" in policy:
            location_condition = f'assertion.submods.gce.zone == "{policy["location"]}"'
            attribute_condition += f" && {location_condition}"

        if "hardware" in policy:
            hardware_condition = f'assertion.hwmodel == "{policy["hardware"]}"'
            attribute_condition += f" && {hardware_condition}"

        if "gpu_cc_mode" in policy:
            gpu_cc_mode_condition = (
                f'assertion.submods.nvidia_gpu.cc_mode == "{policy["gpu_cc_mode"]}"'
            )
            attribute_condition += f" && {gpu_cc_mode_condition}"

        gcp_utils.create_workload_identity_pool_oidc_provider(
            self.config, attribute_mapping, attribute_condition
        )

    def __bind_kms_decrypter_role(self, permitted_workloads: list[dict[str, str]]):
        principal_set = (
            f"principalSet://iam.googleapis.com/projects/{self.config.project_number}/"
            f"locations/global/workloadIdentityPools/{self.config.wip}/attribute.workload_uid/"
        )
        principal_set_list = []

        for workload in permitted_workloads:
            workload_props = [
                workload["image_digest"],
                workload["EXPECTED_DATA_HASH"],
                workload["EXPECTED_MODEL_HASH"],
                workload["EXPECTED_RESULT_COLLECTOR_HASH"],
            ]
            principal_set_list.append(principal_set + "::".join(workload_props))

        gcp_utils.set_kms_iam_policy(
            self.config,
            principal_set_list,
            "roles/cloudkms.cryptoKeyDecrypter",
        )

    def setup(self):
        self.__create_keyring()
        self.__create_key()
        self.__add_key_iam_binding()
        self.__create_workload_identity_pool()

    def setup_policy(self, policy: dict[str, str]):
        tmp_encrypted_key_path = self.__encrypt_key()
        self.__upload_encrypted_key(tmp_encrypted_key_path)
        self.__create_wip_oidc_provider(policy)

    def configure_policy(self, permitted_workloads: list[dict[str, str]]):
        self.__bind_kms_decrypter_role(permitted_workloads)
