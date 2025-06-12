from medperf.exceptions import CleanExit, InvalidArgumentError
import pytest
from unittest.mock import ANY

from medperf.tests.mocks.execution import TestExecution
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.commands.dataset.associate import AssociateDataset

PATCH_ASSOC = "medperf.commands.dataset.associate_benchmark.{}"


@pytest.fixture
def dataset(mocker, request):
    dset = TestDataset(id=1, data_preparation_mlcube=request.param, name="test")
    mocker.patch(PATCH_ASSOC.format("Dataset.get"), return_value=dset)
    return dset


@pytest.fixture
def benchmark(mocker, request):
    bm = TestBenchmark(data_preparation_mlcube=request.param, name="name")
    mocker.patch(PATCH_ASSOC.format("Benchmark"), return_value=bm)
    mocker.patch(PATCH_ASSOC.format("Benchmark.get"), return_value=bm)
    return bm


@pytest.mark.parametrize("dataset", [1, 4, 381], indirect=True)
@pytest.mark.parametrize("benchmark", [2, 12, 32], indirect=True)
def test_fails_if_dataset_inexecatible_with_benchmark(
    mocker, comms, ui, dataset, benchmark
):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        AssociateDataset.run(1, 1)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [2], indirect=True)
def test_fails_if_dataset_is_not_registered(mocker, comms, ui, dataset, benchmark):
    # Arrange
    dataset.id = None

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        AssociateDataset.run(1, 1)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_requests_approval_from_user(mocker, comms, ui, dataset, benchmark):
    # Arrange
    result = TestExecution()
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    exec_ret = [result]
    mocker.patch(PATCH_ASSOC.format("BenchmarkExecution.run"), return_value=exec_ret)
    mocker.patch.object(result, "read_results", return_value={})

    # Act
    AssociateDataset.run(1, 1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
@pytest.mark.parametrize("data_uid", [1562, 951])
@pytest.mark.parametrize("benchmark_uid", [3557, 423, 1528])
def test_associates_if_approved(
    mocker, comms, ui, dataset, data_uid, benchmark_uid, benchmark
):
    # Arrange
    result = TestExecution()
    assoc_func = "associate_benchmark_dataset"
    mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    exec_ret = [result]
    mocker.patch(PATCH_ASSOC.format("BenchmarkExecution.run"), return_value=exec_ret)
    mocker.patch.object(result, "read_results", return_value={})
    spy = mocker.patch.object(comms, assoc_func)
    dataset.id = data_uid

    # Act
    AssociateDataset.run(data_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(data_uid, benchmark_uid, ANY)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_stops_if_not_approved(mocker, comms, ui, dataset, benchmark):
    # Arrange
    result = TestExecution()
    exec_ret = [result]
    mocker.patch(PATCH_ASSOC.format("BenchmarkExecution.run"), return_value=exec_ret)
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, "associate_benchmark_dataset")
    mocker.patch.object(result, "read_results", return_value={})

    # Act & Assert
    with pytest.raises(CleanExit):
        AssociateDataset.run(1, 1)

        spy.assert_called_once()
        assoc_spy.assert_not_called()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_associate_calls_allows_cache_by_default(mocker, comms, ui, dataset, benchmark):
    # Arrange
    result = TestExecution()
    data_uid = 1562
    benchmark_uid = 3557
    assoc_func = "associate_benchmark_dataset"
    mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=True)
    exec_ret = [result]
    spy = mocker.patch(
        PATCH_ASSOC.format("BenchmarkExecution.run"), return_value=exec_ret
    )
    mocker.patch.object(result, "read_results", return_value={})
    mocker.patch.object(comms, assoc_func)
    dataset.id = data_uid

    # Act
    AssociateDataset.run(data_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(
        benchmark_uid, data_uid, [benchmark.reference_model_mlcube], no_cache=False
    )
