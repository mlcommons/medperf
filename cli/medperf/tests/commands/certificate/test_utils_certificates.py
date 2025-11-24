import pytest
import os
import base64
from medperf.commands.certificate.utils import (
    current_user_certificate_status,
    check_matching_certificates,
    load_user_private_key,
)
from medperf.tests.mocks.certificate import TestCertificate
from medperf import config

PATCH_STATUS = "medperf.commands.certificate.utils.{}"


@pytest.mark.parametrize(
    "remote_exists,local_exists,local_matches,expected_flags",
    [
        # No remote, no local
        (
            None,
            False,
            False,
            {
                "no_certs_found": True,
                "should_be_submitted": False,
                "should_be_invalidated": False,
                "no_action_required": False,
            },
        ),
        # No remote, local exists
        (
            None,
            True,
            False,
            {
                "no_certs_found": False,
                "should_be_submitted": True,
                "should_be_invalidated": False,
                "no_action_required": False,
            },
        ),
        # Remote exists, no local
        (
            TestCertificate(
                id=1, certificate_content_base64=base64.b64encode(b"abc").decode()
            ),
            False,
            False,
            {
                "no_certs_found": False,
                "should_be_submitted": False,
                "should_be_invalidated": True,
                "no_action_required": False,
            },
        ),
        # Remote exists, local exists, match
        (
            TestCertificate(
                id=1, certificate_content_base64=base64.b64encode(b"abc").decode()
            ),
            True,
            True,
            {
                "no_certs_found": False,
                "should_be_submitted": False,
                "should_be_invalidated": False,
                "no_action_required": True,
            },
        ),
        # Remote exists, local exists, mismatch
        (
            TestCertificate(
                id=1, certificate_content_base64=base64.b64encode(b"abc").decode()
            ),
            True,
            False,
            {
                "no_certs_found": False,
                "should_be_submitted": False,
                "should_be_invalidated": True,
                "no_action_required": False,
            },
        ),
    ],
)
def test_current_user_certificate_status(
    mocker, fs, remote_exists, local_exists, local_matches, expected_flags
):
    # Arrange
    mocker.patch(
        PATCH_STATUS.format("Certificate.get_user_certificate"),
        return_value=remote_exists,
    )
    mocker.patch(
        PATCH_STATUS.format("get_medperf_user_data"),
        return_value={"email": "alice@example.com"},
    )
    local_path = f"/pki/alice/{config.certificate_authority_id}"
    mocker.patch(PATCH_STATUS.format("get_pki_assets_path"), return_value=local_path)
    if local_exists:
        fs.create_dir(local_path)
        if remote_exists and local_matches:
            fs.create_file(
                os.path.join(local_path, config.certificate_file), contents=b"abc"
            )
        elif remote_exists and not local_matches:
            fs.create_file(
                os.path.join(local_path, config.certificate_file), contents=b"xyz"
            )

    # Act
    status = current_user_certificate_status()

    # Assert
    assert status["user_cert_object"] == remote_exists
    for key, val in expected_flags.items():
        assert status[key] is val


def test_check_matching_certificates_returns_correctly(mocker, fs):
    # Arrange
    cert_content = b"certificate-bytes"
    remote_cert_base64 = base64.b64encode(cert_content).decode()
    user_cert = TestCertificate(certificate_content_base64=remote_cert_base64)
    folder_path = "/pki/alice/1"
    fs.create_dir(folder_path)
    fs.create_file(
        os.path.join(folder_path, config.certificate_file), contents=cert_content
    )

    # Act
    result = check_matching_certificates(user_cert, folder_path)

    # Assert
    assert result is True

    # Change local content to mismatch
    fs.remove(os.path.join(folder_path, config.certificate_file))
    fs.create_file(
        os.path.join(folder_path, config.certificate_file), contents=b"other"
    )
    result = check_matching_certificates(user_cert, folder_path)
    assert result is False

    # Remove local certificate
    fs.remove(os.path.join(folder_path, config.certificate_file))
    result = check_matching_certificates(user_cert, folder_path)
    assert result is False


def test_load_user_private_key_reads_file(mocker, fs):
    # Arrange
    email = "alice@example.com"
    folder = f"/pki/{email}/{config.certificate_authority_id}"
    key_path = os.path.join(folder, config.private_key_file)

    mocker.patch(
        PATCH_STATUS.format("get_medperf_user_data"), return_value={"email": email}
    )
    mocker.patch(PATCH_STATUS.format("get_pki_assets_path"), return_value=folder)

    fs.create_dir(folder)
    fs.create_file(key_path, contents=b"private-key-bytes")

    # Act
    result = load_user_private_key()

    # Assert
    assert result == b"private-key-bytes"

    # Remove file, should return None
    fs.remove(key_path)
    result = load_user_private_key()
    assert result is None
