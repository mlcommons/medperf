"""Google Cloud key release: KMS wraps the key, IAM decides who may unwrap it.

The workload identity pool is told how to build a workload's identity out of
attestation assertions, and the key is bound to the identities the owner
permits. Both are rendered from the same `WorkloadScope`, so they cannot end
up describing different sets of terms.
"""

from typing import List

from pydantic import BaseModel

from medperf_cc.backends.gcp import checks
from medperf_cc.backends.gcp.config import WorkloadIdentityPool
from medperf_cc.backends.gcp.credentials import get_user_credentials
from medperf_cc.errors import ConfigurationError, OperationError
from medperf_cc.identity import TERM_CLAIMS, WorkloadScope
from medperf_cc.policy import AssetPolicy
from medperf_cc.storage.gcp import client as gcs
from medperf_cc.vault.base import AssetVault
from medperf_cc.vault.gcp import kms, workload_identity

GCP_VAULT = "gcp"

KMS_DECRYPTER_ROLE = "roles/cloudkms.cryptoKeyDecrypter"
KMS_ENCRYPTER_ROLE = "roles/cloudkms.cryptoKeyEncrypter"
KMS_ADMIN_ROLE = "roles/cloudkms.admin"
WIP_ADMIN_ROLE = "roles/iam.workloadIdentityPoolAdmin"

# IMPORTANT: https://docs.cloud.google.com/confidential-computing/
# confidential-space/docs/create-grant-access-confidential-resources#attestation-assertions
GOOGLE_SUBJECT_ASSERTION = (
    '"gcpcs::"'
    '+assertion.submods.container.image_digest+"::"'
    '+assertion.submods.gce.project_number+"::"'
    "+assertion.submods.gce.instance_id"
)


def workload_uid_assertion(scope: WorkloadScope) -> str:
    """The CEL that rebuilds a workload's identity from its attestation.

    `assertion.` is how a workload identity pool addresses a token claim, so
    this is the same claim paths the scope is defined over, in the same
    order, spelled the way Google evaluates them."""
    return '+"::"+'.join(f"assertion.{TERM_CLAIMS[term]}" for term in scope.terms)


class GCPVaultConfig(BaseModel):
    project_id: str
    project_number: str
    bucket: str
    keyring_name: str
    key_name: str
    key_location: str
    wip: str
    wip_provider: str

    @property
    def full_key_name(self) -> str:
        return (
            f"projects/{self.project_id}/locations/{self.key_location}/"
            f"keyRings/{self.keyring_name}/cryptoKeys/{self.key_name}"
        )

    class Config:
        extra = "ignore"


class GCPVault(AssetVault):
    SETTINGS = GCPVaultConfig

    def __init__(
        self,
        config: dict,
        asset_name: str,
        scope: WorkloadScope,
        policy: AssetPolicy,
    ):
        super().__init__(config, asset_name, scope, policy)
        self.gcp = GCPVaultConfig(**config)
        self.pool = WorkloadIdentityPool(**config)

    @property
    def backend(self) -> str:
        return GCP_VAULT

    @property
    def wrapped_key_path(self) -> str:
        return f"{self.asset_name}_key.enc"

    def verify(self) -> None:
        credentials = get_user_credentials()
        # Every check is a network call that returns a message when something
        # is missing, so the chain stops at the first thing that is wrong.
        problem = (
            checks.check_user_role_on_kms_key(
                credentials, self.gcp.full_key_name, KMS_ENCRYPTER_ROLE
            )
            or checks.check_user_role_on_kms_key(
                credentials, self.gcp.full_key_name, KMS_ADMIN_ROLE
            )
            or checks.check_user_role_on_wip(
                credentials, self.pool.full_name, WIP_ADMIN_ROLE
            )
        )
        if problem:
            raise ConfigurationError(f"Key release is not usable: {problem}")

    def publish_key(self, encryption_key: bytes) -> None:
        wrapped = kms.encrypt(self.gcp.full_key_name, encryption_key)
        gcs.upload_string(self.gcp.bucket, wrapped, self.wrapped_key_path)
        self.__install_attribute_mapping()

    def permit(self, identities: List[str]) -> None:
        principals = [self.pool.principal(identity) for identity in identities]
        kms.set_iam_policy(self.gcp.full_key_name, principals, KMS_DECRYPTER_ROLE)

    def workload_config(self) -> dict:
        return {
            "backend": self.backend,
            "bucket": self.gcp.bucket,
            "wrapped_key_path": self.wrapped_key_path,
            "key_name": self.gcp.full_key_name,
            "workload_identity_pool_provider": self.__provider_name(),
        }

    def __provider_name(self) -> str:
        return self.pool.provider_name

    def __install_attribute_mapping(self) -> None:
        attribute_mapping = {
            "google.subject": GOOGLE_SUBJECT_ASSERTION,
            "attribute.workload_uid": workload_uid_assertion(self.scope),
        }

        condition = 'assertion.swname == "CONFIDENTIAL_SPACE"'
        gpu_mode = 'assertion.submods.nvidia_gpu.cc_mode == "ON"'
        stable_image = (
            "'STABLE' in assertion.submods.confidential_space.support_attributes"
        )
        # The cGPU images do not report STABLE yet. Whatever this grants a key
        # to, `AttestationRequirements.__is_hardened` has to accept a proof
        # from, or a released key produces results nobody can verify.
        condition += f" && ({gpu_mode} || {stable_image})"

        if self.policy.location:
            condition += f' && assertion.submods.gce.zone == "{self.policy.location}"'
        if self.policy.hardware:
            condition += f' && assertion.hwmodel == "{self.policy.hardware}"'

        try:
            workload_identity.update_oidc_provider(
                self.__provider_name(), attribute_mapping, condition
            )
        except Exception as e:
            raise OperationError(
                f"Failed to update workload identity pool provider: {e}"
            )
