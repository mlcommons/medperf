from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.commands.benchmark.update_associations_poilcy import (
    UpdateAssociationsPolicy,
)

PATCH_BENCHMARK = "medperf.commands.benchmark.submit.{}"


@pytest.mark.parametrize("mode", ["", "allow", "false"])
def test_invalid_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, mode)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.validate()


@pytest.mark.parametrize("mode", ["never", "Never", "allowlist", "always"])
def test_valid_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, mode)

    # Act & Assert
    obj.validate()


def test_email_list_filled(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="test@example.com\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, None, file)

    # Act
    obj.read_and_validate_auto_approve_file()

    # Assert
    assert obj.allowed_emails == ["test@example.com", "bmk@org.com"]


def test_invalid_email_list(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="invalidemail\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, None, file)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.read_and_validate_auto_approve_file()


def test_update_calls_comms_with_correct_body1(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1, "NEVER")
    obj.allowed_emails = ["test@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {
            "association_auto_approval_allow_list": ["test@example.com"],
            "association_auto_approval_mode": "NEVER",
        },
    )


def test_update_calls_comms_with_correct_body2(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1)
    obj.allowed_emails = ["test@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {"association_auto_approval_allow_list": ["test@example.com"]},
    )
