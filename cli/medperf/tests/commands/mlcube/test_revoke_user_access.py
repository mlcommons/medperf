import pytest
from medperf.exceptions import CleanExit
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.tests.mocks.encrypted_key import TestEncryptedKey

PATCH_REVOKEUSERACCESS = "medperf.commands.mlcube.revoke_user_access.{}"
KEY_ID = 1


@pytest.fixture
def revokeuseraccess(mocker):
    mocker.patch(
        PATCH_REVOKEUSERACCESS.format("EncryptedKey.get"),
        return_value=TestEncryptedKey(id=KEY_ID, encrypted_key_base64="original_key"),
    )
    mocker.patch(
        PATCH_REVOKEUSERACCESS.format("generate_container_key_redaction_record"),
        return_value="redacted_key",
    )

    return RevokeUserAccess(KEY_ID)


def test_get_approval_skips_if_preapproved(revokeuseraccess):
    # Arrange
    revokeuseraccess.approved = True

    # Act & Assert (Should not raise)
    revokeuseraccess.get_approval()


def test_get_approval_raises_if_not_approved(mocker, revokeuseraccess):
    # Arrange
    mocker.patch(PATCH_REVOKEUSERACCESS.format("approval_prompt"), return_value=False)

    # Act & Assert
    with pytest.raises(CleanExit):
        revokeuseraccess.get_approval()


def test_get_approval_succeeds_if_approved_by_prompt(mocker, revokeuseraccess):
    # Arrange
    mocker.patch(PATCH_REVOKEUSERACCESS.format("approval_prompt"), return_value=True)

    # Act & Assert (Should not raise)
    revokeuseraccess.get_approval()


def test_revoke_access_updates_key_with_redaction(mocker, revokeuseraccess, comms):
    # Arrange
    spy = mocker.patch(
        PATCH_REVOKEUSERACCESS.format("generate_container_key_redaction_record"),
        return_value="redacted_key",
    )

    # Act
    revokeuseraccess.revoke_access()

    # Assert
    spy.assert_called_once_with("original_key")
    expected_body = {
        "is_valid": False,
        "encrypted_key_base64": "redacted_key",
    }
    comms.update_encrypted_key.assert_called_once_with(KEY_ID, expected_body)


def test_revoke_access_gets_correct_key(mocker, revokeuseraccess, comms):
    # Arrange
    get_spy = mocker.patch(
        PATCH_REVOKEUSERACCESS.format("EncryptedKey.get"),
        return_value=TestEncryptedKey(id=KEY_ID, encrypted_key_base64="original_key"),
    )

    # Act
    revokeuseraccess.revoke_access()

    # Assert
    get_spy.assert_called_once_with(KEY_ID)


def test_run_executes_full_workflow(mocker, comms, revokeuseraccess):
    # Act
    RevokeUserAccess.run(KEY_ID, approved=True)

    # Assert
    expected_body = {
        "is_valid": False,
        "encrypted_key_base64": "redacted_key",
    }
    comms.update_encrypted_key.assert_called_once_with(KEY_ID, expected_body)
