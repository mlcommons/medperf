from tkinter import N
import pytest
from unittest.mock import call

from medperf.config import config
from medperf.tests.utils import rand_l
from medperf.entities import Benchmark, Dataset
from medperf.commands import CompatibilityTestExecution

PATCH_TEST = "medperf.commands.compatibility_test.{}"


@pytest.fixture
def benchmark(mocker):
    def benchmark_gen(uid, reference_model):
        bmk = mocker.create_autospec(spec=Benchmark)
        bmk.uid = uid
        bmk.reference_model = reference_model
        return bmk

    return benchmark_gen


@pytest.fixture
def dataset(mocker):
    return mocker.create_autospec(spec=Dataset)


@pytest.fixture
def default_setup(mocker, benchmark, dataset):
    bmk = benchmark(1, 1)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    mocker.patch(PATCH_TEST.format("Dataset"), return_value=dataset)


@pytest.mark.parametrize("data_uid", [None] + rand_l(1, 500, 1))
@pytest.mark.parametrize("model_uid", [None] + rand_l(1, 500, 1))
@pytest.mark.parametrize("cube_path", [None, "cube_path"])
def test_validate_passes_when_passing_one_param(
    mocker, benchmark, data_uid, model_uid, cube_path, comms, ui
):
    # Arrange
    benchmark_uid = 1
    ref_uid = 501
    bmk = benchmark(benchmark_uid, ref_uid)
    patch_pretty_error = PATCH_TEST.format("pretty_error")
    side_effect = lambda *args, **kwargs: exit()
    patch_bmk_get = PATCH_TEST.format("Benchmark.get")
    mocker.patch(patch_bmk_get, return_value=bmk)
    spy = mocker.patch(patch_pretty_error, side_effect=side_effect)
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    mocker.patch(PATCH_TEST.format("BenchmarkExecution.run"), return_value="")
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("os.path.join", return_value="")
    params = [data_uid, model_uid, cube_path]
    num_params = sum([param is not None for param in params])
    exec = CompatibilityTestExecution(
        benchmark_uid, data_uid, model_uid, cube_path, comms, ui
    )

    # Act
    if num_params != 1:
        with pytest.raises(SystemExit):
            exec.validate()

        # Assert
        spy.assert_called_once()
    else:
        # Assert
        spy.assert_not_called()


@pytest.mark.parametrize("ref_uid", rand_l(1, 500, 5))
def test_set_model_uid_sets_ref_model_by_default(mocker, benchmark, ref_uid, comms, ui):
    # Arrange
    bmk = benchmark(1, ref_uid)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    exec = CompatibilityTestExecution(1, None, None, None, comms, ui)

    # Act
    exec.set_model_uid()

    # Assert
    assert exec.model_uid == ref_uid


@pytest.mark.parametrize("model_uid", rand_l(1, 500, 5))
def test_set_model_uid_keeps_passed_uid_intact(default_setup, model_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, None, model_uid, None, comms, ui)

    # Act
    exec.set_model_uid()

    # Assert
    assert exec.model_uid == model_uid


def test_set_model_uid_sets_local_id_for_cube_path(mocker, default_setup, comms, ui):
    # Arrange
    mocker.patch("os.path.join", return_value="")
    mocker.patch("os.symlink")
    exec = CompatibilityTestExecution(1, None, None, "cube_path", comms, ui)

    # Act
    exec.set_model_uid()

    # Assert
    assert exec.model_uid.startswith(config["test_cube_prefix"])


def test_set_model_uid_symlinks_local_cube(mocker, default_setup, comms, ui):
    # Arrange
    mocker.patch("os.path.join", return_value="")
    spy = mocker.patch("os.symlink")
    exec = CompatibilityTestExecution(1, None, None, "cube_path", comms, ui)

    # Act
    exec.set_model_uid()

    # Assert
    spy.assert_called_once()


def test_set_data_uid_retrieves_demo_data_by_default(mocker, default_setup, comms, ui):
    # Arrange
    spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    exec = CompatibilityTestExecution(1, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    spy.assert_called_once()


def test_set_data_uid_calls_DataPreparation_by_default(
    mocker, default_setup, comms, ui
):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    exec = CompatibilityTestExecution(1, None, None, None, comms, ui)

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
    exec = CompatibilityTestExecution(1, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


@pytest.mark.parametrize("data_uid", rand_l(1, 500, 5))
def test_set_data_uid_keeps_passed_data_uid(default_setup, data_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, data_uid, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


def test_execute_benchmark_runs_benchmark_workflow(mocker, default_setup, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("BenchmarkExecution.run"))
    exec = CompatibilityTestExecution(1, None, None, None, comms, ui)

    # Act
    exec.execute_benchmark()

    # Assert
    spy.assert_called_once()


def test_run_executes_all_the_expected_steps(mocker, comms, ui):
    # Arrange
    validate_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.validate")
    )
    set_model_uid_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.set_model_uid")
    )
    set_data_uid_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.set_data_uid")
    )
    execute_benchmark_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.execute_benchmark")
    )

    # Act
    CompatibilityTestExecution.run(1, comms, ui)

    # Assert
    validate_spy.assert_called_once()
    set_model_uid_spy.assert_called_once()
    set_data_uid_spy.assert_called_once()
    execute_benchmark_spy.assert_called_once()


@pytest.mark.parametrize("bmk_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("data_uid", rand_l(1, 500, 2))
@pytest.mark.parametrize("model_uid", rand_l(1, 500, 2))
def test_run_returns_uids(mocker, bmk_uid, data_uid, model_uid, comms, ui):
    # Arrange
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.validate"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.set_model_uid"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.set_data_uid"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.execute_benchmark"))

    # Act
    ret_uids = CompatibilityTestExecution.run(
        bmk_uid, comms, ui, data_uid=data_uid, model_uid=model_uid
    )

    # Assert
    assert ret_uids == (bmk_uid, data_uid, model_uid)
