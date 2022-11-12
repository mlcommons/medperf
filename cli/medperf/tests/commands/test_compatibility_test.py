import os
from medperf import config
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
def default_setup(mocker, benchmark, dataset):
    bmk = benchmark(1, 1, 2, 3)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch(PATCH_TEST.format("Benchmark.tmp"), return_value=bmk)
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    mocker.patch(PATCH_TEST.format("DataPreparation.run"), return_value="")
    mocker.patch(PATCH_TEST.format("Dataset.from_generated_uid"), return_value=dataset)
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.cached_result"), return_value=None
    )
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
    spy = mocker.patch(PATCH_TEST.format("pretty_error"))

    # Act
    exec.validate()

    # Assert
    if should_be_valid:
        spy.assert_not_called()
    else:
        spy.assert_called()


@pytest.mark.parametrize("uid", [None, "1"])
def test_prepare_test_gets_benchmark_or_tmp(mocker, uid, benchmark, comms, ui):
    # Arrange
    bmk = benchmark(uid, 1, 2, 3)
    data = "1"
    prep = "2"
    model = "3"
    eval = "4"
    get_spy = mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    exec = CompatibilityTestExecution(uid, data, prep, model, eval)

    # Act
    exec.prepare_test()

    # Assert
    if uid:
        get_spy.assert_called_once_with(uid)
    else:
        get_spy.assert_not_called()


@pytest.mark.parametrize("uid", [None, "1"])
def test_prepare_test_sets_uids(mocker, uid, benchmark, comms, ui):
    # Arrange
    bmk = benchmark(uid, 1, 2, 3)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    exec = CompatibilityTestExecution(uid, None, None, None, None)
    spy = mocker.spy(exec, "set_cube_uid")
    attrs = ["data_prep", "model", "evaluator"]
    calls = [call(attr, ANY) for attr in attrs]
    no_bmk_calls = [call(attr) for attr in attrs]

    # Act
    exec.prepare_test()

    # Assert
    if uid:
        spy.assert_has_calls(calls)
    else:
        spy.assert_has_calls(no_bmk_calls)


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
    spy = mocker.patch(
        PATCH_TEST.format("pretty_error"), side_effect=lambda *args: exit()
    )

    # Act & Assert
    with pytest.raises(SystemExit):
        exec.set_cube_uid("model")

    spy.assert_called_once()


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


@pytest.mark.parametrize("data_uid", [343, 324, 96, 443, 185])
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


@pytest.mark.parametrize("data_uid", [85, 388, 397])
def test_set_data_uid_keeps_passed_data_uid(mocker, default_setup, data_uid, comms, ui):
    # Arrange
    exec = CompatibilityTestExecution(1, data_uid, None, None, None)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


def test_execute_benchmark_runs_benchmark_workflow(
    mocker, dataset, default_setup, comms, ui
):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("BenchmarkExecution.run"))
    mocker.patch(PATCH_TEST.format("Result.from_entities_uids"))
    exec = CompatibilityTestExecution(1, None, None, None, None)
    exec.dataset = dataset

    # Act
    exec.execute_benchmark()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("cache_exists", [False, True])
def test_run_executes_all_the_expected_steps(
    mocker, default_setup, comms, ui, cache_exists
):
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
    cached_result_spy = mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.cached_result"),
        return_value=cache_exists,
    )
    bmk = default_setup
    cube_uid_calls = [
        call("data_prep", bmk.data_preparation),
        call("model", bmk.reference_model),
        call("evaluator", bmk.evaluator),
    ]

    # Act
    CompatibilityTestExecution.run(1)

    # Assert
    validate_spy.assert_called_once()
    set_cube_uid_spy.assert_has_calls(cube_uid_calls)
    set_data_uid_spy.assert_called_once()
    cached_result_spy.assert_called_once()
    if not cache_exists:
        execute_benchmark_spy.assert_called_once()
    else:
        execute_benchmark_spy.assert_not_called()


@pytest.mark.parametrize("bmk_uid", [255, 238])
@pytest.mark.parametrize("data_uid", [312, 498])
@pytest.mark.parametrize("model_uid", [241, 411])
@pytest.mark.parametrize("results", [{}, {"AUC": 0.6}])
def test_run_returns_uids(
    mocker, benchmark, bmk_uid, data_uid, model_uid, results, comms, ui
):
    # Arrange
    bmk = benchmark(bmk_uid, data_uid, model_uid, "3")
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.validate"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.set_cube_uid"))
    mocker.patch(PATCH_TEST.format("CompatibilityTestExecution.set_data_uid"))
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.cached_result"), return_value=None
    )
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.execute_benchmark"),
        return_value=results,
    )

    # Act
    ret_uids = CompatibilityTestExecution.run(
        bmk_uid, data_uid=data_uid, model=model_uid, force_test=True
    )

    # Assert
    assert ret_uids == (bmk_uid, data_uid, model_uid, results)


