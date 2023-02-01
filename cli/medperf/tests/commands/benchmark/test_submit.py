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
        bmk.generated_uid = f"p{bmk.data_preparation}m{bmk.reference_model}e{bmk.evaluator}"
        return bmk

    return benchmark_gen


@pytest.mark.parametrize(
    "name,desc,docs_url,demo_url,prep_uid,model_uid,eval_uid,should_pass",
    [
        # Valid minimal submission
        ("valid", "", "", "", "1", "1", "1", True),
        # Invalid empty name
        ("", "", "", "", "1", "1", "1", False),
        # Invalid name length
        ("1" * NAME_MAX_LEN, "", "", "", "1", "1", "1", False),
        # Invalid desc length
        ("valid", "1" * DESC_MAX_LEN, "", "", "1", "1", "1", False),
        # Invalid docs_url string
        ("valid", "", "invalid", "", "1", "1", "1", False),
        # Invalid demo_url
        ("valid", "", "", "invalid", "1", "1", "1", False),
        # Invalid empty prep_uid
        ("valid", "", "", "", "", "1", "1", False),
        # Invalid prep_uid string
        ("valid", "", "", "", "invalid", "1", "1", False),
        # Invalid empty prep_uid
        ("valid", "", "", "", "1", "", "1", False),
        # Invalid prep_uid string
        ("valid", "", "", "", "1", "invalid", "1", False),
        # Invalid empty prep_uid
        ("valid", "", "", "", "1", "1", "", False),
        # Invalid prep_uid string
        ("valid", "", "", "", "1", "1", "invalid", False),
        # Valid full submission
        (
            "valid",
            "desc",
            "https://test.test",
            "https://test.test",
            "1",
            "1",
            "1",
            True,
        ),
    ],
)
def test_is_valid_passes_valid_fields(
    comms,
    ui,
    name,
    desc,
    docs_url,
    demo_url,
    prep_uid,
    model_uid,
    eval_uid,
    should_pass,
):
    # Arrange
    benchmark_info = {
        "name": name,
        "description": desc,
        "docs_url": docs_url,
        "demo_url": demo_url,
        "demo_hash": "test",
        "data_preparation_mlcube": prep_uid,
        "reference_model_mlcube": model_uid,
        "evaluator_mlcube": eval_uid,
    }
    submission = SubmitBenchmark(benchmark_info)

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


def test_run_compatibility_test_executes_test_with_force(mocker, benchmark, comms, ui):
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
    comp_spy.assert_called_once_with(bmk.generated_uid, force_test=True)


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
    mv_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.to_permanent_path"))
    wr_spy = mocker.patch(PATCH_BENCHMARK.format("SubmitBenchmark.write"))

    # Act
    SubmitBenchmark.run(benchmark_info)

    # Assert
    val_spy.assert_called_once()
    extra_spy.assert_called_once()
    sub_spy.assert_called_once()
    mv_spy.assert_called_once()
    wr_spy.assert_called_once()
