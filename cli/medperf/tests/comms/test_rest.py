from medperf.exceptions import CommunicationRequestError, CommunicationRetrievalError
import pytest
import requests
from unittest.mock import ANY, call

from medperf import config
from medperf.enums import Status
from medperf.comms.rest import REST
from medperf.tests.mocks import MockResponse

url = "https://mock.url"
full_url = REST.parse_url(url)
patch_server = "medperf.comms.rest.{}"


@pytest.fixture
def server(mocker, ui):
    server = REST(url)
    return server


@pytest.mark.parametrize(
    "method_params",
    [
        ("get_benchmark", "get", 200, [1], {}, (f"{full_url}/benchmarks/1",), {}),
        (
            "get_benchmark_models",
            "get_list",
            200,
            [1],
            [],
            (f"{full_url}/benchmarks/1/models",),
            {},
        ),
        ("get_cube_metadata", "get", 200, [1], {}, (f"{full_url}/mlcubes/1/",), {}),
        (
            "upload_dataset",
            "post",
            201,
            [{}],
            {"id": 1},
            (f"{full_url}/datasets/",),
            {"json": {}},
        ),
        (
            "upload_result",
            "post",
            201,
            [{}],
            {"id": 1},
            (f"{full_url}/results/",),
            {"json": {}},
        ),
        (
            "associate_dset",
            "post",
            201,
            [1, 1],
            {},
            (f"{full_url}/datasets/benchmarks/",),
            {
                "json": {
                    "benchmark": 1,
                    "dataset": 1,
                    "approval_status": Status.PENDING.value,
                    "metadata": {},
                }
            },
        ),
        (
            "_REST__set_approval_status",
            "put",
            200,
            [f"{full_url}/mlcubes/1/benchmarks/1", Status.APPROVED.value],
            {},
            (f"{full_url}/mlcubes/1/benchmarks/1",),
            {"json": {"approval_status": Status.APPROVED.value}},
        ),
        (
            "_REST__set_approval_status",
            "put",
            200,
            [f"{full_url}/mlcubes/1/benchmarks/1", Status.REJECTED.value],
            {},
            (f"{full_url}/mlcubes/1/benchmarks/1",),
            {"json": {"approval_status": Status.REJECTED.value}},
        ),
    ],
)
def test_methods_run_authorized_method(mocker, server, method_params):
    # Arrange
    method, type, status, args, body, out_args, kwargs = method_params
    res = MockResponse(body, status)
    if type == "get_list":
        patch_method = patch_server.format("REST._REST__get_list")
        return_value = body
    else:
        patch_method = patch_server.format(f"REST._REST__auth_{type}")
        return_value = res
    spy = mocker.patch(patch_method, return_value=return_value)
    method = getattr(server, method)

    # Act
    method(*args)

    # Assert
    spy.assert_called_once_with(*out_args, **kwargs)


@pytest.mark.parametrize("status", [400, 401, 500, 502])
@pytest.mark.parametrize(
    "method_params",
    [
        ("get_benchmark", [1], {}, CommunicationRetrievalError),
        ("get_cube_metadata", [1], {}, CommunicationRetrievalError),
        ("upload_dataset", [{}], {"id": 1}, CommunicationRequestError),
        ("upload_result", [{}], {"id": 1}, CommunicationRequestError),
        ("associate_dset", [1, 1], {}, CommunicationRequestError),
    ],
)
def test_methods_exit_if_status_not_200(mocker, server, status, method_params):
    # Arrange
    method, args, body, raised_exception = method_params
    res = MockResponse(body, status)
    mocker.patch("requests.get", return_value=res)
    mocker.patch("requests.post", return_value=res)
    mocker.patch(patch_server.format("REST._REST__auth_req"), return_value=res)
    mocker.patch(patch_server.format("format_errors_dict"))
    method = getattr(server, method)

    # Act & Assert
    with pytest.raises(raised_exception):
        method(*args)


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


