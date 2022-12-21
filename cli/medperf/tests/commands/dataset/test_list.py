from medperf.commands.dataset.list import DatasetsList

PATCH_DATASETS = "medperf.commands.dataset.list.{}"


def test_retrieves_all_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_DATASETS.format("Dataset.all"), return_value=[])

    # Act
    DatasetsList.run()

    # Assert
    spy.assert_called_once()


def test_retrieves_all_remote_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_datasets", return_value=[])
    mocker.patch(PATCH_DATASETS.format("Dataset._Dataset__local_all"), return_value=[])

    # Act
    DatasetsList.run()

    # Assert
    spy.assert_called_once()


def test_all_retrieves_all_local_datasets(mocker, comms, ui):
    # Arrange
    spy = mocker.patch(
        PATCH_DATASETS.format("Dataset._Dataset__local_all"), return_value=[]
    )

    # Act
    DatasetsList.run(local=True)

    # Assert
    spy.assert_called_once()


def test_all_retrieves_all_user_datasets(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_datasets", return_value=[])
    mocker.patch(PATCH_DATASETS.format("Dataset._Dataset__local_all"), return_value=[])

    # Act
    DatasetsList.run(mine=True)

    # Assert
    spy.assert_called_once()
