import pytest
import base64
import uuid
import medperf.config as config

from medperf.commands.certificate.submit import SubmitCertificate
from medperf.exceptions import CleanExit, MedperfException
from medperf.tests.mocks.certificate import TestCertificate

PATCH_SUBMIT = "medperf.commands.certificate.submit.{}"


@pytest.fixture
def submit(mocker, fs):
    # Arrange
    mocker.patch(
        PATCH_SUBMIT.format("get_medperf_user_data"),
        return_value={"email": "alice@example.com"},
    )
    mocker.patch(PATCH_SUBMIT.format("get_pki_assets_path"), return_value="/pki")
    mocker.patch(PATCH_SUBMIT.format("uuid.uuid4"), return_value=uuid.UUID(int=999))
    mocker.patch(PATCH_SUBMIT.format("verify_certificate"))
    mocker.patch(PATCH_SUBMIT.format("approval_prompt"), return_value=True)

    fs.create_file(f"/pki/{config.certificate_file}", contents=b"certificate-bytes")

    return SubmitCertificate(approved=False)


def test_prepare_raises_if_no_certificate(mocker):
    # Arrange
    mocker.patch(
        PATCH_SUBMIT.format("get_medperf_user_data"),
        return_value={"email": "alice@example.com"},
    )
    mocker.patch(PATCH_SUBMIT.format("get_pki_assets_path"), return_value="/missing")
    sc = SubmitCertificate()

    # Act & Assert
    with pytest.raises(MedperfException):
        sc.prepare()


def test_prepare_loads_certificate(submit):
    # Act
    submit.prepare()

    # Assert
    assert submit.certificate.ca == submit.ca_id
    assert submit.certificate.name == uuid.UUID(int=999).hex
    assert (
        submit.certificate.certificate_content_base64
        == base64.b64encode(b"certificate-bytes").decode()
    )


def test_verify_user_certificate_calls_verify(mocker, submit):
    # Arrange
    spy = mocker.patch(PATCH_SUBMIT.format("verify_certificate"))
    submit.certificate = TestCertificate()

    # Act
    submit.verify_user_certificate()

    # Assert
    spy.assert_called_once()
    _, kwargs = spy.call_args
    assert kwargs["expected_cn"] == "alice@example.com"


def test_submit_aborts_when_not_approved(mocker, submit):
    # Arrange
    submit.certificate = TestCertificate()
    mocker.patch(PATCH_SUBMIT.format("approval_prompt"), return_value=False)

    # Act & Assert
    with pytest.raises(CleanExit):
        submit.submit()


def test_submit_uploads_when_approved(mocker, submit):
    # Arrange
    submit.certificate = TestCertificate()
    upload_spy = mocker.patch.object(submit.certificate, "upload")

    # Act
    submit.submit()

    # Assert
    upload_spy.assert_called_once()


def test_write_creates_certificate_and_writes(mocker, submit):
    # Arrange
    spy = mocker.patch(PATCH_SUBMIT.format("Certificate.write"))

    # Act
    submit.write(TestCertificate().todict())

    # Assert
    spy.assert_called_once()
