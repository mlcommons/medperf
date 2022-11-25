from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.commands.association.priority import AssociationPriority

PATCH_PRIORITY = "medperf.commands.association.priority.{}"


def test_run_executes_expected_flow(mocker, comms, ui):
    # Arrange
    spy_validate = mocker.patch(PATCH_PRIORITY.format("AssociationPriority.validate"),)
    spy_convert = mocker.patch(
        PATCH_PRIORITY.format("AssociationPriority.convert_priority_to_float"),
    )
    spy_update = mocker.patch(PATCH_PRIORITY.format("AssociationPriority.update"),)

    # Act
    AssociationPriority.run(1, 1, 1)

    # Assert
    spy_validate.assert_called_once()
    spy_convert.assert_called_once()
    spy_update.assert_called_once()


@pytest.mark.parametrize(
    "priority_and_fails", [(-2, True), (-1, False), (1330, False), (0, True)]
)
def test_validate_validates_as_expected(mocker, comms, ui, priority_and_fails):
    # Arrange
    priority, fails = priority_and_fails
    setter = AssociationPriority(1, 1, priority)

    # Act & Assert
    if fails:
        with pytest.raises(InvalidArgumentError):
            setter.validate()
    else:
        setter.validate()


@pytest.mark.parametrize(
    "testcases",
    [
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
        ([1.0, 3.0, 5.11, 7.230, 10.382], 1, 0.0),
    ],
)
def test_priority_is_correctly_converted_to_float(
    mocker, comms, ui, mlcube_uid, status
):
    # Arrange
    spy = mocker.patch.object(comms, "set_mlcube_association_approval")

    # Act
    Approval.run("1", status, mlcube_uid=mlcube_uid)

    # Assert
    spy.assert_called_once_with("1", mlcube_uid, status.value)
