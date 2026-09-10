"""Google Cloud KMS calls, on one key."""

import logging

from google.cloud import kms_v1 as kms
from google.iam.v1 import policy_pb2


def encrypt(key_name: str, plaintext: bytes) -> bytes:
    """Wraps a key with a KMS key that never leaves the service."""
    client = kms.KeyManagementServiceClient()
    response = client.encrypt(request={"name": key_name, "plaintext": plaintext})
    logging.debug(f"Encrypted using {key_name}")
    return response.ciphertext


def set_iam_policy(key_name: str, members: list, role: str):
    """Replaces every member holding `role` on the key.

    Replaces rather than adds, because this is how a grant is taken away: what
    the caller leaves out stops being able to decrypt."""
    client = kms.KeyManagementServiceClient()
    policy = client.get_iam_policy(request={"resource": key_name})

    for binding in [b for b in policy.bindings if b.role == role]:
        policy.bindings.remove(binding)
    policy.bindings.append(policy_pb2.Binding(role=role, members=members))

    client.set_iam_policy(request={"resource": key_name, "policy": policy})
