import pytest

from medperf.commands.execution.model_benchmark_run import ModelBenchmarkRun
from medperf.enums import BenchmarkTopology
from medperf.exceptions import InvalidArgumentError, InvalidEntityError
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.model import TestAssetModel, TestContainerModel

PATCH_RUN = "medperf.commands.execution.model_benchmark_run.{}"
PATCH_PLAN = "medperf.commands.execution.plan.{}"

BENCHMARK_UID = 1
MODEL_UID = 4
ME = 7
SOMEBODY_ELSE = 8

# Two datasets take part in the benchmark; only one of them has published a
# confidential asset for a model owner to run against.
CC_DATASET = 20
PLAIN_DATASET = 21


def mock_benchmark(mocker, state_variables):
    """A benchmark of the given topology, with the containers it calls for.

    Each topology fixes which of the two it has, and the server refuses one
    carrying a container its topology does not use."""
    topology = BenchmarkTopology(state_variables["topology"])

    def __get_side_effect(id):
        return TestBenchmark(
            id=id,
            name="bmk name",
            reference_model=2,
            topology=topology.value,
            benchmark_script=9 if topology.requires_benchmark_script else None,
            data_evaluator_mlcube=3 if topology.requires_evaluator else None,
        )

    mocker.patch(PATCH_RUN.format("Benchmark.get"), side_effect=__get_side_effect)
    return mocker.patch(
        PATCH_RUN.format("Benchmark.get_datasets_uids"),
        return_value=state_variables["benchmark_datasets"],
    )


def mock_model(mocker, state_variables):
    """The model as the server describes it: whose it is, and what it is.

    An asset model whose weights never left its owner's machine is one that
    only runs inside a confidential VM, which is what `requires_cc` means
    today."""
    if state_variables["model_requires_cc"]:
        model = TestAssetModel(
            id=MODEL_UID,
            owner=state_variables["model_owner"],
            asset={
                "id": 5,
                "name": "asset",
                "asset_hash": "asset_hash",
                "asset_url": "local",
                "state": "OPERATION",
                "is_valid": True,
            },
        )
    else:
        model = TestContainerModel(id=MODEL_UID, owner=state_variables["model_owner"])

    mocker.patch(PATCH_RUN.format("Model.get"), return_value=model)
    return model


def mock_datasets(mocker, state_variables):
    def __get_side_effect(id):
        dataset = TestDataset(id=id)
        if id in state_variables["cc_configured_datasets"]:
            dataset.set_cc_config({"storage": {"backend": "mock"}})
        return dataset

    mocker.patch(PATCH_RUN.format("Dataset.get"), side_effect=__get_side_effect)


def mock_associations(mocker, state_variables):
    """This user's own approved model associations.

    A model owner cannot read the benchmark's model roster -- it is the whole
    field of competitors -- so their own listing is what answers whether their
    model may run here."""
    associations = []
    if state_variables["model_is_associated"]:
        associations.append({"benchmark": BENCHMARK_UID, "model": MODEL_UID})
    return mocker.patch(
        PATCH_RUN.format("get_user_associations"), return_value=associations
    )


@pytest.fixture()
def setup(request, mocker, ui, fs):
    state_variables = {
        "model_owner": ME,
        "model_requires_cc": True,
        "model_is_associated": True,
        "topology": BenchmarkTopology.END_TO_END_SCRIPT.value,
        "benchmark_datasets": [CC_DATASET, PLAIN_DATASET],
        "cc_configured_datasets": [CC_DATASET],
    }
    state_variables.update(request.param)

    benchmark_datasets_spy = mock_benchmark(mocker, state_variables)
    model = mock_model(mocker, state_variables)
    mock_datasets(mocker, state_variables)
    associations_spy = mock_associations(mocker, state_variables)
    mocker.patch(PATCH_PLAN.format("Cube.get"), side_effect=lambda id: TestCube(id=id))
    mocker.patch("medperf.entities.cube.Cube.download_run_files")
    mocker.patch(
        PATCH_RUN.format("get_medperf_user_data"), return_value={"id": ME}
    )
    runner_spy = mocker.patch(PATCH_RUN.format("ExperimentsRunner.run"), return_value=[])

    spies = {
        "benchmark_datasets": benchmark_datasets_spy,
        "associations": associations_spy,
        "runner": runner_spy,
        "model": model,
    }
    return state_variables, spies


def ran_datasets(spies):
    """The datasets the runner was handed, in order"""
    experiments = spies["runner"].call_args.kwargs["experiments"]
    return [experiment.dataset.id for experiment in experiments]


@pytest.mark.parametrize("setup", [{"model_owner": SOMEBODY_ELSE}], indirect=True)
def test_running_somebody_elses_model_is_refused(setup):
    """The data it would run against is not this user's to point a model at"""
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="is not yours"):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)


