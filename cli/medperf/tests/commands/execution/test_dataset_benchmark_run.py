import pytest

from medperf.commands.execution.dataset_benchmark_run import DatasetBenchmarkRun
from medperf.exceptions import InvalidArgumentError, InvalidEntityError
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.model import TestContainerModel

PATCH_RUN = "medperf.commands.execution.dataset_benchmark_run.{}"
PATCH_PLAN = "medperf.commands.execution.plan.{}"

BENCHMARK_UID = 1
DATA_UID = 2
REFERENCE_MODEL = 2
ASSOCIATED_MODELS = [4, 5, 6, 7]


def mock_benchmark(mocker, state_variables):
    benchmark_prep_cube = state_variables["benchmark_prep_cube"]

    def __get_side_effect(id):
        return TestBenchmark(
            id=id,
            name="bmk name",
            data_evaluator_mlcube=state_variables["evaluator"]["uid"],
            data_preparation_mlcube=benchmark_prep_cube,
            reference_model=REFERENCE_MODEL,
        )

    mocker.patch(PATCH_RUN.format("Benchmark.get"), side_effect=__get_side_effect)
    return mocker.patch(
        PATCH_RUN.format("Benchmark.get_models_uids"),
        return_value=list(ASSOCIATED_MODELS),
    )


def mock_dataset(mocker, state_variables):
    def __get_side_effect(id):
        return TestDataset(
            id=id,
            data_preparation_mlcube=state_variables["dataset_prep_cube"],
            state="OPERATION" if state_variables["operational_dataset"] else "DEVELOPMENT",
        )

    mocker.patch(PATCH_RUN.format("Dataset.get"), side_effect=__get_side_effect)


def mock_cube(mocker, state_variables):
    """The benchmark's own containers, as the plan resolves them"""
    evaluator = state_variables["evaluator"]

    def __get_side_effect(id):
        if id == evaluator["uid"] and evaluator["invalid"]:
            raise InvalidEntityError
        return TestCube(id=id)

    mocker.patch(PATCH_PLAN.format("Cube.get"), side_effect=__get_side_effect)
    mocker.patch("medperf.entities.cube.Cube.download_run_files")


@pytest.fixture()
def setup(request, mocker, ui, fs):
    state_variables = {
        "benchmark_prep_cube": 1,
        "dataset_prep_cube": 1,
        "evaluator": {"uid": 3, "invalid": False},
        "operational_dataset": True,
    }
    state_variables.update(request.param)

    benchmark_models_spy = mock_benchmark(mocker, state_variables)
    mock_dataset(mocker, state_variables)
    mock_cube(mocker, state_variables)
    model_get_spy = mocker.patch(
        PATCH_RUN.format("Model.get"),
        side_effect=lambda uid: TestContainerModel(id=uid),
    )
    runner_spy = mocker.patch(PATCH_RUN.format("ExperimentsRunner.run"), return_value=[])

    spies = {
        "benchmark_models": benchmark_models_spy,
        "model_get": model_get_spy,
        "runner": runner_spy,
    }
    return state_variables, spies


def ran_models(spies):
    """The models the runner was handed, in order"""
    experiments = spies["runner"].call_args.kwargs["experiments"]
    return [experiment.model.id for experiment in experiments]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_failure_with_unregistered_dset(setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        DatasetBenchmarkRun.run(BENCHMARK_UID, data_uid=None)


@pytest.mark.parametrize("setup", [{"operational_dataset": False}], indirect=True)
def test_failure_with_development_dataset(setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID, models_uids=[5])


@pytest.mark.parametrize(
    "setup", [{"benchmark_prep_cube": 11, "dataset_prep_cube": 7}], indirect=True
)
def test_failure_with_unmatching_prep(setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID)


@pytest.mark.parametrize(
    "setup", [{"evaluator": {"uid": 3, "invalid": True}}], indirect=True
)
def test_failure_with_invalid_eval(setup):
    # Act & Assert
    with pytest.raises(InvalidEntityError):
        DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID)


@pytest.mark.parametrize("setup", [{}], indirect=True)
class TestInputFile:
    def test_failure_with_nonexisting_file(self, setup):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            DatasetBenchmarkRun.run(
                BENCHMARK_UID, DATA_UID, models_input_file="inputs.txt"
            )

    def test_failure_with_invalid_content(self, setup, fs):
        # Arrange
        fs.create_file("inputs.txt", contents="1,2,text,3")

        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            DatasetBenchmarkRun.run(
                BENCHMARK_UID, DATA_UID, models_input_file="inputs.txt"
            )

    def test_models_are_read_from_the_file(self, setup, fs):
        # Arrange
        _, spies = setup
        fs.create_file("inputs.txt", contents="4,5")

        # Act
        DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID, models_input_file="inputs.txt")

        # Assert
        assert ran_models(spies) == [4, 5]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_failure_with_unassociated_model(setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="Model of UID 10 is"):
        DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID, models_uids=[4, 10])


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_several_unassociated_models_are_named_in_the_plural(setup):
    """The two branches of that message used to be the wrong way round"""
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="Models of UIDs 10, 11 are"):
        DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID, models_uids=[10, 11])


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_execution_of_reference_model_does_not_read_the_roster(setup):
    """The reference model is part of the benchmark without being in that
    listing, so asking for it alone needs no request at all"""
    # Arrange
    _, spies = setup

    # Act
    DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID, models_uids=[REFERENCE_MODEL])

    # Assert
    spies["benchmark_models"].assert_not_called()
    assert ran_models(spies) == [REFERENCE_MODEL]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_asking_for_no_models_runs_the_whole_benchmark(setup):
    """Every model the benchmark approved, and its reference model"""
    # Arrange
    _, spies = setup

    # Act
    DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID)

    # Assert
    assert ran_models(spies) == ASSOCIATED_MODELS + [REFERENCE_MODEL]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_every_experiment_is_the_one_dataset(setup):
    """A data owner runs many models against the one dataset they own"""
    # Arrange
    _, spies = setup

    # Act
    DatasetBenchmarkRun.run(BENCHMARK_UID, DATA_UID, models_uids=[4, 5])

    # Assert
    experiments = spies["runner"].call_args.kwargs["experiments"]
    assert [experiment.dataset.id for experiment in experiments] == [DATA_UID, DATA_UID]
