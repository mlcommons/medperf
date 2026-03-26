from cryptography.hazmat.primitives import serialization
import yaml
from distutils.dir_util import copy_tree
import os
import tomllib
import tomli_w
import base64
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    Encoding,
    PublicFormat,
)
from cryptography import x509


def get_train_val_paths(data_path, labels_path):
    return data_path, labels_path, data_path, labels_path


def get_server_connection(plan_path):
    with open(plan_path) as f:
        plan = yaml.safe_load(f)
    address = plan["aggregator"]["address"]
    port = plan["aggregator"]["port"]
    admin_port = plan["aggregator"]["admin_port"]
    return address, port, admin_port


def setup_job(src_folder, plan_path, ca_cert_path):
    workspace_folder = "/tmp/flwr_ws"
    copy_tree(src_folder, workspace_folder)
    toml_template = os.path.join(workspace_folder, "pyproject_tpl.toml")
    with open(toml_template, "rb") as f:
        toml_config = tomllib.load(f)
    with open(plan_path) as f:
        plan = yaml.safe_load(f)
    toml_config["tool"]["flwr"]["app"]["config"] = plan["config"]
    deployment = toml_config["tool"]["flwr"]["federations"]["default"]

    address, _, admin_port = get_server_connection(plan_path)
    toml_config["tool"]["flwr"]["federations"][deployment]["address"] = (
        f"{address}:{admin_port}"
    )
    toml_config["tool"]["flwr"]["federations"][deployment]["root-certificates"] = (
        ca_cert_path
    )

    toml_file = os.path.join(workspace_folder, "pyproject.toml")

    with open(toml_file, "w") as f:
        f.write(tomli_w.dumps(toml_config))
    return workspace_folder


def get_collaborators_public_keys(collaborators_path) -> list[bytes]:
    with open(collaborators_path) as f:
        collaborators = yaml.safe_load(f)
    public_keys = []
    for col_info in collaborators.values():
        cert_b64 = col_info["certificate"]
        certificate_bytes = base64.b64decode(cert_b64)
        certificate_obj = x509.load_pem_x509_certificate(data=certificate_bytes)
        public_key = certificate_obj.public_key()
        ssh_bytes = public_key.public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH)
        public_keys.append(ssh_bytes)
    return public_keys


def get_openssh_format_private_key_path(node_cert_folder):
    key_path = os.path.join(node_cert_folder, "key.key")
    ssh_formatted_key_path = os.path.join("/tmp", ".openssh_key.pem")
    with open(key_path, "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)

    # Re-serialize in OpenSSH format
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with open(ssh_formatted_key_path, "wb") as f:
        f.write(private_bytes)

    return ssh_formatted_key_path
