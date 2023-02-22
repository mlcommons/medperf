import os
import pytest
import medperf.config as config
from medperf.comms.entity_resources import resources

url = "https://mock.url"


def test_get_cube_file_calls_download_resource(mocker):
    # Arrange
    cube_path = "path/to/cube"
    path = "path"
    filename = "filename"
    mocker.patch.object(resources, "get_file_sha1", return_value="hash")
    spy = mocker.patch.object(resources, "download_resource")

    filepath = os.path.join(cube_path, path, filename)

    # Act
    resources.get_cube_file(url, cube_path, path, filename)

    # Assert
    spy.assert_called_once_with(url, filepath)


@pytest.mark.parametrize(
    "url", ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"]
)
def test_get_cube_image_retrieves_image_if_not_local(mocker, url):
    # Arrange
    spy = mocker.patch.object(resources, "get_cube_file", return_value=("", ""))
    cube_path = "cube/1"
    exp_filename = "some name"
    mocker.patch("os.makedirs")
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.symlink")
    mocker.patch("shutil.move")
    mocker.patch.object(resources, "get_file_sha1", return_value="hash")
    mocker.patch.object(resources, "get_cube_image_name", return_value=exp_filename)

    # Act
    resources.get_cube_image(url, cube_path, "hash")

    # Assert
    spy.assert_called_once_with(url, cube_path, config.image_path, exp_filename)


@pytest.mark.parametrize(
    "method", ["get_cube", "get_cube_params", "get_cube_additional"]
)
def test_get_cube_methods_run_get_cube_file(mocker, method):
    # Arrange
    spy = mocker.patch.object(resources, "get_cube_file", return_value="")
    method = getattr(resources, method)

    # Act
    method(url, 1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize(
    "url", ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"]
)
def test_get_cube_image_uses_cache_if_available(mocker, url):
    # Arrange
    spy = mocker.patch.object(resources, "get_cube_file", return_value=("", ""))
    mocker.patch("os.makedirs")
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.symlink")
    mocker.patch("os.unlink")
    mocker.patch.object(resources, "get_cube_image_name", return_value="some name")
    mocker.patch.object(resources, "get_file_sha1", return_value="hash")

    # Act
    resources.get_cube_image(url, "cube/1", "hash")

    # Assert
    spy.assert_not_called()
