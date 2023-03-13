from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.commands.benchmark.associate import AssociateBenchmark

PATCH_ASSOC = "medperf.commands.benchmark.associate.{}"


@pytest.mark.parametrize("model_uid", [None, 1])
@pytest.mark.parametrize("data_uid", [None, 1])
def test_run_fails_if_model_and_dset_passed(mocker, model_uid, data_uid, comms, ui):
    # Arrange
    num_arguments = int(data_uid is None) + int(model_uid is None)
    mocker.patch.object(comms, "associate_cube")
    mocker.patch.object(comms, "associate_dset")
    mocker.patch(PATCH_ASSOC.format("AssociateCube.run"))
    mocker.patch(PATCH_ASSOC.format("AssociateDataset.run"))

    # Act & Assert
    if num_arguments != 1:
        with pytest.raises(InvalidArgumentError):
            AssociateBenchmark.run(1, model_uid, data_uid)
    else:
        AssociateBenchmark.run(1, model_uid, data_uid)


@pytest.mark.parametrize("approved", [True, False])
def test_run_executes_cube_association(mocker, approved, comms, ui):
    # Arrange
    bmk_uid = 87
    model_uid = 987
    spy = mocker.patch(PATCH_ASSOC.format("AssociateCube.run"))

    # Act
    AssociateBenchmark.run(bmk_uid, model_uid, None, approved=approved)

    # Assert
    spy.assert_called_once_with(model_uid, bmk_uid, approved=approved, no_cache=False)


@pytest.mark.parametrize("bmk_uid", [243, 217])
@pytest.mark.parametrize("dset_uid", [386, 24])
@pytest.mark.parametrize("approved", [True, False])
def test_run_executes_dset_association(mocker, bmk_uid, dset_uid, approved, comms, ui):
    # Arrange
    bmk_uid = str(bmk_uid)
    dset_uid = str(dset_uid)
    spy = mocker.patch(PATCH_ASSOC.format("AssociateDataset.run"))

    # Act
    AssociateBenchmark.run(bmk_uid, None, dset_uid, approved=approved)

    # Assert
    spy.assert_called_once_with(dset_uid, bmk_uid, approved=approved, no_cache=False)
