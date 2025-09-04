from __future__ import annotations
from medperf.exceptions import CleanExit
import pytest
from unittest.mock import call
from pytest_mock import MockerFixture
from typing import TYPE_CHECKING, List
from medperf.entities.cube import Cube
from medperf.entities.ca import CA
from medperf.commands.mlcube.associate import AssociateCubeWithCAs
from pathlib import Path
from medperf import config

if TYPE_CHECKING:
    from medperf.comms.rest import REST
    from medperf.ui.interface import UI
    from pyfakefs.fake_filesystem import FakeFilesystem

PATCH_ASSOC = "medperf.commands.mlcube.associate.{}"
ORIGINAL_KEY_NAME = 'key.bin'


@pytest.fixture
def cube(mocker: MockerFixture, cube_uid: int) -> Cube:
    cube = mocker.create_autospec(spec=Cube)
    mocker.patch.object(Cube, "get", return_value=cube)
    cube.name = "TestCube"
    cube.id = cube_uid
    cube.trusted_cas = []
    # cube.trusted_cas = [ca.id for ca in ca_list]
    return cube


@pytest.fixture
def ca_list(mocker: MockerFixture, ca_uids: int) -> List[CA]:
    cas = []
    for i, ca_uid in enumerate(ca_uids):
        ca = mocker.create_autospec(spec=CA)
        ca.name = f"TestCA{i+1}"
        ca.id = ca_uid
        cas.append(ca)

    mocker.patch.object(CA, "get_many", return_value=cas)
    return cas


@pytest.fixture
def decryption_key_path(mocker: MockerFixture, fs: FakeFilesystem) -> Path:
    path_to_key = Path('/path/to') / ORIGINAL_KEY_NAME
    fs.create_file(path_to_key, contents='not_a_real_key')
    return path_to_key


@pytest.fixture
def key_destination_path(fs: FakeFilesystem) -> Path:
    fake_destination_path = Path('/path/to/key/dest')
    fs.create_dir(fake_destination_path)
    return fake_destination_path


@pytest.mark.parametrize("cube_uid", [2405, 4186])
@pytest.mark.parametrize("ca_uids", [[4416, 5518], [1522]])
def test_run_associates_cube_with_comms(
    mocker: MockerFixture,
    cube: Cube,
    ca_list: CA,
    cube_uid: int,
    ca_uids: List[int],
    comms: REST,
    ui: UI,
    decryption_key_path: Path,
    key_destination_path: Path,
    fs: FakeFilesystem
):
    # Arrange
    spy = mocker.patch.object(comms, "update_mlcube")
    mocker.patch.object(ui, "prompt", return_value="y")
    spy_destination_key = mocker.patch('medperf.utils.get_container_key_dir_path', return_value=key_destination_path)
    key_file_dest_path = key_destination_path / config.container_key_file
    updated_body = {'trusted_cas': sorted(ca_uids)}
    expected_calls = [call(container_id=cube_uid, ca_name=ca.name) for ca in ca_list]

    # Act
    AssociateCubeWithCAs.run(cube_uid=cube_uid, ca_uids=ca_uids, decryption_key_path=decryption_key_path)

    # Assert
    spy.assert_called_once_with(mlcube_id=cube_uid, mlcube_updated_body=updated_body)
    spy_destination_key.assert_has_calls(expected_calls)
    assert fs.exists(key_file_dest_path)


@pytest.mark.parametrize("cube_uid", [2405, 4186])
@pytest.mark.parametrize("ca_uids", [[4416, 5518], [1522]])
def test_fails_if_no_decryption_key_provided(
    mocker: MockerFixture,
    cube: Cube,
    ca_list: CA,
    cube_uid: int,
    ca_uids: int,
    comms: REST,
    ui: UI,
    key_destination_path: Path,
    fs: FakeFilesystem
):
    # Arrange
    spy = mocker.patch.object(comms, "associate_ca_model")
    mocker.patch.object(ui, "prompt", return_value="y")
    spy_destination_key = mocker.patch('medperf.utils.get_container_key_dir_path', return_value=key_destination_path)
    key_file_dest_path = key_destination_path / config.container_key_file

    # Act
    with pytest.raises(TypeError):
        AssociateCubeWithCAs.run(cube_uid=cube_uid, ca_uids=ca_uids)

    # Assert
    spy.assert_not_called()
    spy_destination_key.assert_not_called()
    assert not fs.exists(key_file_dest_path)


@pytest.mark.parametrize("cube_uid", [2405])
def test_stops_if_not_approved(
    mocker: MockerFixture,
    comms: REST,
    decryption_key_path: Path,
    cube: Cube,
    cube_uid: int
):
    # Arrange
    spy = mocker.patch(PATCH_ASSOC.format("approval_prompt"), return_value=False)
    assoc_spy = mocker.patch.object(comms, 'associate_ca_model')

    # Act
    with pytest.raises(CleanExit):
        AssociateCubeWithCAs.run(cube_uid=cube_uid, ca_uids=[1], decryption_key_path=decryption_key_path)

    # Assert
    spy.assert_called_once()
    assoc_spy.assert_not_called()
