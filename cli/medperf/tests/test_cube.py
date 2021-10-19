from unittest import mock

from medperf.entities import Cube, Server
from medperf.config import config
from medperf.tests.mocks import requests as mock_requests
import medperf


cube_uid = 1


def mocked_get_responses(*args, **kwargs):
    base_url = f"{config['server']}/mlcubes"
    if args[0] == f"{base_url}/{cube_uid}/":
        body = mock_requests.cube_body(cube_uid)
        res = mock_requests.MockResponse(body, 200)
        return res
    elif args[0] in ["mlcube_url", "parameters_url", "tarball_url"]:
        return mock_requests.MockResponse({}, 200)


def test_get(mocker):
    """Can retrieve cubes from the server, and all get calls are authenticated
    """
    server = Server(config["server"])
    server.token = "123"

    mocker.patch("os.makedirs")
    mocker.patch("builtins.open")
    mocker.patch(
        "medperf.entities.server.requests.get", side_effect=mocked_get_responses
    )
    mocker.patch("medperf.entities.cube.get_file_sha1", return_value="tarball_hash")
    mocker.patch("medperf.entities.cube.untar_additional")
    get_spy = mocker.spy(medperf.entities.server.requests, "get")
    auth_spy = mocker.spy(Server, "_Server__auth_req")
    cube = Cube.get(cube_uid, server)
    assert type(cube) is Cube and cube.uid == cube_uid
    assert get_spy.call_count == 4
    assert auth_spy.call_count == 1

