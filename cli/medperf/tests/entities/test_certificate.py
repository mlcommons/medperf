import pytest
from medperf.entities.certificate import Certificate
from medperf.exceptions import MedperfException

PATCH_CERT = "medperf.entities.certificate.{}"


def test_get_user_certificate_returns_none_if_no_cert(mocker):
    # Arrange
    mocker.patch(PATCH_CERT.format("get_medperf_user_data"), return_value={"id": 1})
    mocker.patch(
        PATCH_CERT.format("Certificate.all"),
        return_value=[],
    )

    # Act
    result = Certificate.get_user_certificate()

    # Assert
    assert result is None


def test_get_user_certificate_raises_if_multiple(mocker):
    # Arrange
    mocker.patch(PATCH_CERT.format("get_medperf_user_data"), return_value={"id": 1})
    cert1 = Certificate(name="a", ca=1, certificate_content_base64="x")
    cert2 = Certificate(name="b", ca=1, certificate_content_base64="y")

    mocker.patch(
        PATCH_CERT.format("Certificate.all"),
        return_value=[cert1, cert2],
    )

    # Act + Assert
    with pytest.raises(MedperfException):
        Certificate.get_user_certificate()


def test_get_user_certificate_returns_single(mocker):
    # Arrange
    mocker.patch(PATCH_CERT.format("get_medperf_user_data"), return_value={"id": 1})
    cert = Certificate(name="a", ca=1, certificate_content_base64="x")

    mocker.patch(
        PATCH_CERT.format("Certificate.all"),
        return_value=[cert],
    )

    # Act
    result = Certificate.get_user_certificate()

    # Assert
    assert result is cert
