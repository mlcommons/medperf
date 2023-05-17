import os
from medperf.utils import base_storage_path, get_file_sha1
import pytest
import medperf.config as config
from medperf.comms.entity_resources import resources
import yaml

url = "https://mock.url"


@pytest.fixture(autouse=True)
def setup(mocker, fs):
    def download_resource_side_effect(url, outpath, expected_hash=None):
        fs.create_file(outpath, contents=url)
        return get_file_sha1(outpath)

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
        cube_path = "cube/1"
        image_name = "some_name"
        cube_yaml_path = os.path.join(cube_path, config.cube_filename)
        fs.create_file(
            cube_yaml_path, contents=yaml.dump({"singularity": {"image": image_name}})
        )
        exp_file = os.path.join(cube_path, config.image_path, image_name)
        os.makedirs(base_storage_path(config.images_storage), exist_ok=True)

        # Act
        resources.get_cube_image(url, cube_path)

        # Assert
        assert os.path.exists(exp_file)

    @pytest.mark.parametrize(
        "url",
        ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"],
    )
    def test_get_cube_image_uses_cache_if_available(self, mocker, url, fs):
        # Arrange
        spy = mocker.spy(resources, "download_resource")
        cube_path = "cube/1"
        image_name = "some_name"
        cube_yaml_path = os.path.join(cube_path, config.cube_filename)
        fs.create_file(
            cube_yaml_path, contents=yaml.dump({"singularity": {"image": image_name}})
        )
        img_path = os.path.join(base_storage_path(config.images_storage), "hash")
        fs.create_file(img_path, contents="img")

        # Act
        resources.get_cube_image(url, "cube/1", "hash")

        # Assert
        spy.assert_not_called()


class TestGetAdditionalFiles:
    @pytest.fixture(autouse=True)
    def class_setup(self, mocker):
        mocker.patch.object(resources, "untar")
        mocker.patch.object(resources, "get_folder_sha1", return_value="folder_hash")

    def test_get_additional_files_does_not_download_if_valid_folder_hash(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, config.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")

        # Act
        resources.get_cube_additional(
            url, cube_path, expected_folder_hash="folder_hash"
        )

        # Assert
        spy.assert_not_called()

    def test_get_additional_files_downloads_if_invalid_folder_hash(self, mocker, fs):
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, config.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")

        # Act
        resources.get_cube_additional(
            url, cube_path, expected_folder_hash="unmatching folder hash"
        )

        # Assert
        spy.assert_called_once()
