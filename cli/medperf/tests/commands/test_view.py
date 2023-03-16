import pytest
import yaml
import json
from medperf.entities.interface import Entity
from medperf.exceptions import InvalidArgumentError
from medperf.commands.view import EntityView


def expected_output(entities, format):
    if isinstance(entities, list):
        data = [entity.todict() for entity in entities]
    else:
        data = entities.todict()

    if format == "yaml":
        return yaml.dump(data)
    if format == "json":
        return json.dumps(data)


def generate_entity(id, mocker):
    entity = mocker.create_autospec(spec=Entity)
    mocker.patch.object(entity, "todict", return_value={"id": id})
    return entity


@pytest.fixture
def ui_spy(mocker, ui):
    return mocker.patch.object(ui, "print")


@pytest.fixture(
    params=[{"local": ["1", "2", "3"], "remote": ["4", "5", "6"], "user": ["4"]}]
)
def setup(request, mocker):
    local_ids = request.param.get("local", [])
    remote_ids = request.param.get("remote", [])
    user_ids = request.param.get("user", [])
    all_ids = list(set(local_ids + remote_ids + user_ids))

    local_entities = [generate_entity(id, mocker) for id in local_ids]
    remote_entities = [generate_entity(id, mocker) for id in remote_ids]
    user_entities = [generate_entity(id, mocker) for id in user_ids]
    all_entities = list(set(local_entities + remote_entities + user_entities))

    def mock_all(mine_only=False, local_only=False):
        if mine_only:
            return user_entities
        if local_only:
            return local_entities
        return all_entities

    def mock_get(entity_id):
        if entity_id in all_ids:
            return generate_entity(entity_id, mocker)
        else:
            raise InvalidArgumentError

    mocker.patch.object(Entity, "all", side_effect=mock_all)
    mocker.patch.object(Entity, "get", side_effect=mock_get)

    return local_entities, remote_entities, user_entities, all_entities


class TestViewEntityID:
    def test_view_displays_entity_if_given(self, mocker, setup, ui_spy):
        # Arrange
        entity_id = "1"
        entity = generate_entity(entity_id, mocker)
        output = expected_output(entity, "yaml")

        # Act
        EntityView.run(entity_id, Entity)

        # Assert
        ui_spy.assert_called_once_with(output)

    def test_view_displays_all_if_no_id(self, setup, ui_spy):
        # Arrange
        *_, entities = setup
        output = expected_output(entities, "yaml")

        # Act
        EntityView.run(None, Entity)

        # Assert
        ui_spy.assert_called_once_with(output)


class TestViewFilteredEntities:
    def test_view_displays_local_entities(self, setup, ui_spy):
        # Arrange
        entities, *_ = setup
        output = expected_output(entities, "yaml")

        # Act
        EntityView.run(None, Entity, local_only=True)

        # Assert
        ui_spy.assert_called_once_with(output)

    def test_view_displays_user_entities(self, setup, ui_spy):
        # Arrange
        *_, entities, _ = setup
        output = expected_output(entities, "yaml")

        # Act
        EntityView.run(None, Entity, mine_only=True)

        # Assert
        ui_spy.assert_called_once_with(output)


@pytest.mark.parametrize("entity_id", ["4", None])
@pytest.mark.parametrize("format", ["yaml", "json"])
class TestViewOutput:
    @pytest.fixture
    def output(self, setup, mocker, entity_id, format):
        if entity_id is None:
            *_, entities = setup
            return expected_output(entities, format)
        else:
            entity = generate_entity(entity_id, mocker)
            return expected_output(entity, format)

    def test_view_displays_specified_format(self, entity_id, output, ui_spy, format):
        # Act
        EntityView.run(entity_id, Entity, format=format)

        # Assert
        ui_spy.assert_called_once_with(output)

    def test_view_stores_specified_format(self, entity_id, output, format, fs):
        # Arrange
        filename = "file.txt"

        # Act
        EntityView.run(entity_id, Entity, format=format, output=filename)

        # Assert
        contents = open(filename, "r").read()
        assert contents == output
