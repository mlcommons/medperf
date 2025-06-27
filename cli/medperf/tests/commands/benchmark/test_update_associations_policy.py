from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.commands.benchmark.update_associations_poilcy import (
    UpdateAssociationsPolicy,
)


@pytest.mark.parametrize("mode", ["", "allow", "false"])
def test_invalid_model_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, model_auto_approve_mode=mode)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.validate()


@pytest.mark.parametrize("mode", ["", "allow", "false"])
def test_invalid_dataset_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, dataset_auto_approve_mode=mode)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.validate()


@pytest.mark.parametrize("mode", ["never", "Never", "allowlist", "always"])
def test_valid_model_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, model_auto_approve_mode=mode)

    # Act & Assert
    obj.validate()


@pytest.mark.parametrize("mode", ["never", "Never", "allowlist", "always"])
def test_valid_dataset_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, dataset_auto_approve_mode=mode)

    # Act & Assert
    obj.validate()


def test_dataset_email_list_filled(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="test@example.com\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, dataset_auto_approve_file=file)

    # Act
    obj.read_and_files_contents()

    # Assert
    assert obj.allowed_dataset_emails == ["test@example.com", "bmk@org.com"]
    assert obj.allowed_model_emails is None


def test_model_email_list_filled(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="test@example.com\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, model_auto_approve_file=file)

    # Act
    obj.read_and_files_contents()

    # Assert
    assert obj.allowed_model_emails == ["test@example.com", "bmk@org.com"]
    assert obj.allowed_dataset_emails is None


def test_invalid_email_list(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="invalidemail\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, dataset_auto_approve_file=file)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.read_and_files_contents()


def test_update_calls_comms_with_correct_body1(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1, dataset_auto_approve_mode="NEVER")
    obj.allowed_dataset_emails = ["test@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {
            "dataset_auto_approval_allow_list": ["test@example.com"],
            "dataset_auto_approval_mode": "NEVER",
        },
    )


def test_update_calls_comms_with_correct_body2(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1)
    obj.allowed_dataset_emails = ["test@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {"dataset_auto_approval_allow_list": ["test@example.com"]},
    )


def test_update_calls_comms_with_correct_body3(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1, model_auto_approve_mode="NEVER")
    obj.allowed_model_emails = ["test@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {
            "model_auto_approval_allow_list": ["test@example.com"],
            "model_auto_approval_mode": "NEVER",
        },
    )


def test_update_calls_comms_with_correct_body4(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1)
    obj.allowed_model_emails = ["test@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {"model_auto_approval_allow_list": ["test@example.com"]},
    )


def test_update_calls_comms_with_correct_body5(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(
        1, model_auto_approve_mode="NEVER", dataset_auto_approve_mode="ALLOWLIST"
    )
    obj.allowed_model_emails = ["test1@example.com"]
    obj.allowed_dataset_emails = ["test2@example.com", "test3@example.com"]

    # Act
    obj.update()

    # Assert
    spy.assert_called_once_with(
        1,
        {
            "model_auto_approval_allow_list": ["test1@example.com"],
            "model_auto_approval_mode": "NEVER",
            "dataset_auto_approval_allow_list": [
                "test2@example.com",
                "test3@example.com",
            ],
            "dataset_auto_approval_mode": "ALLOWLIST",
        },
    )
