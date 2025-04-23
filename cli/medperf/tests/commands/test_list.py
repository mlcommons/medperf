from medperf.commands.list import EntityList
import medperf.commands.list as list_module
from medperf.exceptions import InvalidArgumentError
import pytest
from medperf.entities.interface import Entity


def generate_display_dicts():
    """Mocks a list of dicts to be returned by Entity.display_dict"""
    return [
        {"UID": 1, "Registered": True, "Is Valid": False, "Benchmark": 4},
        {"UID": 2, "Registered": True, "Is Valid": False, "Benchmark": 1},
        {"UID": 3, "Registered": False, "Is Valid": True, "Benchmark": 7},
    ]


@pytest.fixture()
def setup(request, mocker, ui):
    # system inputs
    display_dicts = request.param["display_dicts"]

    # mocks
    entity_object = mocker.create_autospec(spec=Entity)
    mocker.patch.object(entity_object, "display_dict", side_effect=display_dicts)
    mocker.patch("medperf.commands.list.get_medperf_user_data", return_value={"id": 1})

    # spies
    generated_entities = [entity_object for _ in display_dicts]
    all_spy = mocker.patch(
        "medperf.entities.interface.Entity.all", return_value=generated_entities
    )
    ui_spy = mocker.patch.object(ui, "print")
    tabulate_spy = mocker.spy(list_module, "tabulate")

    state_variables = {"display_dicts": display_dicts}
    spies = {"ui": ui_spy, "all": all_spy, "tabulate": tabulate_spy}
    return state_variables, spies


@pytest.mark.parametrize(
    "setup", [{"display_dicts": generate_display_dicts()}], indirect=True
)
class TestEntityList:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        state_variables, spies = setup
        self.state_variables = state_variables
        self.spies = spies

    @pytest.mark.parametrize("unregistered", [False, True])
    @pytest.mark.parametrize("mine_only", [False, True])
    def test_entity_all_is_called_properly(self, mocker, unregistered, mine_only):
        # Arrange
        filters = {"owner": 1} if mine_only else {}

        # Act
        EntityList.run(Entity, [], unregistered, mine_only)

        # Assert
        self.spies["all"].assert_called_once_with(
            unregistered=unregistered, filters=filters
        )

    @pytest.mark.parametrize("fields", [["UID", "MLCube"]])
    def test_exception_raised_for_invalid_input(self, fields):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            EntityList.run(Entity, fields)
