import os
from medperf.utils import base_storage_path
import pytest
import medperf.config as config
from medperf.comms.entity_resources import resources
import yaml

url = "https://mock.url"


@pytest.fixture
def setup(mocker, fs):
    def download_resource_side_effect(url, outpath):
        fs.create_file(outpath, contents=url)

    mocker.patch.object(
        resources, "download_resource", side_effect=download_resource_side_effect
    )


@pytest.mark.parametrize(
    "url", ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"]
)
def test_get_cube_image_retrieves_image_if_not_local(mocker, url, setup, fs):
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
    "url", ["https://localhost:8000/image.sif", "https://test.com/docker_image.tar.gz"]
)
def test_get_cube_image_uses_cache_if_available(mocker, url, fs):
    # Arrange
    spy = mocker.patch.object(resources, "get_cube_file", return_value=("", ""))
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
