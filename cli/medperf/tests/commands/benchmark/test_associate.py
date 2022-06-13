import pytest

from medperf.tests.utils import rand_l
from medperf.commands.benchmark.associate import AssociateBenchmark

PATCH_ASSOC = "medperf.commands.benchmark.associate.{}"


@pytest.mark.parametrize("model_uid", [None, "1"])
@pytest.mark.parametrize("data_uid", [None, "1"])
def test_run_fails_if_model_and_dset_passed(mocker, model_uid, data_uid, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("pretty_error"))
    mocker.patch.object(comms, "associate_cube")
    mocker.patch.object(comms, "associate_dset")
    mocker.patch(PATCH_ASSOC.format("AssociateCube.run"))
    mocker.patch(PATCH_ASSOC.format("AssociateDataset.run"))

    # Act
    AssociateBenchmark.run("1", model_uid, data_uid, comms, ui)

    # Assert
    if model_uid and data_uid:
        spy.assert_called_once()
    else:
        spy.assert_not_called()


@pytest.mark.parametrize("bmk_uid", rand_l(1, 500, 1))
@pytest.mark.parametrize("model_uid", rand_l(1, 500, 1))
@pytest.mark.parametrize("approved", [True, False])
def test_run_executes_cube_association(mocker, bmk_uid, model_uid, approved, comms, ui):
    # Arrange
    bmk_uid = str(bmk_uid)
    model_uid = str(model_uid)
    spy = mocker.patch(PATCH_ASSOC.format("AssociateCube.run"))

    # Act
    AssociateBenchmark.run(bmk_uid, model_uid, None, comms, ui, approved=approved)

    # Assert
    spy.assert_called_once_with(model_uid, bmk_uid, comms, ui, approved=approved)


@pytest.mark.parametrize("bmk_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("dset_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("approved", [True, False])
def test_run_executes_dset_association(mocker, bmk_uid, dset_uid, approved, comms, ui):
    # Arrange
    bmk_uid = str(bmk_uid)
    dset_uid = str(dset_uid)
    spy = mocker.patch(PATCH_ASSOC.format("AssociateDataset.run"))

    # Act
    AssociateBenchmark.run(bmk_uid, None, dset_uid, comms, ui, approved=approved)

    # Assert
    spy.assert_called_once_with(dset_uid, bmk_uid, comms, ui, approved=approved)
