import os
import medperf.config as config
from medperf.exceptions import InvalidArgumentError
from medperf.utils import storage_path
import pytest
from unittest.mock import MagicMock, call

from medperf.tests.mocks import MockCube
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.dataset import TestDataset
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


@pytest.fixture
def preparation(mocker, comms, ui):
    mocker.patch("os.path.abspath", side_effect=lambda x: x)
    mocker.patch(PATCH_DATAPREP.format("init_storage"))
    mocker.patch(
        PATCH_DATAPREP.format("generate_tmp_path"), return_value=OUT_PATH,
    )
    mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=TestBenchmark())
    preparation = DataPreparation(
        BENCHMARK_UID, None, DATA_PATH, LABELS_PATH, NAME, DESCRIPTION, LOCATION,
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

        # Act & Assert
        if should_fail:
            with pytest.raises(InvalidArgumentError):
                preparation.validate()
        else:
            preparation.validate()

    @pytest.mark.parametrize("cube_uid", [1776, 4342, 573])
    def test_get_prep_cube_gets_prep_cube_if_provided(
        self, mocker, preparation, cube_uid, comms, ui
    ):
        # Arrange
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation = DataPreparation(None, cube_uid, *[""] * 5)
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid)

    @pytest.mark.parametrize("cube_uid", [998, 68, 109])
    def test_get_prep_cube_gets_benchmark_cube_if_provided(
        self, mocker, preparation, cube_uid, comms, ui
    ):
        # Arrange
        benchmark = TestBenchmark(data_preparation_mlcube=cube_uid)
        mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=benchmark)
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation = DataPreparation(cube_uid, None, *[""] * 5)
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid)

    def test_get_prep_cube_checks_validity(self, mocker, preparation):
        # Arrange
        mocker.patch(PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True))
        spy = mocker.patch(PATCH_DATAPREP.format("check_cube_validity"))

        # Act
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(preparation.cube)

    def test_run_cube_tasks_runs_required_tasks(self, mocker, preparation):
        # Arrange
        spy = mocker.patch.object(preparation.cube, "run")
        mocker.patch.object(preparation.cube, "get_default_output", return_value=None)
        out_statistics_path = os.path.join(OUT_PATH, config.statistics_filename)
        prepare = call(
            task="prepare",
            timeout=None,
            data_path=DATA_PATH,
            labels_path=LABELS_PATH,
            output_path=OUT_DATAPATH,
            string_params={
                "Ptasks.prepare.parameters.input.data_path.opts": "ro",
                "Ptasks.prepare.parameters.input.labels_path.opts": "ro",
            },
        )
        check = call(
            task="sanity_check",
            string_params={"Ptasks.sanity_check.parameters.input.data_path.opts": "ro"},
            data_path=OUT_DATAPATH,
            timeout=None,
        )
        stats = call(
            task="statistics",
            data_path=OUT_DATAPATH,
            timeout=None,
            output_path=out_statistics_path,
            string_params={"Ptasks.statistics.parameters.input.data_path.opts": "ro"},
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
        out_statistics_path = os.path.join(OUT_PATH, config.statistics_filename)
        prepare = call(
            task="prepare",
            timeout=None,
            data_path=DATA_PATH,
            labels_path=LABELS_PATH,
            output_path=OUT_DATAPATH,
            output_labels_path=OUT_LABELSPATH,
            string_params={
                "Ptasks.prepare.parameters.input.data_path.opts": "ro",
                "Ptasks.prepare.parameters.input.labels_path.opts": "ro",
            },
        )
        check = call(
            task="sanity_check",
            timeout=None,
            data_path=OUT_DATAPATH,
            labels_path=OUT_LABELSPATH,
            string_params={"Ptasks.sanity_check.parameters.input.data_path.opts": "ro"},
        )
        stats = call(
            task="statistics",
            timeout=None,
            data_path=OUT_DATAPATH,
            labels_path=OUT_LABELSPATH,
            output_path=out_statistics_path,
            string_params={"Ptasks.statistics.parameters.input.data_path.opts": "ro"},
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
        remove_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.remove_temp_stats"),
        )

        # Act
        DataPreparation.run("", "", "", "")

        # Assert
        validate_spy.assert_called_once()
        get_cube_spy.assert_called_once()
        run_cube_spy.assert_called_once()
        generate_uids_spy.assert_called_once()
        to_permanent_path_spy.assert_called_once()
        write_spy.assert_called_once()
        remove_spy.assert_called_once()

    @pytest.mark.parametrize("benchmark_uid", [None, 1])
    @pytest.mark.parametrize("cube_uid", [None, 1])
    def test_fails_if_invalid_params(
        self, mocker, preparation, benchmark_uid, cube_uid, comms, ui
    ):
        # Arrange
        num_arguments = int(benchmark_uid is None) + int(cube_uid is None)

        # Act
        preparation = DataPreparation(benchmark_uid, cube_uid, *[""] * 5)
        # Assert

        if num_arguments != 1:
            with pytest.raises(InvalidArgumentError):
                preparation.validate()

        else:
            preparation.validate()

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

    def test_todict_calls_get_temp_stats(self, mocker, preparation):
        # Arrange
        spy = mocker.patch(PATCH_DATAPREP.format("DataPreparation.get_temp_stats"))
        # Act
        preparation.todict()

        # Assert
        spy.assert_called_once()

    @pytest.mark.parametrize("path", ["stats_path", "path/to/folder"])
    def test_get_temp_stats_opens_stats_path(self, mocker, path, preparation):
        # Arrange
        preparation.out_path = path
        spy = mocker.patch("builtins.open", MagicMock())
        mocker.patch(PATCH_DATAPREP.format("yaml.safe_load"), return_value={})
        opened_path = os.path.join(path, config.statistics_filename)
        # Act
        preparation.get_temp_stats()

        # Assert
        spy.assert_called_once_with(opened_path, "r")

    @pytest.mark.parametrize("path", ["stats_path", "path/to/folder"])
    def test_remove_temp_stats_removes_file(self, mocker, path, preparation):
        # Arrange
        preparation.out_path = path
        spy = mocker.patch(PATCH_DATAPREP.format("os.remove"))
        deleted = os.path.join(path, config.statistics_filename)
        # Act
        preparation.remove_temp_stats()

        # Assert
        spy.assert_called_once_with(deleted)

    @pytest.mark.parametrize("out_path", ["./test", "~/.medperf", "./workspace"])
    @pytest.mark.parametrize("uid", [858, 2770, 2052])
    def test_to_permanent_path_modifies_output_path(
        self, mocker, out_path, uid, preparation
    ):
        # Arrange
        mocker.patch("os.rename")
        mocker.patch("os.path.exists", return_value=False)
        preparation.generated_uid = str(uid)
        preparation.out_path = out_path
        expected_path = os.path.join(storage_path(config.data_storage), str(uid))

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
        preparation.generated_uid = "hash0"
        preparation.out_path = out_path

        # Act
        preparation.to_permanent_path()

        # Assert
        if exists:
            rmtree_spy.assert_called_once_with(new_path)
        else:
            rmtree_spy.assert_not_called()
        rename_spy.assert_called_once_with(out_path, new_path)

    def test_write_calls_dataset_write(self, mocker, preparation):
        # Arrange
        data_dict = TestDataset().todict()
        mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.todict"), return_value=data_dict
        )
        spy = mocker.patch(PATCH_DATAPREP.format("Dataset.write"))
        # Act
        preparation.write()

        # Assert
        spy.assert_called_once()


@pytest.mark.parametrize("uid", ["hash574", "hash1059", "hash1901"])
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
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.remove_temp_stats"),)

    # Act
    returned_uid = DataPreparation.run("", "", "", "")

    # Assert
    assert returned_uid == uid
