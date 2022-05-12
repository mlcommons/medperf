import pytest
from unittest.mock import call

from medperf.tests.utils import rand_l
from medperf.tests.mocks import Benchmark, MockCube
from medperf.entities.registration import Registration
from medperf.commands.dataset.create import DataPreparation

PATCH_DATAPREP = "medperf.commands.dataset.create.{}"
OUT_PATH = "out_path"
OUT_DATAPATH = "out_datapath"
BENCHMARK_UID = "benchmark_uid"
DATA_PATH = "data_path"
LABELS_PATH = "labels_path"
NAME = "name"
DESCRIPTION = "description"
LOCATION = "location"


@pytest.fixture
def registration(mocker, request):
    mock_reg = mocker.create_autospec(spec=Registration)
    mocker.patch.object(mock_reg, "generate_uids")
    mocker.patch.object(mock_reg, "is_registered", return_value=False)
    mocker.patch.object(mock_reg, "to_permanent_path")
    mocker.patch.object(mock_reg, "write")
    mock_reg.generated_uid = request.param
    return mock_reg


@pytest.fixture
def preparation(mocker, comms, ui, registration):
    mocker.patch("os.path.abspath", side_effect=lambda x: x)
    mocker.patch(PATCH_DATAPREP.format("init_storage"))
    mocker.patch(
        PATCH_DATAPREP.format("generate_tmp_datapath"),
        return_value=(OUT_PATH, OUT_DATAPATH),
    )
    mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=Benchmark())
    preparation = DataPreparation(
        BENCHMARK_UID, DATA_PATH, LABELS_PATH, NAME, DESCRIPTION, LOCATION, comms, ui
    )
    mocker.patch(PATCH_DATAPREP.format("Registration"), return_value=registration)
    mocker.patch(PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True))
    preparation.get_prep_cube()
    preparation.data_path = DATA_PATH
    preparation.labels_path = LABELS_PATH
    return preparation


@pytest.mark.parametrize("registration", ["uid"], indirect=True)
class TestWithDefaultUID:
    @pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
    def test_get_prep_cube_gets_benchmark_cube(self, mocker, preparation, cube_uid):
        # Arrange
        preparation.benchmark.data_preparation = cube_uid
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid, preparation.comms, preparation.ui)

    @pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
    def test_get_prep_cube_checks_validity(self, mocker, preparation, cube_uid):
        # Arrange
        preparation.benchmark.data_preparation = cube_uid
        mocker.patch(PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True))
        spy = mocker.patch(PATCH_DATAPREP.format("check_cube_validity"))

        # Act
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(preparation.cube, preparation.ui)

    def test_run_cube_tasks_runs_required_tasks(self, mocker, preparation):
        # Arrange
        spy = mocker.patch.object(preparation.cube, "run")
        ui = preparation.ui
        prepare = call(
            ui,
            task="prepare",
            data_path=DATA_PATH,
            labels_path=LABELS_PATH,
            output_path=OUT_DATAPATH,
        )
        check = call(ui, task="sanity_check", data_path=OUT_DATAPATH)
        stats = call(ui, task="statistics", data_path=OUT_DATAPATH)
        calls = [prepare, check, stats]

        # Act
        preparation.run_cube_tasks()

        # Assert
        spy.assert_has_calls(calls)

    def test_create_registration_generates_uid_of_output(
        self, mocker, preparation, registration
    ):
        # Arrange
        spy = mocker.patch.object(registration, "generate_uids")
        print(preparation.data_path)

        # Act
        preparation.create_registration()

        # Assert
        spy.assert_called_once_with(DATA_PATH, OUT_DATAPATH)

    def test_create_registration_fails_if_already_registered(
        self, mocker, preparation, registration
    ):
        # Arrange
        spy = mocker.patch.object(registration, "is_registered", return_value=True)
        mocker.patch(
            PATCH_DATAPREP.format("pretty_error"),
            side_effect=lambda *args, **kwargs: exit(),
        )

        # Act
        with pytest.raises(SystemExit):
            preparation.create_registration()

        # Assert
        spy.assert_called_once()

    def test_create_registration_prints_error_when_prev_registered(
        self, mocker, preparation, registration
    ):
        # Arrange
        mocker.patch.object(registration, "is_registered", return_value=True)
        spy = mocker.patch(
            PATCH_DATAPREP.format("pretty_error"),
            side_effect=lambda *args, **kwargs: exit(),
        )

        # Act
        with pytest.raises(SystemExit):
            preparation.create_registration()

        # Assert
        spy.assert_called_once()

    def test_create_registration_moves_to_permanent_path(
        self, mocker, preparation, registration
    ):
        # Arrange
        spy = mocker.patch.object(registration, "to_permanent_path")

        # Act
        preparation.create_registration()

        # Assert
        spy.assert_called_once_with(OUT_PATH)

    def test_create_registration_writes_reg_file(
        self, mocker, preparation, registration
    ):
        # Arrange
        spy = mocker.patch.object(registration, "write")

        # Act
        preparation.create_registration()

        # Assert
        spy.assert_called_once()

    @pytest.mark.parametrize("uid", rand_l(1, 5000, 5))
    def test_create_registration_returns_generated_uid(
        self, mocker, preparation, registration, uid
    ):
        # Arrange
        registration.generated_uid = uid

        # Act
        returned_uid = preparation.create_registration()

        # Assert
        assert returned_uid == uid

    def test_run_executes_expected_flow(self, mocker, comms, ui, preparation):
        # Arrange
        get_cube_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.get_prep_cube")
        )
        run_cube_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.run_cube_tasks")
        )
        create_reg_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.create_registration"),
            return_value="",
        )

        # Act
        DataPreparation.run("", "", "", "", "", "", comms, ui)

        # Assert
        get_cube_spy.assert_called_once()
        run_cube_spy.assert_called_once()
        create_reg_spy.assert_called_once()


@pytest.mark.parametrize(
    "registration", [str(x) for x in rand_l(1, 5000, 5)], indirect=True
)
def test_run_returns_registration_generated_uid(
    mocker, comms, ui, preparation, registration
):
    # Arrange
    mocker.patch.object(preparation.cube, "run")

    # Act
    returned_uid = DataPreparation.run("", "", "", "", "", "", comms, ui)

    # Assert
    assert returned_uid == registration.generated_uid