@pytest.mark.parametrize("hash", ["test", "invalid"])
def test_download_demo_data_fails_if_incorrect_hash(mocker, benchmark, comms, hash, ui):
    # Arrange
    uid = "1"
    data = "1"
    prep = "2"
    model = "3"
    eval = "4"
    bmk = benchmark(uid, prep, model, eval)
    bmk.demo_dataset_url = "url"
    bmk.demo_dataset_hash = hash
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch.object(comms, "get_benchmark_demo_dataset", return_value=("", ""))
    mocker.patch(PATCH_TEST.format("get_file_sha1"), return_value="hash")
    exec = CompatibilityTestExecution(uid, data, prep, model, eval)
    spy = mocker.patch(
        PATCH_TEST.format("pretty_error"), side_effect=lambda *args, **kwargs: exit(),
    )
    exec.prepare_test()

    # Act
    with pytest.raises(SystemExit):
        exec.download_demo_data()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize(
    "paths", [("data", "labels"), ("path/to/data", "path/to/labels")]
)
def test_download_demo_data_extracts_expected_paths(
    mocker, benchmark, paths, comms, ui
):
    # Arrange
    uid = "1"
    data = "1"
    prep = "2"
    model = "3"
    eval = "4"
    bmk = benchmark("1", "2", "3", "4")
    bmk.demo_dataset_url = "url"
    bmk.demo_dataset_hash = "hash"
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch.object(comms, "get_benchmark_demo_dataset", return_value=("", ""))
    mocker.patch(PATCH_TEST.format("get_file_sha1"), return_value="hash")

    untar_path = "untar/path"
    paths_dict = {"data_path": paths[0], "labels_path": paths[1]}
    mocker.patch("yaml.safe_load", return_value=paths_dict)
    mocker.patch(PATCH_TEST.format("untar"), return_value=untar_path)
    mocker.patch("builtins.open", mock_open())
    exp_data_path = os.path.join(untar_path, paths[0])
    exp_labels_path = os.path.join(untar_path, paths[1])

    exec = CompatibilityTestExecution(uid, data, prep, model, eval)
    exec.prepare_test()

    # Act
    data_path, labels_path = exec.download_demo_data()

    # Assert
    assert data_path == exp_data_path
    assert labels_path == exp_labels_path


@pytest.mark.parametrize("bmk_uid", [83, None])
@pytest.mark.parametrize("data_uid", [254, None])
@pytest.mark.parametrize("prep_uid", [466, None])
@pytest.mark.parametrize("model_uid", [145, None])
@pytest.mark.parametrize("eval_uid", [97, None])
def test_run_uses_correct_uids(
    mocker,
    benchmark,
    dataset,
    bmk_uid,
    data_uid,
    prep_uid,
    model_uid,
    eval_uid,
    comms,
    ui,
):
    # Arrange
    bmk_prep_uid = "b1"
    bmk_model_uid = "b2"
    bmk_eval_uid = "b3"
    demo_dataset_uid = "d1"
    tmp_uid = "t1"

    bmk = benchmark(bmk_uid, bmk_prep_uid, bmk_model_uid, bmk_eval_uid)
    bmk.demo_dataset_url = "url"
    bmk.demo_dataset_hash = "hash"

    error_spy = mocker.patch(PATCH_TEST.format("pretty_error"))
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch(
        PATCH_TEST.format("CompatibilityTestExecution.download_demo_data"),
        return_value=("", ""),
    )
    mocker.patch(
        PATCH_TEST.format("DataPreparation.run"), return_value=demo_dataset_uid
    )
    mocker.patch(PATCH_TEST.format("Dataset.from_generated_uid"), return_value=dataset)
    mocker.patch(PATCH_TEST.format("Result.from_entities_uids"))

    def tmp_side_effect(prep, model, eval):
        return benchmark(tmp_uid, prep, model, eval)

    tmp_spy = mocker.patch(
        PATCH_TEST.format("Benchmark.tmp"), side_effect=tmp_side_effect
    )
    exec_spy = mocker.patch(PATCH_TEST.format("BenchmarkExecution.run"))

    exp_data_uid = demo_dataset_uid if data_uid is None else data_uid
    exp_model_uid = bmk_model_uid if model_uid is None else model_uid
    exp_eval_uid = bmk_eval_uid if eval_uid is None else eval_uid
    if prep_uid is not None:
        exp_prep_uid = prep_uid
    elif data_uid is not None:
        exp_prep_uid = dataset.preparation_cube_uid
    else:
        exp_prep_uid = bmk_prep_uid

    # Act
    CompatibilityTestExecution.run(
        bmk_uid, data_uid, prep_uid, model_uid, eval_uid, force_test=True
    )

    # Assert
    if error_spy.call_count != 0:
        return

    tmp_spy.assert_called_once_with(exp_prep_uid, exp_model_uid, exp_eval_uid)
    exec_spy.assert_called_once_with(
        tmp_uid, exp_data_uid, exp_model_uid, run_test=True
    )


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


@pytest.mark.parametrize("force_test", [True, False])
def test_cached_result_looks_for_result_if_not_force(
    mocker, comms, ui, dataset, force_test
):
    # Arrange
    cls = CompatibilityTestExecution("1", "1", "1", "1", None, force_test=force_test)
    cls.dataset = dataset
    spy = mocker.patch(PATCH_TEST.format("Result.from_entities_uids"))

    # Act
    cls.cached_result()

    # Assert
    if force_test:
        spy.assert_not_called()
    else:
        spy.assert_called_once()
