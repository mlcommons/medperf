from medperf.exceptions import (
    CommunicationError,
    InvalidArgumentError,
    ExecutionError,
    CleanExit,
)
import pytest

from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.cube import TestCube
from medperf.commands.dataset.prepare import DataPreparation

PATCH_REGISTER = "medperf.commands.dataset.prepare.{}"


@pytest.fixture
def dataset(mocker):
    dset = TestDataset(id=None, generated_uid="generated_uid", state="DEVELOPMENT")
    return dset


@pytest.fixture
def cube(mocker):
    cube = TestCube(is_valid=True)
    return cube


@pytest.fixture
def data_preparation(mocker, dataset, cube):
    dataprep = DataPreparation(None, None)
    dataprep.dataset = dataset
    dataprep.cube = cube
    return dataprep


def test_validate_fails_if_dataset_already_in_operation(mocker, data_preparation):
    # Arrange
    data_preparation.dataset.state = "OPERATION"

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        data_preparation.validate()


def test_get_prep_cube_downloads_cube_file(mocker, data_preparation, cube):
    # Arrange
    spy = mocker.patch.object(cube, "download_run_files")
    mocker.patch(PATCH_REGISTER.format("Cube.get"), return_value=cube)

    # Act
    data_preparation.get_prep_cube()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("allow_sending_reports", [False, True])
def test_prepare_runs_then_stops_report_handler(
    mocker, data_preparation, allow_sending_reports, cube
):
    # Arrange
    data_preparation.allow_sending_reports = allow_sending_reports
    mocker.patch.object(cube, "run")
    start_spy = mocker.patch(PATCH_REGISTER.format("ReportSender.start"))
    stop_spy = mocker.patch(PATCH_REGISTER.format("ReportSender.stop"))

    # Act
    data_preparation.run_prepare()

    # Assert
    if allow_sending_reports:
        start_spy.assert_called_once()
        stop_spy.assert_called_once_with("finished")
    else:
        start_spy.assert_not_called()
        stop_spy.assert_not_called()


@pytest.mark.parametrize("allow_sending_reports", [False, True])
def test_prepare_runs_then_stops_report_handler_on_failure(
    mocker, data_preparation, allow_sending_reports, cube
):
    # Arrange
    def _failure_run(*args, **kwargs):
        raise Exception()

    data_preparation.allow_sending_reports = allow_sending_reports
    mocker.patch.object(cube, "run", side_effect=_failure_run)
    start_spy = mocker.patch(PATCH_REGISTER.format("ReportSender.start"))
    stop_spy = mocker.patch(PATCH_REGISTER.format("ReportSender.stop"))

    # Act
    with pytest.raises(Exception):
        data_preparation.run_prepare()

    # Assert
    if allow_sending_reports:
        start_spy.assert_called_once()
        stop_spy.assert_called_once_with("failed")
    else:
        start_spy.assert_not_called()
        stop_spy.assert_not_called()


@pytest.mark.parametrize("allow_sending_reports", [False, True])
def test_prepare_runs_then_stops_report_handler_on_interrupt(
    mocker, data_preparation, allow_sending_reports, cube
):
    # Arrange
    def _failure_run(*args, **kwargs):
        raise KeyboardInterrupt()

    data_preparation.allow_sending_reports = allow_sending_reports
    mocker.patch.object(cube, "run", side_effect=_failure_run)
    start_spy = mocker.patch(PATCH_REGISTER.format("ReportSender.start"))
    stop_spy = mocker.patch(PATCH_REGISTER.format("ReportSender.stop"))

    # Act
    with pytest.raises(KeyboardInterrupt):
        data_preparation.run_prepare()

    # Assert
    if allow_sending_reports:
        start_spy.assert_called_once()
        stop_spy.assert_called_once_with("interrupted")
    else:
        start_spy.assert_not_called()
        stop_spy.assert_not_called()


@pytest.mark.parametrize("report_specified", [False, True])
@pytest.mark.parametrize("metadata_specified", [False, True])
def test_prepare_checks_report_and_metadata_path(
    mocker, data_preparation, report_specified, metadata_specified, cube
):
    # Arrange
    spy = mocker.patch.object(cube, "run")
    mocker.patch(PATCH_REGISTER.format("ReportSender.start"))
    mocker.patch(PATCH_REGISTER.format("ReportSender.stop"))
    data_preparation.report_specified = report_specified
    data_preparation.metadata_specified = metadata_specified

    # Act
    data_preparation.run_prepare()

    # Assert
    if report_specified:
        assert "report_file" in spy.call_args.kwargs.keys()
    else:
        assert "report_file" not in spy.call_args.kwargs.keys()
    if metadata_specified:
        assert "metadata_path" in spy.call_args.kwargs.keys()
    else:
        assert "metadata_path" not in spy.call_args.kwargs.keys()


@pytest.mark.parametrize(
    "report_specified,exception", [[False, ExecutionError], [True, CleanExit]]
)
def test_sanity_checks_unmarks_the_dataset_as_ready_on_failure(
    mocker, data_preparation, cube, report_specified, exception
):
    # Arrange
    def _failure_run(*args, **kwargs):
        raise ExecutionError()

    mocker.patch.object(cube, "run", side_effect=_failure_run)
    unmark_spy = mocker.patch.object(data_preparation.dataset, "unmark_as_ready")
    data_preparation.report_specified = report_specified

    # Act & assert
    with pytest.raises(exception):
        data_preparation.run_sanity_check()

    # Assert
    unmark_spy.assert_called_once()


def test_statistics_unmarks_the_dataset_as_ready_on_failure(
    mocker, data_preparation, cube
):
    # Arrange
    def _failure_run(*args, **kwargs):
        raise ExecutionError()

    mocker.patch.object(cube, "run", side_effect=_failure_run)
    unmark_spy = mocker.patch.object(data_preparation.dataset, "unmark_as_ready")

    # Act & assert
    with pytest.raises(ExecutionError):
        data_preparation.run_statistics()

    # Assert
    unmark_spy.assert_called_once()


@pytest.mark.parametrize("metadata_specified", [False, True])
def test_statistics_checks_metadata_path(
    mocker, data_preparation, metadata_specified, cube
):
    # Arrange
    spy = mocker.patch.object(cube, "run")
    data_preparation.metadata_specified = metadata_specified

    # Act
    data_preparation.run_statistics()

    # Assert
    if metadata_specified:
        assert "metadata_path" in spy.call_args.kwargs.keys()
    else:
        assert "metadata_path" not in spy.call_args.kwargs.keys()


def test_dataset_is_updated_after_report_sending(mocker, data_preparation, comms):
    # Arrange
    send_spy = mocker.patch.object(comms, "update_dataset")
    write_spy = mocker.patch.object(data_preparation.dataset, "write")
    data_preparation.dataset.report = None
    mocker.patch.object(data_preparation, "_DataPreparation__generate_report_dict")

    # Act
    data_preparation._send_report({})

    # Assert
    send_spy.assert_called_once()
    write_spy.assert_called_once()
    assert data_preparation.dataset.report is not None


def test_dataset_is_not_updated_after_report_sending_failure(
    mocker, data_preparation, comms
):
    # Arrange
    def _failure_run(*args, **kwargs):
        raise CommunicationError()

    mocker.patch.object(comms, "update_dataset", side_effect=_failure_run)
    write_spy = mocker.patch.object(data_preparation.dataset, "write")
    data_preparation.dataset.report = None
    mocker.patch.object(data_preparation, "_DataPreparation__generate_report_dict")

    # Act
    data_preparation._send_report({})

    # Assert
    write_spy.assert_not_called()
    assert data_preparation.dataset.report is None
