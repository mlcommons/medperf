import os
from pathlib import Path
import medperf.config as config
import pytest
from unittest.mock import MagicMock, call

from medperf.tests.utils import rand_l
from medperf.tests.mocks import Benchmark, MockCube
from medperf.commands.dataset.create import DataPreparation

PATCH_DATAPREP = "medperf.commands.dataset.create.{}"
OUT_PATH = "out_path"
OUT_DATAPATH = "out_path/data"
OUT_LABELSPATH = "out_path/labels"
BENCHMARK_UID = "benchmark_uid"
DATA_PATH = "data_path"
LABELS_PATH = "labels_path"
NAME = "name"
DESCRIPTION = "description"
LOCATION = "location"

REG_DICT_KEYS = [
    "name",
    "description",
    "location",
    "split_seed",
    "data_preparation_mlcube",
    "generated_uid",
    "input_data_hash",
    "generated_metadata",
    "status",
    "uid",
    "state",
    "separate_labels",
]


@pytest.fixture
def preparation(mocker, comms, ui):
    mocker.patch("os.path.abspath", side_effect=lambda x: x)
    mocker.patch(PATCH_DATAPREP.format("init_storage"))
    mocker.patch(
        PATCH_DATAPREP.format("generate_tmp_datapath"), return_value=OUT_PATH,
    )
    mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=Benchmark())
    preparation = DataPreparation(
        BENCHMARK_UID,
        None,
        DATA_PATH,
        LABELS_PATH,
        NAME,
        DESCRIPTION,
        LOCATION,
        comms,
        ui,
    )
    mocker.patch(PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True))
    preparation.get_prep_cube()
    preparation.data_path = DATA_PATH
    preparation.labels_path = LABELS_PATH
    return preparation


