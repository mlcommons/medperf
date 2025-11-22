import pytest
import base64
from medperf.tests.mocks.certificate import TestCertificate
from medperf.entities.encrypted_key import EncryptedKey
from medperf.exceptions import (
    MedperfException,
    PrivateContainerAccessError,
    DecryptionError,
)

PATCH_EK = "medperf.entities.encrypted_key.{}"


# -------------------------------------------------------------------
# get_user_container_key
# -------------------------------------------------------------------
def test_get_user_container_key_happy_path(mocker, comms):
    # Arrange
    user_cert = TestCertificate(id=100)
    status = {
        "no_action_required": True,
        "user_cert_object": user_cert,
    }
    mocker.patch(
        PATCH_EK.format("current_user_certificate_status"), return_value=status
    )

    returned_key = {
        "id": 55,
        "name": "k",
        "certificate": 100,
        "container": 1,
        "encrypted_key_base64": base64.b64encode(b"data").decode(),
    }

    mocker.patch.object(
        comms,
        "get_certificate_encrypted_keys",
        return_value=[returned_key],
    )

    # Act
    result = EncryptedKey.get_user_container_key(container_id=1)

    # Assert
    assert isinstance(result, EncryptedKey)
    assert result.id == 55
    assert result.container == 1
    assert result.certificate == 100


def test_get_user_container_key_invalid_certificate(mocker):
    # Arrange
    status = {"no_action_required": False}
    mocker.patch(
        PATCH_EK.format("current_user_certificate_status"), return_value=status
    )

    # Act + Assert
    with pytest.raises(PrivateContainerAccessError):
        EncryptedKey.get_user_container_key(1)


def test_get_user_container_key_no_keys(mocker, comms):
    # Arrange
    user_cert = TestCertificate(id=1)
    mocker.patch(
        PATCH_EK.format("current_user_certificate_status"),
        return_value={"no_action_required": True, "user_cert_object": user_cert},
    )
    mocker.patch.object(comms, "get_certificate_encrypted_keys", return_value=[])

    # Act + Assert
    with pytest.raises(PrivateContainerAccessError):
        EncryptedKey.get_user_container_key(1)


def test_get_user_container_key_multiple_keys(mocker, comms):
    # Arrange
    user_cert = TestCertificate(id=1)
    mocker.patch(
        PATCH_EK.format("current_user_certificate_status"),
        return_value={"no_action_required": True, "user_cert_object": user_cert},
    )

    mocker.patch.object(
        comms, "get_certificate_encrypted_keys", return_value=[{"id": 1}, {"id": 2}]
    )

    # Act + Assert
    with pytest.raises(MedperfException):
        EncryptedKey.get_user_container_key(1)


# -------------------------------------------------------------------
# decrypt
# -------------------------------------------------------------------
def test_decrypt_happy_path(mocker, fs):
    # Arrange
    plaintext = b"my-secret-key"
    private_key = b"private"

    encrypted_key = EncryptedKey(
        id=1,
        name="k",
        certificate=1,
        container=1,
        encrypted_key_base64=base64.b64encode(b"cipher").decode(),
    )

    # Private key exists
    mocker.patch(PATCH_EK.format("load_user_private_key"), return_value=private_key)

    # Path for output
    output_path = "/tmp/decrypted-key"
    mocker.patch(
        PATCH_EK.format("tmp_path_for_key_decryption"),
        return_value=output_path,
    )

    # Mock decrypt() call on AsymmetricEncryption
    mock_decrypt = mocker.patch(
        PATCH_EK.format("AsymmetricEncryption.decrypt"),
        return_value=plaintext,
    )

    # Track secure write
    mock_write = mocker.patch(PATCH_EK.format("secure_write_to_file"))

    # Act
    result = encrypted_key.decrypt()

    # Assert
    assert result == output_path
    mock_decrypt.assert_called_once()
    mock_write.assert_called_once_with(output_path, plaintext, exec_permission=True)


def test_decrypt_missing_private_key(mocker):
    # Arrange
    encrypted_key = EncryptedKey(
        id=1,
        name="k",
        certificate=1,
        container=1,
        encrypted_key_base64=base64.b64encode(b"cipher").decode(),
    )

    mocker.patch(PATCH_EK.format("load_user_private_key"), return_value=None)

    # Act + Assert
    with pytest.raises(DecryptionError):
        encrypted_key.decrypt()
