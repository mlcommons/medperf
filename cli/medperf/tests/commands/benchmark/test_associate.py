import pytest

from medperf.commands.benchmark import AssociateBenchmark

PATCH_ASSOC = "medperf.commands.benchmark.associate.{}"


@pytest.mark.parametrize("model_uid", [None, "1"])
@pytest.mark.parametrize("data_uid", [None, "1"])
def test_run_fails_if_model_and_dset_passed(mocker, model_uid, data_uid, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("pretty_error"))
    mocker.patch.object(comms, "associate_cube")
    mocker.patch.object(comms, "associate_dset")

    # Act
    AssociateBenchmark.run("1", model_uid, data_uid, comms, ui)

    # Assert
    if model_uid and data_uid:
        spy.assert_called_once()
    else:
        spy.assert_not_called()
