from medperf.tests.mocks.requests import benchmark_body
import pytest

from medperf.entities.result import Result
from medperf.entities.benchmark import Benchmark
from medperf.commands.benchmark.submit import SubmitBenchmark

PATCH_BENCHMARK = "medperf.commands.benchmark.submit.{}"
NAME_MAX_LEN = 20
DESC_MAX_LEN = 100

# benchmark_info = {
#     "name": name,
#     "description": description,
#     "docs_url": docs_url,
#     "demo_url": "",
#     "demo_hash": "",
#     "data_preparation_mlcube": prep_uid,
#     "reference_model_mlcube": model_uid,
#     "evaluator_mlcube": eval_uid,
# }


@pytest.fixture
def result(mocker):
    result_obj = mocker.create_autospec(spec=Result)
    # mocker.patch.object(result_obj, "todict", return_value={})
    result_obj.results = {}
    return result_obj


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


@pytest.mark.parametrize(
    "name", [("", False), ("valid", True), ("1" * NAME_MAX_LEN, False)]
)
@pytest.mark.parametrize(
    "desc", [("", True), ("valid", True), ("1" * DESC_MAX_LEN, False)]
)
@pytest.mark.parametrize(
    "docs_url", [("", True), ("invalid", False), ("https://test.test", True)]
)
@pytest.mark.parametrize(
    "demo_url", [("", True), ("invalid", False), ("https://test.test", True)]
)
@pytest.mark.parametrize("prep_uid", [("", False), ("1", True), ("test", False)])
@pytest.mark.parametrize("model_uid", [("", False), ("1", True), ("test", False)])
@pytest.mark.parametrize("eval_uid", [("", False), ("1", True), ("test", False)])
def test_is_valid_passes_valid_fields(
    comms, ui, name, desc, docs_url, demo_url, prep_uid, model_uid, eval_uid
):
    # Arrange
    benchmark_info = {
        "name": name[0],
        "description": desc[0],
        "docs_url": docs_url[0],
        "demo_url": demo_url[0],
        "demo_hash": "test",
        "data_preparation_mlcube": prep_uid[0],
        "reference_model_mlcube": model_uid[0],
        "evaluator_mlcube": eval_uid[0],
    }
    submission = SubmitBenchmark(benchmark_info)
    should_pass = all(
        [
            name[1],
            desc[1],
            docs_url[1],
            demo_url[1],
            prep_uid[1],
            model_uid[1],
            eval_uid[1],
        ]
    )

    # Act
    valid = submission.is_valid()

    # Assert
    assert valid == should_pass


def test_submit_uploads_benchmark_data(mocker, result, comms, ui):
    # Arrange
    benchmark_info = {
        "name": "",
        "description": "",
        "docs_url": "",
        "demo_url": "demo_url",
        "demo_hash": "",
        "data_preparation_mlcube": 0,
        "reference_model_mlcube": 0,
        "evaluator_mlcube": 0,
    }
    submission = SubmitBenchmark(benchmark_info)
    submission.results = result
    expected_data = Benchmark(submission.todict()).todict()
    spy_upload = mocker.patch.object(
        comms, "upload_benchmark", return_value=benchmark_body(1)
    )

    # Act
    submission.submit()

    # Assert
    spy_upload.assert_called_once_with(expected_data)


@pytest.mark.parametrize("demo_hash", ["demo_hash", "437289fa3d"])
@pytest.mark.parametrize("demo_uid", ["demo_uid", "1"])
@pytest.mark.parametrize("results", [{}, {"result": "result_val"}])
def test_get_extra_information_retrieves_expected_info(
    mocker, demo_hash, demo_uid, results, comms, ui
):
    # Arrange
    benchmark_info = {
        "name": "",
        "description": "",
        "docs_url": "",
        "demo_url": "demo_url",
        "demo_hash": "",
        "data_preparation_mlcube": "",
        "reference_model_mlcube": "",
        "evaluator_mlcube": "",
    }
    submission = SubmitBenchmark(benchmark_info)
    mocker.patch.object(comms, "get_benchmark_demo_dataset", return_value="demo_path")
    mocker.patch(PATCH_BENCHMARK.format("get_file_sha1"), return_value=demo_hash)
    mocker.patch(
        PATCH_BENCHMARK.format("SubmitBenchmark.run_compatibility_test"),
        return_value=(demo_uid, results),
    )

    # Act
    submission.get_extra_information()

    # Assert
    assert submission.demo_hash == demo_hash
    assert submission.demo_uid == demo_uid
    assert submission.results == results


def test_run_compatibility_test_executes_test(mocker, benchmark, comms, ui):
    # Arrange
    bmk = benchmark("1", "2", "3", "4")
    benchmark_info = {
        "name": "",
        "description": "",
        "docs_url": "",
        "demo_url": "demo_url",
        "demo_hash": "",
        "data_preparation_mlcube": "",
        "reference_model_mlcube": "",
        "evaluator_mlcube": "",
    }
    submission = SubmitBenchmark(benchmark_info)
    tmp_bmk_spy = mocker.patch(
        PATCH_BENCHMARK.format("Benchmark.tmp"), return_value=bmk
    )
    comp_spy = mocker.patch(
        PATCH_BENCHMARK.format("CompatibilityTestExecution.run"),
        return_value=("bmk_uid", "data_uid", "model_uid", {}),
    )

    # Act
    submission.run_compatibility_test()

    # Assert
    tmp_bmk_spy.assert_called_once()
    comp_spy.assert_called_once()


def test_write_writes_using_entity(mocker, result, comms, ui):
    # Arrange
    benchmark_info = {
        "name": "",
        "description": "",
        "docs_url": "",
        "demo_url": "demo_url",
        "demo_hash": "",
        "data_preparation_mlcube": 0,
        "reference_model_mlcube": 0,
        "evaluator_mlcube": 0,
    }
    submission = SubmitBenchmark(benchmark_info)
    submission.results = result
    spy = mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))
    mockdata = Benchmark(submission.todict()).todict()

    # Act
    submission.write(mockdata)

    # Assert
    spy.assert_called_once_with()


def test_run_executes_expected_flow(mocker, result, comms, ui):
    # Arrange
    benchmark_info = {
        "name": "",
        "description": "",
        "docs_url": "",
        "demo_url": "demo_url",
        "demo_hash": "",
        "data_preparation_mlcube": 0,
        "reference_model_mlcube": 0,
        "evaluator_mlcube": 0,
    }
    val_spy = mocker.patch(
        PATCH_BENCHMARK.format("SubmitBenchmark.is_valid"), return_value=True
    )
    extra_spy = mocker.patch(
        PATCH_BENCHMARK.format("SubmitBenchmark.get_extra_information")
    )
    sub_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.submit"))
    wr_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.write"))

    # Act
    SubmitBenchmark.run(benchmark_info)

    # Assert
    val_spy.assert_called_once()
    extra_spy.assert_called_once()
    sub_spy.assert_called_once()
    wr_spy.assert_called_once()
