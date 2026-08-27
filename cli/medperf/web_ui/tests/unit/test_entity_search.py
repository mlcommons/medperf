import requests

from medperf.web_ui.auth import AUTH_COOKIE_NAME
from medperf.web_ui.tests import config as tests_config

BASE_URL = tests_config.BASE_URL
PATCH_GET_USER_DATA = "medperf.web_ui.entity_search.get_medperf_user_data"


class _Entity:
    def __init__(
        self, id, name, owner=1, address=None, port=None, container_config=None
    ):
        self.id = id
        self.name = name
        self.owner = owner
        self.address = address
        self.port = port
        self.container_config = container_config or {}


def _search(sec_token, **params):
    return requests.get(
        BASE_URL.format("/api/entity_search"),
        params=params,
        cookies={AUTH_COOKIE_NAME: sec_token},
    )


def test_entity_search_requires_auth():
    resp = requests.get(
        BASE_URL.format("/api/entity_search"),
        params={"entity_type": "container", "q": "ab"},
    )
    assert resp.status_code == 401


def test_entity_search_unknown_entity_type(sec_token):
    resp = _search(sec_token, entity_type="bogus", q="ab")
    assert resp.status_code == 200
    assert resp.json() == {"results": [], "error": "Unknown entity type: bogus"}


def test_entity_search_query_too_short_returns_hint(sec_token):
    resp = _search(sec_token, entity_type="container", q="a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["hint"] == "Type at least 2 characters to search"


def test_entity_search_benchmark_results_shape(sec_token, mocker):
    mocker.patch(
        "medperf.entities.benchmark.Benchmark.all",
        return_value=[_Entity(id=1, name="bmk1")],
    )
    resp = _search(sec_token, entity_type="benchmark", q="bmk")
    assert resp.json() == {
        "results": [{"id": 1, "name": "bmk1", "label": "bmk1 (ID: 1)"}]
    }


def test_entity_search_aggregator_label_includes_address_and_port(sec_token, mocker):
    mocker.patch(
        "medperf.entities.aggregator.Aggregator.all",
        return_value=[_Entity(id=5, name="agg1", address="127.0.0.1", port=7000)],
    )
    resp = _search(sec_token, entity_type="aggregator", q="agg")
    assert resp.json() == {
        "results": [{"id": 5, "name": "agg1", "label": "agg1 (ID: 5) (127.0.0.1:7000)"}]
    }


def test_entity_search_mine_only_filters_by_owner(sec_token, mocker):
    mocker.patch(PATCH_GET_USER_DATA, return_value={"id": 7})
    spy = mocker.patch("medperf.entities.cube.Cube.all", return_value=[])
    _search(sec_token, entity_type="container", q="ab", mine_only=True)
    assert spy.call_args.kwargs["filters"]["owner"] == 7


def test_entity_search_mine_only_false_does_not_call_get_medperf_user_data(
    sec_token, mocker
):
    spy_user = mocker.patch(
        PATCH_GET_USER_DATA, side_effect=AssertionError("should not be called")
    )
    mocker.patch("medperf.entities.cube.Cube.all", return_value=[])
    resp = _search(sec_token, entity_type="container", q="ab", mine_only=False)
    assert resp.status_code == 200
    spy_user.assert_not_called()


def test_entity_search_selected_id_bypasses_query_length_and_mine_only(
    sec_token, mocker
):
    spy_get = mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=_Entity(id=9, name="cont9")
    )
    spy_user = mocker.patch(
        PATCH_GET_USER_DATA, side_effect=AssertionError("should not be called")
    )
    resp = _search(sec_token, entity_type="container", selected_id=9, mine_only=True)
    assert resp.json() == {
        "results": [{"id": 9, "name": "cont9", "label": "cont9 (ID: 9)"}]
    }
    spy_get.assert_called_once_with(9)
    spy_user.assert_not_called()


def test_entity_search_selected_id_not_in_allowed_ids_returns_empty(sec_token, mocker):
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=_Entity(id=9, name="cont9")
    )
    resp = _search(sec_token, entity_type="container", selected_id=9, ids="1,2,3")
    assert resp.json() == {"results": []}


def test_entity_search_selected_id_not_found_returns_empty_results(sec_token, mocker):
    mocker.patch("medperf.entities.cube.Cube.get", side_effect=Exception("not found"))
    resp = _search(sec_token, entity_type="container", selected_id=999)
    assert resp.json() == {"results": []}


def test_entity_search_allowed_ids_filters_query_results(sec_token, mocker):
    mocker.patch(
        "medperf.entities.cube.Cube.all",
        return_value=[_Entity(id=1, name="a"), _Entity(id=2, name="b")],
    )
    resp = _search(sec_token, entity_type="container", q="ab", ids="2")
    assert resp.json() == {"results": [{"id": 2, "name": "b", "label": "b (ID: 2)"}]}


def test_entity_search_container_type_data_prep_filter(sec_token, mocker):
    prep = _Entity(
        id=1,
        name="prep",
        container_config={"tasks": {"prepare": {}, "sanity_check": {}}},
    )
    metrics = _Entity(
        id=2, name="metrics", container_config={"tasks": {"evaluate": {}}}
    )
    mocker.patch("medperf.entities.cube.Cube.all", return_value=[prep, metrics])
    resp = _search(
        sec_token, entity_type="container", q="ab", container_type="data-prep-container"
    )
    ids = [item["id"] for item in resp.json()["results"]]
    assert ids == [1]


def test_entity_search_container_type_non_data_prep_filter(sec_token, mocker):
    # "non-data-prep-container" means anything that ISN'T a data-prep container,
    # including containers whose type can't be determined at all.
    prep = _Entity(
        id=1,
        name="prep",
        container_config={"tasks": {"prepare": {}, "sanity_check": {}}},
    )
    metrics = _Entity(
        id=2, name="metrics", container_config={"tasks": {"evaluate": {}}}
    )
    unknown = _Entity(id=3, name="unknown", container_config={})
    mocker.patch(
        "medperf.entities.cube.Cube.all", return_value=[prep, metrics, unknown]
    )
    resp = _search(
        sec_token,
        entity_type="container",
        q="ab",
        container_type="non-data-prep-container",
    )
    ids = sorted(item["id"] for item in resp.json()["results"])
    assert ids == [2, 3]


def test_entity_search_limit_rejected_out_of_range(sec_token):
    resp = _search(sec_token, entity_type="container", q="ab", limit=51)
    assert resp.status_code == 422

    resp = _search(sec_token, entity_type="container", q="ab", limit=0)
    assert resp.status_code == 422
