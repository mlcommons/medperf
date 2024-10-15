import os
from medperf.utils import get_file_hash
import pytest
from medperf import settings
from medperf.comms.entity_resources import resources
import yaml

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
        cube_path = "cube/1"
        image_name = "some_name"
        cube_yaml_path = os.path.join(cube_path, settings.cube_filename)
        fs.create_file(
            cube_yaml_path, contents=yaml.dump({"singularity": {"image": image_name}})
        )
        exp_file = os.path.join(cube_path, settings.image_path, image_name)
        os.makedirs(settings.images_folder, exist_ok=True)

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
        cube_yaml_path = os.path.join(cube_path, settings.cube_filename)
        fs.create_file(
            cube_yaml_path, contents=yaml.dump({"singularity": {"image": image_name}})
        )
        img_path = os.path.join(settings.images_folder, "hash")
        fs.create_file(img_path, contents="img")

        # Act
        resources.get_cube_image(url, "cube/1", "hash")

        # Assert
        spy.assert_not_called()


class TestGetAdditionalFiles:
    @pytest.fixture(autouse=True)
    def class_setup(self, mocker):
        mocker.patch.object(resources, "untar")

    def test_get_additional_files_does_not_download_if_folder_exists_and_hash_valid(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, settings.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")
        exp_hash = resources.get_cube_additional(url, cube_path)

        # Act
        resources.get_cube_additional(url, cube_path, exp_hash)

        # Assert
        spy.assert_called_once()  # second time shouldn't download

    def test_get_additional_files_will_download_if_folder_exists_and_hash_outdated(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        additional_files_folder = os.path.join(cube_path, settings.additional_path)
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
        additional_files_folder = os.path.join(cube_path, settings.additional_path)
        fs.create_dir(additional_files_folder)
        spy = mocker.spy(resources, "download_resource")
        exp_hash = resources.get_cube_additional(url, cube_path)
        hash_cache_file = os.path.join(cube_path, settings.mlcube_cache_file)
        os.remove(hash_cache_file)

        # Act
        resources.get_cube_additional(url, cube_path, exp_hash)

        # Assert
        assert spy.call_count == 2


class TestGetCube:
    def test_get_cube_does_not_download_if_folder_exists_and_hash_valid(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        spy = mocker.spy(resources, "download_resource")
        _, exp_hash = resources.get_cube(url, cube_path)

        # Act
        resources.get_cube(url, cube_path, exp_hash)

        # Assert
        spy.assert_called_once()  # second time shouldn't download

    def test_get_cube_does_will_download_if_folder_exists_and_hash_outdated(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        spy = mocker.spy(resources, "download_resource")
        resources.get_cube(url, cube_path)

        # Act
        resources.get_cube(url, cube_path, "incorrect hash")

        # Assert
        assert spy.call_count == 2


class TestGetCubeParams:
    def test_get_cube_params_does_not_download_if_folder_exists_and_hash_valid(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        spy = mocker.spy(resources, "download_resource")
        _, exp_hash = resources.get_cube_params(url, cube_path)

        # Act
        resources.get_cube_params(url, cube_path, exp_hash)

        # Assert
        spy.assert_called_once()  # second time shouldn't download

    def test_get_cube_params_does_will_download_if_folder_exists_and_hash_outdated(
        self, mocker, fs
    ):
        # Arrange
        cube_path = "cube/1"
        spy = mocker.spy(resources, "download_resource")
        resources.get_cube_params(url, cube_path)

        # Act
        resources.get_cube_params(url, cube_path, "incorrect hash")

        # Assert
        assert spy.call_count == 2
