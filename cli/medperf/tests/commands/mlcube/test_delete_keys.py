import pytest
from medperf.exceptions import CleanExit
from medperf.commands.mlcube.delete_keys import DeleteKeys
from medperf.tests.mocks.encrypted_key import TestEncryptedKey

PATCH_DELETEKEYS = "medperf.commands.mlcube.delete_keys.{}"
CONTAINER_ID = 1


@pytest.fixture
def deletekeys(mocker):
    mocker.patch(
        PATCH_DELETEKEYS.format("EncryptedKey.get_container_keys"),
        return_value=[
            TestEncryptedKey(id=1, encrypted_key_base64="key1"),
            TestEncryptedKey(id=2, encrypted_key_base64="key2"),
        ],
    )
    mocker.patch(PATCH_DELETEKEYS.format("generate_container_key_redaction_record"))

    return DeleteKeys(CONTAINER_ID)


def test_get_approval_skips_if_preapproved(deletekeys):
    # Arrange
    deletekeys.approved = True

    # Act & Assert (Should not raise)
    deletekeys.get_approval()


def test_get_approval_raises_if_not_approved(mocker):
    # Arrange
    mocker.patch(PATCH_DELETEKEYS.format("approval_prompt"), return_value=False)
    dk = DeleteKeys(CONTAINER_ID, approved=False)

    # Act & Assert
    with pytest.raises(CleanExit):
        dk.get_approval()


def test_get_approval_succeeds_if_approved_by_prompt(mocker):
    # Arrange
    mocker.patch(PATCH_DELETEKEYS.format("approval_prompt"), return_value=True)
    dk = DeleteKeys(CONTAINER_ID, approved=False)

    # Act & Assert (Should not raise)
    dk.get_approval()


def test_revoke_access_updates_keys_with_redaction(mocker, deletekeys, comms):
    # Arrange
    spy = mocker.patch(
        PATCH_DELETEKEYS.format("generate_container_key_redaction_record"),
        side_effect=lambda x: f"redacted_{x}",
    )

    # Act
    deletekeys.revoke_access()

    # Assert
    assert spy.call_count == 2
    spy.assert_any_call("key1")
    spy.assert_any_call("key2")

    expected_bodies = [
        {
            "id": 1,
            "is_valid": False,
            "encrypted_key_base64": "redacted_key1",
        },
        {
            "id": 2,
            "is_valid": False,
            "encrypted_key_base64": "redacted_key2",
        },
    ]
    comms.update_many_encrypted_keys.assert_called_once_with(expected_bodies)


def test_revoke_access_handles_empty_keys_list(mocker, comms):
    # Arrange
    mocker.patch(
        PATCH_DELETEKEYS.format("EncryptedKey.get_container_keys"), return_value=[]
    )
    dk = DeleteKeys(CONTAINER_ID)

    # Act & Assert
    with pytest.raises(CleanExit):
        dk.revoke_access()

    # Assert
    comms.update_many_encrypted_keys.assert_not_called()


def test_run_executes_full_workflow(mocker, comms):
    # Arrange
    mocker.patch(
        PATCH_DELETEKEYS.format("EncryptedKey.get_container_keys"),
        return_value=[TestEncryptedKey(id=1, encrypted_key_base64="key1")],
    )
    mocker.patch(
        PATCH_DELETEKEYS.format("generate_container_key_redaction_record"),
        return_value="redacted_key1",
    )

    # Act
    DeleteKeys.run(CONTAINER_ID, approved=True)

    # Assert
    expected_bodies = [
        {
            "id": 1,
            "is_valid": False,
            "encrypted_key_base64": "redacted_key1",
        }
    ]
    comms.update_many_encrypted_keys.assert_called_once_with(expected_bodies)