class TestWithDefaultUID:
    @pytest.mark.parametrize("data_exists", [True, False])
    @pytest.mark.parametrize("labels_exist", [True, False])
    def test_validate_fails_when_paths_dont_exist(
        self, mocker, preparation, data_exists, labels_exist
    ):
        # Arrange
        def exists(path):
            if path == DATA_PATH:
                return data_exists
            elif path == LABELS_PATH:
                return labels_exist
            return False

        mocker.patch("os.path.exists", side_effect=exists)
        should_fail = not data_exists or not labels_exist
        spy = mocker.patch(
            PATCH_DATAPREP.format("pretty_error"), side_effect=lambda *args: exit()
        )

        # Act
        if should_fail:
            with pytest.raises(SystemExit):
                preparation.validate()
        else:
            preparation.validate()

        # Assert
        if should_fail:
            spy.assert_called_once()
        else:
            spy.asset_not_called()

    @pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
    def test_get_prep_cube_gets_prep_cube_if_provided(
        self, mocker, preparation, cube_uid, comms, ui
    ):
        # Arrange
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation = DataPreparation(None, cube_uid, *[""] * 5, comms, ui)
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid, preparation.comms, preparation.ui)

    @pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
    def test_get_prep_cube_gets_benchmark_cube_if_provided(
        self, mocker, preparation, cube_uid, comms, ui
    ):
        # Arrange
        benchmark = Benchmark()
        benchmark.data_preparation = cube_uid
        mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=benchmark)
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation = DataPreparation(cube_uid, None, *[""] * 5, comms, ui)
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid, preparation.comms, preparation.ui)

    def test_get_prep_cube_checks_validity(self, mocker, preparation):
        # Arrange
        mocker.patch(PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True))
        spy = mocker.patch(PATCH_DATAPREP.format("check_cube_validity"))

        # Act
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(preparation.cube, preparation.ui)

    def test_run_cube_tasks_runs_required_tasks(self, mocker, preparation):
        # Arrange
        spy = mocker.patch.object(preparation.cube, "run")
        mocker.patch.object(preparation.cube, "get_default_output", return_value=None)
        ui = preparation.ui
        out_statistics_path = os.path.join(OUT_PATH, config.statistics_filename)
        prepare = call(
            ui,
            task="prepare",
            timeout=None,
            data_path=DATA_PATH,
            labels_path=LABELS_PATH,
            output_path=OUT_DATAPATH,
        )
        check = call(ui, task="sanity_check", data_path=OUT_DATAPATH, timeout=None)
        stats = call(
            ui,
            task="statistics",
            data_path=OUT_DATAPATH,
            timeout=None,
            output_path=out_statistics_path,
        )
        calls = [prepare, check, stats]

        # Act
        preparation.run_cube_tasks()

        # Assert
        spy.assert_has_calls(calls)

    def test_run_cube_tasks_uses_labels_path_if_specified(self, mocker, preparation):
        # Arrange
        spy = mocker.patch.object(preparation.cube, "run")
        # Make sure getting the labels_output returns a value
        mocker.patch.object(
            preparation.cube, "get_default_output", return_value=OUT_LABELSPATH
        )
        ui = preparation.ui
        out_statistics_path = os.path.join(OUT_PATH, config.statistics_filename)
        prepare = call(
            ui,
            task="prepare",
            timeout=None,
            data_path=DATA_PATH,
            labels_path=LABELS_PATH,
            output_path=OUT_DATAPATH,
            output_labels_path=OUT_LABELSPATH,
        )
        check = call(
            ui,
            task="sanity_check",
            timeout=None,
            data_path=OUT_DATAPATH,
            labels_path=OUT_LABELSPATH,
        )
        stats = call(
            ui,
            task="statistics",
            timeout=None,
            data_path=OUT_DATAPATH,
            labels_path=OUT_LABELSPATH,
            output_path=out_statistics_path,
        )
        calls = [prepare, check, stats]

        # Act
        preparation.run_cube_tasks()

        # Assert
        spy.assert_has_calls(calls)

    def test_run_executes_expected_flow(self, mocker, comms, ui, preparation):
        # Arrange
        validate_spy = mocker.patch(PATCH_DATAPREP.format("DataPreparation.validate"))
        get_cube_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.get_prep_cube")
        )
        run_cube_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.run_cube_tasks")
        )
        generate_uids_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.generate_uids"),
        )
        to_permanent_path_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.to_permanent_path"),
        )
        write_spy = mocker.patch(PATCH_DATAPREP.format("DataPreparation.write"),)

        # Act
        DataPreparation.run("", "", "", "", comms, ui)

        # Assert
        validate_spy.assert_called_once()
        get_cube_spy.assert_called_once()
        run_cube_spy.assert_called_once()
        generate_uids_spy.assert_called_once()
        to_permanent_path_spy.assert_called_once()
        write_spy.assert_called_once()

    @pytest.mark.parametrize("benchmark_uid", [None, "1"])
    @pytest.mark.parametrize("cube_uid", [None, "1"])
    def test_fails_if_invalid_params(
        self, mocker, preparation, benchmark_uid, cube_uid, comms, ui
    ):
        # Arrange
        num_arguments = int(benchmark_uid is None) + int(cube_uid is None)

        spy = mocker.patch(PATCH_DATAPREP.format("pretty_error"))

        # Act
        preparation = DataPreparation(benchmark_uid, cube_uid, *[""] * 5, comms, ui)
        preparation.validate()
        # Assert

        if num_arguments != 1:
            spy.assert_called_once()
        else:
            spy.assert_not_called()

    @pytest.mark.parametrize("in_path", ["data_path", "input_path", "/usr/data/path"])
    @pytest.mark.parametrize("out_path", ["out_path", "~/.medperf/data/123"])
    def test_generate_uids_assigns_uids_to_obj_properties(
        self, mocker, in_path, out_path, preparation
    ):
        # Arrange
        mocker.patch(PATCH_DATAPREP.format("get_folder_sha1"), side_effect=lambda x: x)
        preparation.data_path = in_path
        preparation.out_datapath = out_path

        # Act
        preparation.generate_uids()

        # Assert
        assert preparation.in_uid == in_path
        assert preparation.generated_uid == out_path

    def test_todict_calls_get_stats(self, mocker, preparation):
        # Arrange
        spy = mocker.patch(PATCH_DATAPREP.format("get_stats"))
        # Act
        preparation.todict()

        # Assert
        spy.assert_called_once_with(preparation.out_path)

    def test_todict_returns_expected_keys(self, mocker, preparation):
        # Arrange
        mocker.patch(PATCH_DATAPREP.format("get_stats"))

        # Act
        keys = preparation.todict().keys()

        # Assert
        assert set(keys) == set(REG_DICT_KEYS)

    @pytest.mark.parametrize("out_path", ["./test", "~/.medperf", "./workspace"])
    @pytest.mark.parametrize("uid", rand_l(1, 5000, 5))
    def test_to_permanent_path_modifies_output_path(
        self, mocker, out_path, uid, preparation
    ):
        # Arrange
        mocker.patch("os.rename")
        mocker.patch("os.path.exists", return_value=False)
        preparation.generated_uid = str(uid)
        preparation.out_path = out_path
        expected_path = os.path.join(str(Path(out_path).parent), str(uid))

        # Act
        preparation.to_permanent_path()

        # Assert
        assert preparation.out_path == expected_path

    @pytest.mark.parametrize(
        "out_path", ["test", "out", "out_path", "~/.medperf/data/tmp_0"]
    )
    @pytest.mark.parametrize(
        "new_path", ["test", "new", "new_path", "~/.medperf/data/34"]
    )
    @pytest.mark.parametrize("exists", [True, False])
    def test_to_permanent_path_renames_folder_correctly(
        self, mocker, out_path, new_path, preparation, exists
    ):
        # Arrange
        rename_spy = mocker.patch("os.rename")
        rmtree_spy = mocker.patch("shutil.rmtree")
        mocker.patch("os.path.exists", return_value=exists)
        mocker.patch("os.path.join", return_value=new_path)
        preparation.generated_uid = "0"
        preparation.out_path = out_path

        # Act
        preparation.to_permanent_path()

        # Assert
        if exists:
            rmtree_spy.assert_called_once_with(new_path)
        else:
            rmtree_spy.assert_not_called()
        rename_spy.assert_called_once_with(out_path, new_path)

    @pytest.mark.parametrize("filepath", ["filepath"])
    def test_write_writes_to_desired_file(self, mocker, filepath, preparation):
        # Arrange
        mocker.patch("os.path.join", return_value=filepath)
        open_spy = mocker.patch("builtins.open", MagicMock())
        mocker.patch("yaml.dump", MagicMock())
        mocker.patch(PATCH_DATAPREP.format("DataPreparation.todict"), return_value={})

        # Act
        preparation.write()

        # Assert
        open_spy.assert_called_once_with(filepath, "w")


@pytest.mark.parametrize("uid", [str(x) for x in rand_l(1, 5000, 5)])
def test_run_returns_generated_uid(mocker, comms, ui, preparation, uid):
    # Arrange
    def generate_uids(cls):
        cls.generated_uid = uid

    mocker.patch(PATCH_DATAPREP.format("DataPreparation.validate"))
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.get_prep_cube"))
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.run_cube_tasks"))
    mocker.patch(
        PATCH_DATAPREP.format("DataPreparation.generate_uids"),
        side_effect=generate_uids,
        autospec=True,
    )
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.to_permanent_path"),)
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.write"),)

    # Act
    returned_uid = DataPreparation.run("", "", "", "", comms, ui)

    # Assert
    assert returned_uid == uid
