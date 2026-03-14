from medperf.exceptions import MedperfException
from medperf.asset_management.gcp_utils import (
    GCPAssetConfig,
    CCWorkloadID,
    upload_string_to_gcs,
    encrypt_with_kms_key,
    set_kms_iam_policy,
    set_gcs_iam_policy,
    update_workload_identity_pool_oidc_provider,
)


def get_workload_id_scheme(for_model: bool = False):
    if for_model:
        return (
            'assertion.submods.container.image_digest+"::"+'
            "assertion.submods.container.env_override.EXPECTED_MODEL_HASH"
        )

    else:
        return (
            'assertion.submods.container.image_digest+"::"+'
            'assertion.submods.container.env_override.EXPECTED_DATA_HASH+"::"+'
            'assertion.submods.container.env_override.EXPECTED_MODEL_HASH+"::"+'
            "assertion.submods.container.env_override.EXPECTED_RESULT_COLLECTOR_HASH"
        )


class AssetPolicyManager:
    def __init__(self, config: dict, for_model: bool = False):
        self.config = GCPAssetConfig(**config)
        self.for_model = for_model

    def __encrypt_key(self, encryption_key: bytes):
        encrypted_key = encrypt_with_kms_key(self.config, encryption_key)
        return encrypted_key

    def __upload_encrypted_key(self, encrypted_key):
        upload_string_to_gcs(
            self.config,
            encrypted_key,
            self.config.encrypted_key_bucket_file,
        )

    def __update_wip_oidc_provider(
        self, policy: dict[str, str], for_model: bool = False
    ):
        # IMPORTANT: https://docs.cloud.google.com/confidential-computing/
        # confidential-space/docs/create-grant-access-confidential-resources#attestation-assertions
        google_subject_attr = (
            '"gcpcs::"'
            '+assertion.submods.container.image_digest+"::"'
            '+assertion.submods.gce.project_number+"::"'
            "+assertion.submods.gce.instance_id"
        )
        workload_uid_attr = get_workload_id_scheme(for_model=for_model)
        attribute_mapping = {
            "google.subject": google_subject_attr,
            "attribute.workload_uid": workload_uid_attr,
        }
        attribute_condition = 'assertion.swname == "CONFIDENTIAL_SPACE"'
        attribute_condition += (
            " && 'STABLE' in assertion.submods.confidential_space.support_attributes"
        )
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
        try:
            update_workload_identity_pool_oidc_provider(
                self.config, attribute_mapping, attribute_condition
            )
        except Exception as e:
            raise MedperfException(
                f"Failed to update workload identity pool OIDC provider: {e}"
            )

    def __get_principal_set(
        self, permitted_workloads: list[CCWorkloadID], for_model: bool = False
    ):
        principal_set = (
            f"principalSet://iam.googleapis.com/projects/{self.config.project_number}/"
            f"locations/global/workloadIdentityPools/{self.config.wip}/attribute.workload_uid/"
        )
        principal_set_list = []

        for workload in permitted_workloads:
            workload_id = workload.id_for_model if for_model else workload.id
            principal_set_list.append(principal_set + workload_id)

        return principal_set_list

    def __bind_kms_decrypter_role(
        self, permitted_workloads: list[CCWorkloadID], for_model: bool = False
    ):
        principal_set_list = self.__get_principal_set(permitted_workloads, for_model)
        set_kms_iam_policy(
            self.config,
            principal_set_list,
            "roles/cloudkms.cryptoKeyDecrypter",
        )

    def __bind_gcs_object_viewer_role(
        self, permitted_workloads: list[CCWorkloadID], for_model: bool = False
    ):
        principal_set_list = self.__get_principal_set(permitted_workloads, for_model)
        set_gcs_iam_policy(
            self.config,
            principal_set_list,
            "roles/storage.objectViewer",
        )

    def setup(self):
        pass

    def setup_policy(self, policy: dict[str, str], encryption_key: bytes):
        encrypted_key = self.__encrypt_key(encryption_key)
        self.__upload_encrypted_key(encrypted_key)
        self.__update_wip_oidc_provider(policy, for_model=self.for_model)

    def configure_policy(self, permitted_workloads: list[CCWorkloadID]):
        self.__bind_kms_decrypter_role(permitted_workloads, for_model=self.for_model)
        self.__bind_gcs_object_viewer_role(
            permitted_workloads, for_model=self.for_model
        )
