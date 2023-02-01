from medperf.exceptions import CleanExit, InvalidArgumentError
import pytest
from unittest.mock import ANY

from medperf.entities.result import Result
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.commands.dataset.associate import AssociateDataset

PATCH_ASSOC = "medperf.commands.dataset.associate.{}"


@pytest.fixture
def dataset(mocker, request):
    dset = mocker.create_autospec(spec=Dataset)
    mocker.patch(PATCH_ASSOC.format("Dataset.get"), return_value=dset)
    dset.name = "test"
    dset.preparation_cube_uid = request.param
    dset.uid = 1
    return dset


@pytest.fixture
def benchmark(mocker, request):
    bm = mocker.create_autospec(spec=Benchmark)
    mocker.patch(PATCH_ASSOC.format("Benchmark"), return_value=bm)
    mocker.patch(PATCH_ASSOC.format("Benchmark.get"), return_value=bm)
    bm.data_preparation = request.param
    bm.name = "name"
    return bm


@pytest.fixture
def result(mocker):
    result = mocker.create_autospec(spec=Result)
    result.results = {}
    return result


@pytest.mark.parametrize("dataset", [1, 4, 381], indirect=True)
@pytest.mark.parametrize("benchmark", [2, 12, 32], indirect=True)
def test_fails_if_dataset_incompatible_with_benchmark(
    mocker, comms, ui, dataset, benchmark
):

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        AssociateDataset.run(1, 1)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [2], indirect=True)
def test_fails_if_dataset_is_not_registered(mocker, comms, ui, dataset, benchmark):
    # Arrange
    dataset.uid = None

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        AssociateDataset.run(1, 1)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_requests_approval_from_user(mocker, comms, ui, dataset, result, benchmark):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    comp_ret = ("", "", "", result)
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )
    dataset.uid = 1
    dataset.name = "test"

    # Act
    AssociateDataset.run(1, 1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
@pytest.mark.parametrize("data_uid", ["1562", "951"])
@pytest.mark.parametrize("benchmark_uid", [3557, 423, 1528])
def test_associates_if_approved(
    mocker, comms, ui, dataset, result, data_uid, benchmark_uid, benchmark
):
    # Arrange
    assoc_func = "associate_dset"
    mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    comp_ret = ("", "", "", result)
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )
    spy = mocker.patch.object(comms, assoc_func)
    dataset.uid = data_uid

    # Act
    AssociateDataset.run(data_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(data_uid, benchmark_uid, ANY)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_stops_if_not_approved(mocker, comms, ui, dataset, result, benchmark):
    # Arrange
    comp_ret = ("", "", "", result)
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, "associate_dset")

    # Act
    with pytest.raises(CleanExit):
        AssociateDataset.run(1, 1)

    # Assert
    spy.assert_called_once()
    assoc_spy.assert_not_called()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_associate_calls_comp_test_without_force_by_default(
    mocker, comms, ui, dataset, result, benchmark
):
    # Arrange
    data_uid = "1562"
    benchmark_uid = 3557
    assoc_func = "associate_dset"
    mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    comp_ret = ("", "", "", result)
    spy = mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )
    mocker.patch.object(comms, assoc_func)
    dataset.uid = data_uid

    # Act
    AssociateDataset.run(data_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(benchmark_uid, data_uid=data_uid, force_test=False)
