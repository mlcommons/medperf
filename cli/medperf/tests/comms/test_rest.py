import os
import pytest
import requests
from unittest.mock import mock_open, ANY

from medperf.ui.interface import UI
from medperf.enums import Role
from medperf.comms.rest import REST
from medperf.tests.utils import rand_l
from medperf.tests.mocks import MockResponse

url = "mock.url"
patch_server = "medperf.comms.rest.{}"


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.fixture
def server(mocker, ui):
    server = REST(url, ui)
    return server


@pytest.mark.parametrize(
    "method_params",
    [
        (
            "benchmark_association",
            "get",
            200,
            [1],
            [],
            (f"https://{url}/me/benchmarks",),
            {},
        ),
        ("get_benchmark", "get", 200, [1], {}, (f"https://{url}/benchmarks/1",), {}),
        (
            "get_benchmark_models",
            "get",
            200,
            [1],
            [],
            (f"https://{url}/benchmarks/1/models",),
            {},
        ),
        ("get_cube_metadata", "get", 200, [1], {}, (f"https://{url}/mlcubes/1/",), {}),
        (
            "upload_dataset",
            "post",
            201,
            [{}],
            {"id": 1},
            (f"https://{url}/datasets/",),
            {"json": {}},
        ),
        (
            "upload_results",
            "post",
            201,
            [{}],
            {"id": 1},
            (f"https://{url}/results/",),
            {"json": {}},
        ),
        (
            "associate_dset",
            "post",
            201,
            [1, 1],
            {},
            (f"https://{url}/datasets/benchmarks/",),
            {
                "json": {
                    "benchmark": 1,
                    "dataset": 1,
                    "approval_status": "PENDING",
                    "metadata": {},
                }
            },
        ),
        (
            "_REST__set_approval_status",
            "put",
            200,
            [f"https://{url}/mlcubes/1/benchmarks/1", "APPROVED"],
            {},
            (f"https://{url}/mlcubes/1/benchmarks/1",),
            {"json": {"approval_status": "APPROVED"}},
        ),
        (
            "_REST__set_approval_status",
            "put",
            200,
            [f"https://{url}/mlcubes/1/benchmarks/1", "REJECTED"],
            {},
            (f"https://{url}/mlcubes/1/benchmarks/1",),
            {"json": {"approval_status": "REJECTED"}},
        ),
    ],
)
def test_methods_run_authorized_method(mocker, server, method_params):
    # Arrange
    method, type, status, args, body, out_args, kwargs = method_params
    res = MockResponse(body, status)
    if type == "get":
        patch_method = patch_server.format("REST._REST__auth_get")
    elif type == "put":
        patch_method = patch_server.format("REST._REST__auth_put")
    else:
        patch_method = patch_server.format("REST._REST__auth_post")
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
        ("_REST__get_cube_file", ["", 1, "", ""], {}),
        ("upload_dataset", [{}], {"id": 1}),
        ("upload_results", [{}], {"id": 1}),
        ("associate_dset", [1, 1], {}),
    ],
)
def test_methods_exit_if_status_not_200(mocker, server, status, method_params):
    # Arrange
    method, args, body = method_params
    res = MockResponse(body, status)
    mocker.patch("requests.get", return_value=res)
    mocker.patch("requests.post", return_value=res)
    mocker.patch(patch_server.format("REST._REST__auth_req"), return_value=res)
    spy = mocker.patch(patch_server.format("pretty_error"))
    method = getattr(server, method)

    # Act
    method(*args)

    # Assert
    spy.assert_called()


@pytest.mark.parametrize("uname", ["test", "admin", "user"])
@pytest.mark.parametrize("pwd", ["test", "admin", "123456"])
def test_login_with_user_and_pwd(mocker, server, ui, uname, pwd):
    # Arrange
    res = MockResponse({"token": ""}, 200)
    spy = mocker.patch("requests.post", return_value=res)
    exp_body = {"username": uname, "password": pwd}
    exp_path = f"https://{url}/auth-token/"

    # Act
    server.login(ui, uname, pwd)

    # Assert
    spy.assert_called_once_with(exp_path, json=exp_body, verify=True)


