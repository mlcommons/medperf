from typing import Union
from google.cloud import storage
from .types import GCPAssetConfig, GCPOperatorConfig


def upload_file_to_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], local_file: str, gcs_path: str
):
    """Upload file to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_file)


def upload_from_file_object_to_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], file: object, gcs_path: str
):
    """Upload file to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    blob = bucket.blob(gcs_path)
    blob.upload_from_file(file)


def upload_string_to_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], content: bytes, gcs_path: str
):
    """Upload string content to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(content)


def download_file_from_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], gcs_path: str, local_file: str
):
    """Download file from Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(local_file)


def download_string_from_gcs(
    config: Union[GCPAssetConfig, GCPOperatorConfig], gcs_path: str
) -> bytes:
    """Download string content from Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    blob = bucket.blob(gcs_path)
    return blob.download_as_bytes()


def check_gcs_file_exists(
    config: Union[GCPAssetConfig, GCPOperatorConfig], gcs_path: str
) -> bool:
    client = storage.Client()
    bucket = client.bucket(config.bucket)
    return bucket.blob(gcs_path).exists()


def set_gcs_iam_policy(config: GCPAssetConfig, members: list[str], role: str):
    client = storage.Client()
    # Get current policy

    policy = client.bucket(config.bucket).get_iam_policy()

    # remove current objectviewer roles
    to_remove = []
    for binding in policy.bindings:
        if binding["role"] == role:
            to_remove.append(binding)

    for binding in to_remove:
        policy.bindings.remove(binding)

    policy.bindings.append({"role": role, "members": members})

    # Set new policy
    client.bucket(config.bucket).set_iam_policy(policy)
