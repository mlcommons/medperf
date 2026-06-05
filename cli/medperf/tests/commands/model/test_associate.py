from medperf.exceptions import CleanExit
import pytest
from unittest.mock import ANY

from medperf.entities.model import Model
from medperf.entities.benchmark import Benchmark
from medperf.commands.model.associate import AssociateModel

PATCH_ASSOC = "medperf.commands.model.associate.{}"


@pytest.fixture
def model(mocker):
    model = mocker.create_autospec(spec=Model)
    mocker.patch.object(Model, "get", return_value=model)
    model.name = "name"
    return model


@pytest.fixture
def benchmark(mocker):
    benchmark = mocker.create_autospec(spec=Benchmark)
    mocker.patch.object(Benchmark, "get", return_value=benchmark)
    benchmark.name = "name"
    benchmark.metadata = {}
    return benchmark


@pytest.mark.parametrize("model_uid", [2405, 4186])
@pytest.mark.parametrize("benchmark_uid", [4416, 1522])
def test_run_associates_model_with_comms(
    mocker, model, benchmark, model_uid, benchmark_uid, comms, ui
):
    # Arrange
    spy = mocker.patch.object(comms, "associate_benchmark_model")
    comp_ret = ("", {})
    mocker.patch.object(ui, "prompt", return_value="y")
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateModel.run(model_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(model_uid, benchmark_uid, ANY)


@pytest.mark.parametrize("model_uid", [3081, 1554])
@pytest.mark.parametrize("benchmark_uid", [3739, 4419])
def test_run_calls_compatibility_test_without_force_by_default(
    mocker, model, benchmark, model_uid, benchmark_uid, comms, ui
):
    # Arrange
    comp_ret = ("", {})
    mocker.patch.object(ui, "prompt", return_value="y")
    spy = mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateModel.run(model_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(
        benchmark=benchmark_uid, model=model_uid, no_cache=False
    )


def test_stops_if_not_approved(mocker, comms, ui, model, benchmark):
    # Arrange
    comp_ret = ("", {})
    mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, "associate_benchmark_model")

    # Act
    with pytest.raises(CleanExit):
        AssociateModel.run(1, 1)

    # Assert
    spy.assert_called_once()
    assoc_spy.assert_not_called()


@pytest.mark.parametrize("model_uid", [3081])
@pytest.mark.parametrize("benchmark_uid", [3739])
def test_run_calls_compatibility_test_if_needed(
    mocker, model, benchmark, model_uid, benchmark_uid, comms, ui
):
    # Arrange
    benchmark.metadata = {"skip_compatibility_tests": True}
    comp_ret = ("", {})
    mocker.patch.object(ui, "prompt", return_value="y")
    spy = mocker.patch(
        PATCH_ASSOC.format("CompatibilityTestExecution.run"), return_value=comp_ret
    )

    # Act
    AssociateModel.run(model_uid, benchmark_uid)

    # Assert
    spy.assert_not_called()
