import pytest
from unittest.mock import call, Mock

from medperf.tests.utils import rand_l
from medperf.tests.mocks import Benchmark, MockCube
from medperf.commands import DataPreparation
from medperf.entities import Registration

patch_dataprep = "medperf.commands.prepare.{}"
out_path = "out_path"
out_datapath = "out_datapath"
benchmark_uid = "benchmark_uid"
data_path = "data_path"
labels_path = "labels_path"


@pytest.fixture
def registration(mocker):
    mock_reg = mocker.create_autospec(spec=Registration)
    mocker.patch.object(mock_reg, "generate_uid")
    mocker.patch.object(mock_reg, "is_registered", return_value=False)
    mocker.patch.object(mock_reg, "retrieve_additional_data")
    mocker.patch.object(mock_reg, "to_permanent_path")
    mocker.patch.object(mock_reg, "write")
    mock_reg.generated_uid = ""
    return mock_reg


@pytest.fixture
def preparation(mocker, comms, ui, registration):
    mocker.patch("os.path.abspath", side_effect=lambda x: x)
    mocker.patch(patch_dataprep.format("init_storage"))
    mocker.patch(
        patch_dataprep.format("generate_tmp_datapath"),
        return_value=(out_path, out_datapath),
    )
    mocker.patch(patch_dataprep.format("Benchmark.get"), return_value=Benchmark())
    preparation = DataPreparation(benchmark_uid, data_path, labels_path, comms, ui)
    mocker.patch(patch_dataprep.format("Registration"), return_value=registration)
    mocker.patch(patch_dataprep.format("Cube.get"), return_value=MockCube(True))
    preparation.get_prep_cube()
    return preparation


@pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
def test_get_prep_cube_gets_benchmark_cube(mocker, preparation, cube_uid):
    # Arrange
    preparation.benchmark.data_preparation = cube_uid
    spy = mocker.patch(patch_dataprep.format("Cube.get"), return_value=MockCube(True))

    # Act
    preparation.get_prep_cube()

    # Assert
    spy.assert_called_once_with(cube_uid, preparation.comms)


@pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
def test_get_prep_cube_checks_validity(mocker, preparation, cube_uid):
    # Arrange
    preparation.benchmark.data_preparation = cube_uid
    mocker.patch(patch_dataprep.format("Cube.get"), return_value=MockCube(True))
    spy = mocker.patch(patch_dataprep.format("check_cube_validity"))

    # Act
    preparation.get_prep_cube()

    # Assert
    spy.assert_called_once_with(preparation.cube, preparation.ui)


def test_run_cube_tasks_runs_required_tasks(mocker, preparation):
    # Arrange
    spy = mocker.patch.object(preparation.cube, "run")
    ui = preparation.ui
    prepare = call(
        ui,
        task="prepare",
        data_path=data_path,
        labels_path=labels_path,
        output_path=out_datapath,
    )
    check = call(ui, task="sanity_check", data_path=out_datapath)
    stats = call(ui, task="statistics", data_path=out_datapath)
    calls = [prepare, check, stats]

    # Act
    preparation.run_cube_tasks()

    # Assert
    spy.assert_has_calls(calls)


def test_create_registration_generates_uid_of_output(mocker, preparation, registration):
    # Arrange
    spy = mocker.patch.object(registration, "generate_uid")

    # Act
    preparation.create_registration()

    # Assert
    spy.assert_called_once_with(out_datapath)


def test_create_registration_fails_if_already_registered(
    mocker, preparation, registration
):
    # Arrange
    spy = mocker.patch.object(registration, "is_registered", return_value=True)
    mocker.patch(
        patch_dataprep.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        preparation.create_registration()

    # Assert
    spy.assert_called_once()


def test_create_registration_prints_error_when_prev_registered(
    mocker, preparation, registration
):
    # Arrange
    mocker.patch.object(registration, "is_registered", return_value=True)
    spy = mocker.patch(
        patch_dataprep.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        preparation.create_registration()

    # Assert
    spy.assert_called_once()


def test_create_registration_retrieves_additional_data(
    mocker, preparation, registration
):
    # Arrange
    ui = preparation.ui
    spy = mocker.patch.object(registration, "retrieve_additional_data")

    # Act
    preparation.create_registration()

    # Assert
    spy.assert_called_once_with(ui)


def test_create_registration_moves_to_permanent_path(mocker, preparation, registration):
    # Arrange
    spy = mocker.patch.object(registration, "to_permanent_path")

    # Act
    preparation.create_registration()

    # Assert
    spy.assert_called_once_with(out_path)


def test_create_registration_writes_reg_file(mocker, preparation, registration):
    # Arrange
    spy = mocker.patch.object(registration, "write")

    # Act
    preparation.create_registration()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("uid", rand_l(1, 5000, 5))
def test_create_registration_returns_generated_uid(
    mocker, preparation, registration, uid
):
    # Arrange
    registration.generated_uid = uid

    # Act
    returned_uid = preparation.create_registration()

    # Assert
    assert returned_uid == uid
