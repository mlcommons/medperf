import os
import pytest
from unittest.mock import call, ANY, mock_open

import medperf.config as config
from medperf.tests.utils import rand_l
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
        return bmk

    return benchmark_gen


@pytest.fixture
def dataset(mocker):
    dataset = mocker.create_autospec(spec=Dataset)
    dataset.uid = "uid"
    return dataset


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


@pytest.mark.parametrize(
    "test_params",
    [
        ((None, "data", "prep", "model", "eval"), True),
        ((None, None, "prep", "model", "eval"), False),
        ((None, "data", None, "model", "eval"), False),
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
    exec = CompatibilityTestExecution(*in_params, comms, ui)
    spy = mocker.patch(PATCH_TEST.format("pretty_error"))

    # Act
    exec.validate()

    # Assert
    if should_be_valid:
        spy.assert_not_called()
    else:
        spy.assert_called_once()


@pytest.mark.parametrize("uid", [None, "1"])
def test_prepare_test_gets_benchmark_or_tmp(mocker, uid, benchmark, comms, ui):
    # Arrange
    bmk = benchmark(uid, 1, 2, 3)
    data = "1"
    prep = "2"
    model = "3"
    eval = "4"
    get_spy = mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    exec = CompatibilityTestExecution(uid, data, prep, model, eval, comms, ui)
    tmp_spy = mocker.patch(PATCH_TEST.format("Benchmark.tmp"), return_value=bmk)

    # Act
    exec.prepare_test()

    # Assert
    if uid:
        get_spy.assert_called_once_with(uid, comms)
    else:
        tmp_spy.assert_called_once_with(prep, model, eval)


@pytest.mark.parametrize("uid", [None, "1"])
def test_prepare_test_sets_uids(mocker, uid, benchmark, comms, ui):
    # Arrange
    bmk = benchmark(uid, 1, 2, 3)
    mocker.patch(PATCH_TEST.format("Benchmark.get"), return_value=bmk)
    mocker.patch.object(Benchmark, "write")
    exec = CompatibilityTestExecution(uid, None, None, None, None, comms, ui)
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
def test_set_cube_uid_keeps_passed_uid_intact(
    mocker, default_setup, model_uid, comms, ui
):
    # Arrange
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)
    exec.model = model_uid
    mocker.patch("os.symlink")

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
def test_set_data_uid_keeps_passed_data_uid(mocker, default_setup, data_uid, comms, ui):
    # Arrange
    mocker.patch(PATCH_TEST.format("get_uids"), return_value=[str(data_uid)])
    exec = CompatibilityTestExecution(1, data_uid, None, None, None, comms, ui)

    # Act
    exec.set_data_uid()

    # Assert
    assert exec.data_uid == data_uid


def test_execute_benchmark_runs_benchmark_workflow(
    mocker, dataset, default_setup, comms, ui
):
    # Arrange
    spy = mocker.patch(PATCH_TEST.format("BenchmarkExecution.run"))
    mocker.patch(PATCH_TEST.format("Result.get_results"), return_value=[])
    exec = CompatibilityTestExecution(1, None, None, None, None, comms, ui)
    exec.dataset = dataset

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
    exec = CompatibilityTestExecution(uid, data, prep, model, eval, comms, ui)
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
    paths_file = config.demo_dset_paths_file
    paths_dict = {"data_path": paths[0], "labels_path": paths[1]}
    mocker.patch("yaml.safe_load", return_value=paths_dict)
    mocker.patch(PATCH_TEST.format("untar"), return_value=untar_path)
    mocker.patch("builtins.open", mock_open())
    exp_data_path = os.path.join(untar_path, paths[0])
    exp_labels_path = os.path.join(untar_path, paths[1])

    exec = CompatibilityTestExecution(uid, data, prep, model, eval, comms, ui)
    exec.prepare_test()

    # Act
    data_path, labels_path = exec.download_demo_data()

    # Assert
    assert data_path == exp_data_path
    assert labels_path == exp_labels_path
