from medperf.entities.ca import CA
from medperf.entities.cube import Cube
from medperf.entities.certificate import Certificate
from medperf import config
from medperf.exceptions import (
    MedperfException,
    InvalidCertificateError,
    InvalidCertificateAuthorityError,
)


def get_client_cert(ca: CA, email: str, output_path: str):
    """Responsible for getting a user cert"""
    common_name = email
    ca.prepare_config()
    mounts = {
        "ca_config": ca.config_path,
        "pki_assets": output_path,
    }
    env = {"MEDPERF_INPUT_CN": common_name}

    mlcube = Cube.get(ca.client_mlcube)
    mlcube.download_run_files()
    mlcube.run(task="get_client_cert", mounts=mounts, env=env, disable_network=False)


def get_server_cert(ca: CA, address: str, output_path: str):
    """Responsible for getting a server cert"""
    common_name = address
    ca.prepare_config()
    mounts = {
        "ca_config": ca.config_path,
        "pki_assets": output_path,
    }
    env = {"MEDPERF_INPUT_CN": common_name}

    mlcube = Cube.get(ca.server_mlcube)
    mlcube.download_run_files()
    mlcube.run(
        task="get_server_cert",
        mounts=mounts,
        env=env,
        ports=["0.0.0.0:80:80"],
        disable_network=False,
    )


def verify_certificate_authority(ca: CA, expected_fingerprint=None):
    """Verifies the CA cert fingerprint and writes it to the MedPerf storage."""
    if expected_fingerprint is None:
        expected_fingerprint = config.certificate_authority_fingerprint
    if ca.config["fingerprint"] != expected_fingerprint:
        raise InvalidCertificateAuthorityError(
            "Certificate authority fingerprint doesn't match the configured one"
        )
    ca.prepare_config()
    mounts = {
        "ca_config": ca.config_path,
        "pki_assets": ca.pki_assets,
    }
    mlcube = Cube.get(ca.ca_mlcube)
    mlcube.download_run_files()
    try:
        mlcube.run(task="trust", mounts=mounts, disable_network=False)
    except MedperfException as e:
        raise InvalidCertificateAuthorityError(
            f"Failed to verify the certificate authority: {str(e)}"
        )


def verify_certificate(
    certificate: Certificate, expected_cn: str, verify_ca: bool = True
):
    ca = CA.get(certificate.ca)
    if verify_ca:
        verify_certificate_authority(ca)
    ca.prepare_config()
    ca_container = Cube.get(ca.ca_mlcube)
    cert_folder = certificate.prepare_certificate_file()
    mounts = {"pki_assets": cert_folder, "ca_config": ca.config_path}
    env = {"MEDPERF_INPUT_CN": expected_cn}
    try:
        ca_container.run(
            task="verify_cert", mounts=mounts, env=env, disable_network=False
        )
    except MedperfException as e:
        raise InvalidCertificateError(f"Failed to verify the certificate: {str(e)}")


def verify_certificate_authority_by_id(ca_id: int, expected_fingerprint: str):
    ca = CA.get(ca_id)
    verify_certificate_authority(ca, expected_fingerprint)
