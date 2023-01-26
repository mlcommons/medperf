from medperf.commands.list import EntityList
import medperf.commands.list as list_module
from medperf.exceptions import InvalidArgumentError
import pytest
from medperf.entities.interface import Entity


def generate_display_dicts():
    """Mocks a list of dicts to be returned by Entity.display_dict
    """
    return [{f"k{j}": f"v{i}{j}" for j in range(4)} for i in range(3)]


@pytest.fixture()
def setup(request, mocker, ui):
    # system inputs
    display_dicts = request.param["display_dicts"]

    # mocks
    entity_object = mocker.create_autospec(spec=Entity)
    mocker.patch.object(entity_object, "display_dict", side_effect=display_dicts)

    # spies
    generated_entities = [entity_object for _ in display_dicts]
    all_spy = mocker.patch(
        "medperf.entities.interface.Entity.all", return_value=generated_entities
    )
    ui_spy = mocker.patch.object(ui, "print")
    tabulate_spy = mocker.spy(list_module, "tabulate")

    system_inputs = {"display_dicts": display_dicts}
    spies = {"ui": ui_spy, "all": all_spy, "tabulate": tabulate_spy}
    return system_inputs, spies


@pytest.mark.parametrize(
    "setup", [{"display_dicts": generate_display_dicts()}], indirect=True
)
class TestEntityList:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        system_inputs, spies = setup
        self.system_inputs = system_inputs
        self.spies = spies

    @pytest.mark.parametrize("local_only", [False, True])
    @pytest.mark.parametrize("mine_only", [False, True])
    def test_entity_all_is_called_properly(self, local_only, mine_only):
        # Act
        EntityList.run(Entity, [], local_only, mine_only)

        # Assert
        self.spies["all"].assert_called_once_with(
            local_only=local_only, mine_only=mine_only
        )

    @pytest.mark.parametrize(
        "fields,raises", [([], False), (["k1", "k2"], False), (["k1", "k5"], True)]
    )
    def test_exception_raised_for_invalid_input(self, fields, raises):
        # Act & Assert
        if raises:
            with pytest.raises(InvalidArgumentError):
                EntityList.run(Entity, fields)
        else:
            EntityList.run(Entity, fields)

    @pytest.mark.parametrize("fields", [["k1", "k2"], ["k0"]])
    def test_display_calls_tabulate_and_ui_as_expected(self, fields):
        # Arrange
        expected_list = [
            [dict_[field] for field in fields]
            for dict_ in self.system_inputs["display_dicts"]
        ]

        # Act
        EntityList.run(Entity, fields)

        # Assert
        self.spies["tabulate"].assert_called_once_with(expected_list, headers=fields)
        tabulate_return = self.spies["tabulate"].return_value
        self.spies["ui"].assert_called_once_with(tabulate_return)
