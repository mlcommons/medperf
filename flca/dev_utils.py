import json
import os


def safe_store(content: str, path: str):
    with open(path, "w") as f:
        pass
    os.chmod(path, 0o600)
    with open(path, "a") as f:
        f.write(content)


def get_all_secrets():
    # load settings
    with open("/assets/settings.json") as f:
        settings = json.load(f)

    # get secrets
    secrets = {}
    for key in settings.keys():
        with open(settings[key]) as f:
            secrets[key] = f.read()
    return secrets
