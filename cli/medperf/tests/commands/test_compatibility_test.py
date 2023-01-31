import os
from medperf import config
from medperf.exceptions import InvalidArgumentError
import pytest
from pathlib import Path
from unittest.mock import call, ANY, mock_open

from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.commands.compatibility_test import CompatibilityTestExecution

PATCH_TEST = "medperf.commands.compatibility_test.{}"


@pytest.fixture
def benchmark(mocker):
    def benchmark_gen(uid, data_prep, reference_model, evaluator):
        bmk = mocker.create_autospec(spec=Benchmark)
        bmk.uid = uid
        bmk.data_preparation = data_prep
        bmk.reference_model = reference_model
        bmk.evaluator = evaluator
        bmk.demo_dataset_url = None
        bmk.demo_dataset_hash = None
        bmk.generated_uid = (
            f"p{bmk.data_preparation}m{bmk.reference_model}e{bmk.evaluator}"
        )
        return bmk

    return benchmark_gen


@pytest.fixture
def dataset(mocker):
    dataset = mocker.create_autospec(spec=Dataset)
    dataset.uid = "uid"
    dataset.generated_uid = "gen_uid"
    dataset.preparation_cube_uid = "cube_uid"
    return dataset


@pytest.fixture
def default_setup(mocker, benchmark, dataset, fs):
    bmk = benchmark(1, 1, 2, 3)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch(PATCH_TEST.format("Benchmark.tmp"), return_value=bmk)
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.validate"), return_value=("", ""),
    )
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    mocker.patch(PATCH_TEST.format("Dataset.get"), return_value=dataset)
    bmk.generated_uid = "generated_uid"
    return bmk


@pytest.mark.parametrize(
    "test_params",
    [
        ((None, "data", "prep", "model", "eval"), False),
        (("bmk", "data", None, "model", "eval"), False),
        ((None, "data", None, "model", "eval"), True),
        ((None, None, "prep", "model", "eval"), False),
        ((None, "data", "prep", None, "eval"), False),
        ((None, "data", "prep", "model", None), False),
    ],
)
def test_validate_fails_if_incomplete_tmp_benchmark_passed(
    mocker, test_params, comms, ui
):
    # Arrange
    in_params = test_params[0]
    should_be_valid = test_params[1]
    exec = CompatibilityTestExecution(*in_params)

    # Act & Assert
    if should_be_valid:
        exec.validate()
    else:
        with pytest.raises(InvalidArgumentError):
            exec.validate()


@pytest.mark.parametrize("attr", ["data_prep", "model", "evaluator"])
@pytest.mark.parametrize("ref_uid", [436])
def test_set_cube_uid_sets_ref_model_by_default(attr, ref_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, None, None, None, None)

    # Act
    exec.set_cube_uid(attr, ref_uid)

    # Assert
    assert getattr(exec, attr) == ref_uid


@pytest.mark.parametrize("src", ["path/to/mlcube", "~/.medperf/cubes/1"])
@pytest.mark.parametrize("dst", ["path/to/symlink"])
def test_set_cube_uid_creates_symlink_if_path_provided(mocker, src, dst, comms, ui):
    # Arrange
    cubes_loc = "~/.medperf/cubes"
    mocker.patch("os.path.exists", return_value=True)
    join_spy = mocker.patch("os.path.join", return_value=dst)
    syml_spy = mocker.patch("os.symlink")
    mocker.patch(PATCH_TEST.format("storage_path"), return_value=cubes_loc)
    exec = CompatibilityTestExecution(1, None, None, None, None)
    exec.model = src
    expected_path = Path(src).resolve()

    # Act
    exec.set_cube_uid("model")

    # Assert
    syml_spy.assert_called_once_with(expected_path, dst)
    assert call(cubes_loc, ANY) in join_spy.mock_calls


@pytest.mark.parametrize("src", ["path/to/mlcube/mlcube.yaml"])
@pytest.mark.parametrize("dst", ["path/to/symlink"])
def test_set_cube_uid_corrects_path_if_file(mocker, src, dst, comms, ui):
    # Arrange
    cubes_loc = "~/.medperf/cubes"
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch("medperf.utils.cleanup")
    syml_spy = mocker.patch("os.symlink")
    mocker.patch(PATCH_TEST.format("storage_path"), return_value=cubes_loc)
    exec = CompatibilityTestExecution(1, None, None, None, None)
    exec.model = src
    expected_src = Path(src).parent.resolve()

    # Act
    exec.set_cube_uid("model")

    # Assert
    syml_spy.assert_called_once_with(expected_src, ANY)


@pytest.mark.parametrize("model_uid", [418, 165])
def test_set_cube_uid_keeps_passed_uid_intact_if_digit(
    mocker, default_setup, model_uid, comms, ui
):
    # Arrange
    exec = CompatibilityTestExecution(1, None, None, None, None)
    exec.model = model_uid
    mocker.patch("os.symlink")

    # Act
    exec.set_cube_uid("model")

    # Assert
    assert exec.model == model_uid


@pytest.mark.parametrize("model_uid", ["path/to/mlcube.py", "test"])
def test_set_cube_uid_fails_if_unrecognized_input(
    mocker, default_setup, model_uid, comms, ui
):
    # Arrange
    exec = CompatibilityTestExecution(1, None, None, None, None)
    exec.model = model_uid
    mocker.patch("os.symlink")

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        exec.set_cube_uid("model")


def test_set_data_uid_retrieves_demo_data_by_default(mocker, default_setup, comms, ui):
    # Arrange
    spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    exec = CompatibilityTestExecution(1, None, None, None, None)

    # Act
    exec.set_data_uid()

    # Assert
    spy.assert_called_once()


def test_set_data_uid_calls_DataPreparation_by_default(
    mocker, default_setup, comms, ui
):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    exec = CompatibilityTestExecution(1, None, None, None, None)

    # Act
    exec.set_data_uid()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("data_uid", [343, 324])
def test_set_data_uid_sets_demo_data_uid_by_default(
    mocker, default_setup, data_uid, comms, ui
):
    # Arrange
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value=data_uid)
    exec = CompatibilityTestExecution(1, None, None, None, None)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


@pytest.mark.parametrize("data_uid", [85, 397])
def test_set_data_uid_keeps_passed_data_uid(mocker, default_setup, data_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, data_uid, None, None, None)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


@pytest.mark.parametrize("files_already_exist", [True, False])
def test_custom_cubes_metadata_files_creation(mocker, comms, ui, files_already_exist):
    # Arrange
    model_path = "/path/to/model"
    if files_already_exist:

        def exists_side_effect(path):
            return True

        num_calls_expected = 0
    else:
        cube_metadata_file = os.path.join(model_path, config.cube_metadata_filename)
        cube_hashes_filename = os.path.join(model_path, config.cube_hashes_filename)

        def exists_side_effect(path):
            return path not in [
                cube_metadata_file,
                cube_hashes_filename,
            ]

        num_calls_expected = 2

    mocker.patch("os.symlink")
    mocker.patch("os.path.exists", side_effect=exists_side_effect)
    open_spy = mocker.patch("builtins.open", mock_open())
    yml_spy = mocker.patch(PATCH_TEST.format("yaml.dump"))
    # Act
    cls = CompatibilityTestExecution("1", None, None, model_path, None)
    cls.set_cube_uid("model")

    # Assert
    assert open_spy.call_count == num_calls_expected
    assert yml_spy.call_count == num_calls_expected
