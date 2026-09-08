"""The model owner's side of the web UI: the datasets they can run against."""

import types

import pytest

from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
from medperf.tests.mocks.model import TestAssetModel
from medperf.entities.user import User
from medperf.web_ui.common import templates, templates_folder_path
from medperf.web_ui.models.routes import cc_run_status, datasets_to_run

PATCH_ROUTES = "medperf.web_ui.models.routes.{}"

BENCHMARK_UID = 1
MODEL_UID = 4
ME = 7
CC_DATASET = 20
PLAIN_DATASET = 21


def confidential_model(**kwargs):
    """An asset model whose weights never left its owner's machine"""
    return TestAssetModel(
        id=MODEL_UID,
        owner=ME,
        asset={
            "id": 5,
            "name": "asset",
            "asset_hash": "asset_hash",
            "asset_url": "local",
            "state": "OPERATION",
            "is_valid": True,
        },
        **kwargs,
    )


def configured(entity):
    entity.set_cc_config({"storage": {"backend": "mock"}})
    return entity


def operator(cc_configured: bool) -> User:
    """The model owner, with or without somewhere to run workloads"""
    metadata = {"cc": {"operator": {"backend": "mock"}}} if cc_configured else {}
    return User(
        id=ME,
        username="model_owner",
        email="model.owner@example.com",
        first_name="Model",
        last_name="Owner",
        metadata=metadata,
    )


class TestCanRun:
    """Three things have to be in place, and each has an owner"""

    def test_the_model_owner_hears_about_their_own_model_first(self):
        status = cc_run_status(
            confidential_model(), configured(TestDataset(id=CC_DATASET)), operator(True)
        )
        assert not status["can_run"]
        assert "Your model is not configured" in status["reason"]

    def test_an_unconfigured_dataset_is_the_data_owners_to_fix(self):
        status = cc_run_status(
            configured(confidential_model()), TestDataset(id=PLAIN_DATASET), operator(True)
        )
        assert not status["can_run"]
        assert "data owner" in status["reason"]

    def test_a_missing_operator_setup_is_the_model_owners_to_fix(self):
        status = cc_run_status(
            configured(confidential_model()),
            configured(TestDataset(id=CC_DATASET)),
            operator(False),
        )
        assert not status["can_run"]
        assert "workload run settings" in status["reason"]

    def test_everything_in_place_means_the_button_works(self):
        status = cc_run_status(
            configured(confidential_model()),
            configured(TestDataset(id=CC_DATASET)),
            operator(True),
        )
        assert status == {"can_run": True, "reason": ""}


@pytest.fixture()
def benchmark_datasets(mocker, fs):
    """Both of the benchmark's datasets, only one of them confidential"""
    mocker.patch(
        PATCH_ROUTES.format("Benchmark.get_datasets_uids"),
        return_value=[CC_DATASET, PLAIN_DATASET],
    )

    def __dataset(uid):
        dataset = TestDataset(id=uid, name=f"dataset {uid}")
        return configured(dataset) if uid == CC_DATASET else dataset

    mocker.patch(PATCH_ROUTES.format("Dataset.get"), side_effect=__dataset)
    return mocker.patch(PATCH_ROUTES.format("Execution.all"), return_value=[])


def test_every_dataset_is_listed_whether_or_not_it_can_be_run(benchmark_datasets):
    """A greyed-out row says the data owner has not configured theirs yet;
    leaving it out would say the dataset does not exist"""
    # Act
    listed = datasets_to_run(
        configured(confidential_model()),
        {BENCHMARK_UID: TestBenchmark(id=BENCHMARK_UID, name="bmk")},
        [BENCHMARK_UID],
        operator(True),
    )

    # Assert
    assert [dataset.id for dataset in listed[BENCHMARK_UID]] == [
        CC_DATASET,
        PLAIN_DATASET,
    ]
    assert listed[BENCHMARK_UID][0].cc_run_status["can_run"]
    assert not listed[BENCHMARK_UID][1].cc_run_status["can_run"]


def test_an_execution_that_produced_nothing_readable_is_not_a_result(
    mocker, benchmark_datasets, fs
):
    """A run collected by the data owner leaves the model owner an execution
    with nothing in it -- offering to view or report that would be a lie"""
    # Arrange
    execution = TestExecution(
        id=30,
        benchmark=BENCHMARK_UID,
        model=MODEL_UID,
        dataset=CC_DATASET,
        owner=ME,
        created_at="2026-01-01T00:00:00Z",
    )
    fs.create_dir(execution.path)
    execution.mark_as_executed()
    mocker.patch.object(TestExecution, "read_results", return_value=None)
    mocker.patch(PATCH_ROUTES.format("Execution.all"), return_value=[execution])

    # Act
    listed = datasets_to_run(
        configured(confidential_model()),
        {BENCHMARK_UID: TestBenchmark(id=BENCHMARK_UID, name="bmk")},
        [BENCHMARK_UID],
        operator(True),
    )

    # Assert
    result = listed[BENCHMARK_UID][0].result
    assert result["ran"]
    assert not result["results_exist"]


