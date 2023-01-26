from medperf.commands.list import EntityList
import medperf.commands.list as list_module
from medperf.exceptions import InvalidArgumentError
import pytest
from medperf.entities.interface import Entity

"""
Inputs:
    entity_class
    fields
    local_only
    mine_only
Interactions:
    Entity:
        all (1):
            spy how it was called
            mock the return value
        display_dict (multiple):
            no need to spy.
            mock the return value

    ui:
        print (1): spy how it was called
"""


def generate_display_dicts():
    """Generates a list of dicts returned by Entity.display_dict
    """
    return [{f"k{j}": f"v{i}{j}" for j in range(4)} for i in range(3)]


@pytest.fixture()
def setup(request, mocker, ui):
    display_dicts = request.param.get("display_dicts", generate_display_dicts())

    entity_object = mocker.create_autospec(spec=Entity)
    generated_entities = [entity_object for _ in display_dicts]
    all_spy = mocker.patch(
        "medperf.entities.interface.Entity.all", return_value=generated_entities
    )
    mocker.patch.object(entity_object, "display_dict", side_effect=display_dicts)
    ui_spy = mocker.patch.object(ui, "print")
    tabulate_spy = mocker.spy(list_module, "tabulate")

    spies = {"ui": ui_spy, "all": all_spy, "tabulate": tabulate_spy}
    return request.param, spies


@pytest.mark.parametrize(
    "setup", [{"display_dicts": generate_display_dicts()}], indirect=True
)
class TestEntityList:
    @pytest.mark.parametrize("local_only", [False, True])
    @pytest.mark.parametrize("mine_only", [False, True])
    def test_entity_all_is_called_properly(self, setup, local_only, mine_only):
        # Act
        EntityList.run(Entity, [], local_only, mine_only)

        # Assert
        setup[1]["all"].assert_called_once_with(
            local_only=local_only, mine_only=mine_only
        )

    @pytest.mark.parametrize(
        "fields,raises", [([], False), (["k1", "k2"], False), (["k1", "k5"], True)]
    )
    def test_exception_raised_for_invalid_input(self, setup, fields, raises):
        # Act & Assert
        if raises:
            with pytest.raises(InvalidArgumentError):
                EntityList.run(Entity, fields)
        else:
            EntityList.run(Entity, fields)

    @pytest.mark.parametrize("fields", [["k1", "k2"], ["k0"]])
    def test_display_calls_tabulate_and_ui_as_expected(self, setup, fields):
        # Arrange
        expected_list = [
            [dict_[field] for field in fields] for dict_ in setup[0]["display_dicts"]
        ]

        # Act
        EntityList.run(Entity, fields)

        # Assert
        setup[1]["tabulate"].assert_called_once_with(expected_list, headers=fields)
        setup[1]["ui"].assert_called_once_with(setup[1]["tabulate"].return_value)
