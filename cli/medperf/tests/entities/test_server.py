import medperf
from medperf.entities import Server
from medperf.enums import Role
from medperf.tests.mocks import MockResponse
from medperf.tests.utils import rand_l

import pytest
from unittest.mock import MagicMock, mock_open
import requests
import os

URL = "mock.url"
PATCH_SERVER = "medperf.entities.server.{}"


@pytest.mark.parametrize(
    "method_params",
    [
        ("benchmark_association", "get", 200, [1], [], (f"{URL}/me/benchmarks",), {}),
        ("get_benchmark", "get", 200, [1], {}, (f"{URL}/benchmarks/1",), {}),
        (
            "get_benchmark_models",
            "get",
            200,
            [1],
            [],
            (f"{URL}/benchmarks/1/models",),
            {},
        ),
        ("get_cube_metadata", "get", 200, [1], {}, (f"{URL}/mlcubes/1/",), {}),
        (
            "upload_dataset",
            "post",
            201,
            [{}],
            {"id": 1},
            (f"{URL}/datasets/",),
            {"json": {}},
        ),
        (
            "upload_results",
            "post",
            201,
            [{}],
            {"id": 1},
            (f"{URL}/results/",),
            {"json": {}},
        ),
        (
            "associate_dset_benchmark",
            "post",
            201,
            [1, 1],
            {},
            (f"{URL}/datasets/benchmarks/",),
            {"json": {"benchmark": 1, "dataset": 1}},
        ),
    ],
)
def test_methods_run_authorized_method(mocker, method_params):
    # Arrange
    server = Server(URL)
    method, type, status, args, body, out_args, kwargs = method_params
    res = MockResponse(body, status)
    if type == "get":
        patch_method = PATCH_SERVER.format("Server._Server__auth_get")
    else:
        patch_method = PATCH_SERVER.format("Server._Server__auth_post")
    spy = mocker.patch(patch_method, return_value=res)
    method = getattr(server, method)

    # Act
    method(*args)

    # Assert
    spy.assert_called_once_with(*out_args, **kwargs)


@pytest.mark.parametrize("status", [400, 401, 500, 502])
@pytest.mark.parametrize(
    "method_params",
    [
        ("benchmark_association", [1], []),
        ("get_benchmark", [1], {}),
        ("get_benchmark_models", [1], []),
        ("get_cube_metadata", [1], {}),
        ("_Server__get_cube_file", ["", 1, "", ""], {}),
        ("upload_dataset", [{}], {"id": 1}),
        ("upload_results", [{}], {"id": 1}),
        ("associate_dset_benchmark", [1, 1], {}),
    ],
)
def test_methods_exit_if_status_not_200(mocker, status, method_params):
    # Arrange
    server = Server(URL)
    method, args, body = method_params
    res = MockResponse(body, status)
    mocker.patch("requests.get", return_value=res)
    mocker.patch("requests.post", return_value=res)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_req"), return_value=res)
    spy = mocker.patch(PATCH_SERVER.format("pretty_error"))
    method = getattr(server, method)

    # Act
    method(*args)

    # Assert
    spy.assert_called()


@pytest.mark.parametrize("uname", ["test", "admin", "user"])
@pytest.mark.parametrize("pwd", ["test", "admin", "123456"])
def test_login_with_user_and_pwd(mocker, uname, pwd):
    # Arrange
    server = Server(URL)
    res = MockResponse({"token": ""}, 200)
    spy = mocker.patch("requests.post", return_value=res)
    exp_body = {"username": uname, "password": pwd}
    exp_path = f"{URL}/auth-token/"

    # Act
    server.login(uname, pwd)

    # Assert
    spy.assert_called_once_with(exp_path, json=exp_body)


@pytest.mark.parametrize("token", ["test", "token"])
def test_login_stores_token(mocker, token):
    # Arrange
    server = Server(URL)
    res = MockResponse({"token": token}, 200)
    mocker.patch("requests.post", return_value=res)

    # Act
    server.login("testuser", "testpwd")

    # Assert
    assert server.token == token


def test_auth_get_calls_authorized_request(mocker):
    # Arrange
    server = Server(URL)
    mocker.patch("requests.get")
    spy = mocker.patch(PATCH_SERVER.format("Server._Server__auth_req"))

    # Act
    server._Server__auth_get(URL)

    # Assert
    spy.called_once_with(URL, requests.get)


def test_auth_post_calls_authorized_request(mocker):
    # Arrange
    server = Server(URL)
    mocker.patch("requests.post")
    spy = mocker.patch(PATCH_SERVER.format("Server._Server__auth_req"))

    # Act
    server._Server__auth_post(URL)

    # Assert
    spy.called_once_with(URL, requests.post)


def test_auth_req_fails_if_token_missing(mocker):
    # Arrange
    server = Server(URL)
    mocker.patch("requests.post")
    spy = mocker.patch(PATCH_SERVER.format("pretty_error"))

    # Act
    server._Server__auth_req(URL, requests.post)

    # Assert
    spy.assert_called()


@pytest.mark.parametrize("req_type", ["get", "post"])
@pytest.mark.parametrize("token", ["test", "token", "auth_token"])
def test_auth_get_adds_token_to_request(mocker, token, req_type):
    # Arrange
    server = Server(URL)
    server.token = token

    if req_type == "get":
        spy = mocker.patch("requests.get")
        func = requests.get
    else:
        spy = mocker.patch("requests.post")
        func = requests.post

    exp_headers = {"Authorization": f"Token {token}"}

    # Act
    server._Server__auth_req(URL, func)

    # Assert
    spy.assert_called_once_with(URL, headers=exp_headers)


