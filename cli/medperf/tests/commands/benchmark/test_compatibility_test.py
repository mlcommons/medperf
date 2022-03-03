from tkinter import N
import pytest
from unittest.mock import call

from medperf import config
from medperf.tests.utils import rand_l
from medperf.entities import Benchmark, Dataset
from medperf.commands.benchmark import CompatibilityTestExecution

PATCH_TEST = "medperf.commands.benchmark.compatibility_test.{}"


@pytest.fixture
def benchmark(mocker):
    def benchmark_gen(uid, data_prep, reference_model, evaluator):
        bmk = mocker.create_autospec(spec=Benchmark)
        bmk.uid = uid
        bmk.data_preparation = data_prep
        bmk.reference_model = reference_model
        bmk.evaluator = evaluator
        return bmk

    return benchmark_gen


@pytest.fixture
def dataset(mocker):
    return mocker.create_autospec(spec=Dataset)


@pytest.fixture
def default_setup(mocker, benchmark, dataset):
    bmk = benchmark(1, 1, 2, 3)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    mocker.patch(PATCH_TEST.format("Dataset"), return_value=dataset)
    return bmk


@pytest.mark.parametrize("attr", ["data_prep", "model", "evaluator"])
@pytest.mark.parametrize("ref_uid", rand_l(1, 500, 1))
def test_set_cube_uid_sets_ref_model_by_default(attr, ref_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)

    # Act
    exec.set_cube_uid(attr, ref_uid)

    # Assert
    assert getattr(exec, attr) == ref_uid


@pytest.mark.parametrize("src", ["path/to/mlcube", "~/.medperf/cubes/1"])
@pytest.mark.parametrize("dst", ["path/to/symlink"])
def test_set_cube_uid_creates_symlink_if_path_provided(mocker, src, dst, comms, ui):
    # Arrange
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.join", return_value=dst)
    spy = mocker.patch("os.symlink")
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)
    exec.model = src

    # Act
    exec.set_cube_uid("model")

    # Assert
    spy.assert_called_once_with(src, dst)


@pytest.mark.parametrize("model_uid", rand_l(1, 500, 5))
def test_set_cube_uid_keeps_passed_uid_intact(default_setup, model_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)
    exec.model = model_uid

    # Act
    exec.set_cube_uid("model")

    # Assert
    assert exec.model == model_uid


def test_set_data_uid_retrieves_demo_data_by_default(mocker, default_setup, comms, ui):
    # Arrange
    spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    spy.assert_called_once()


def test_set_data_uid_calls_DataPreparation_by_default(
    mocker, default_setup, comms, ui
):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("data_uid", rand_l(1, 500, 5))
def test_set_data_uid_sets_demo_data_uid_by_default(
    mocker, default_setup, data_uid, comms, ui
):
    # Arrange
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value=data_uid)
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


@pytest.mark.parametrize("data_uid", rand_l(1, 500, 5))
def test_set_data_uid_keeps_passed_data_uid(default_setup, data_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, data_uid, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


def test_execute_benchmark_runs_benchmark_workflow(mocker, default_setup, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("BenchmarkExecution.run"))
    mocker.patch(PATCH_TEST.format("Result.get_results"), return_value=[])
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)

    # Act
    exec.execute_benchmark()

    # Assert
    spy.assert_called_once()


def test_run_executes_all_the_expected_steps(mocker, default_setup, comms, ui):
    # Arrange
    validate_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.validate")
    )
    set_cube_uid_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.set_cube_uid")
    )
    set_data_uid_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.set_data_uid")
    )
    execute_benchmark_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.execute_benchmark")
    )
    bmk = default_setup
    cube_uid_calls = [
        call("data_prep", bmk.data_preparation),
        call("model", bmk.reference_model),
        call("evaluator", bmk.evaluator),
    ]

    # Act
    CompatibilityTestExecution.run(1, comms, ui)

    # Assert
    validate_spy.assert_called_once()
    set_cube_uid_spy.assert_has_calls(cube_uid_calls)
    set_data_uid_spy.assert_called_once()
    execute_benchmark_spy.assert_called_once()


@pytest.mark.parametrize("bmk_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("data_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("model_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("results", [{}, {"AUC": 0.6}])
def test_run_returns_uids(mocker, bmk_uid, data_uid, model_uid, results, comms, ui):
    # Arrange
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.validate"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.set_cube_uid"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.set_data_uid"))
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.execute_benchmark"),
        return_value=results,
    )
    mocker.patch(PATCH_TEST.format("Benchmark.write"))

    # Act
    ret_uids = CompatibilityTestExecution.run(
        bmk_uid, comms, ui, data_uid=data_uid, model=model_uid
    )

    # Assert
    assert ret_uids == (bmk_uid, data_uid, model_uid, results)
