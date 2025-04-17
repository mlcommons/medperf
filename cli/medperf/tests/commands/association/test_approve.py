from medperf.enums import Status
import pytest

from medperf.commands.association.approval import Approval

PATCH_APPROVE = "medperf.commands.association.approval.{}"


@pytest.mark.parametrize(
    "kwargs, comms_method",
    [
        (
            {"benchmark_uid": 1, "dataset_uid": 1},
            "update_benchmark_dataset_association",
        ),
        (
            {"benchmark_uid": 1, "mlcube_uid": 1},
            "update_benchmark_model_association",
        ),
        (
            {"training_exp_uid": 1, "dataset_uid": 1},
            "update_training_dataset_association",
        ),
        (
            {"training_exp_uid": 1, "aggregator_uid": 1},
            "update_training_aggregator_association",
        ),
        (
            {"training_exp_uid": 1, "ca_uid": 1},
            "update_training_ca_association",
        ),
    ],
)
def test_run_calls_correct_comms_method(mocker, comms, ui, kwargs, comms_method):
    # Arrange
    spy = mocker.patch.object(comms, comms_method)

    # Act
    Approval.run(Status.APPROVED, **kwargs)

    # Assert
    spy.assert_called_once()