@pytest.mark.parametrize("exp_role", ["BenchmarkOwner", "DataOwner", "ModelOwner"])
def test_benchmark_association_returns_expected_role(mocker, exp_role):
    # Arrange
    server = Server(URL)
    benchmarks = [
        {"benchmark": 1, "role": exp_role},
        {"benchmark": 2, "role": "DataOwner"},
    ]
    res = MockResponse(benchmarks, 200)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_get"), return_value=res)

    # Act
    role = server.benchmark_association(1)

    # Assert
    assert role == Role(exp_role)


def test_benchmark_association_returns_none_if_not_found(mocker):
    # Arrange
    server = Server(URL)
    res = MockResponse([], 200)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_get"), return_value=res)

    # Act
    role = server.benchmark_association(1)

    # Assert
    assert role is Role(None)


@pytest.mark.parametrize("benchmark_uid", rand_l(1, 500, 5))
def test_authorized_by_role_calls_benchmark_association(mocker, benchmark_uid):
    # Arrange
    server = Server(URL)
    spy = mocker.patch(
        PATCH_SERVER.format("Server.benchmark_association"), return_value=Role(None)
    )

    # Act
    server.authorized_by_role(benchmark_uid, "ModelOwner")

    # Assert
    spy.assert_called_once_with(benchmark_uid)


@pytest.mark.parametrize("exp_role", ["BENCHMARK_OWNER", "DATA_OWNER", "MODEL_OWNER"])
@pytest.mark.parametrize("role", ["BenchmarkOwner", "DataOwner", "ModelOwner"])
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 500, 1))
def test_authorized_by_role_returns_true_when_authorized(
    mocker, role, exp_role, benchmark_uid
):
    # Arrange
    server = Server(URL)
    benchmarks = [
        {"benchmark": benchmark_uid, "role": role},
        {"benchmark": 501, "role": "DataOwner"},
    ]
    res = MockResponse(benchmarks, 200)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_get"), return_value=res)

    # Act
    authorized = server.authorized_by_role(benchmark_uid, exp_role)

    # Assert
    assert authorized == (Role(role).name == exp_role)


@pytest.mark.parametrize("body", [{"benchmark": 1}, {}, {"test": "test"}])
def test_get_benchmark_returns_benchmark_body(mocker, body):
    # Arrange
    server = Server(URL)
    res = MockResponse(body, 200)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_get"), return_value=res)

    # Act
    benchmark_body = server.get_benchmark(1)

    # Assert
    assert benchmark_body == body


@pytest.mark.parametrize("exp_uids", [rand_l(1, 500, 5) for _ in range(5)])
def test_get_benchmark_models_return_uids(mocker, exp_uids):
    # Arrange
    server = Server(URL)
    body = [{"id": uid} for uid in exp_uids]
    res = MockResponse(body, 200)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_get"), return_value=res)

    # Act
    uids = server.get_benchmark_models(1)

    # Assert
    assert set(uids) == set(exp_uids)


@pytest.mark.parametrize("exp_body", [{"test": "test"}, {}, {"cube": "body"}])
def test_get_cube_metadata_returns_retrieved_body(mocker, exp_body):
    # Arrange
    server = Server(URL)
    res = MockResponse(exp_body, 200)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_get"), return_value=res)

    # Act
    body = server.get_cube_metadata(1)

    # Assert
    assert body == exp_body


@pytest.mark.parametrize(
    "method", ["get_cube", "get_cube_params", "get_cube_additional"]
)
def test_get_cube_methods_run_get_cube_file(mocker, method):
    # Arrange
    server = Server(URL)
    spy = mocker.patch(
        PATCH_SERVER.format("Server._Server__get_cube_file"), return_value=""
    )
    method = getattr(server, method)

    # Act
    method(URL, 1)

    # Assert
    spy.assert_called_once()


def test_get_cube_file_writes_to_file(mocker):
    # Arrange
    server = Server(URL)
    cube_uid = 1
    path = "path"
    filename = "filename"
    res = MockResponse({}, 200)
    mocker.patch("requests.get", return_value=res)
    mocker.patch(PATCH_SERVER.format("cube_path"), return_value="")
    mocker.patch("os.path.isdir", return_value=True)
    filepath = os.path.join(path, filename)
    spy = mocker.patch("builtins.open", mock_open())

    # Act
    server._Server__get_cube_file(URL, cube_uid, path, filename)

    # Assert
    spy.assert_called_once_with(filepath, "wb+")


@pytest.mark.parametrize("exp_id", rand_l(1, 500, 5))
def test_upload_dataset_returns_dataset_uid(mocker, exp_id):
    # Arrange
    server = Server(URL)
    body = {"id": exp_id}
    res = MockResponse(body, 201)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_post"), return_value=res)

    # Act
    id = server.upload_dataset({})

    # Assert
    assert id == exp_id


@pytest.mark.parametrize("exp_id", rand_l(1, 500, 5))
def test_upload_results_returns_result_uid(mocker, exp_id):
    server = Server(URL)
    body = {"id": exp_id}
    res = MockResponse(body, 201)
    mocker.patch(PATCH_SERVER.format("Server._Server__auth_post"), return_value=res)

    # Act
    id = server.upload_results({})

    # Assert
    assert id == exp_id