@pytest.mark.parametrize("token", ["test", "token"])
def test_login_stores_token(mocker, ui, server, token):
    # Arrange
    res = MockResponse({"token": token}, 200)
    mocker.patch("requests.post", return_value=res)

    # Act
    server.login(ui, "testuser", "testpwd")

    # Assert
    assert server.token == token


def test_auth_get_calls_authorized_request(mocker, server):
    # Arrange
    mocker.patch("requests.get")
    spy = mocker.patch(patch_server.format("REST._REST__auth_req"))

    # Act
    server._REST__auth_get(url)

    # Assert
    spy.called_once_with(url, requests.get)


def test_auth_post_calls_authorized_request(mocker, server):
    # Arrange
    mocker.patch("requests.post")
    spy = mocker.patch(patch_server.format("REST._REST__auth_req"))

    # Act
    server._REST__auth_post(url)

    # Assert
    spy.called_once_with(url, requests.post)


def test_auth_req_authenticates_if_token_missing(mocker, server):
    # Arrange
    mocker.patch("requests.post")
    spy = mocker.patch(patch_server.format("REST.authenticate"))

    # Act
    server._REST__auth_req(url, requests.post)

    # Assert
    spy.assert_called()


@pytest.mark.parametrize("req_type", ["get", "post"])
@pytest.mark.parametrize("token", ["test", "token", "auth_token"])
def test_auth_get_adds_token_to_request(mocker, server, token, req_type):
    # Arrange
    server.token = token

    if req_type == "get":
        spy = mocker.patch("requests.get")
        func = requests.get
    else:
        spy = mocker.patch("requests.post")
        func = requests.post

    exp_headers = {"Authorization": f"Token {token}"}

    # Act
    server._REST__auth_req(url, func)

    # Assert
    spy.assert_called_once_with(url, headers=exp_headers, verify=True)