def stub_request():
    """Enough of a request for the template: the mode it renders in, and where
    static files live."""
    state = types.SimpleNamespace(
        ui_mode="evaluation",
        EVALUATION_MODE="evaluation",
        TRAINING_MODE="training",
        task_running=False,
        task=types.SimpleNamespace(formData={}, name=""),
        global_events=[],
        logged_in=True,
        user_email="model.owner@example.com",
        notifications=[],
        unread_count=0,
        MAXLOGMESSAGES=100,
    )
    app = types.SimpleNamespace(state=state)
    return types.SimpleNamespace(
        app=app,
        url=types.SimpleNamespace(path="/models/ui/display/4"),
        url_for=lambda name, **kwargs: "/static/" + kwargs.get("path", ""),
    )


def render_model_detail(datasets, requires_cc=True):
    model = configured(confidential_model())
    model._encrypted = False
    model._requires_cc = requires_cc
    asset = model.asset_obj
    asset._is_local = True
    return templates.get_template("model/model_detail.html").render(
        request=stub_request(),
        entity=model,
        entity_is_container=False,
        container_object=None,
        asset_object=asset,
        entity_name=model.name,
        is_owner=True,
        benchmarks_associations={
            BENCHMARK_UID: {"benchmark": BENCHMARK_UID, "approval_status": "APPROVED"}
        },
        benchmarks={BENCHMARK_UID: TestBenchmark(id=BENCHMARK_UID, name="bmk")},
        approved_benchmarks=[BENCHMARK_UID],
        benchmark_datasets={BENCHMARK_UID: datasets},
        cc_config_defaults={},
        cc_policy={},
        cc_backends={"storage": {}, "vault": {}},
        cc_backend={"storage": None, "vault": None},
        cc_settings={"storage": {}, "vault": {}},
        cc_field_label=lambda *args, **kwargs: "",
        cc_configured=True,
        cc_initialized=True,
        cc_last_synced=None,
        task_running=False,
    )


@pytest.fixture()
def real_templates(fs):
    fs.add_real_directory(templates_folder_path)


def listed_dataset(uid, can_run, reason=""):
    dataset = TestDataset(id=uid, name=f"dataset {uid}")
    dataset.cc_run_status = {"can_run": can_run, "reason": reason}
    dataset.result = None
    return dataset


def is_disabled(html, button_id):
    """Whether that button carries the `disabled` attribute.

    Read off the end of the tag rather than searched for: `disabled:` is also
    the prefix of a styling class every one of these buttons carries."""
    attributes = html.split(f'id="{button_id}"')[1].split(">")[0]
    return attributes.rstrip().endswith("disabled")


def test_the_run_button_is_disabled_for_a_dataset_that_cannot_be_run(real_templates):
    # Act
    html = render_model_detail(
        [
            listed_dataset(CC_DATASET, can_run=True),
            listed_dataset(
                PLAIN_DATASET, can_run=False, reason="Wait for the data owner"
            ),
        ]
    )

    # Assert
    assert not is_disabled(html, f"run-{BENCHMARK_UID}-{CC_DATASET}")
    assert is_disabled(html, f"run-{BENCHMARK_UID}-{PLAIN_DATASET}")
    assert "Wait for the data owner" in html


def test_run_all_only_carries_the_datasets_that_can_be_run(real_templates):
    """Posting a dataset the run would refuse anyway just fails slower"""
    # Act
    html = render_model_detail(
        [
            listed_dataset(CC_DATASET, can_run=True),
            listed_dataset(PLAIN_DATASET, can_run=False),
        ]
    )

    # Assert
    run_all = html.split('id="run-all-1-form"')[1].split("</form>")[0]
    assert f'name="data_ids" value="{CC_DATASET}"' in run_all
    assert f'name="data_ids" value="{PLAIN_DATASET}"' not in run_all


def test_a_model_that_does_not_run_confidentially_gets_no_dataset_list(
    real_templates,
):
    """There is nothing for its owner to run: somebody else's data is not
    theirs to point a model at"""
    # Act
    html = render_model_detail(
        [listed_dataset(CC_DATASET, can_run=True)], requires_cc=False
    )

    # Assert
    assert 'data-testid="benchmark-datasets"' not in html
    assert 'action="/models/run"' not in html


def test_every_run_form_goes_through_the_cost_warning(real_templates):
    """`model-run-form` is what model_detail.js binds the "this will incur
    costs to your cloud provider" prompt to"""
    # Act
    html = render_model_detail([listed_dataset(CC_DATASET, can_run=True)])

    # Assert
    assert html.count('action="/models/run"') == html.count(
        'class="inline model-run-form"'
    )


def test_run_all_is_disabled_when_nothing_can_be_run(real_templates):
    """It would post an empty list of datasets otherwise"""
    # Act
    html = render_model_detail([listed_dataset(PLAIN_DATASET, can_run=False)])

    # Assert
    assert is_disabled(html, f"run-all-{BENCHMARK_UID}")
