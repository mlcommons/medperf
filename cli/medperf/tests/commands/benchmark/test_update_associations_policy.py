from medperf.exceptions import CleanExit, InvalidArgumentError
import pytest

from medperf.commands.benchmark.update_associations_poilcy import (
    UpdateAssociationsPolicy,
)
from medperf.tests.mocks.benchmark import TestBenchmark


@pytest.mark.parametrize("mode", ["", "allow", "false"])
def test_invalid_model_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, model_mode=mode)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.validate()


@pytest.mark.parametrize("mode", ["", "allow", "false"])
def test_invalid_dataset_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, dataset_mode=mode)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.validate()


@pytest.mark.parametrize("mode", ["never", "Never", "allowlist", "always"])
def test_valid_model_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, model_mode=mode)

    # Act & Assert
    obj.validate()


@pytest.mark.parametrize("mode", ["never", "Never", "allowlist", "always"])
def test_valid_dataset_modes(mocker, mode):
    # Arrange
    obj = UpdateAssociationsPolicy(1, dataset_mode=mode)

    # Act & Assert
    obj.validate()


def test_dataset_email_list_filled(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="test@example.com\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, dataset_emails_file=file)

    # Act
    obj.read_emails()
    obj.validate_emails()

    # Assert
    assert obj.dataset_emails == ["test@example.com", "bmk@org.com"]
    assert obj.model_emails is None


def test_model_email_list_filled(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="test@example.com\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, model_emails_file=file)

    # Act
    obj.read_emails()
    obj.validate_emails()

    # Assert
    assert obj.model_emails == ["test@example.com", "bmk@org.com"]
    assert obj.dataset_emails is None


def test_invalid_email_list(mocker, fs):
    # Arrange
    file = "/somefile"
    fs.create_file(file, contents="invalidemail\nbmk@org.com")
    obj = UpdateAssociationsPolicy(1, dataset_emails_file=file)
    obj.read_emails()

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.validate_emails()


def test_update_calls_comms_with_correct_body1(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "update_benchmark")
    obj = UpdateAssociationsPolicy(1, dataset_mode="NEVER")
    obj.dataset_emails = ["test@example.com"]

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
    obj.dataset_emails = ["test@example.com"]

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
    obj = UpdateAssociationsPolicy(1, model_mode="NEVER")
    obj.model_emails = ["test@example.com"]

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
    obj.model_emails = ["test@example.com"]

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
        1,
        model_mode="NEVER",
        dataset_mode="ALLOWLIST",
        model_emails="test1@example.com",
        dataset_emails="test2@example.com test3@example.com",
    )
    obj.read_emails()
    obj.validate_emails()

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


PATCH_POLICY = "medperf.commands.benchmark.update_associations_poilcy.{}"


def test_empty_allow_list_refused_when_saved_one_is_empty(mocker):
    # Arrange
    mocker.patch(
        PATCH_POLICY.format("Benchmark.get"),
        return_value=TestBenchmark(dataset_auto_approval_allow_list=[]),
    )
    obj = UpdateAssociationsPolicy(1, dataset_mode="ALLOWLIST", approved=True)
    obj.dataset_emails = []

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        obj.check_empty_allow_lists()


@pytest.mark.parametrize("mode", ["ALLOWLIST", None])
def test_emptying_allow_list_sets_mode_to_never(mocker, mode):
    # Arrange
    mocker.patch(
        PATCH_POLICY.format("Benchmark.get"),
        return_value=TestBenchmark(
            model_auto_approval_mode="ALLOWLIST",
            model_auto_approval_allow_list=["test@example.com"],
        ),
    )
    obj = UpdateAssociationsPolicy(1, model_mode=mode, approved=True)
    obj.model_emails = []

    # Act
    obj.check_empty_allow_lists()

    # Assert
    assert obj.model_mode == "NEVER"


def test_emptying_allow_list_cancelled_if_not_approved(mocker):
    # Arrange
    mocker.patch(
        PATCH_POLICY.format("Benchmark.get"),
        return_value=TestBenchmark(dataset_auto_approval_allow_list=["a@example.com"]),
    )
    mocker.patch(PATCH_POLICY.format("approval_prompt"), return_value=False)
    obj = UpdateAssociationsPolicy(1, dataset_mode="ALLOWLIST")
    obj.dataset_emails = []

    # Act & Assert
    with pytest.raises(CleanExit):
        obj.check_empty_allow_lists()


@pytest.mark.parametrize("mode", ["NEVER", "ALWAYS"])
def test_empty_allow_list_allowed_with_other_modes(mocker, mode):
    # Arrange
    mocker.patch(
        PATCH_POLICY.format("Benchmark.get"),
        return_value=TestBenchmark(dataset_auto_approval_allow_list=[]),
    )
    obj = UpdateAssociationsPolicy(1, dataset_mode=mode)
    obj.dataset_emails = []

    # Act
    obj.check_empty_allow_lists()

    # Assert
    assert obj.dataset_mode == mode


def test_allow_lists_not_checked_when_not_emptied(mocker):
    # Arrange
    spy = mocker.patch(PATCH_POLICY.format("Benchmark.get"))
    obj = UpdateAssociationsPolicy(1, dataset_mode="ALLOWLIST")
    obj.dataset_emails = ["test@example.com"]

    # Act
    obj.check_empty_allow_lists()

    # Assert
    spy.assert_not_called()
