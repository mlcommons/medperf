from medperf.tests.mocks.benchmark import TestBenchmark
import pytest

from medperf.entities.result import Result
from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf import config

PATCH_BENCHMARK = "medperf.commands.benchmark.submit.{}"
NAME_MAX_LEN = 20
DESC_MAX_LEN = 100

BENCHMARK_INFO = {
    "name": "test",
    "description": "",
    "docs_url": "",
    "demo_dataset_tarball_url": "https://test.test/data.tar.gz",
    "demo_dataset_tarball_hash": "",
    "data_preparation_mlcube": 0,
    "reference_model_mlcube": 0,
    "data_evaluator_mlcube": 0,
}


@pytest.fixture
def result(mocker):
    result_obj = mocker.create_autospec(spec=Result)
    # mocker.patch.object(result_obj, "todict", return_value={})
    result_obj.results = {}
    return result_obj


def test_submit_prepares_tmp_path_for_cleanup():
    # Act
    submission = SubmitBenchmark(BENCHMARK_INFO)

    # Assert
    assert submission.bmk.path in config.tmp_paths


def test_submit_uploads_benchmark_data(mocker, result, comms, ui):
    # Arrange
    submission = SubmitBenchmark(BENCHMARK_INFO)
    submission.bmk.metadata = {"results": result}
    expected_data = submission.bmk.todict()
    spy_upload = mocker.patch.object(
        comms, "upload_benchmark", return_value=TestBenchmark().todict()
    )

    # Act
    submission.submit()

    # Assert
    spy_upload.assert_called_once_with(expected_data)


@pytest.mark.parametrize("demo_hash", ["demo_hash", "437289fa3d"])
@pytest.mark.parametrize("demo_uid", ["demo_uid", "hash1"])
@pytest.mark.parametrize("results", [{}, {"result": "result_val"}])
def test_get_extra_information_retrieves_expected_info(
    mocker, demo_hash, demo_uid, results, comms, ui
):
    # Arrange
    submission = SubmitBenchmark(BENCHMARK_INFO)
    mocker.patch(
        PATCH_BENCHMARK.format("resources.get_benchmark_demo_dataset"),
        return_value="demo_path",
    )
    mocker.patch(PATCH_BENCHMARK.format("get_file_sha1"), return_value=demo_hash)
    mocker.patch(
        PATCH_BENCHMARK.format("SubmitBenchmark.run_compatibility_test"),
        return_value=(demo_uid, results),
    )

    # Act
    submission.get_extra_information()

    # Assert
    assert submission.bmk.demo_dataset_tarball_hash == demo_hash
    assert submission.bmk.demo_dataset_generated_uid == demo_uid
    assert submission.bmk.metadata["results"] == results


def test_run_compatibility_test_executes_test_with_force(mocker, comms, ui):
    # Arrange
    bmk = TestBenchmark()
    submission = SubmitBenchmark(BENCHMARK_INFO)
    submission.bmk = bmk
    comp_spy = mocker.patch(
        PATCH_BENCHMARK.format("CompatibilityTestExecution.run"),
        return_value=("data_uid", {}),
    )

    # Act
    submission.run_compatibility_test()

    # Assert
    comp_spy.assert_called_once_with(benchmark=bmk.generated_uid, no_cache=True)


def test_write_writes_using_entity(mocker, result, comms, ui):
    # Arrange
    submission = SubmitBenchmark(BENCHMARK_INFO)
    submission.results = result
    spy = mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))
    mockdata = submission.bmk.todict()

    # Act
    submission.write(mockdata)

    # Assert
    spy.assert_called_once_with()


def test_run_executes_expected_flow(mocker, result, comms, ui):
    # Arrange
    extra_spy = mocker.patch(
        PATCH_BENCHMARK.format("SubmitBenchmark.get_extra_information")
    )
    sub_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.submit"))
    mv_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.to_permanent_path"))
    wr_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.write"))

    # Act
    SubmitBenchmark.run(BENCHMARK_INFO)

    # Assert
    extra_spy.assert_called_once()
    sub_spy.assert_called_once()
    mv_spy.assert_called_once()
    wr_spy.assert_called_once()
