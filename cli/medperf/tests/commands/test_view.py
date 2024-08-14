import pytest
from medperf.entities.interface import Entity
from medperf.commands.view import EntityView

PATCH_VIEW = "medperf.commands.view.{}"


@pytest.fixture
def entity(mocker):
    return mocker.create_autospec(Entity)


@pytest.fixture
def entity_view(mocker):
    view_class = EntityView(None, Entity, "", "", "", "")
    return view_class


def test_prepare_with_id_given(mocker, entity_view, entity):
    # Arrange
    entity_view.entity_id = 1
    get_spy = mocker.patch(PATCH_VIEW.format("Entity.get"), return_value=entity)
    all_spy = mocker.patch(PATCH_VIEW.format("Entity.all"), return_value=[entity])

    # Act
    entity_view.prepare()

    # Assert
    get_spy.assert_called_once_with(1)
    all_spy.assert_not_called()
    assert not isinstance(entity_view.data, list)


def test_prepare_with_no_id_given(mocker, entity_view, entity):
    # Arrange
    entity_view.entity_id = None
    entity_view.mine_only = False
    get_spy = mocker.patch(PATCH_VIEW.format("Entity.get"), return_value=entity)
    all_spy = mocker.patch(PATCH_VIEW.format("Entity.all"), return_value=[entity])

    # Act
    entity_view.prepare()

    # Assert
    all_spy.assert_called_once()
    get_spy.assert_not_called()
    assert isinstance(entity_view.data, list)


@pytest.mark.parametrize("unregistered", [False, True])
def test_prepare_with_no_id_calls_all_with_unregistered_properly(
    mocker, entity_view, entity, unregistered
):
    # Arrange
    entity_view.entity_id = None
    entity_view.mine_only = False
    entity_view.unregistered = unregistered
    all_spy = mocker.patch(PATCH_VIEW.format("Entity.all"), return_value=[entity])

    # Act
    entity_view.prepare()

    # Assert
    all_spy.assert_called_once_with(unregistered=unregistered, filters={})


@pytest.mark.parametrize("filters", [{}, {"f1": "v1"}])
@pytest.mark.parametrize("mine_only", [False, True])
def test_prepare_with_no_id_calls_all_with_proper_filters(
    mocker, entity_view, entity, filters, mine_only
):
    # Arrange
    entity_view.entity_id = None
    entity_view.mine_only = False
    entity_view.unregistered = False
    entity_view.filters = filters
    all_spy = mocker.patch(PATCH_VIEW.format("Entity.all"), return_value=[entity])
    mocker.patch(PATCH_VIEW.format("get_medperf_user_data"), return_value={"id": 1})
    if mine_only:
        filters["owner"] = 1

    # Act
    entity_view.prepare()

    # Assert
    all_spy.assert_called_once_with(unregistered=False, filters=filters)