@pytest.mark.parametrize("req_type", ["get", "post"])
@pytest.mark.parametrize("token", ["test", "token", "auth_token"])
def test_auth_get_adds_token_to_request(mocker, server, token, req_type, auth):
    # Arrange
    auth.access_token = token

    if req_type == "get":
        spy = mocker.patch("requests.get")
        func = requests.get
    else:
        spy = mocker.patch("requests.post")
        func = requests.post

    exp_headers = {"Authorization": f"Bearer {token}"}
    cert_verify = config.certificate or True

    # Act
    server._REST__auth_req(url, func)

    # Assert
    spy.assert_called_once_with(url, headers=exp_headers, verify=cert_verify)


def test__req_sanitizes_json(mocker, server):
    # Arrange
    body = {}
    spy = mocker.patch(patch_server.format("sanitize_json"))
    mocker.patch("requests.post")
    func = requests.post

    # Act
    server._REST__req(url, func, json=body)

    # Assert
    spy.assert_called_once_with(body)


def test__get_list_uses_default_page_size(mocker, server):
    # Arrange
    exp_page_size = config.default_page_size
    exp_url = f"{full_url}?limit={exp_page_size}&offset=0"
    ret_body = MockResponse({"count": 1, "next": None, "results": []}, 200)
    spy = mocker.patch.object(server, "_REST__auth_get", return_value=ret_body)

    # Act
    server._REST__get_list(full_url)

    # Assert
    spy.assert_called_once_with(exp_url)


@pytest.mark.parametrize("num_pages", [3, 5, 10])
def test__get_list_iterates_until_done(mocker, server, num_pages):
    # Arrange
    ret_body = MockResponse({"count": 1, "next": url, "results": ["element"]}, 200)
    ret_last = MockResponse({"count": 1, "next": None, "results": ["element"]}, 200)
    ret_bodies = [ret_body] * (num_pages - 1) + [ret_last]
    spy = mocker.patch.object(server, "_REST__auth_get", side_effect=ret_bodies)

    # Act
    server._REST__get_list(url)

    # Assert
    assert spy.call_count == num_pages


@pytest.mark.parametrize("num_elements", [23, 178, 299])
def test__get_list_returns_desired_number_of_elements(mocker, server, num_elements):
    # Arrange
    ret_body = MockResponse(
        {"count": 32, "next": url, "results": ["element"] * 32}, 200
    )
    ret_last = MockResponse({"count": 1, "next": None, "results": ["element"]}, 200)
    ret_bodies = [ret_body] * 500 + [ret_last]  # Default to a high number of pages
    mocker.patch.object(server, "_REST__auth_get", side_effect=ret_bodies)

    # Act
    elements = server._REST__get_list(url, num_elements=num_elements)

    # Assert
    assert len(elements) == num_elements


def test__get_list_splits_page_size_on_error(mocker, server):
    # Arrange
    failing_body = MockResponse({}, 500)
    reduced_body = MockResponse(
        {"count": 16, "next": url, "results": ["element"] * 16}, 200
    )
    next_body = MockResponse(
        {"count": 32, "next": None, "results": ["element"] * 32}, 200
    )
    ret_bodies = [failing_body, reduced_body, next_body]
    gen_url = url + "?limit={}&offset={}"
    exp_calls = [
        call(gen_url.format(32, 0)),
        call(gen_url.format(16, 0)),
        call(gen_url.format(16, 16)),
    ]
    spy = mocker.patch.object(server, "_REST__auth_get", side_effect=ret_bodies)

    # Act
    server._REST__get_list(url, binary_reduction=True)

    # Assert
    spy.assert_has_calls(exp_calls)


def test__get_list_fails_if_failing_element_encountered(mocker, server):
    # Arrange
    failing_body = MockResponse({}, 500)
    mocker.patch.object(server, "_REST__auth_get", return_value=failing_body)

    # Act & Assert
    with pytest.raises(CommunicationRetrievalError):
        server._REST__get_list(url, page_size=1)


@pytest.mark.parametrize("body", [{"benchmark": 1}, {}, {"test": "test"}])
def test_get_benchmarks_calls_benchmarks_path(mocker, server, body):
    # Arrange
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=[body])

    # Act
    bmarks = server.get_benchmarks()

    # Assert
    spy.assert_called_once_with(f"{full_url}/benchmarks/")
    assert bmarks == [body]


