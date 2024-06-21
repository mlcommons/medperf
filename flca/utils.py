import google.auth
from google.cloud import secretmanager
import json
import os


def get_secret(secret_name: str):
    """Code copied and modified from medperf/server/medperf/settings.py"""

    try:
        _, os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default()
    except google.auth.exceptions.DefaultCredentialsError:
        raise Exception(
            "No local .env or GOOGLE_CLOUD_PROJECT detected. No secrets found."
        )

    # Pull secrets from Secret Manager
    print("Loading env from GCP secrets manager")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    client = secretmanager.SecretManagerServiceClient()
    settings_version = os.environ.get("SETTINGS_SECRETS_VERSION", "latest")
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{settings_version}"
    payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")
    return payload


def safe_store(content: str, path: str):
    with open(path, "w") as f:
        pass
    os.chmod(path, 0o600)
    with open(path, "a") as f:
        f.write(content)


def get_all_secrets():
    settings_name = os.environ.get("SETTINGS_SECRETS_NAME", None)
    if settings_name is None:
        raise Exception("SETTINGS_SECRETS_NAME var is not set")

    # load settings
    settings = get_secret(settings_name)
    settings_dict: dict = json.loads(settings)

    # get secrets
    secrets = {}
    for key in settings_dict.keys():
        secrets[key] = get_secret(settings_dict[key])
    return secrets