@pytest.mark.parametrize("setup", [{"model_requires_cc": False}], indirect=True)
def test_a_model_that_does_not_run_confidentially_is_refused(setup):
    """Without a confidential VM there is nothing here for a model owner to
    operate -- the datasets are not theirs to read"""
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="does not run confidentially"):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)


@pytest.mark.parametrize("setup", [{"model_is_associated": False}], indirect=True)
def test_a_model_not_approved_for_the_benchmark_is_refused(setup):
    """Owning it is not the question; being approved for this benchmark is"""
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="not associated"):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)


@pytest.mark.parametrize(
    "setup",
    [
        {"topology": BenchmarkTopology.INFERENCE_SCRIPT.value},
        {"topology": BenchmarkTopology.BYO_INFERENCE_SCRIPT.value},
    ],
    indirect=True,
)
def test_a_benchmark_scored_on_prem_cannot_be_run_from_this_side(setup):
    """Its predictions are scored against ground truth only the data owner
    holds, so only they can operate one. End to end is the one topology that
    does not, which is why this side asks for that rather than ruling out the
    topologies it knows about"""
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="on-prem"):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_the_benchmark_model_roster_is_never_read(mocker, setup):
    """It is the model owner's competitors, and the server refuses it to them.
    Their own approved associations answer the same question"""
    # Arrange
    _, spies = setup
    roster = mocker.patch(
        "medperf.entities.benchmark.Benchmark.get_models_uids",
        side_effect=AssertionError("a model owner may not read this"),
    )

    # Act
    ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)

    # Assert
    roster.assert_not_called()
    spies["associations"].assert_called_once()
    spies["benchmark_datasets"].assert_called_once_with(BENCHMARK_UID)


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_asking_for_no_datasets_takes_the_confidential_ones(setup):
    """Every dataset the benchmark approved, minus those with nothing
    confidential to run against"""
    # Arrange
    _, spies = setup

    # Act
    ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)

    # Assert
    assert ran_datasets(spies) == [CC_DATASET]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_no_demo_dataset_is_added(setup):
    """The data owner's side runs the benchmark's reference model on top of
    what it was asked for. This side has no such counterpart: the demo dataset
    is a compatibility fixture, not a participant's data"""
    # Arrange
    state_variables, spies = setup

    # Act
    ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)

    # Assert
    assert set(ran_datasets(spies)).issubset(set(state_variables["benchmark_datasets"]))


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_naming_an_unassociated_dataset_is_refused(setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="Dataset of UID 99 is"):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID, data_uids=[99])


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_naming_a_dataset_without_confidential_computing_is_refused(setup):
    """Skipping it silently would answer a question nobody asked"""
    # Act & Assert
    with pytest.raises(InvalidArgumentError, match="not configured for confidential"):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID, data_uids=[PLAIN_DATASET])


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_named_datasets_are_run_in_the_order_given(setup):
    # Arrange
    _, spies = setup

    # Act
    ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID, data_uids=[CC_DATASET])

    # Assert
    assert ran_datasets(spies) == [CC_DATASET]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_every_experiment_is_the_one_model(setup):
    """A model owner runs the one model they own against many datasets"""
    # Arrange
    _, spies = setup

    # Act
    ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)

    # Assert
    experiments = spies["runner"].call_args.kwargs["experiments"]
    assert [experiment.model.id for experiment in experiments] == [MODEL_UID]


@pytest.mark.parametrize("setup", [{}], indirect=True)
class TestInputFile:
    def test_failure_with_nonexisting_file(self, setup):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            ModelBenchmarkRun.run(
                BENCHMARK_UID, MODEL_UID, datasets_input_file="inputs.txt"
            )

    def test_failure_with_invalid_content(self, setup, fs):
        # Arrange
        fs.create_file("inputs.txt", contents="1,2,text,3")

        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            ModelBenchmarkRun.run(
                BENCHMARK_UID, MODEL_UID, datasets_input_file="inputs.txt"
            )

    def test_datasets_are_read_from_the_file(self, setup, fs):
        # Arrange
        _, spies = setup
        fs.create_file("inputs.txt", contents=str(CC_DATASET))

        # Act
        ModelBenchmarkRun.run(
            BENCHMARK_UID, MODEL_UID, datasets_input_file="inputs.txt"
        )

        # Assert
        assert ran_datasets(spies) == [CC_DATASET]


@pytest.mark.parametrize("setup", [{"cc_configured_datasets": []}], indirect=True)
def test_an_invalid_benchmark_container_still_surfaces(mocker, setup):
    """Nothing about this side swallows the ordinary preparation errors"""
    # Arrange
    mocker.patch(PATCH_PLAN.format("Cube.get"), side_effect=InvalidEntityError)

    # Act & Assert
    with pytest.raises(InvalidEntityError):
        ModelBenchmarkRun.run(BENCHMARK_UID, MODEL_UID)