@pytest.mark.parametrize("exp_uids", [[142, 437, 196], [303, 27, 24], [40, 19, 399]])
def test_get_benchmark_models_return_uids(mocker, server, exp_uids):
    # Arrange
    body = [{"id": uid} for uid in exp_uids]
    mocker.patch(patch_server.format("REST._REST__get_list"), return_value=body)

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
    spy = mocker.patch(
        patch_server.format("REST._REST__get_list"), return_value=benchmarks
    )

    # Act
    server.get_user_benchmarks()

    # Assert
    spy.assert_called_once_with(f"{full_url}/me/benchmarks/")


def test_get_user_benchmarks_returns_benchmarks(mocker, server):
    # Arrange
    benchmarks = [
        {"id": 1, "name": "benchmark1", "description": "desc", "state": "DEVELOPMENT"},
        {"id": 2, "name": "benchmark2", "description": "desc", "state": "OPERATION"},
    ]
    mocker.patch(patch_server.format("REST._REST__get_list"), return_value=benchmarks)

    # Act
    retrieved_benchmarks = server.get_user_benchmarks()

    # Assert
    assert benchmarks == retrieved_benchmarks


@pytest.mark.parametrize("body", [{"mlcube": 1}, {}, {"test": "test"}])
def test_get_mlcubes_calls_mlcubes_path(mocker, server, body):
    # Arrange
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=[body])

    # Act
    cubes = server.get_cubes()

    # Assert
    spy.assert_called_once_with(f"{full_url}/mlcubes/")
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


def test_get_user_cubes_calls_auth_get_for_expected_path(mocker, server):
    # Arrange
    cubes = [
        {"id": 1, "name": "name1", "state": "OPERATION"},
        {"id": 2, "name": "name2", "state": "DEVELOPMENT"},
    ]
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=cubes)

    # Act
    server.get_user_cubes()

    # Assert
    spy.assert_called_once_with(f"{full_url}/me/mlcubes/")


@pytest.mark.parametrize("body", [{"dset": 1}, {}, {"test": "test"}])
def test_get_datasets_calls_datasets_path(mocker, server, body):
    # Arrange
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=[body])

    # Act
    dsets = server.get_datasets()

    # Assert
    spy.assert_called_once_with(f"{full_url}/datasets/")
    assert dsets == [body]


@pytest.mark.parametrize("uid", [475, 28, 293])
@pytest.mark.parametrize("body", [{"test": "test"}, {"body": "body"}])
def test_get_dataset_calls_specific_dataset_path(mocker, server, uid, body):
    # Arrange
    res = MockResponse(body, 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)

    # Act
    dset = server.get_dataset(uid)

    # Assert
    spy.assert_called_once_with(f"{full_url}/datasets/{uid}/")
    assert dset == body


def test_get_user_datasets_calls_auth_get_for_expected_path(mocker, server):
    # Arrange
    cubes = [
        {"id": 1, "name": "name1", "state": "OPERATION"},
        {"id": 2, "name": "name2", "state": "DEVELOPMENT"},
    ]
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=cubes)

    # Act
    server.get_user_datasets()

    # Assert
    spy.assert_called_once_with(f"{full_url}/me/datasets/")


@pytest.mark.parametrize("body", [{"mlcube": 1}, {}, {"test": "test"}])
def test_upload_mlcube_returns_cube_uid(mocker, server, body):
    # Arrange
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    exp_body = server.upload_dataset({})

    # Assert
    assert body == exp_body


@pytest.mark.parametrize("body", [{"dataset": 1}, {}, {"test": "test"}])
def test_upload_dataset_returns_dataset_body(mocker, server, body):
    # Arrange
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    exp_body = server.upload_dataset({})

    # Assert
    assert body == exp_body


@pytest.mark.parametrize("body", [{"result": 1}, {}, {"test": "test"}])
def test_upload_results_returns_result_body(mocker, server, body):
    # Arrange
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    exp_body = server.upload_result({})

    # Assert
    assert body == exp_body


