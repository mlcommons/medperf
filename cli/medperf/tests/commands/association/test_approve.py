from medperf.enums import Status
import pytest

from medperf.commands.association.approval import Approval

PATCH_APPROVE = "medperf.commands.association.approval.{}"


@pytest.mark.parametrize("dset_uid", [None, "1"])
@pytest.mark.parametrize("mlcube_uid", [None, "1"])
def test_run_fails_if_invalid_arguments(mocker, comms, ui, dset_uid, mlcube_uid):
    # Arrange
    num_arguments = int(dset_uid is None) + int(mlcube_uid is None)
    spy = mocker.patch(
        PATCH_APPROVE.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act & Assert
    if num_arguments != 1:
        with pytest.raises(SystemExit):
            Approval.run("1", Status.APPROVED, comms, ui, dset_uid, mlcube_uid)
    else:
        Approval.run("1", Status.APPROVED, comms, ui, dset_uid, mlcube_uid)

    # Assert
    if num_arguments == 1:
        spy.assert_not_called()


@pytest.mark.parametrize("dset_uid", [402, 173])
@pytest.mark.parametrize("status", [Status.APPROVED, Status.REJECTED])
def test_run_calls_comms_dset_approval_with_status(mocker, comms, ui, dset_uid, status):
    # Arrange
    spy = mocker.patch.object(comms, "set_dataset_association_approval")

    # Act
    Approval.run("1", status, comms, ui, dataset_uid=dset_uid)

    # Assert
    spy.assert_called_once_with("1", dset_uid, status.value)


@pytest.mark.parametrize("mlcube_uid", [294, 439])
@pytest.mark.parametrize("status", [Status.APPROVED, Status.REJECTED])
def test_run_calls_comms_mlcube_approval_with_status(
    mocker, comms, ui, mlcube_uid, status
):
    # Arrange
    spy = mocker.patch.object(comms, "set_mlcube_association_approval")

    # Act
    Approval.run("1", status, comms, ui, mlcube_uid=mlcube_uid)

    # Assert
    spy.assert_called_once_with("1", mlcube_uid, status.value)