@pytest.mark.parametrize("exp_role", ["BenchmarkOwner", "DataOwner", "ModelOwner"])
def test_benchmark_association_returns_expected_role(mocker, server, exp_role):
    # Arrange
    benchmarks = [
        {"benchmark": 1, "role": exp_role},
        {"benchmark": 2, "role": "DataOwner"},
    ]
    res = MockResponse(benchmarks, 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    role = server.benchmark_association(1)

    # Assert
    assert role == Role(exp_role)


def test_benchmark_association_returns_none_if_not_found(mocker, server):
    # Arrange
    res = MockResponse([], 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    role = server.benchmark_association(1)

    # Assert
    assert role is Role(None)


@pytest.mark.parametrize("benchmark_uid", rand_l(1, 500, 5))
def test_authorized_by_role_calls_benchmark_association(mocker, server, benchmark_uid):
    # Arrange
    spy = mocker.patch(
        patch_server.format("REST.benchmark_association"), return_value=Role(None)
    )

    # Act
    server.authorized_by_role(benchmark_uid, "ModelOwner")

    # Assert
    spy.assert_called_once_with(benchmark_uid)


@pytest.mark.parametrize("exp_role", ["BENCHMARK_OWNER", "DATA_OWNER", "MODEL_OWNER"])
@pytest.mark.parametrize("role", ["BenchmarkOwner", "DataOwner", "ModelOwner"])
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 500, 1))
def test_authorized_by_role_returns_true_when_authorized(
    mocker, server, role, exp_role, benchmark_uid
):
    # Arrange
    benchmarks = [
        {"benchmark": benchmark_uid, "role": role},
        {"benchmark": 501, "role": "DataOwner"},
    ]
    res = MockResponse(benchmarks, 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    authorized = server.authorized_by_role(benchmark_uid, exp_role)

    # Assert
    assert authorized == (Role(role).name == exp_role)


@pytest.mark.parametrize("body", [{"benchmark": 1}, {}, {"test": "test"}])
def test_get_benchmarks_calls_benchmarks_path(mocker, server, body):
    # Arrange
    res = MockResponse([body], 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    bmarks = server.get_benchmarks()

    # Assert
    spy.assert_called_once_with(f"https://{url}/benchmarks/")
    assert bmarks == [body]


@pytest.mark.parametrize("body", [{"benchmark": 1}, {}, {"test": "test"}])
def test_get_benchmark_returns_benchmark_body(mocker, server, body):
    # Arrange
    res = MockResponse(body, 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    benchmark_body = server.get_benchmark(1)

    # Assert
    assert benchmark_body == body


@pytest.mark.parametrize("exp_uids", [rand_l(1, 500, 5) for _ in range(5)])
def test_get_benchmark_models_return_uids(mocker, server, exp_uids):
    # Arrange
    body = [{"id": uid} for uid in exp_uids]
    res = MockResponse(body, 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    uids = server.get_benchmark_models(1)

    # Assert
    assert set(uids) == set(exp_uids)


def test_get_user_benchmarks_calls_auth_get_for_expected_path(mocker, server):
    # Arrange
    benchmarks = [
        {"id": 1, "name": "benchmark1", "description": "desc", "state": "DEVELOPMENT"},
        {"id": 2, "name": "benchmark2", "description": "desc", "state": "OPERATION"},
    ]
    res = MockResponse(benchmarks, 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    server.get_user_benchmarks()

    # Assert
    spy.assert_called_once_with(f"https://{url}/me/benchmarks/")


def test_get_user_benchmarks_returns_benchmarks(mocker, server):
    # Arrange
    benchmarks = [
        {"id": 1, "name": "benchmark1", "description": "desc", "state": "DEVELOPMENT"},
        {"id": 2, "name": "benchmark2", "description": "desc", "state": "OPERATION"},
    ]
    res = MockResponse(benchmarks, 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    retrieved_benchmarks = server.get_user_benchmarks()

    # Assert
    assert benchmarks == retrieved_benchmarks


@pytest.mark.parametrize("body", [{"mlcube": 1}, {}, {"test": "test"}])
def test_get_mlcubes_calls_mlcubes_path(mocker, server, body):
    # Arrange
    res = MockResponse([body], 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    cubes = server.get_cubes()

    # Assert
    spy.assert_called_once_with(f"https://{url}/mlcubes/")
    assert cubes == [body]


@pytest.mark.parametrize("exp_body", [{"test": "test"}, {}, {"cube": "body"}])
def test_get_cube_metadata_returns_retrieved_body(mocker, server, exp_body):
    # Arrange
    res = MockResponse(exp_body, 200)
    mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    body = server.get_cube_metadata(1)

    # Assert
    assert body == exp_body


@pytest.mark.parametrize(
    "method", ["get_cube", "get_cube_params", "get_cube_additional"]
)
def test_get_cube_methods_run_get_cube_file(mocker, server, method):
    # Arrange
    spy = mocker.patch(
        patch_server.format("REST._REST__get_cube_file"), return_value=""
    )
    method = getattr(server, method)

    # Act
    method(url, 1)

    # Assert
    spy.assert_called_once()


def test_get_user_cubes_calls_auth_get_for_expected_path(mocker, server):
    # Arrange
    cubes = [
        {"id": 1, "name": "name1", "state": "OPERATION"},
        {"id": 2, "name": "name2", "state": "DEVELOPMENT"},
    ]
    res = MockResponse(cubes, 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    server.get_user_cubes()

    # Assert
    spy.assert_called_once_with(f"https://{url}/me/mlcubes/")


def test_get_cube_file_writes_to_file(mocker, server):
    # Arrange
    cube_uid = 1
    path = "path"
    filename = "filename"
    res = MockResponse({}, 200)
    mocker.patch("requests.get", return_value=res)
    mocker.patch(patch_server.format("cube_path"), return_value="")
    mocker.patch("os.path.isdir", return_value=True)
    filepath = os.path.join(path, filename)
    spy = mocker.patch("builtins.open", mock_open())

    # Act
    server._REST__get_cube_file(url, cube_uid, path, filename)

    # Assert
    spy.assert_called_once_with(filepath, "wb+")


@pytest.mark.parametrize("body", [{"mlcube": 1}, {}, {"test": "test"}])
def test_get_datasets_calls_datasets_path(mocker, server, body):
    # Arrange
    res = MockResponse([body], 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    cubes = server.get_datasets()

    # Assert
    spy.assert_called_once_with(f"https://{url}/datasets/")
    assert cubes == [body]


def test_get_user_datasets_calls_auth_get_for_expected_path(mocker, server):
    # Arrange
    cubes = [
        {"id": 1, "name": "name1", "state": "OPERATION"},
        {"id": 2, "name": "name2", "state": "DEVELOPMENT"},
    ]
    res = MockResponse(cubes, 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    server.get_user_datasets()

    # Assert
    spy.assert_called_once_with(f"https://{url}/me/datasets/")


@pytest.mark.parametrize("exp_id", rand_l(1, 500, 5))
def test_upload_mlcube_returns_cube_uid(mocker, server, exp_id):
    # Arrange
    body = {"id": exp_id}
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    id = server.upload_mlcube({})

    # Assert
    assert id == exp_id


@pytest.mark.parametrize("exp_id", rand_l(1, 500, 5))
def test_upload_dataset_returns_dataset_uid(mocker, server, exp_id):
    # Arrange
    body = {"id": exp_id}
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    id = server.upload_dataset({})

    # Assert
    assert id == exp_id


@pytest.mark.parametrize("exp_id", rand_l(1, 500, 5))
def test_upload_results_returns_result_uid(mocker, server, exp_id):
    # Arrange
    body = {"id": exp_id}
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    id = server.upload_results({})

    # Assert
    assert id == exp_id


@pytest.mark.parametrize("cube_uid", rand_l(1, 5000, 5))
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 5))
def test_associate_cube_posts_association_data(mocker, server, cube_uid, benchmark_uid):
    # Arrange
    data = {
        "results": {},
        "approval_status": "PENDING",
        "model_mlcube": cube_uid,
        "benchmark": benchmark_uid,
        "metadata": {},
    }
    res = MockResponse({}, 201)
    spy = mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    server.associate_cube(cube_uid, benchmark_uid)

    # Assert
    spy.assert_called_once_with(ANY, json=data)


@pytest.mark.parametrize("dataset_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("status", ["APPROVED", "REJECTED"])
def test_set_dataset_association_approval_sets_approval(
    mocker, server, dataset_uid, benchmark_uid, status
):
    # Arrange
    res = MockResponse({}, 200)
    spy = mocker.patch(
        patch_server.format("REST._REST__set_approval_status"), return_value=res
    )
    exp_url = f"https://{url}/datasets/{dataset_uid}/benchmarks/{benchmark_uid}/"

    # Act
    server.set_dataset_association_approval(dataset_uid, benchmark_uid, status)

    # Assert
    spy.assert_called_once_with(exp_url, status)


@pytest.mark.parametrize("mlcube_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("benchmark_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("status", ["APPROVED", "REJECTED"])
def test_set_mlcube_association_approval_sets_approval(
    mocker, server, mlcube_uid, benchmark_uid, status
):
    # Arrange
    res = MockResponse({}, 200)
    spy = mocker.patch(
        patch_server.format("REST._REST__set_approval_status"), return_value=res
    )
    exp_url = f"https://{url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"

    # Act
    server.set_mlcube_association_approval(mlcube_uid, benchmark_uid, status)

    # Assert
    spy.assert_called_once_with(exp_url, status)


def test_get_datasets_associations_gets_associations(mocker, server):
    # Arrange
    res = MockResponse([], 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)
    exp_path = f"https://{url}/me/datasets/associations/"

    # Act
    server.get_datasets_associations()

    # Assert
    spy.assert_called_once_with(exp_path)


def test_get_cubes_associations_gets_associations(mocker, server):
    # Arrange
    res = MockResponse([], 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)
    exp_path = f"https://{url}/me/mlcubes/associations/"

    # Act
    server.get_cubes_associations()

    # Assert
    spy.assert_called_once_with(exp_path)
