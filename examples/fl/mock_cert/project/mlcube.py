"""MLCube handler file"""

import typer
import shutil
import json
import os

app = typer.Typer()


def asserts(ca_config):
    with open(ca_config) as f:
        config = json.load(f)
    assert config["address"] == "https://127.0.0.1"
    assert config["port"] == 443
    assert config["fingerprint"] == "fingerprint"
    assert config["client_provisioner"] == "auth0"
    assert config["server_provisioner"] == "acme"


@app.command("trust")
def trust(
    ca_config: str = typer.Option(..., "--ca_config"),
    pki_assets: str = typer.Option(..., "--pki_assets"),
):
    asserts(ca_config)
    shutil.copytree("/mlcube_project/ca/cert", pki_assets, dirs_exist_ok=True)


@app.command("get_client_cert")
def get_client_cert(
    ca_config: str = typer.Option(..., "--ca_config"),
    pki_assets: str = typer.Option(..., "--pki_assets"),
):
    asserts(ca_config)
    os.system(f"sh /mlcube_project/sign.sh -o {pki_assets}")


@app.command("get_server_cert")
def get_server_cert(
    ca_config: str = typer.Option(..., "--ca_config"),
    pki_assets: str = typer.Option(..., "--pki_assets"),
):
    asserts(ca_config)
    os.system(f"sh /mlcube_project/sign.sh -o {pki_assets} -s")


@app.command("verify_cert")
def verify_cert(
    ca_config: str = typer.Option(..., "--ca_config"),
    pki_assets: str = typer.Option(..., "--pki_assets"),
):
    asserts(ca_config)
    assert os.path.exists(os.path.join(pki_assets, "crt.crt"))


if __name__ == "__main__":
    app()
