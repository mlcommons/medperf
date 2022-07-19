import pytest

from medperf.tests.utils import rand_l
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.commands.dataset.associate import DatasetBenchmarkAssociation

patch_associate = "medperf.commands.dataset.associate.{}"
req_func = "request_association_approval"


@pytest.fixture
def dataset(mocker, request):
    dset = mocker.create_autospec(spec=Dataset)
    mocker.patch(patch_associate.format("Dataset"), return_value=dset)
    dset.preparation_cube_uid = request.param
    return dset


@pytest.fixture
def benchmark(mocker, request):
    bm = mocker.create_autospec(spec=Benchmark)
    mocker.patch(patch_associate.format("Benchmark"), return_value=bm)
    mocker.patch(patch_associate.format("Benchmark.get"), return_value=bm)
    bm.data_preparation = request.param
    return bm


@pytest.mark.parametrize("dataset", [1, 4, 381], indirect=True)
@pytest.mark.parametrize("benchmark", [2, 12, 32], indirect=True)
def test_fails_if_dataset_incompatible_with_benchmark(
    mocker, comms, ui, dataset, benchmark
):
    # Arrange
    spy = mocker.patch(
        patch_associate.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        DatasetBenchmarkAssociation.run(1, 1, comms, ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_requests_approval_from_user(mocker, comms, ui, dataset, benchmark):
    # Arrange
    spy = mocker.patch.object(dataset, req_func, return_value=True)
    dataset.uid = 1

    # Act
    DatasetBenchmarkAssociation.run(1, 1, comms, ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
@pytest.mark.parametrize("data_uid", [str(rand_l(1, 5000, 5))])
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 5))
def test_associates_if_approved(
    mocker, comms, ui, dataset, data_uid, benchmark_uid, benchmark
):
    # Arrange
    assoc_func = "associate_dset"
    mocker.patch.object(dataset, req_func, return_value=True)
    spy = mocker.patch.object(comms, assoc_func)
    dataset.uid = data_uid

    # Act
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid, comms, ui)

    # Assert
    spy.assert_called_once_with(data_uid, benchmark_uid)


@pytest.mark.parametrize("dataset", [1], indirect=True)
@pytest.mark.parametrize("benchmark", [1], indirect=True)
def test_stops_if_not_approved(mocker, comms, ui, dataset, benchmark):
    # Arrange
    mocker.patch(
        patch_associate.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )
    spy = mocker.patch.object(dataset, req_func, return_value=False)

    # Act
    with pytest.raises(SystemExit):
        DatasetBenchmarkAssociation.run(1, 1, comms, ui)

    # Assert
    spy.assert_called_once()
