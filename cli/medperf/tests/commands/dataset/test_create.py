import os
import medperf.config as config
from medperf.exceptions import InvalidArgumentError
from medperf.utils import storage_path
import pytest
from unittest.mock import call

from medperf.tests.mocks import MockCube
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.dataset import TestDataset
from medperf.commands.dataset.prepare import DataPreparation

PATCH_DATAPREP = "medperf.commands.dataset.create.{}"
OUT_PATH = "out_path"
STATISTICS_PATH = "statistics_path"
OUT_DATAPATH = "out_path/data"
OUT_LABELSPATH = "out_path/labels"
BENCHMARK_UID = "benchmark_uid"
DATA_PATH = "data_path"
LABELS_PATH = "labels_path"
NAME = "name"
DESCRIPTION = "description"
LOCATION = "location"
SUMMARY_PATH = "summary"
REPORT_PATH = "report"


@pytest.fixture
def preparation(mocker, comms, ui):
    mocker.patch("os.path.abspath", side_effect=lambda x: x)
    mocker.patch(
        PATCH_DATAPREP.format("generate_tmp_path"), return_value=STATISTICS_PATH
    )
    mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=TestBenchmark())
    preparation = DataPreparation(
        BENCHMARK_UID,
        None,
        DATA_PATH,
        LABELS_PATH,
        NAME,
        DESCRIPTION,
        LOCATION,
        SUMMARY_PATH,
    )
    mocker.patch(PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True))
    preparation.get_prep_cube()
    preparation.data_path = DATA_PATH
    preparation.labels_path = LABELS_PATH
    preparation.out_datapath = OUT_DATAPATH
    preparation.out_labelspath = OUT_LABELSPATH
    preparation.report_path = REPORT_PATH
    preparation.report_specified = False
    preparation.labels_specified = True
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
        self, mocker, cube_uid, comms, ui, fs
    ):
        # Arrange
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation = DataPreparation(None, cube_uid, *[""] * 6)
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid)

    @pytest.mark.parametrize("cube_uid", [998, 68, 109])
    def test_get_prep_cube_gets_benchmark_cube_if_provided(
        self, mocker, cube_uid, comms, ui, fs
    ):
        # Arrange
        benchmark = TestBenchmark(data_preparation_mlcube=cube_uid)
        mocker.patch(PATCH_DATAPREP.format("Benchmark.get"), return_value=benchmark)
        spy = mocker.patch(
            PATCH_DATAPREP.format("Cube.get"), return_value=MockCube(True)
        )

        # Act
        preparation = DataPreparation(cube_uid, None, *[""] * 6)
        preparation.get_prep_cube()

        # Assert
        spy.assert_called_once_with(cube_uid)

    def test_run_cube_tasks_runs_required_tasks(self, mocker, preparation):
        # Arrange
        spy = mocker.patch.object(preparation.cube, "run")

        prepare = call(
            task="prepare",
            timeout=None,
            data_path=DATA_PATH,
            labels_path=LABELS_PATH,
            output_path=OUT_DATAPATH,
            output_labels_path=OUT_LABELSPATH,
        )
        check = call(
            task="sanity_check",
            timeout=None,
            data_path=OUT_DATAPATH,
            labels_path=OUT_LABELSPATH,
        )
        stats = call(
            task="statistics",
            timeout=None,
            data_path=OUT_DATAPATH,
            labels_path=OUT_LABELSPATH,
            output_path=STATISTICS_PATH,
        )
        calls = [prepare, check, stats]

        # Act
        preparation.run_prepare()
        preparation.run_sanity_check()
        preparation.run_statistics()

        # Assert
        spy.assert_has_calls(calls)

    def test_run_executes_expected_flow(self, mocker, comms, ui, fs):
        # Arrange
        validate_spy = mocker.patch(PATCH_DATAPREP.format("DataPreparation.validate"))
        get_cube_spy = mocker.spy(DataPreparation, "get_prep_cube")
        mocker.patch(
            PATCH_DATAPREP.format("Cube.get"),
            side_effect=lambda id: MockCube(True, id),
        )
        run_prepare_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.run_prepare")
        )
        run_sanity_check_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.run_sanity_check")
        )
        run_statistics_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.run_statistics")
        )
        get_stat_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.get_statistics"),
        )
        generate_uids_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.generate_uids"),
        )
        to_permanent_path_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.to_permanent_path"),
        )
        write_spy = mocker.patch(
            PATCH_DATAPREP.format("DataPreparation.write"),
        )

        # Act
        DataPreparation.run("", "", "", "")

        # Assert
        validate_spy.assert_called_once()
        get_cube_spy.assert_called_once()
        run_prepare_spy.assert_called_once()
        run_sanity_check_spy.assert_called_once()
        run_statistics_spy.assert_called_once()
        get_stat_spy.assert_called_once()
        generate_uids_spy.assert_called_once()
        to_permanent_path_spy.assert_called_once()
        write_spy.assert_called_once()

    @pytest.mark.parametrize("benchmark_uid", [None, 1])
    @pytest.mark.parametrize("cube_uid", [None, 1])
    def test_fails_if_invalid_params(self, mocker, benchmark_uid, cube_uid, comms, ui):
        # Arrange
        num_arguments = int(benchmark_uid is None) + int(cube_uid is None)

        # Act
        preparation = DataPreparation(benchmark_uid, cube_uid, *[""] * 6)
        # Assert

        if num_arguments != 1:
            with pytest.raises(InvalidArgumentError):
                preparation.validate()

        else:
            preparation.validate()

    @pytest.mark.parametrize(
        "in_path",
        [
            ["data", "labels"],
            ["in_data", "in_labels"],
            ["/usr/data/path", "usr/labels/path"],
        ],
    )
    @pytest.mark.parametrize(
        "out_path",
        [
            ["out_data", "out_labels"],
            ["~/.medperf/data/123/data", "~/.medperf/data/123/labels"],
        ],
    )
    def test_generate_uids_assigns_uids_to_obj_properties(
        self, mocker, in_path, out_path, preparation
    ):
        # Arrange
        mocker.patch(PATCH_DATAPREP.format("get_folders_hash"), side_effect=lambda x: x)
        preparation.data_path = in_path[0]
        preparation.labels_path = in_path[1]
        preparation.out_datapath = out_path[0]
        preparation.out_labelspath = out_path[1]

        # Act
        preparation.generate_uids()

        # Assert
        assert preparation.in_uid == in_path
        assert preparation.generated_uid == out_path

    def test_todict_calls_get_stats_sets_statistics(self, mocker, preparation, fs):
        # Arrange
        contents = "stats: 123"
        exp_contents = {"stats": 123}
        fs.create_file(STATISTICS_PATH, contents=contents)

        # Act
        preparation.get_statistics()

        # Assert
        assert preparation.generated_metadata == exp_contents

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
        cleanup_spy = mocker.patch(PATCH_DATAPREP.format("remove_path"))
        mocker.patch("os.path.exists", return_value=exists)
        mocker.patch("os.path.join", return_value=new_path)
        preparation.generated_uid = "hash0"
        preparation.out_path = out_path

        # Act
        preparation.to_permanent_path()

        # Assert
        cleanup_spy.assert_called_once_with(new_path)
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
def test_run_returns_generated_uid(mocker, comms, ui, uid):
    # Arrange
    def generate_uids(cls):
        cls.generated_uid = uid

    mocker.patch(PATCH_DATAPREP.format("DataPreparation.validate"))
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.run_prepare"))
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.run_sanity_check"))
    mocker.patch(PATCH_DATAPREP.format("DataPreparation.run_statistics"))
    mocker.patch(
        PATCH_DATAPREP.format("DataPreparation.get_statistics"),
    )
    mocker.patch(
        PATCH_DATAPREP.format("DataPreparation.generate_uids"),
        side_effect=generate_uids,
        autospec=True,
    )
    mocker.patch(
        PATCH_DATAPREP.format("DataPreparation.to_permanent_path"),
    )
    mocker.patch(
        PATCH_DATAPREP.format("DataPreparation.write"),
    )
    mocker.patch(
        PATCH_DATAPREP.format("Cube.get"),
        side_effect=lambda id: MockCube(True, id),
    )

    # Act
    returned_uid = DataPreparation.run("", 1, "", "")

    # Assert
    assert returned_uid == uid
