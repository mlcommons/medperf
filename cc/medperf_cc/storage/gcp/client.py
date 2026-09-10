"""Google Cloud Storage calls, on one bucket."""

from google.cloud import storage


def upload_file_object(bucket_name: str, file_object, path: str):
    client = storage.Client()
    client.bucket(bucket_name).blob(path).upload_from_file(file_object)


def upload_string(bucket_name: str, content: bytes, path: str):
    client = storage.Client()
    client.bucket(bucket_name).blob(path).upload_from_string(content)


def download_file(bucket_name: str, path: str, local_file: str):
    client = storage.Client()
    client.bucket(bucket_name).blob(path).download_to_filename(local_file)


def download_string(bucket_name: str, path: str) -> bytes:
    client = storage.Client()
    return client.bucket(bucket_name).blob(path).download_as_bytes()


def file_exists(bucket_name: str, path: str) -> bool:
    client = storage.Client()
    return client.bucket(bucket_name).blob(path).exists()


def set_iam_policy(bucket_name: str, members: list, role: str):
    """Replaces every member holding `role` on the bucket.

    Replaces rather than adds, because this is how a grant is taken away: what
    the caller leaves out stops being able to read."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    policy = bucket.get_iam_policy()

    for binding in [b for b in policy.bindings if b["role"] == role]:
        policy.bindings.remove(binding)
    policy.bindings.append({"role": role, "members": members})

    bucket.set_iam_policy(policy)