@pytest.mark.parametrize("cube_uid", [2156, 915])
@pytest.mark.parametrize("benchmark_uid", [1206, 3741])
def test_associate_cube_posts_association_data(mocker, server, cube_uid, benchmark_uid):
    # Arrange
    data = {
        "approval_status": Status.PENDING.value,
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


@pytest.mark.parametrize("dataset_uid", [4417, 1057])
@pytest.mark.parametrize("benchmark_uid", [1011, 635])
@pytest.mark.parametrize("status", [Status.APPROVED.value, Status.REJECTED.value])
def test_set_dataset_association_approval_sets_approval(
    mocker, server, dataset_uid, benchmark_uid, status
):
    # Arrange
    res = MockResponse({}, 200)
    spy = mocker.patch(
        patch_server.format("REST._REST__set_approval_status"), return_value=res
    )
    exp_url = f"{full_url}/datasets/{dataset_uid}/benchmarks/{benchmark_uid}/"

    # Act
    server.set_dataset_association_approval(benchmark_uid, dataset_uid, status)

    # Assert
    spy.assert_called_once_with(exp_url, status)


@pytest.mark.parametrize("mlcube_uid", [4596, 3530])
@pytest.mark.parametrize("benchmark_uid", [3966, 4188])
@pytest.mark.parametrize("status", [Status.APPROVED.value, Status.REJECTED.value])
def test_set_mlcube_association_approval_sets_approval(
    mocker, server, mlcube_uid, benchmark_uid, status
):
    # Arrange
    res = MockResponse({}, 200)
    spy = mocker.patch(
        patch_server.format("REST._REST__set_approval_status"), return_value=res
    )
    exp_url = f"{full_url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"

    # Act
    server.set_mlcube_association_approval(benchmark_uid, mlcube_uid, status)

    # Assert
    spy.assert_called_once_with(exp_url, status)


def test_get_datasets_associations_gets_associations(mocker, server):
    # Arrange
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=[])
    exp_path = f"{full_url}/me/datasets/associations/"

    # Act
    server.get_datasets_associations()

    # Assert
    spy.assert_called_once_with(exp_path)


def test_get_cubes_associations_gets_associations(mocker, server):
    # Arrange
    spy = mocker.patch(patch_server.format("REST._REST__get_list"), return_value=[])
    exp_path = f"{full_url}/me/mlcubes/associations/"

    # Act
    server.get_cubes_associations()

    # Assert
    spy.assert_called_once_with(exp_path)


@pytest.mark.parametrize("uid", [448, 53, 312])
@pytest.mark.parametrize("body", [{"test": "test"}, {"body": "body"}])
def test_get_result_calls_specified_path(mocker, server, uid, body):
    # Arrange
    res = MockResponse(body, 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_get"), return_value=res)
    exp_path = f"{full_url}/results/{uid}/"

    # Act
    result = server.get_result(uid)

    # Assert
    spy.assert_called_once_with(exp_path)
    assert result == body


@pytest.mark.parametrize("body", [{"benchmark": 1}, {}, {"test": "test"}])
def test_upload_benchmark_returns_benchmark_body(mocker, server, body):
    # Arrange
    res = MockResponse(body, 201)
    mocker.patch(patch_server.format("REST._REST__auth_post"), return_value=res)

    # Act
    exp_body = server.upload_benchmark({})

    # Assert
    assert body == exp_body


@pytest.mark.parametrize("mlcube_uid", [4596, 3530])
@pytest.mark.parametrize("benchmark_uid", [3966, 4188])
@pytest.mark.parametrize("priority", [2, -10])
def test_set_mlcube_association_priority_sets_priority(
    mocker, server, mlcube_uid, benchmark_uid, priority
):
    # Arrange
    res = MockResponse({}, 200)
    spy = mocker.patch(patch_server.format("REST._REST__auth_put"), return_value=res)
    exp_url = f"{full_url}/mlcubes/{mlcube_uid}/benchmarks/{benchmark_uid}/"

    # Act
    server.set_mlcube_association_priority(benchmark_uid, mlcube_uid, priority)

    # Assert
    spy.assert_called_once_with(exp_url, json={"priority": priority})
