from medperf.utils import generate_tmp_path
from medperf.asset_management import gcp_utils


class AssetPolicyManager:
    def __init__(self, config: dict, encryption_key_file: str):
        self.encryption_key_file = encryption_key_file

        self.asset_path = config["asset_path"]
        self.gcp_project_id = config["gcp_project_id"]
        self.gcp_project_number = config["gcp_project_number"]
        self.gcp_keyring_name = config["gcp_keyring_name"]
        self.gcp_key_name = config["gcp_key_name"]
        self.gcp_account = config["gcp_account"]
        self.gcp_wip = config["gcp_wip"]
        self.gcp_bucket = config["gcp_bucket"]
        self.gcp_encrypted_key_bucket_file = config["gcp_encrypted_key_bucket_file"]

    def __create_keyring(self):
        gcp_utils.create_keyring(self.gcp_keyring_name)

    def __create_key(self):
        gcp_utils.create_kms_key(self.gcp_key_name, self.gcp_keyring_name)

    def __add_key_iam_binding(self):
        key_resource = (
            f"projects/{self.gcp_project_id}/locations/global/"
            f"keyRings/{self.gcp_keyring_name}/cryptoKeys/{self.gcp_key_name}"
        )
        gcp_utils.add_kms_key_iam_policy_binding(
            key_resource,
            f"user:{self.gcp_account}",
            "roles/cloudkms.cryptoKeyEncrypter",
        )

    def __create_workload_identity_pool(self):
        gcp_utils.create_workload_identity_pool(self.gcp_wip)

    def __encrypt_key(self):
        tmp_encrypted_key_path = generate_tmp_path()
        key_resource = (
            f"projects/{self.gcp_project_id}/locations/global/"
            f"keyRings/{self.gcp_keyring_name}/cryptoKeys/{self.gcp_key_name}"
        )
        gcp_utils.encrypt_with_kms_key(
            self.encryption_key_file,
            tmp_encrypted_key_path,
            key_resource,
        )
        return tmp_encrypted_key_path

    def __upload_encrypted_key(self, tmp_encrypted_key_path):
        gcp_utils.upload_file_to_gcs(
            tmp_encrypted_key_path,
            f"gs://{self.gcp_bucket}/{self.gcp_encrypted_key_bucket_file}",
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
        attributes = [google_subject_attr]
        for key in policy:
            attribute = f"attribute.{key}={gcp_utils.POLICY_ATTRIBUTES_MAPPING[key]}"
            attributes.append(attribute)

        attribute_mapping = ",".join(attributes)

        gcp_utils.create_workload_identity_pool_oidc_provider(
            self.gcp_wip, attribute_mapping
        )

    def __bind_kms_decrypter_role(self, policy: dict[str, str]):
        key_resource = (
            f"projects/{self.gcp_project_id}/locations/global/"
            f"keyRings/{self.gcp_keyring_name}/cryptoKeys/{self.gcp_key_name}"
        )

        principal_set = (
            f"principalSet://iam.googleapis.com/projects/{self.gcp_project_number}/"
            f"locations/global/workloadIdentityPools/{self.gcp_wip}"
        )
        for key, val in policy.items():
            principal_set += f"/attribute.{key}/{val}"

        gcp_utils.add_kms_key_iam_policy_binding(
            key_resource,
            principal_set,
            "roles/cloudkms.cryptoKeyDecrypter",
        )

    def __reset_kms_binding(self, role, member):
        """Clear all members from a role, then add the new member"""
        key_name = self.__get_kms_key_resource()

        # Get current policy
        policy = self.kms_client.get_iam_policy(request={"resource": key_name})

        # Remove all bindings for this role
        policy.bindings[:] = [
            binding for binding in policy.bindings if binding.role != role
        ]

        # Add new binding
        new_binding = policy_pb2.Binding(role=role, members=[member])
        policy.bindings.append(new_binding)

        # Set updated policy
        self.kms_client.set_iam_policy(request={"resource": key_name, "policy": policy})

        print(f"Set {role} to: {member}")

    def setup(self):
        self.__create_keyring()
        self.__create_key()
        self.__add_key_iam_binding()
        self.__create_workload_identity_pool()

    def setup_policy(self):
        tmp_encrypted_key_path = self.__encrypt_key()
        self.__upload_encrypted_key(tmp_encrypted_key_path)

    def configure_policy(self, policy: dict[str, str]):
        # todo: split to create, and update. use gcloud python sdk
        self.__create_wip_oidc_provider(policy)
        self.__bind_kms_decrypter_role(policy)
