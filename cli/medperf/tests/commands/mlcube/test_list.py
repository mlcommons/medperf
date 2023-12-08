from typing import Any

import pytest

from medperf.entities.cube import Cube
from medperf.commands.list import EntityList

PATCH_CUBE = "medperf.entities.cube.Cube.{}"


def generate_cube(id: int, is_valid: bool, owner: int) -> dict[str, Any]:
    git_mlcube_url = f"{id}-{is_valid}-{owner}"
    name = git_mlcube_url
    return {
        'id': id,
        'is_valid': is_valid,
        'owner': owner,
        'git_mlcube_url': git_mlcube_url,
        'name': name
    }


def cls_local_cubes(*args, **kwargs) -> list[Cube]:
    return [
        Cube(**generate_cube(id=101, is_valid=True, owner=1)),
        Cube(**generate_cube(id=102, is_valid=False, owner=1)),
        # Intended: for local mlcubes owner is never checked.
        # All local cubes are supposed to be owned by current user

        # generate_cube(id=103, is_valid=True, owner=12345),
        # generate_cube(id=104, is_valid=False, owner=12345),
    ]


def comms_remote_cubes_dict_mine_only() -> list[dict[str, Any]]:
    return [
        generate_cube(id=201, is_valid=True, owner=1),
        generate_cube(id=202, is_valid=False, owner=1),
    ]


def comms_remote_cubes_dict() -> list[dict[str, Any]]:
    mine_only = comms_remote_cubes_dict_mine_only()
    someone_else = [
        generate_cube(id=203, is_valid=True, owner=12345),
        generate_cube(id=204, is_valid=False, owner=12345),
    ]
    return mine_only + someone_else


def cls_remote_cubes(*args, **kwargs) -> list[Cube]:
    return [Cube(**d) for d in comms_remote_cubes_dict()]


@pytest.mark.parametrize("local_only", [False, True])
@pytest.mark.parametrize("mine_only", [False, True])
@pytest.mark.parametrize("valid_only", [False, True])
def test_run_list_mlcubes(mocker, comms, ui, local_only, mine_only, valid_only):
    # Arrange
    mocker.patch("medperf.commands.list.get_medperf_user_data", return_value={"id": 1})
    mocker.patch("medperf.entities.cube.get_medperf_user_data", return_value={"id": 1})

    # Implementation-specific: for local cubes there is a private classmethod.
    mocker.patch(PATCH_CUBE.format("_Cube__local_all"), new=cls_local_cubes)
    # For remote cubes there are two different endpoints - for all cubes and for mine only
    mocker.patch.object(comms, 'get_user_cubes', new=comms_remote_cubes_dict_mine_only)
    mocker.patch.object(comms, 'get_cubes', new=comms_remote_cubes_dict)

    tab_spy = mocker.patch("medperf.commands.list.tabulate", return_value="")

    local_cubes = cls_local_cubes()
    remote_cubes = cls_remote_cubes()
    cubes = local_cubes + remote_cubes

    # Act
    EntityList.run(Cube, fields=['UID'], local_only=local_only, mine_only=mine_only, valid_only=valid_only)

    # Assert
    tab_call = tab_spy.call_args_list[0]
    received_cubes: list[list[Any]] = tab_call[0][0]
    received_ids = {cube_fields[0] for cube_fields in received_cubes}

    local_ids = {c.id for c in local_cubes}

    expected_ids = set()
    for c in cubes:
        if local_only:
            if c.id not in local_ids:
                continue

        if mine_only:
            if c.owner != 1:
                continue

        if valid_only:
            if not c.is_valid:
                continue

        expected_ids.add(c.id)

    assert received_ids == expected_ids
