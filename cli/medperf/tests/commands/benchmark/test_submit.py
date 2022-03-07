import pytest

from medperf.entities.benchmark import Benchmark
from medperf.commands.benchmark.submit import SubmitBenchmark

PATCH_BENCHMARK = "medperf.commands.benchmark.submit.{}"
NAME_MAX_LEN = 20
DESC_MAX_LEN = 100


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


@pytest.mark.parametrize("name", [None, "", "name"])
@pytest.mark.parametrize("description", [None, "description"])
@pytest.mark.parametrize("docs_url", [None, "docs_url"])
@pytest.mark.parametrize("prep_uid", [None, "", "prep_uid"])
@pytest.mark.parametrize("model_uid", [None, "", "model_uid"])
@pytest.mark.parametrize("eval_uid", [None, "", "eval_uid"])
def test_get_information_promps_unassigned_fields(
    mocker, comms, ui, name, description, docs_url, prep_uid, model_uid, eval_uid
):
    # Arrange
    assign_val = "assign_val"
    submission = SubmitBenchmark(comms, ui)
    submission.name = name
    submission.description = description
    submission.docs_url = docs_url
    submission.data_preparation_mlcube = prep_uid
    submission.reference_model_mlcube = model_uid
    submission.data_evaluator_mlcube = eval_uid
    mocker.patch.object(ui, "prompt", return_value=assign_val)

    # Act
    submission.get_information()

    # Assert
    if not name:
        assert submission.name == assign_val
    else:
        assert submission.name == name
    if not description:
        assert submission.description == assign_val
    else:
        assert submission.description == description
    if not docs_url:
        assert submission.docs_url == assign_val
    else:
        assert submission.docs_url == docs_url
    if not prep_uid:
        assert submission.data_preparation_mlcube == assign_val
    else:
        assert submission.data_preparation_mlcube == prep_uid
    if not model_uid:
        assert submission.reference_model_mlcube == assign_val
    else:
        assert submission.reference_model_mlcube == model_uid
    if not eval_uid:
        assert submission.data_evaluator_mlcube == assign_val
    else:
        assert submission.data_evaluator_mlcube == eval_uid


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
    submission = SubmitBenchmark(comms, ui)
    submission.name = name[0]
    submission.description = desc[0]
    submission.docs_url = docs_url[0]
    submission.demo_url = demo_url[0]
    submission.data_preparation_mlcube = prep_uid[0]
    submission.reference_model_mlcube = model_uid[0]
    submission.data_evaluator_mlcube = eval_uid[0]
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


def test_submit_uploads_benchmark_data(mocker, comms, ui):
    # Arrange
    mock_body = {}
    submission = SubmitBenchmark(comms, ui)
    spy_todict = mocker.patch.object(submission, "todict", return_value=mock_body)
    spy_upload = mocker.patch.object(comms, "upload_benchmark", return_value=1)

    # Act
    submission.submit()

    # Assert
    spy_todict.assert_called_once()
    spy_upload.assert_called_once_with(mock_body)


@pytest.mark.parametrize("demo_hash", ["demo_hash", "437289fa3d"])
@pytest.mark.parametrize("demo_uid", ["demo_uid", "1"])
@pytest.mark.parametrize("results", [{}, {"result": "result_val"}])
def test_get_extra_information_retrieves_expected_info(
    mocker, demo_hash, demo_uid, results, comms, ui
):
    # Arrange
    submission = SubmitBenchmark(comms, ui)
    submission.demo_url = "demo_url"
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
    submission = SubmitBenchmark(comms, ui)
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
