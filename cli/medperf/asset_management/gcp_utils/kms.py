from google.cloud import kms_v1 as kms
from google.iam.v1 import policy_pb2
from .types import GCPAssetConfig
import logging


def set_kms_iam_policy(config: GCPAssetConfig, members: list[str], role: str):
    client = kms.KeyManagementServiceClient()
    # Get current policy
    policy = client.get_iam_policy(request={"resource": config.full_key_name})

    # remove current decryptor roles
    to_remove = []
    for binding in policy.bindings:
        if binding.role == role:
            to_remove.append(binding)

    for binding in to_remove:
        policy.bindings.remove(binding)

    policy.bindings.append(policy_pb2.Binding(role=role, members=members))
    # Set new policy
    client.set_iam_policy(request={"resource": config.full_key_name, "policy": policy})


def encrypt_with_kms_key(config: GCPAssetConfig, plaintext: bytes) -> bytes:
    """Encrypt a string using a KMS key via Python client."""
    client = kms.KeyManagementServiceClient()

    # Encrypt
    response = client.encrypt(
        request={"name": config.full_key_name, "plaintext": plaintext}
    )

    logging.debug(f"Encrypted using {config.full_key_name}")
    return response.ciphertext
