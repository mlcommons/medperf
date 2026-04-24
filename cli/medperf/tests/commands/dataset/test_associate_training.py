from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.commands.dataset.associate_training import AssociateTrainingDataset

PATCH_ASSOC = "medperf.commands.dataset.associate_training.{}"


@pytest.fixture
def dataset(mocker, request):
    dset = TestDataset(id=1, data_preparation_mlcube=request.param, name="test")
    mocker.patch(PATCH_ASSOC.format("Dataset.get"), return_value=dset)
    return dset


@pytest.fixture
def training_exp(mocker, request):
    bm = TestTrainingExp(data_preparation_mlcube=request.param, name="name")
    mocker.patch(PATCH_ASSOC.format("TrainingExp"), return_value=bm)
    mocker.patch(PATCH_ASSOC.format("TrainingExp.get"), return_value=bm)
    return bm


@pytest.mark.parametrize("dataset", [1, 4, 381], indirect=True)
@pytest.mark.parametrize("training_exp", [2, 12, 32], indirect=True)
def test_fails_if_dataset_inexecatible_with_training_exp(
    mocker, comms, ui, dataset, training_exp
):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        AssociateTrainingDataset.run(1, 1)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("training_exp", [2], indirect=True)
def test_fails_if_dataset_is_not_registered(mocker, comms, ui, dataset, training_exp):
    # Arrange
    dataset.id = None

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        AssociateTrainingDataset.run(1, 1)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("training_exp", [1], indirect=True)
def test_requests_approval_from_user(mocker, comms, ui, dataset, training_exp):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)

    # Act
    AssociateTrainingDataset.run(1, 1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("training_exp", [1], indirect=True)
@pytest.mark.parametrize("data_uid", [1562, 951])
@pytest.mark.parametrize("training_exp_uid", [3557, 423, 1528])
def test_associates_if_approved(
    mocker, comms, ui, dataset, data_uid, training_exp_uid, training_exp
):
    # Arrange
    assoc_func = "associate_training_dataset"
    mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    spy = mocker.patch.object(comms, assoc_func)
    dataset.id = data_uid

    # Act
    AssociateTrainingDataset.run(data_uid, training_exp_uid)

    # Assert
    spy.assert_called_once_with(data_uid, training_exp_uid)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("training_exp", [1], indirect=True)
def test_stops_if_not_approved(mocker, comms, ui, dataset, training_exp):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, "associate_training_dataset")

    # Act
    AssociateTrainingDataset.run(1, 1)

    # Assert
    spy.assert_called_once()
    assoc_spy.assert_not_called()
