import pytest
from medperf.exceptions import (
    InvalidCertificateAuthorityError,
    InvalidCertificateError,
    MedperfException,
)
from medperf import certificates as certs
from medperf.tests.mocks.certificate import TestCertificate
from medperf.tests.mocks.ca import TestCA
from medperf.tests.mocks.cube import TestCube

PATCH_CERTS = "medperf.certificates.{}"


# -------------------------------------------------------------------------
# verify_certificate_authority
# -------------------------------------------------------------------------


def test_verify_certificate_authority_success(mocker):
    # Arrange
    ca = TestCA()
    ca.config["fingerprint"] = "correct_fp"

    mock_cube = TestCube()
    mocker.patch(PATCH_CERTS.format("Cube.get"), return_value=mock_cube)

    mock_prepare = mocker.patch.object(ca, "prepare_config")
    mock_download = mocker.patch.object(mock_cube, "download_run_files")
    mock_run = mocker.patch.object(mock_cube, "run")

    # Act
    certs.verify_certificate_authority(ca, expected_fingerprint="correct_fp")

    # Assert
    mock_prepare.assert_called_once()
    mock_download.assert_called_once()
    mock_run.assert_called_once_with(
        task="trust",
        mounts={"ca_config": ca.config_path, "pki_assets": ca.pki_assets},
        disable_network=False,
    )


def test_verify_certificate_authority_failure_fingerprint_mismatch():
    # Arrange
    ca = TestCA()
    ca.config["fingerprint"] = "wrong_fp"

    # Act & Assert
    with pytest.raises(InvalidCertificateAuthorityError):
        certs.verify_certificate_authority(ca, expected_fingerprint="correct_fp")


# -------------------------------------------------------------------------
# verify_certificate
# -------------------------------------------------------------------------


def test_verify_certificate_success_verify_ca_true(mocker):
    # Arrange
    certificate = TestCertificate(id=1)
    certificate.ca = 1

    ca = TestCA()
    mocker.patch(PATCH_CERTS.format("CA.get"), return_value=ca)

    mock_cube = TestCube()
    mocker.patch(PATCH_CERTS.format("Cube.get"), return_value=mock_cube)

    mock_ca_prepare = mocker.patch.object(ca, "prepare_config")
    mock_cert_prepare = mocker.patch.object(
        certificate, "prepare_certificate_file", return_value="/tmp/certfolder"
    )
    mock_run = mocker.patch.object(mock_cube, "run")
    mock_verify_ca = mocker.patch(PATCH_CERTS.format("verify_certificate_authority"))

    # Act
    certs.verify_certificate(
        certificate, expected_cn="alice@example.com", verify_ca=True
    )

    # Assert
    mock_verify_ca.assert_called_once_with(ca)
    mock_ca_prepare.assert_called_once()
    mock_cert_prepare.assert_called_once()
    mock_run.assert_called_once()


def test_verify_certificate_success_verify_ca_false(mocker):
    # Arrange
    certificate = TestCertificate(id=1)
    certificate.ca = 1

    ca = TestCA()
    mocker.patch(PATCH_CERTS.format("CA.get"), return_value=ca)

    mock_cube = TestCube()
    mocker.patch(PATCH_CERTS.format("Cube.get"), return_value=mock_cube)

    mock_ca_prepare = mocker.patch.object(ca, "prepare_config")
    mock_cert_prepare = mocker.patch.object(
        certificate, "prepare_certificate_file", return_value="/tmp/certfolder"
    )
    mock_run = mocker.patch.object(mock_cube, "run")
    mock_verify_ca = mocker.patch(PATCH_CERTS.format("verify_certificate_authority"))

    # Act
    certs.verify_certificate(
        certificate, expected_cn="alice@example.com", verify_ca=False
    )

    # Assert
    mock_verify_ca.assert_not_called()
    mock_ca_prepare.assert_called_once()
    mock_cert_prepare.assert_called_once()
    mock_run.assert_called_once()


def test_verify_certificate_failure_run_exception(mocker):
    # Arrange
    certificate = TestCertificate(id=1)
    certificate.ca = 1

    ca = TestCA()
    mocker.patch(PATCH_CERTS.format("CA.get"), return_value=ca)

    mock_cube = TestCube()
    mocker.patch(PATCH_CERTS.format("Cube.get"), return_value=mock_cube)

    mocker.patch.object(ca, "prepare_config")
    mocker.patch.object(
        certificate, "prepare_certificate_file", return_value="/tmp/certfolder"
    )

    mocker.patch.object(mock_cube, "run", side_effect=MedperfException("failed"))

    # Act & Assert
    with pytest.raises(InvalidCertificateError):
        certs.verify_certificate(
            certificate, expected_cn="alice@example.com", verify_ca=False
        )
