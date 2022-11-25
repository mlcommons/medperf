from medperf.exceptions import CleanExit
import pytest
from unittest.mock import ANY

from medperf.entities.cube import Cube
from medperf.entities.result import Result
from medperf.entities.benchmark import Benchmark
from medperf.commands.mlcube.associate import AssociateCube

PATCH_ASSOC = "medperf.commands.mlcube.associate.{}"


@pytest.fixture
def cube(mocker):
    cube = mocker.create_autospec(spec=Cube)
    mocker.patch.object(Cube, "get", return_value=cube)
    cube.name = "name"
    return cube


@pytest.fixture
def benchmark(mocker):
    benchmark = mocker.create_autospec(spec=Benchmark)
    mocker.patch.object(Benchmark, "get", return_value=benchmark)
    benchmark.name = "name"
    return benchmark


@pytest.fixture
def result(mocker):
    result = mocker.create_autospec(spec=Result)
    result.results = {}
    return result


@pytest.mark.parametrize("cube_uid", [2405, 4186])
@pytest.mark.parametrize("benchmark_uid", [4416, 1522])
def test_run_associates_cube_with_comms(
    mocker, cube, benchmark, result, cube_uid, benchmark_uid, comms, ui
):
    # Arrange
    spy = mocker.patch.object(comms, "associate_cube")
    comp_ret = ("", "", "", result)
    mocker.patch.object(ui, "prompt", return_value="y")
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateCube.run(cube_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(cube_uid, benchmark_uid, ANY)


@pytest.mark.parametrize("cube_uid", [3081, 1554])
@pytest.mark.parametrize("benchmark_uid", [3739, 4419])
def test_run_calls_compatibility_test_without_force_by_default(
    mocker, cube, benchmark, cube_uid, benchmark_uid, result, comms, ui
):
    # Arrange
    comp_ret = ("", "", "", result)
    mocker.patch.object(ui, "prompt", return_value="y")
    spy = mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateCube.run(cube_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(benchmark_uid, model=cube_uid, force_test=False)


def test_stops_if_not_approved(mocker, comms, ui, cube, result, benchmark):
    # Arrange
    comp_ret = ("", "", "", result)
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, "associate_cube")

    # Act
    with pytest.raises(CleanExit):
        AssociateCube.run(1, 1)
    # Assert
    spy.assert_called_once()
    assoc_spy.assert_not_called()
