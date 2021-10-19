from medperf.entities import Benchmark
from medperf.entities import Server
from medperf.config import config
from medperf.tests.mocks import requests as mock_requests
import medperf

benchmark_uid = 1


def mocked_get_responses(*args, **kwargs):
    base_url = f"{config['server']}/benchmarks"
    if args[0] == f"{base_url}/{benchmark_uid}":
        body = mock_requests.benchmark_body(benchmark_uid)
        return mock_requests.MockResponse(body, 200)
    elif args[0] == f"{base_url}/{benchmark_uid}/models":
        body = [mock_requests.cube_body(4)]
        return mock_requests.MockResponse(body, 200)


def test_get(mocker):
    """Can retrieve benchmarks from the server, and all get calls are authenticated
    """
    server = Server(config["server"])
    server.token = "123"
    mocker.patch(
        "medperf.entities.server.requests.get", side_effect=mocked_get_responses
    )
    get_spy = mocker.spy(medperf.entities.server.requests, "get")
    auth_spy = mocker.spy(Server, "_Server__auth_req")
    benchmark = Benchmark.get(benchmark_uid, server)
    assert type(benchmark) is Benchmark and benchmark.uid == benchmark_uid
    assert get_spy.call_count > 0
    assert get_spy.call_count == auth_spy.call_count


def test_models_uids(mocker):
    """Retrieves a list of model uids related to the benchmark
    """
    server = Server(config["server"])
    server.token = "123"
    mocker.patch(
        "medperf.entities.server.requests.get", side_effect=mocked_get_responses
    )
    uids = Benchmark.get_models_uids(benchmark_uid, server)
    assert len(uids) == 1 and uids[0] == 4
