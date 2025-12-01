import os
from medperf.utils import get_file_hash
import pytest
import medperf.config as config
from medperf.comms.entity_resources import resources

url = "https://mock.url"


@pytest.fixture(autouse=True)
def setup(mocker, fs):
    def download_resource_side_effect(url, outpath, expected_hash=None):
        fs.create_file(outpath, contents=url)
        return get_file_hash(outpath)

    mocker.patch.object(
        resources, "download_resource", side_effect=download_resource_side_effect
    )


class TestGetCubeImage:
    @pytest.mark.parametrize(
        "url",
        ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"],
    )
    def test_get_cube_image_retrieves_image_if_not_local(self, mocker, url, fs):
        # Arrange
        os.makedirs(config.images_folder, exist_ok=True)

        # Act
        file_path, calc_hash = resources.get_cube_image(url, None)
        exp_file = os.path.join(config.images_folder, calc_hash)

        # Assert
        assert os.path.exists(exp_file) and exp_file == file_path

    @pytest.mark.parametrize(
        "url",
        ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"],
    )
    def test_get_cube_image_uses_cache_if_available(self, mocker, url, fs):
        # Arrange
        spy = mocker.spy(resources, "download_resource")
        os.makedirs(config.images_folder, exist_ok=True)

        # Act
        _, calc_hash = resources.get_cube_image(url, None)
        resources.get_cube_image(url, calc_hash)

        # Assert
        spy.assert_called_once()


class TestGetAdditionalFiles:
    @pytest.fixture(autouse=True)
    def class_setup(self, mocker):
        mocker.patch.object(resources, "untar")

    def test_get_additional_files_does_not_download_if_folder_exists_and_hash_valid(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, config.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")
        _, exp_hash = resources.get_cube_additional(url, cube_path)

        # Act
        resources.get_cube_additional(url, cube_path, exp_hash)

        # Assert
        spy.assert_called_once()  # second time shouldn't download

    def test_get_additional_files_will_download_if_folder_exists_and_hash_outdated(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, config.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")
        resources.get_cube_additional(url, cube_path)

        # Act
        resources.get_cube_additional(url, cube_path, "incorrect hash")

        # Assert
        assert spy.call_count == 2

    def test_get_additional_files_will_download_if_folder_exists_and_hash_valid_but_no_cached_hash(
        self, mocker, fs
    ):  # a test for existing installation before this feature
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, config.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")
        exp_hash = resources.get_cube_additional(url, cube_path)
        hash_cache_file = os.path.join(cube_path, config.mlcube_cache_file)
        os.remove(hash_cache_file)

        # Act
        resources.get_cube_additional(url, cube_path, exp_hash)

        # Assert
        assert spy.call_count == 2
