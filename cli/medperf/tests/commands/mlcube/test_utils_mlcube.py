import pytest
from medperf.exceptions import MedperfException
from medperf.commands.mlcube.utils import check_access_to_container
from medperf.tests.mocks.cube import TestCube

PATCH_UTILS = "medperf.commands.mlcube.utils.{}"
CONTAINER_ID = 1
USER_ID = 100


@pytest.fixture
def mock_user(mocker):
    mocker.patch(
        PATCH_UTILS.format("get_medperf_user_data"),
        return_value={"id": USER_ID},
    )


def test_check_access_returns_true_for_public_container(mocker, mock_user):
    # Arrange
    container = TestCube(id=CONTAINER_ID, owner=999)
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=container)
    mocker.patch.object(container, "is_encrypted", return_value=False)

    # Act
    result = check_access_to_container(CONTAINER_ID)

    # Assert
    assert result["has_access"] is True
    assert result["reason"] == "The container is public"


def test_check_access_returns_true_for_owner(mocker, mock_user):
    # Arrange
    container = TestCube(id=CONTAINER_ID, owner=USER_ID)
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=container)
    mocker.patch.object(container, "is_encrypted", return_value=True)

    # Act
    result = check_access_to_container(CONTAINER_ID)

    # Assert
    assert result["has_access"] is True
    assert result["reason"] == "You own the container"


def test_check_access_returns_true_when_key_exists(mocker, mock_user):
    # Arrange
    container = TestCube(id=CONTAINER_ID, owner=999)
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=container)
    mocker.patch.object(container, "is_encrypted", return_value=True)
    mocker.patch(
        PATCH_UTILS.format("EncryptedKey.get_user_container_key"),
        return_value={"key": "data"},
    )

    # Act
    result = check_access_to_container(CONTAINER_ID)

    # Assert
    assert result["has_access"] is True
    assert result["reason"] == "Access has been granted"


def test_check_access_returns_false_when_no_key(mocker, mock_user):
    # Arrange
    container = TestCube(id=CONTAINER_ID, owner=999)
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=container)
    mocker.patch.object(container, "is_encrypted", return_value=True)
    error_message = "No key found for user"
    mocker.patch(
        PATCH_UTILS.format("EncryptedKey.get_user_container_key"),
        side_effect=MedperfException(error_message),
    )

    # Act
    result = check_access_to_container(CONTAINER_ID)

    # Assert
    assert result["has_access"] is False
    assert result["reason"] == error_message
