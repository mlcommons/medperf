import pytest
from unittest.mock import ANY

from medperf.tests.utils import rand_l
from medperf.entities.cube import Cube
from medperf.entities.result import Result
from medperf.entities.benchmark import Benchmark
from medperf.commands.mlcube.associate import AssociateCube

PATCH_ASSOC = "medperf.commands.mlcube.associate.{}"


@pytest.fixture
def cube(mocker):
    cube = mocker.create_autospec(spec=Cube)
    mocker.patch.object(Cube, "get", return_value=cube)
    return cube


@pytest.fixture
def benchmark(mocker):
    benchmark = mocker.create_autospec(spec=Benchmark)
    mocker.patch.object(Benchmark, "get", return_value=benchmark)
    return benchmark


@pytest.fixture
def result(mocker):
    result = mocker.create_autospec(spec=Result)
    mocker.patch.object(Result, "todict", return_value={})
    return result


@pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 2))
def test_run_associates_cube_with_comms(
    mocker, cube, benchmark, result, cube_uid, benchmark_uid, comms, ui
):
    # Arrange
    spy = mocker.patch.object(comms, "associate_cube")
    comp_ret = ("", "", "", result)
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateCube.run(cube_uid, benchmark_uid, comms, ui)

    # Assert
    spy.assert_called_once_with(cube_uid, benchmark_uid, ANY)


@pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 2))
def test_run_calls_compatibility_test(
    mocker, cube, benchmark, cube_uid, benchmark_uid, result, comms, ui
):
    # Arrange
    comp_ret = ("", "", "", result)
    spy = mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateCube.run(cube_uid, benchmark_uid, comms, ui)

    # Assert
    spy.assert_called_once_with(benchmark_uid, comms, ui, model=cube_uid)
