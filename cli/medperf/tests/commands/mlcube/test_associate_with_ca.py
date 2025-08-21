from __future__ import annotations
from medperf.exceptions import CleanExit
import pytest
from pytest_mock import MockerFixture
from typing import TYPE_CHECKING
from medperf.entities.cube import Cube
from medperf.entities.ca import CA
from medperf.commands.mlcube.associate import AssociateCubeWithCA
from pathlib import Path
from medperf import config

if TYPE_CHECKING:
    from medperf.comms.rest import REST
    from medperf.ui.interface import UI


PATCH_ASSOC = "medperf.commands.mlcube.associate.{}"
ORIGINAL_KEY_NAME = 'key.bin'


@pytest.fixture
def cube(mocker: MockerFixture):
    cube = mocker.create_autospec(spec=Cube)
    mocker.patch.object(Cube, "get", return_value=cube)
    cube.name = "name"
    return cube


@pytest.fixture
def ca(mocker: MockerFixture):
    ca = mocker.create_autospec(spec=CA)
    mocker.patch.object(CA, "get", return_value=ca)
    ca.name = "TestCA"
    return ca


@pytest.fixture
def decryption_key_path(mocker: MockerFixture, fs) -> Path:
    path_to_key = Path('/path/to') / ORIGINAL_KEY_NAME
    fs.create_file(path_to_key, contents='not_a_real_key')
    return path_to_key


@pytest.fixture
def key_destination_path(fs) -> Path:
    fake_destination_path = Path('/path/to/key/dest')
    fs.create_dir(fake_destination_path)
    return fake_destination_path


@pytest.mark.parametrize("cube_uid", [2405, 4186])
@pytest.mark.parametrize("ca_uid", [4416, 1522])
def test_run_associates_cube_with_comms(
    mocker: MockerFixture,
    cube: Cube,
    ca: CA,
    cube_uid: int,
    ca_uid: int,
    comms: REST,
    ui: UI,
    decryption_key_path: Path,
    key_destination_path: Path,
    fs
):
    # Arrange
    spy = mocker.patch.object(comms, "associate_ca_model")
    mocker.patch.object(ui, "prompt", return_value="y")
    spy_destination_key = mocker.patch(PATCH_ASSOC.format('get_container_key_dir_path'), return_value=key_destination_path)
    key_file_dest_path = key_destination_path / config.container_key_file
    cube.id = cube_uid
    ca.id = ca_uid

    # Act
    AssociateCubeWithCA.run(cube_uid, ca_uid, decryption_key_path=decryption_key_path)

    # Assert
    spy.assert_called_once_with(cube_uid, ca_uid)
    spy_destination_key.assert_called_once_with(ca_name=ca.name, container_id=cube_uid)
    assert fs.exists(key_file_dest_path)


@pytest.mark.parametrize("cube_uid", [2405, 4186])
@pytest.mark.parametrize("ca_uid", [4416, 1522])
def test_fails_if_no_decryption_key_provided(
    mocker: MockerFixture,
    cube: Cube,
    ca: CA,
    cube_uid: int,
    ca_uid: int,
    comms: REST,
    ui: UI,
    key_destination_path: Path,
    fs
):
    # Arrange
    spy = mocker.patch.object(comms, "associate_ca_model")
    mocker.patch.object(ui, "prompt", return_value="y")
    spy_destination_key = mocker.patch(PATCH_ASSOC.format('get_container_key_dir_path'), return_value=key_destination_path)
    key_file_dest_path = key_destination_path / config.container_key_file
    cube.id = cube_uid
    ca.id = ca_uid

    # Act
    with pytest.raises(TypeError):
        AssociateCubeWithCA.run(cube_uid, ca_uid)

    # Assert
    spy.assert_not_called()
    spy_destination_key.assert_not_called()
    assert not fs.exists(key_file_dest_path)


def test_stops_if_not_approved(
    mocker: MockerFixture,
    comms: REST,
    decryption_key_path: Path,
    cube: Cube,
    ca: CA,
    ui: UI,
):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, 'associate_ca_model')

    # Act
    with pytest.raises(CleanExit):
        AssociateCubeWithCA.run(1, 1, decryption_key_path=decryption_key_path)

    # Assert
    spy.assert_called_once()
    assoc_spy.assert_not_called()
