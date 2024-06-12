import os
import json
from utils import get_all_secrets, safe_store


def validate(secrets: dict):
    """main settings are expected to be a json file that contains secrets IDs of other objects"""
    expected_keys = set(
        [
            "ca_config",
            "intermediate_ca_key",
            "intermediate_ca_password",
            "root_ca_crt",
            "intermediate_ca_crt",
            "client_x509_template",
            "server_x509_template",
            "db_config",
        ]
    )
    if os.environ.get("USE_PROXY", None):
        expected_keys.add("proxy_config")

    if expected_keys != set(secrets.keys()):
        msg = "Expected keys: " + ", ".join(expected_keys)
        msg += "\nFound keys: " + ", ".join(set(secrets.keys()))
        raise ValueError(msg)


def setup():
    step_path = os.environ.get("STEPPATH", None)
    if step_path is None:
        raise Exception("STEPPATH var is not set")

    secrets = get_all_secrets()
    validate(secrets)

    # Create folders
    secrets_folder = os.path.join(step_path, "secrets")
    certs_folder = os.path.join(step_path, "certs")
    config_folder = os.path.join(step_path, "config")
    templates_folder = os.path.join(step_path, "templates", "certs", "x509")
    os.makedirs(secrets_folder, mode=0o600)
    os.makedirs(certs_folder, mode=0o600)
    os.makedirs(config_folder, mode=0o600)
    os.makedirs(templates_folder, mode=0o600)

    # store key and its password
    intermediate_ca_key_path = os.path.join(secrets_folder, "intermediate_ca_key")
    safe_store(secrets["intermediate_ca_key"], intermediate_ca_key_path)

    password_path = os.path.join(secrets_folder, "pwd.txt")
    safe_store(secrets["intermediate_ca_password"], password_path)

    # store root and intermediate certs
    root_ca_crt_path = os.path.join(certs_folder, "root_ca.crt")
    safe_store(secrets["root_ca_crt"], root_ca_crt_path)

    intermediate_ca_crt_path = os.path.join(certs_folder, "intermediate_ca.crt")
    safe_store(secrets["intermediate_ca_crt"], intermediate_ca_crt_path)

    # store signing templates
    client_tpl_path = os.path.join(templates_folder, "client.tpl")
    safe_store(secrets["client_x509_template"], client_tpl_path)

    server_tpl_path = os.path.join(templates_folder, "server.tpl")
    safe_store(secrets["server_x509_template"], server_tpl_path)

    # Get config
    config = json.loads(secrets["ca_config"])

    # Override config with runtime paths
    config["root"] = root_ca_crt_path
    config["crt"] = intermediate_ca_crt_path
    config["key"] = intermediate_ca_key_path
    # assuming server provisioner is the first one, and client is second
    config["authority"]["provisioners"][0]["options"]["x509"][
        "templateFile"
    ] = server_tpl_path
    config["authority"]["provisioners"][1]["options"]["x509"][
        "templateFile"
    ] = client_tpl_path

    # Override db config
    config["db"] = json.loads(secrets["db_config"])

    # write config
    ca_config_path = os.path.join(config_folder, "ca.json")
    safe_store(json.dumps(config), ca_config_path)

    # setup proxy
    if os.environ.get("USE_PROXY", None):
        safe_store(secrets["proxy_config"], "/etc/nginx/http.d/reverse-proxy.conf")


if __name__ == "__main__":
    setup()
