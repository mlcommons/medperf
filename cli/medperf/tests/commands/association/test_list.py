from medperf.enums import Status
import pytest

from medperf.commands.association.list import ListAssociations

PATCH_LIST = "medperf.commands.association.list.{}"


@pytest.mark.parametrize(
    "kwargs, expected_util_args",
    [
        (
            {"benchmark": True, "dataset": True},
            ["benchmark", "dataset"],
        ),
        (
            {"benchmark": True, "mlcube": True},
            ["benchmark", "model_mlcube"],
        ),
        (
            {"training_exp": True, "dataset": True},
            ["training_exp", "dataset"],
        ),
        (
            {"training_exp": True, "aggregator": True},
            ["training_exp", "aggregator"],
        ),
    ],
)
def test_run_calls_correct_comms_method(mocker, comms, ui, kwargs, expected_util_args):
    # Arrange
    spy = mocker.patch(PATCH_LIST.format("get_user_associations"), return_value=[])
    mocker.patch(PATCH_LIST.format("tabulate"))

    # Act
    ListAssociations.run(Status.APPROVED.value, **kwargs)

    # Assert
    spy.assert_called_once_with(*expected_util_args, Status.APPROVED.value)
